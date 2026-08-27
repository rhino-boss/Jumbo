"""C027 數學模型擬合工具.

C027 與 H027 的差別（每一項都是可驗證的）
----------------------------------------
1. **場景表混合**：每個場景兩張子輪帶表，每一轉獨立抽表，因此
   `P(有球)`、`Hit Rate`、`Hit Rate|有球`、`Hit Rate|無球` 可以同時對齊。
   H027 只有單張表，這四個量互相打死。模型見 `c027_scene_model.py`。
2. **≥10x 走 C3 路徑**：`game_rule.md` §6.1 規定 10x 以上不得由 C2 一般池抽出，
   必須走 Super Multiplier；H027 的 config 把 500x 直接放進 C2 池，違反規則。
   C027 用 `use_super_multiplier` ＋ 每場景 `c3` 權重實作，並因此拿到
   §6.2 的「每次消除 C3 升一級」尾端（最高 2500x）。
3. **BF 入口獨立輪帶**：開發規範 §1.2.1 要求 `BF_Symbol` 專用且入口盤面
   不得產生任何 BG 得分。C027 的 `BF_Symbol` 每 5 格視窗內同一般符號不重複，
   單一符號最多 6 個，數學上不可能達到 Any-8。
4. **RTP 拆分依競品比例縮放**：H027 把競品「小樣本量到的 BG RTP 59.763%」
   當成設計目標，導致 FG 週期與 FG 平均倍數只能對一個。C027 改成
   維持競品的 BG:FG 比例（70.616% : 29.384%）再縮放到版本標籤，
   FG 週期照競品對齊，FG 平均倍數自然落在競品之上。
5. **卡片多維條件**：`ball` 維度讓 Card System 直接鎖住倍數球出現率，
   H027 的 Card-On BG 倍數球率被得分區間選樣放大到 9.6%（競品 2.737%）。

用法
----
    py fit_c027_model.py --strips        # 解場景混合並寫入七張輪帶表
    py fit_c027_model.py --cards         # 跑自然基準並校準 Card System
    py fit_c027_model.py --strips --cards
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from c027_scene_model import (
    C1_INDEX, NORMAL_SYMBOLS, REELS, SYMBOL_INDEX, SYMBOL_ORDER,
    build_sub_reels, mixture_metrics, sample_hit, solve_theta_for_hit,
    sub_board_sample, sub_symbol_counts,
)
from competitor_targets import SCENES, Targets
from strip_model import largest_remainder

ROOT = Path(__file__).resolve().parent.parent
OTHER = ROOT / "其他"
RECORD = ROOT / "Record"
CONFIG_BASE = ROOT / "config.js"
CONFIG_VARIANTS = [ROOT / "config_92A.js", ROOT / "config_94A.js"]

TARGETS = Targets()

# ---------------------------------------------------------------- table layout

BF_ENTRY_TABLE = "BF_Symbol"
SCENE_TABLES = {
    "BG": ["BG_Symbol", "BG_Symbol (2)"],          # A = 有球場景, B = 無球場景
    "FG": ["FG_Symbol", "FG_Symbol (2)"],
    "BF": ["FG_Symbol (3)", "FG_Symbol (4)"],
}
TABLE_ORDER = [BF_ENTRY_TABLE] + SCENE_TABLES["BG"] + SCENE_TABLES["FG"] + SCENE_TABLES["BF"]
TABLE_SCENE = {BF_ENTRY_TABLE: "BF"}
for _scene, _names in SCENE_TABLES.items():
    for _name in _names:
        TABLE_SCENE[_name] = _scene

STRIP_LENGTH = 1080
# 競品的 ≥10x 倍率一律走 C3；C2 一般池只保留 8x 以下（game_rule §6.1）
C2_VALUES = [2, 3, 4, 5, 6, 8]
C3_VALUES = [10, 12, 15, 20, 25, 50, 100, 250, 500]
ALL_MULTIPLIER_VALUES = C2_VALUES + C3_VALUES

# 競品實測 BG:FG RTP 比例，用來把 RTP 拆分縮放到版本標籤
COMPETITOR_FG_RTP_SHARE = TARGETS.basic["fg_rtp"] / TARGETS.basic["total_rtp"]


# --------------------------------------------------------------------------- io

def load_js(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    start, end = text.index("{"), text.rindex("}")
    return json.loads(text[start:end + 1]), text[:start]


def write_js(path: Path, data: dict, prefix: str) -> None:
    path.write_text(prefix + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def cumulative(values) -> list[int]:
    total = 0
    out = []
    for value in values:
        total += int(value)
        out.append(total)
    return out


# ------------------------------------------------------------- scene mixture

def scene_c2_share(scene: str) -> dict[str, float]:
    return {reel: TARGETS.initial[scene][reel]["C2"] for reel in REELS}


def initial_ball_target(scene: str) -> float:
    """P(initial board holds a ball) that the strips must produce.

    Two competitor numbers describe the same thing on different denominators:
    §3.2.1 gives the C2 share of the initial reel window and §5.1.1 gives the share
    of spins that show a ball.  Combined with the balls-per-spin distribution
    (§5.1.1) the marginal implies `30 * share / mean_balls_given_ball`.  Cascade
    drop-ins can only push the measured per-spin rate up, so the strip target is
    the lower of the two.
    """
    share = float(np.mean([TARGETS.initial[scene][reel]["C2"] for reel in REELS]))
    distribution = TARGETS.ball_count_dist[scene]
    mean_given_ball = sum((index + 1) * value for index, value in enumerate(distribution))
    from_marginal = 30.0 * share / mean_given_ball if mean_given_ball > 0 else 0.0
    return min(from_marginal, TARGETS.ball_spin_rate[scene])


DROP_GAIN_PATH = OTHER / "fit_drop_gain.json"


def load_drop_gain() -> dict[str, float]:
    """P(a winning ball-free spin gains a ball from a cascade drop), per scene.

    Written by `--measure-drop` from a Card-Off run.  Empty means "not measured
    yet", in which case the strips are solved against the raw competitor values.
    """
    if not DROP_GAIN_PATH.is_file():
        return {}
    return {key: float(value) for key, value in
            json.loads(DROP_GAIN_PATH.read_text(encoding="utf-8")).items()}


def solve_drop_gain(ball_initial: float, ball_final: float, hit_no_ball_final: float) -> float:
    """Invert the drop-in identity for `d`.

    A ball can only drop in during a cascade, i.e. only on a winning spin, so the
    migration is one-way: winning spins that started ball-free move into the
    "has ball" bucket.  With `b_i` the initial-board ball rate and `d` the chance a
    winning ball-free spin gains one:

        ball_final          = b_i + (1 - b_i) * hit_no_ball_initial * d
        hit_no_ball_final   = hit_no_ball_initial * (1 - d) * (1 - b_i) / (1 - ball_final)

    Dividing the two removes `hit_no_ball_initial` and leaves a closed form for `d`.
    """
    numerator = ball_final - ball_initial
    denominator = hit_no_ball_final * (1.0 - ball_final)
    if numerator <= 0 or denominator <= 0:
        return 0.0
    ratio = numerator / denominator
    return ratio / (1.0 + ratio)


def drop_corrected_targets(scene: str, drop_gain: float) -> dict[str, float]:
    """Initial-board targets whose *final* board reproduces the competitor values.

    The competitor's §5.1.1 / §5.2.1 numbers are measured on the final board, but
    the strips only control the initial board.  Solving the drop-in identity
    backwards gives the initial-board triple the annealer should aim at.  Without
    this correction the drop-ins push `hit | ball` well above target (measured:
    40.2% initial becomes 52.9% final) and pull `hit | no ball` below it.
    """
    conditional = TARGETS.conditional_symbol_hit(scene)
    ball_final = TARGETS.ball_spin_rate[scene]
    hit_ball_final = conditional["with"]
    hit_no_ball_final = conditional["without"]
    if drop_gain <= 0:
        return {"ball": initial_ball_target(scene), "with": hit_ball_final,
                "without": hit_no_ball_final, "drop_gain": 0.0}
    no_ball_mass = hit_no_ball_final * (1.0 - ball_final) / (1.0 - drop_gain)
    ball_initial = ball_final - no_ball_mass * drop_gain
    if not 0.0 < ball_initial < ball_final:
        raise ValueError(f"{scene}: drop_gain={drop_gain:.4f} gives an infeasible initial ball rate")
    hit_no_ball_initial = no_ball_mass / (1.0 - ball_initial)
    hit_ball_initial = (hit_ball_final * ball_final - (ball_final - ball_initial)) / ball_initial
    if not 0.0 < hit_ball_initial < 1.0:
        raise ValueError(f"{scene}: drop_gain={drop_gain:.4f} gives an infeasible hit|ball")
    return {"ball": ball_initial, "with": hit_ball_initial,
            "without": hit_no_ball_initial, "drop_gain": drop_gain}


def solve_scene(scene: str, c2_counts: list[int], seed: int, max_run: int,
                iterations: int, rounds: int, verbose: bool = True) -> dict:
    """Solve one scene's two-table mixture.

    For each candidate C2 cell count of the ball-carrying A table:

    1. bisect `theta_A` so A's `hit | ball` equals the competitor value;
    2. read A's measured `P(ball)` and set `w_A = P(ball target) / P(ball | A)`;
    3. solve the B table's required unconditional hit rate from the mixture
       identity for `hit | no ball`, then bisect `theta_B` onto it.

    The candidate with the smallest weighted error over
    (P(ball), hit, hit|ball, hit|no ball) wins.
    """
    marginals = TARGETS.initial[scene]
    corrected = drop_corrected_targets(scene, load_drop_gain().get(scene, 0.0))
    conditional = {"with": corrected["with"], "without": corrected["without"]}
    ball_target = corrected["ball"]
    hit_target = TARGETS.initial_hit_target(scene)
    if verbose:
        print(f"    initial-board targets (drop_gain={corrected['drop_gain']:.4f}): "
              f"ball={ball_target:.4%} hit={hit_target:.4%} "
              f"hit|ball={conditional['with']:.4%} hit|no={conditional['without']:.4%}")

    best = None
    for candidate in c2_counts:
        solved_a = solve_theta_for_hit(marginals, STRIP_LENGTH, candidate, conditional["with"],
                                       seed, max_run, iterations, rounds=rounds, condition="ball")
        sample_a = solved_a["sample"]
        p_ball_a = float((sample_a["balls"] >= 1).mean())
        if p_ball_a <= 0:
            continue
        weight_a = ball_target / p_ball_a
        if not 0.0 < weight_a <= 0.985:
            if verbose:
                print(f"    c2_A={candidate:>3}  skipped (w_A={weight_a:.4f} out of range)")
            continue
        hit_a_no_ball = sample_hit(sample_a, "no_ball")
        required = conditional["without"] * (1.0 - ball_target) - weight_a * (1.0 - p_ball_a) * hit_a_no_ball
        hit_b_target = required / (1.0 - weight_a)
        if not 0.01 <= hit_b_target <= 0.95:
            if verbose:
                print(f"    c2_A={candidate:>3}  skipped (B table would need hit={hit_b_target:.4%})")
            continue
        solved_b = solve_theta_for_hit(marginals, STRIP_LENGTH, 0, hit_b_target,
                                       seed + 37, max_run, iterations, rounds=rounds)
        metrics = mixture_metrics([sample_a, solved_b["sample"]], [weight_a, 1.0 - weight_a])
        # balls per spin (§5.1.1) is what picks between candidates: a higher C2 cell
        # count keeps the same overall ball rate but piles two and three balls onto
        # the same board, which the competitor does not do.
        ball_dist_error = sum(
            abs(metrics["ball_counts"][index] - target)
            for index, target in enumerate(TARGETS.ball_count_dist[scene])
        )
        error = (2.0 * abs(metrics["ball_present"] - ball_target)
                 + 3.0 * abs(metrics["hit"] - hit_target)
                 + abs(metrics["hit_given_ball"] - conditional["with"])
                 + abs(metrics["hit_given_no_ball"] - conditional["without"])
                 + 0.5 * ball_dist_error)
        if verbose:
            counts = "/".join(f"{value:.1%}" for value in metrics["ball_counts"][:3])
            print(f"    c2_A={candidate:>3}  w_A={weight_a:7.4%}  theta=({solved_a['theta']:.3f},"
                  f"{solved_b['theta']:.3f})  ball={metrics['ball_present']:.4%}"
                  f"  hit={metrics['hit']:.4%}  hit|ball={metrics['hit_given_ball']:.4%}"
                  f"  hit|no={metrics['hit_given_no_ball']:.4%}  balls {counts}"
                  f"  err={error:.5f}")
        if best is None or error < best["error"]:
            best = {
                "c2_count": candidate,
                "weight_a": weight_a,
                "theta": [solved_a["theta"], solved_b["theta"]],
                "reels": [solved_a["reels"], solved_b["reels"]],
                "metrics": metrics,
                "error": error,
                "ball_target": ball_target,
                "drop_gain": corrected["drop_gain"],
            }
    if best is None:
        raise ValueError(f"{scene}: no feasible C2 count in {c2_counts}")
    return best


# ------------------------------------------------------- Buy Feature entry reel

def build_bf_entry_reels(seed: int) -> list[list[str]]:
    """A strip where no five consecutive cells repeat a normal symbol.

    Any board therefore holds at most one copy of a given normal symbol per reel,
    i.e. at most six in total, so the Buy Feature entry can never reach Any-8.
    C1 keeps the >= 6 circular spacing rule; C2 is excluded so the entry board
    cannot hand out a free multiplier either.
    """
    rng = np.random.default_rng(seed)
    length = 66  # 6 blocks of 11 distinct symbols keeps every 5-window clean
    reels = []
    for reel_index in range(6):
        while True:
            sequence: list[str] = []
            for _ in range(length // len(NORMAL_SYMBOLS)):
                block = list(NORMAL_SYMBOLS)
                rng.shuffle(block)
                sequence.extend(block)
            # place the scatters by replacing one cell in every 11-cell block so the
            # circular spacing is >= 6 by construction
            for block_index in range(0, len(sequence), 22):
                position = block_index + int(rng.integers(0, 3))
                if position < len(sequence):
                    sequence[position] = "C1"
            if _windows_are_clean(sequence) and _scatter_spacing_ok(sequence, 6):
                reels.append(sequence)
                break
    return reels


def _windows_are_clean(sequence: list[str]) -> bool:
    length = len(sequence)
    for start in range(length):
        window = [sequence[(start + offset) % length] for offset in range(5)]
        normal = [code for code in window if code in NORMAL_SYMBOLS]
        if len(normal) != len(set(normal)):
            return False
    return True


def _scatter_spacing_ok(sequence: list[str], gap: int) -> bool:
    length = len(sequence)
    positions = [index for index, code in enumerate(sequence) if code == "C1"]
    if len(positions) < 2:
        return True
    gaps = [(positions[(i + 1) % len(positions)] - positions[i]) % length for i in range(len(positions))]
    return min(gaps) >= gap


# ---------------------------------------------------------------- config write

def drop_weights_for(scene: str, symbol_ids: dict[str, int], symbol_count: int) -> list[list[int]]:
    """Competitor drop marginal, identical for both sub-tables of a scene.

    Sharing the drop table is what keeps the pooled drop distribution exact no
    matter how the mixture weights move.
    """
    drop = [[0] * 6 for _ in range(symbol_count)]
    for reel_index, reel in enumerate(REELS):
        probabilities = [TARGETS.drop[scene][reel].get(code, 0.0) for code in SYMBOL_ORDER]
        weights = largest_remainder(probabilities, 1_000_000)
        for code, weight in zip(SYMBOL_ORDER, weights):
            drop[symbol_ids[code] - 1][reel_index] = weight
    return drop


def make_strip(reels: list[list[str]], scene: str, symbol_ids: dict[str, int], symbol_count: int) -> dict:
    length = len(reels[0])
    return {
        "symbols": [[symbol_ids[reels[reel][row]] for reel in range(6)] for row in range(length)],
        "weights": [[1] * 6 for _ in range(length)],
        "drop_weights": drop_weights_for(scene, symbol_ids, symbol_count),
        "reel_lengths": [length] * 6,
        "linked_stop_weight": 0,
        "linked_stop_denominator": 10000,
        "linked_stop_offsets": [0] * 6,
    }


def multiplier_weight_blocks(levels: list[int]) -> dict:
    """Split the competitor multiplier distribution into the C2 pool and the C3 pool.

    `use_super` is the per-scene probability (per 10,000) that a ball candidate turns
    into a Super Multiplier; it equals the competitor's P(value >= 10x).  Rule §6.1
    also requires the probability to rise with the initial ball count, so the six
    ball-count columns are scaled around that mean.
    """
    ramp = np.array([0.80, 0.95, 1.10, 1.25, 1.40, 1.55])
    out = {}
    for scene in SCENES:
        share = dict(zip([2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 250, 500],
                         TARGETS.multiplier_dist[scene]))
        c2_mass = sum(share[value] for value in C2_VALUES)
        c3_mass = sum(share[value] for value in C3_VALUES)
        total = c2_mass + c3_mass
        use_super = c3_mass / total if total > 0 else 0.0
        columns = np.clip(ramp * use_super, 0.0, 1.0)
        # keep the ball-count-weighted mean on target: almost every ball spin sits in
        # the 1-ball column, so normalising on the first column is enough
        columns = columns * (use_super / columns[0]) if columns[0] > 0 else columns
        columns = np.clip(columns, 0.0, 1.0)
        out[scene] = {
            "use_super": [int(round(value * 10_000)) for value in columns],
            "c2": _slot_weights(levels, {v: share[v] for v in C2_VALUES}),
            "c3": _slot_weights(levels, {v: share[v] for v in C3_VALUES}),
        }
    return out


def _slot_weights(levels: list[int], share: dict[int, float], total: int = 10_000) -> list[int]:
    """Put a value->probability map onto the multiplier ladder.

    A value can repeat in `multiplier_levels` (the 2500x plateau); only the first
    slot of a value carries weight so the draw stays unambiguous.
    """
    slots, probabilities, seen = [], [], set()
    for index, value in enumerate(levels):
        if value in share and value not in seen:
            seen.add(value)
            slots.append(index)
            probabilities.append(share[value])
    weights = [0] * len(levels)
    if not slots or sum(probabilities) <= 0:
        return weights
    for index, weight in zip(slots, largest_remainder(probabilities, total)):
        weights[index] = weight
    return weights


def apply_strip_stage(solved: dict, bf_reels: list[list[str]], plan: dict) -> None:
    base, prefix = load_js(CONFIG_BASE)
    symbol_ids = dict(zip(base["symbol_codes"], base["symbol_ids"]))
    symbol_count = len(base["symbol_ids"])
    levels = list(base["multiplier_levels"])

    strips, names = [], []
    names.append(BF_ENTRY_TABLE)
    strips.append(make_strip(bf_reels, "BF", symbol_ids, symbol_count))
    for scene, table_names in SCENE_TABLES.items():
        for sub_index, name in enumerate(table_names):
            names.append(name)
            strips.append(make_strip(solved[scene]["reels"][sub_index], scene, symbol_ids, symbol_count))
    base["strip_names"] = names
    base["strips"] = strips
    base["strip_length"] = STRIP_LENGTH

    blocks = multiplier_weight_blocks(levels)
    normal = base["parameter"]["normal"]
    feature = base["parameter"]["featurebuy"]

    bg_weight_a = solved["BG"]["weight_a"]
    normal["base_reel_names"] = SCENE_TABLES["BG"]
    bg_weights = _weight_pair(bg_weight_a)
    normal["base_reel_weights"] = bg_weights
    normal["base_reel_weights_cum"] = cumulative(bg_weights)
    feature["base_reel_names"] = [BF_ENTRY_TABLE]
    feature["base_reel_weights"] = [1]
    feature["base_reel_weights_cum"] = [1]

    normal["free_table"] = _free_table(SCENE_TABLES["FG"], solved["FG"]["weight_a"])
    feature["free_table"] = _free_table(SCENE_TABLES["BF"], solved["BF"]["weight_a"])

    for profile in (normal, feature):
        profile["c2"]["multipliers"] = levels
        profile["c3"]["multipliers"] = levels
        profile["c2"]["table_names"] = names
        profile["c3"]["table_names"] = names
        profile["c2"]["weights"] = {}
        profile["c2"]["weights_cum"] = {}
        profile["c3"]["weights"] = {}
        profile["c3"]["weights_cum"] = {}
        profile["use_super_multiplier"]["table_names"] = names
        profile["use_super_multiplier"]["initial_ball_counts"] = [1, 2, 3, 4, 5, 6]
        profile["use_super_multiplier"]["denominator"] = 10_000
        profile["use_super_multiplier"]["weights_by_initial_ball_count"] = {}
        for name in names:
            scene = TABLE_SCENE[name]
            block = blocks[scene]
            profile["c2"]["weights"][name] = block["c2"]
            profile["c2"]["weights_cum"][name] = cumulative(block["c2"])
            profile["c3"]["weights"][name] = block["c3"]
            profile["c3"]["weights_cum"][name] = cumulative(block["c3"])
            profile["use_super_multiplier"]["weights_by_initial_ball_count"][name] = block["use_super"]

    base["parameter"]["super_multiplier"]["multipliers"] = levels
    base["parameter"]["super_multiplier"]["weights"] = {"Super Ball": blocks["BG"]["c3"]}
    base["parameter"]["super_multiplier"]["weights_cum"] = {"Super Ball": cumulative(blocks["BG"]["c3"])}

    base["scene_mixture"] = {
        "model": "two-table scene mixture (see 其他/c027_scene_model.py)",
        "strip_length": STRIP_LENGTH,
        "max_run": plan["max_run"],
        "tables": {
            scene: {
                "names": SCENE_TABLES[scene],
                "weight_a": round(solved[scene]["weight_a"], 6),
                "c2_count_a": solved[scene]["c2_count"],
                "theta": [round(value, 4) for value in solved[scene]["theta"]],
                "ball_initial_target": solved[scene]["ball_target"],
                "drop_gain": solved[scene]["drop_gain"],
            }
            for scene in SCENES
        },
        "bf_entry_table": BF_ENTRY_TABLE,
        "bf_entry_rule": "every 5-cell window holds distinct normal symbols, so Any-8 is impossible",
        "multiplier_routing": {
            "c2_pool": C2_VALUES,
            "c3_pool": C3_VALUES,
            "reason": "game_rule.md §6.1 forbids >=10x from the plain C2 pool",
        },
    }
    validate_config(base)
    write_js(CONFIG_BASE, base, prefix)
    for path in CONFIG_VARIANTS:
        config, variant_prefix = load_js(path)
        sync_physical(base, config)
        validate_config(config)
        write_js(path, config, variant_prefix)


def _weight_pair(weight_a: float, total: int = 1_000_000) -> list[int]:
    first = int(round(weight_a * total))
    first = min(max(first, 1), total - 1)
    return [first, total - first]


def _free_table(names: list[str], weight_a: float) -> dict:
    weights = _weight_pair(weight_a)
    return {
        "names": names,
        # the count schedule stays for reference; `weights` switches the runtime to
        # per-spin scene selection (Simulator.schedule_free_spins)
        "initial": [15, 0],
        "retrigger": [5, 0],
        "weights": weights,
        "initial_spins": 15,
        "retrigger_spins": 5,
    }


def sync_physical(base: dict, target: dict) -> None:
    for key in ("strip_names", "strips", "multiplier_levels", "strip_length", "scene_mixture"):
        if key in base:
            target[key] = copy.deepcopy(base[key])
    target["parameter"]["super_multiplier"] = copy.deepcopy(base["parameter"]["super_multiplier"])
    for profile_name in ("normal", "featurebuy"):
        for key in ("base_reel_names", "base_reel_weights", "base_reel_weights_cum",
                    "free_table", "use_super_multiplier", "c2", "c3"):
            target["parameter"][profile_name][key] = copy.deepcopy(base["parameter"][profile_name][key])


def validate_config(config: dict) -> None:
    id_to_code = {int(value): code for code, value in zip(config["symbol_codes"], config["symbol_ids"])}
    names = config["strip_names"]
    if names != TABLE_ORDER:
        raise ValueError(f"strip_names must be {TABLE_ORDER}, got {names}")
    for name, strip in zip(names, config["strips"]):
        length = len(strip["symbols"])
        if any(len(row) != 6 for row in strip["symbols"]):
            raise ValueError(f"{name}: every strip row needs 6 reels")
        if any(value != 1 for row in strip["weights"] for value in row):
            raise ValueError(f"{name}: Symbol Weight must stay 1")
        if strip["reel_lengths"] != [length] * 6:
            raise ValueError(f"{name}: reel_lengths mismatch")
        for reel_index in range(6):
            if sum(row[reel_index] for row in strip["drop_weights"]) != 1_000_000:
                raise ValueError(f"{name} R{reel_index + 1}: drop weights must sum to 1,000,000")
            sequence = [id_to_code[row[reel_index]] for row in strip["symbols"]]
            if not _scatter_spacing_ok(sequence, 6):
                raise ValueError(f"{name} R{reel_index + 1}: C1 circular gap below 6")
            if name == BF_ENTRY_TABLE:
                if not _windows_are_clean(sequence):
                    raise ValueError(f"{name} R{reel_index + 1}: entry window repeats a normal symbol")
                if "C2" in sequence:
                    raise ValueError(f"{name} R{reel_index + 1}: entry strip must not carry C2")
    for profile_name in ("normal", "featurebuy"):
        profile = config["parameter"][profile_name]
        levels = config["multiplier_levels"]
        for name in names:
            for value, weight in zip(levels, profile["c2"]["weights"][name]):
                if weight > 0 and value >= 10:
                    raise ValueError(f"{profile_name}/{name}: C2 pool must not carry {value}x (rule §6.1)")
            for value, weight in zip(levels, profile["c3"]["weights"][name]):
                if weight > 0 and value < 10:
                    raise ValueError(f"{profile_name}/{name}: C3 pool must not carry {value}x (rule §6.1)")


# ------------------------------------------------------------------- simulation

def run_simulator(config_file: str, config_rtp_file: str, bet_mode: int, rounds: int,
                  card_system: bool, newbie: bool, seed: int, base_bet: float = 1.0) -> Path:
    env = dict(os.environ)
    env.update({
        "C027_CONFIG_FILE": config_file,
        "C027_CONFIG_RTP_FILE": config_rtp_file,
        "C027_BET_MODE": str(bet_mode),
        "C027_TOTAL_ROUNDS": str(rounds),
        "C027_CARD_SYSTEM_ENABLED": "true" if card_system else "false",
        "C027_CARD_SYSTEM_IS_NEWBIE": "true" if newbie else "false",
        "C027_BASE_BET": str(base_bet),
        "C027_RUN_ALL_COMBINATIONS": "false",
        "C027_OUTPUT_REPORT": "true",
        "C027_SHOW_CONSOLE_SUMMARY": "false",
        "C027_RANDOM_SEED": str(seed),
    })
    before = set(RECORD.glob("*.xlsx"))
    result = subprocess.run([sys.executable, str(ROOT / "Simulator.py")], cwd=str(ROOT),
                            env=env, capture_output=True, text=True, errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"Simulator failed:\n{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    produced = set(RECORD.glob("*.xlsx")) - before
    if not produced:
        raise RuntimeError("Simulator produced no report")
    return max(produced, key=lambda path: path.stat().st_mtime)


def probe_natural_fg(rounds: int, seed: int = 27301) -> Path:
    """Sample natural-FG sessions at full size by pointing Buy Feature at the FG tables.

    A Normal Bet run only triggers roughly one FG per 430 spins, far too few to
    calibrate 64 interval weights.  The probe config keeps every FG object identical
    (same tables, same drop weights, same multiplier weights) and only swaps which
    free table set the Buy Feature profile schedules.
    """
    probe_path = ROOT / "config_probe_natural_fg.js"
    config, prefix = load_js(CONFIG_BASE)
    config["parameter"]["featurebuy"]["free_table"] = copy.deepcopy(
        config["parameter"]["normal"]["free_table"])
    config["config_code"] = "probe_natural_fg"
    # a distinct model tag keeps the probe report from overwriting the Buy Feature
    # report, which otherwise shares the same generated filename within one minute
    config["model"] = "C0271PROBE"
    write_js(probe_path, config, prefix)
    try:
        return run_simulator(probe_path.name, probe_path.name, 2, rounds, False, False, seed)
    finally:
        probe_path.unlink(missing_ok=True)


def interval_stats(frame: pd.DataFrame, count_col: str, pay_col: str, denominator: float):
    counts = frame[count_col].to_numpy(dtype=float)
    pays = frame[pay_col].to_numpy(dtype=float)
    total = counts.sum()
    natural = counts / total if total else np.zeros_like(counts)
    averages = np.where(counts > 0, pays / np.maximum(counts, 1) / denominator, 0.0)
    return natural, averages


# ------------------------------------------------------------- card calibration

def project_shape(shape, averages, total_mass, target_mean, allowed):
    """Closest distribution (L2) to `shape` on the allowed intervals with the given
    total mass and mean.  Active-set: drop negative components and re-solve."""
    active = [index for index, ok in enumerate(allowed) if ok]
    result = np.zeros(len(shape))
    while True:
        if len(active) < 2:
            raise ValueError("not enough eligible intervals for the mean constraint")
        base_total = sum(shape[index] for index in active)
        if base_total <= 0:
            raise ValueError("eligible intervals carry no reference mass")
        q = np.array([shape[index] / base_total * total_mass for index in active])
        a = np.array([averages[index] for index in active])
        n = len(active)
        m00, m01, m11 = float(n), float(a.sum()), float((a * a).sum())
        r0 = total_mass - q.sum()
        r1 = target_mean - float((a * q).sum())
        determinant = m00 * m11 - m01 * m01
        if abs(determinant) < 1e-12:
            raise ValueError("degenerate interval averages")
        lam0 = (r0 * m11 - r1 * m01) / determinant
        lam1 = (m00 * r1 - m01 * r0) / determinant
        candidate = q + lam0 + lam1 * a
        negative = [(value, position) for position, value in enumerate(candidate) if value < -1e-12]
        if not negative:
            for index, value in zip(active, candidate):
                result[index] = max(0.0, value)
            return result
        active.pop(min(negative)[1])


def remap_shape(shape, allowed, uppers):
    mapped = np.zeros(len(shape))
    valid = [index for index, ok in enumerate(allowed) if ok]
    if not valid:
        raise ValueError("no eligible intervals")
    for index, mass in enumerate(shape):
        if mass <= 0:
            continue
        nearest = min(valid, key=lambda candidate: abs(uppers[candidate] - uppers[index]))
        mapped[nearest] += mass
    return mapped / mapped.sum()


def reset_ball_dimension(cards: list[dict]) -> None:
    """Collapse a previously split with-ball / without-ball pair back to one card.

    Calibration is idempotent: it always starts from one range card per interval so
    re-running never doubles the list.
    """
    merged: list[dict] = []
    seen: dict[tuple, dict] = {}
    for card in cards:
        if card.get("type", "range") != "range":
            merged.append(card)
            continue
        key = (float(card.get("min", 0.0)), float(card.get("max", 0.0)))
        if key in seen:
            seen[key]["weight"] = int(seen[key].get("weight", 0)) + int(card.get("weight", 0))
            continue
        card.pop("ball", None)
        seen[key] = card
        merged.append(card)
    cards[:] = merged


def update_card_list(cards: list[dict], weights, free_game_weight: int | None = None) -> None:
    reset_ball_dimension(cards)
    ranges = [card for card in cards if card.get("type", "range") == "range"]
    if len(ranges) != len(weights):
        raise ValueError(f"card range count {len(ranges)} != weight count {len(weights)}")
    for card, weight in zip(ranges, weights):
        card["weight"] = int(weight)
    if free_game_weight is not None:
        free_cards = [card for card in cards if card.get("type") == "free_game"]
        if len(free_cards) != 1:
            raise ValueError("normal BG card list must hold exactly one free_game card")
        free_cards[0]["weight"] = int(free_game_weight)


def iter_card_modes(card_system: dict):
    for player in ("newbie", "oldhand"):
        player_data = card_system[player]
        for mode in ("normal_bet", "buy_feature"):
            mode_data = player_data[mode]
            if player == "newbie":
                yield mode, mode_data
            else:
                for tier_data in mode_data.values():
                    yield mode, tier_data


# A win above roughly 3x essentially requires a ball multiplier, so a
# "without ball" card at those intervals is unreachable and burns the retry limit.
# Splitting only up to 3x keeps every card reachable (measured: retry limit
# exceeded drops from 0.28% of rounds to ~0).
BALL_SPLIT_MAX = 6.0


def apply_ball_dimension(cards: list[dict], ball_share: float,
                         split_max: float = BALL_SPLIT_MAX) -> None:
    """Give the low-multiplier range cards an explicit ball condition.

    H027's Card-On BG ball rate ran to 9.6% against a 2.737% target because the
    interval selection oversamples ball spins: a ball multiplies the win, so ball
    spins land in higher intervals and the interval line pulls them in.

    Splitting *every* interval into a with-ball / without-ball pair overcorrects —
    a 450x win **without** a ball is close to unreachable, so those cards burn the
    retry limit and the RTP collapses.  Cards up to `split_max` are the ones where
    both ball states are genuinely reachable, so the condition goes there and the
    thin high-interval tail keeps its natural (ball-heavy) behaviour.

    `ball_share` is the fraction of the split mass that must show a ball.
    """
    ball_share = min(max(float(ball_share), 0.0), 1.0)
    rebuilt: list[dict] = []
    for card in cards:
        splittable = (card.get("type", "range") == "range"
                      and float(card.get("max", 0.0)) <= split_max
                      and int(card.get("weight", 0)) > 0)
        if not splittable:
            rebuilt.append(card)
            continue
        weight = int(card["weight"])
        with_weight = int(round(weight * ball_share))
        for mode, mode_weight in (("with", with_weight), ("without", weight - with_weight)):
            if mode_weight <= 0:
                continue
            clone = copy.deepcopy(card)
            clone["ball"] = mode
            clone["weight"] = mode_weight
            rebuilt.append(clone)
    cards[:] = rebuilt


def calibrate_cards(natural_normal: Path, natural_bf: Path, natural_fg: Path, cycle: float,
                    threshold: float = 0.0004, variants: list[Path] | None = None,
                    verbose: bool = True, bg_rtp_offset: float = 0.0,
                    ball_share: float | None = 0.0, fg_shape_source: str = "competitor",
                    ball_split_max: float = BALL_SPLIT_MAX,
                    fg_rtp_share: float | None = None) -> dict:
    """Set every card weight so that, per RTP variant:

        total RTP    = the variant label
        BG : FG RTP  = the competitor's measured ratio, scaled to that label
        FG cycle     = the competitor cycle
        BG Hit Rate  = the competitor BG hit rate

    and the 64-interval shapes stay as close to the competitor line as the natural
    model allows (minimum-L2 projection).
    """
    variants = variants or CONFIG_VARIANTS
    shapes = TARGETS.interval_shape()
    normal_frame = pd.read_excel(natural_normal, sheet_name="Multiplier Line")
    bf_frame = pd.read_excel(natural_bf, sheet_name="Multiplier Line")
    fg_frame = pd.read_excel(natural_fg, sheet_name="Multiplier Line")
    uppers = normal_frame["Interval_Upper"].to_numpy(dtype=float)

    bg_natural, bg_avg = interval_stats(normal_frame, "base_game_cnt", "base_game_pay", 500.0)
    fg_natural, fg_avg = interval_stats(fg_frame, "free_game_cnt_BF", "free_game_pay_BF", 500.0)
    bf_natural, bf_avg = interval_stats(bf_frame, "free_game_cnt_BF", "free_game_pay_BF", 500.0)

    bg_allowed = bg_natural >= threshold
    fg_allowed = fg_natural >= threshold
    bf_allowed = bf_natural >= threshold
    bg_shape = remap_shape(shapes["BG"], bg_allowed, uppers)
    bf_shape = remap_shape(shapes["BF"], bf_allowed, uppers)
    if fg_shape_source == "natural":
        # The competitor's own report calls its 20-session NB-FG line
        # "僅供方向參考", so chasing its shape distorts the accepted FG sessions and
        # drags the per-spin FG Hit Rate down.  Projecting from the natural shape
        # keeps the session character and still hits the RTP mean exactly.
        fg_shape = np.where(fg_allowed, fg_natural, 0.0)
        fg_shape = fg_shape / fg_shape.sum()
    else:
        fg_shape = remap_shape(shapes["FG"], fg_allowed, uppers)

    trigger_probability = 1.0 / cycle
    free_game_weight = round(trigger_probability / (1.0 - trigger_probability) * 1_000_000_000)

    bg_hit_target = TARGETS.basic["bg_hit_rate"]
    positive_mass = (bg_hit_target - trigger_probability) / (1.0 - trigger_probability)
    positive_allowed = bg_allowed.copy()
    positive_allowed[0] = False
    positive_shape = bg_shape.copy()
    positive_shape[0] = 0.0

    trigger_counts = normal_frame["bg_trigger_fg_cnt_lte_upper"].to_numpy(dtype=float)
    trigger_pays = normal_frame["bg_trigger_fg_pay_lte_upper"].to_numpy(dtype=float)
    cap_index = max(index for index, ok in enumerate(positive_allowed) if ok)
    trigger_mean = trigger_pays[cap_index] / trigger_counts[cap_index] / 500.0 if trigger_counts[cap_index] else 0.0

    summary = {}
    for path in variants:
        config, prefix = load_js(path)
        label = float(config.get("rtp_label", 92))
        label = label / 100.0 if label > 1.5 else label
        # FG's share of the total RTP.  The competitor ratio is the default, but it is
        # a genuine design knob: a larger FG share means the cards have to compress the
        # naturally-rich FG packages less, which keeps the per-spin FG Hit Rate and the
        # FG cascade depth closer to the competitor at the cost of a higher FG average
        # multiplier.  See 其他/scan_fg_share.py for the measured trade-off.
        share = COMPETITOR_FG_RTP_SHARE if fg_rtp_share is None else float(fg_rtp_share)
        fg_contribution = label * share
        bg_rtp_target = label - fg_contribution
        fg_mean_target = fg_contribution / trigger_probability
        range_mean = ((bg_rtp_target + bg_rtp_offset - trigger_probability * trigger_mean)
                      / (1.0 - trigger_probability))
        bg_probabilities = project_shape(positive_shape, bg_avg, positive_mass, range_mean, positive_allowed)
        bg_probabilities[0] = 1.0 - positive_mass
        fg_probabilities = project_shape(fg_shape, fg_avg, 1.0, fg_mean_target, fg_allowed)
        bf_probabilities = project_shape(bf_shape, bf_avg, 1.0, label * TARGETS.basic["bf_price"], bf_allowed)

        bg_weights = largest_remainder(bg_probabilities, 1_000_000_000)
        fg_weights = largest_remainder(fg_probabilities, 1_000_000_000)
        bf_weights = largest_remainder(bf_probabilities, 1_000_000_000)
        config["card_system"]["fg_entry_cycle_target"] = cycle
        config["card_system"]["calibration"] = {
            "rtp_family": int(round(label * 100)),
            "method": "L2 projection onto the competitor 64-interval line",
            "rtp_split_rule": "competitor BG:FG ratio scaled to the variant label",
            "competitor_fg_rtp_share": COMPETITOR_FG_RTP_SHARE,
            "fg_rtp_share_used": share,
            "bg_rtp_target": bg_rtp_target,
            "fg_rtp_target": fg_contribution,
            "bg_rtp_solve_offset": bg_rtp_offset,
            "total_rtp_target": label,
            "fg_entry_probability": trigger_probability,
            "fg_package_mean": fg_mean_target,
            "buy_package_mean": label * TARGETS.basic["bf_price"],
            "bg_hit_rate_target": bg_hit_target,
            "bg_ball_rate_target": TARGETS.ball_spin_rate["BG"],
            "ball_share": ball_share,
            "ball_split_max": ball_split_max,
            "fg_shape_source": fg_shape_source,
            "newbie_oldhand_split": "identical",
            "normal_report": natural_normal.name,
            "buy_report": natural_bf.name,
            "natural_fg_probe": natural_fg.name,
        }
        for mode, mode_data in iter_card_modes(config["card_system"]):
            if mode == "normal_bet":
                update_card_list(mode_data["weight_bg"], bg_weights, free_game_weight)
                update_card_list(mode_data["weight_fg"], fg_weights)
                if ball_share is not None:
                    apply_ball_dimension(mode_data["weight_bg"], ball_share, ball_split_max)
            else:
                update_card_list(mode_data["weight_fg"], bf_weights)
        write_js(path, config, prefix)
        expected_total = ((1.0 - trigger_probability) * float((bg_probabilities * bg_avg).sum())
                          + trigger_probability * (trigger_mean + fg_mean_target))
        summary[path.name] = {
            "label": label,
            "cycle": cycle,
            "bg_rtp_target": bg_rtp_target,
            "fg_rtp_target": fg_contribution,
            "fg_mean_target": fg_mean_target,
            "expected_total_rtp": expected_total,
            "expected_bg_hit": trigger_probability + (1 - trigger_probability) * float(bg_probabilities[1:].sum()),
            "eligible": [int(bg_allowed.sum()), int(fg_allowed.sum()), int(bf_allowed.sum())],
            "interval_line": {"BG": bg_probabilities.tolist(),
                              "FG": fg_probabilities.tolist(),
                              "BF": bf_probabilities.tolist()},
        }
        if verbose:
            info = summary[path.name]
            print(f"  {path.name}: BG RTP={bg_rtp_target:.4%} FG RTP={fg_contribution:.4%} "
                  f"total={info['expected_total_rtp']:.4%} cycle=1/{cycle:.1f} "
                  f"FG avg={fg_mean_target:.2f}x BG hit={info['expected_bg_hit']:.4%} "
                  f"eligible={info['eligible']}")
    return summary


# ------------------------------------------------------------------------- main

DEFAULT_PLAN = {
    "max_run": {"BG": 4, "FG": 4, "BF": 3},
    "iterations": 60_000,
    "seed": 27_000,
    "rounds": 150_000,
    # the ball-carrying table needs P(ball|A) >= ball target, so the FG/BF lists
    # start above the ~21 cells that alone reach a 43% single-table ball rate
    # low counts keep the balls-per-spin distribution close to the competitor
    # (1 ball ~75% of ball spins); the floor is set by needing P(ball|A) >= target
    "c2_candidates": {
        "BG": [12, 16, 20, 26],
        "FG": [26, 30, 34],
        "BF": [24, 28, 32],
    },
}


def measure_drop_gain(verbose: bool = True) -> dict[str, float]:
    """Read the Card-Off reports and solve `d` per scene.

    Scene -> which report and which cascade columns carry that scene:
        BG  Normal Bet report, BG_* columns
        FG  natural-FG probe report, FG_* columns
        BF  Buy Feature report, FG_* columns
    """
    manifest_path = OTHER / "verify_c027_reports.json"
    if not manifest_path.is_file():
        raise SystemExit("需要 verify_c027_reports.json（先跑 verify_c027.py --natural）")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = {"BG": (manifest["natural_normal"], "BG"),
               "FG": (manifest["natural_fg_probe"], "FG"),
               "BF": (manifest["natural_buy"], "FG")}
    base, _ = load_js(CONFIG_BASE)
    designed = {scene: base["scene_mixture"]["tables"][scene] for scene in SCENES}
    out = {}
    for scene, (filename, prefix) in sources.items():
        cascade = pd.read_excel(RECORD / filename, sheet_name="Cascade")
        ball = cascade[f"{prefix}_Ball_Count"].to_numpy(dtype=float)
        no_ball = cascade[f"{prefix}_NoBall_Count"].to_numpy(dtype=float)
        total = ball.sum() + no_ball.sum()
        ball_final = ball.sum() / total
        hit_no_ball_final = 1.0 - no_ball[0] / no_ball.sum()
        # the initial-board ball rate the strips were built for
        ball_initial = designed[scene].get("ball_initial_target")
        if ball_initial is None:
            ball_initial = initial_ball_target(scene)
        gain = solve_drop_gain(ball_initial, ball_final, hit_no_ball_final)
        out[scene] = gain
        if verbose:
            print(f"  {scene}: 初始 {ball_initial:.4%} -> 最終 {ball_final:.4%}"
                  f"  hit|no(final) {hit_no_ball_final:.4%}  =>  drop_gain {gain:.4f}")
    DROP_GAIN_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strips", action="store_true")
    parser.add_argument("--measure-drop", action="store_true",
                        help="measure the cascade drop-in ball gain from the Card-Off reports")
    parser.add_argument("--cards", action="store_true")
    parser.add_argument("--cycle", type=float, default=TARGETS.basic["fg_cycle"])
    parser.add_argument("--bg-rtp-offset", type=float, default=0.0)
    parser.add_argument("--iterations", type=int, default=DEFAULT_PLAN["iterations"])
    parser.add_argument("--seed", type=int, default=DEFAULT_PLAN["seed"])
    parser.add_argument("--rounds", type=int, default=DEFAULT_PLAN["rounds"])
    parser.add_argument("--natural-rounds", type=int, default=10 ** 6)
    parser.add_argument("--ball-share", type=float, default=0.0,
                        help="fraction of zero-win rounds that must show a multiplier ball")
    parser.add_argument("--fg-shape", choices=("competitor", "natural"), default="competitor")
    parser.add_argument("--fg-rtp-share", type=float, default=None,
                        help="FG share of total RTP; default is the competitor ratio")
    args = parser.parse_args()

    if args.measure_drop:
        print("[drop] 量測 cascade 掉落補球機率")
        measure_drop_gain()

    if args.strips:
        plan = dict(DEFAULT_PLAN)
        plan.update({"iterations": args.iterations, "seed": args.seed, "rounds": args.rounds})
        solved = {}
        for offset, scene in enumerate(SCENES):
            print(f"[strips] {scene}")
            solved[scene] = solve_scene(scene, plan["c2_candidates"][scene],
                                        plan["seed"] + offset * 500, plan["max_run"][scene],
                                        plan["iterations"], plan["rounds"])
            chosen = solved[scene]
            print(f"  -> c2_A={chosen['c2_count']} w_A={chosen['weight_a']:.4%} "
                  f"theta={[round(v, 3) for v in chosen['theta']]}")
        print("[strips] Buy Feature entry table")
        bf_reels = build_bf_entry_reels(plan["seed"] + 9000)
        apply_strip_stage(solved, bf_reels, plan)
        diagnostics = {
            scene: {
                "c2_count_a": solved[scene]["c2_count"],
                "weight_a": solved[scene]["weight_a"],
                "theta": solved[scene]["theta"],
                "metrics": solved[scene]["metrics"],
                # the annealer aims at the initial board; the competitor numbers are
                # measured on the final board, so both are recorded
                "initial_board_targets": drop_corrected_targets(
                    scene, load_drop_gain().get(scene, 0.0)),
                "final_board_competitor": {
                    "ball_present": TARGETS.ball_spin_rate[scene],
                    "hit": TARGETS.initial_hit_target(scene),
                    **TARGETS.conditional_symbol_hit(scene),
                },
            }
            for scene in SCENES
        }
        (OTHER / "fit_scene_diagnostics.json").write_text(
            json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[strips] written")

    if args.cards:
        print("[cards] natural reference runs")
        normal = run_simulator("config.js", "config.js", 0, args.natural_rounds, False, False, 27001)
        bf = run_simulator("config.js", "config.js", 2, args.natural_rounds, False, False, 27201)
        fg = probe_natural_fg(args.natural_rounds)
        print(f"  normal={normal.name}\n  bf={bf.name}\n  natural-fg probe={fg.name}")
        print("[cards] calibrating")
        summary = calibrate_cards(normal, bf, fg, args.cycle, bg_rtp_offset=args.bg_rtp_offset,
                                  ball_share=args.ball_share, fg_shape_source=args.fg_shape,
                                  fg_rtp_share=args.fg_rtp_share)
        (OTHER / "fit_card_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
