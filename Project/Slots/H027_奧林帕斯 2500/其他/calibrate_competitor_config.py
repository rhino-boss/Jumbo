from __future__ import annotations

import argparse
import copy
import json
import math
import random
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
OTHER = ROOT / "其他"
HTML = OTHER / "遊戲數據_Gates_of_Olympus_1000.html"
CONFIGS = [ROOT / "config.js", ROOT / "config_92A.js", ROOT / "config_94A.js"]
REELS = [f"R{i}" for i in range(1, 7)]
SCENES = ["BG", "FG", "BF"]
SYMBOL_ORDER = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2"]
SOURCE_ORDER = ["S1", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "倍數球"]
SOURCE_TO_CODE = dict(zip(SOURCE_ORDER, SYMBOL_ORDER))
TABLE_FOR_SCENE = {"BG": 6, "FG": 7, "BF": 8}
DROP_FOR_SCENE = {"BG": 9, "FG": 10, "BF": 11}
STRIP_SCENE = {
    "BG_Symbol": "BG",
    "BG_Symbol (2)": "BF",
    "FG_Symbol": "FG",
    "FG_Symbol (2)": "BF",
}
STACK_TARGET = {
    "BG": {1: 0.60868, 2: 0.34952, 3: 0.03772},
    "FG": {1: 0.62149, 2: 0.33735, 3: 0.03966},
    "BF": {1: 0.61704, 2: 0.34560, 3: 0.03417},
}
MULTIPLIERS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 250, 500]
MULTIPLIER_TARGET = {
    "BG": [9.20, 8.96, 7.78, 20.28, 20.99, 14.39, 8.49, 3.30, 1.89, 2.36, 0.24, 0.47, 1.18, 0.24, 0.24],
    "FG": [45.42, 22.18, 13.38, 9.86, 4.58, 3.17, 0.35, 0.35, 0.70, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
    "BF": [46.31, 24.86, 11.66, 10.17, 3.20, 1.43, 0.70, 0.52, 0.42, 0.21, 0.17, 0.28, 0.07, 0.00, 0.00],
}


def parse_percent(value) -> float:
    return float(str(value).replace("%", "").strip()) / 100.0


def load_js(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8-sig")
    start, end = text.index("{"), text.rindex("}")
    return json.loads(text[start:end + 1]), text[:start]


def write_js(path: Path, data: dict, prefix: str) -> None:
    path.write_text(prefix + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


def largest_remainder(probabilities: list[float], total: int) -> list[int]:
    scale = sum(probabilities)
    exact = [value / scale * total for value in probabilities]
    base = [math.floor(value) for value in exact]
    for index in sorted(range(len(exact)), key=lambda i: exact[i] - base[i], reverse=True)[: total - sum(base)]:
        base[index] += 1
    return base


def read_targets() -> tuple[dict, dict]:
    tables = pd.read_html(HTML, encoding="utf-8")
    distributions: dict[str, dict[str, dict[str, float]]] = {}
    drops: dict[str, dict[str, dict[str, float]]] = {}
    for scene in SCENES:
        for destination, table_index in ((distributions, TABLE_FOR_SCENE[scene]), (drops, DROP_FOR_SCENE[scene])):
            frame = tables[table_index]
            first = frame.columns[0]
            by_reel = {reel: {} for reel in REELS}
            for _, row in frame.iterrows():
                source = str(row[first]).strip()
                code = SOURCE_TO_CODE.get(source)
                if not code:
                    continue
                for reel in REELS:
                    by_reel[reel][code] = parse_percent(row[reel])
            destination[scene] = by_reel
    return distributions, drops


def allocate_symbol_counts(target: dict[str, float], length: int) -> dict[str, int]:
    probabilities = [target.get(code, 0.0) for code in SYMBOL_ORDER]
    counts = largest_remainder(probabilities, length)
    return dict(zip(SYMBOL_ORDER, counts))


def split_runs(symbol: str, count: int, target: dict[int, float], rng: random.Random) -> list[tuple[str, int]]:
    if symbol in {"C1", "C2"}:
        return [(symbol, 1)] * count
    best = None
    for triples in range(count // 3 + 1):
        remaining = count - triples * 3
        for doubles in range(remaining // 2 + 1):
            singles = remaining - doubles * 2
            cells = {1: singles, 2: doubles * 2, 3: triples * 3}
            error = sum((cells[size] / max(count, 1) - target[size]) ** 2 for size in (1, 2, 3))
            run_count = singles + doubles + triples
            candidate = (error, -run_count, singles, doubles, triples)
            if best is None or candidate < best:
                best = candidate
    _, _, singles, doubles, triples = best
    runs = [(symbol, 1)] * singles + [(symbol, 2)] * doubles + [(symbol, 3)] * triples
    rng.shuffle(runs)
    return runs


def arrange_runs(counts: dict[str, int], stack_target: dict[int, float], seed: int) -> list[str]:
    rng = random.Random(seed)
    pending = []
    for symbol, count in counts.items():
        pending.extend(split_runs(symbol, count, stack_target, rng))
    sequence: list[str] = []
    last_end: dict[str, int] = {}
    while pending:
        current = len(sequence)
        candidates = []
        for index, (symbol, size) in enumerate(pending):
            gap = current - last_end.get(symbol, -999)
            same_adjacent = bool(sequence and sequence[-1] == symbol)
            penalty = 10_000 if same_adjacent else max(0, 5 - gap) * 100
            remaining_cells = sum(run_size for run_symbol, run_size in pending if run_symbol == symbol)
            score = penalty - remaining_cells + rng.random()
            candidates.append((score, index))
        _, chosen = min(candidates)
        symbol, size = pending.pop(chosen)
        sequence.extend([symbol] * size)
        last_end[symbol] = len(sequence)
    return repair_scatter_gaps(sequence, rng)


def scatter_gap_penalty(sequence: list[str]) -> int:
    positions = [index for index, symbol in enumerate(sequence) if symbol == "C1"]
    if len(positions) < 2:
        return 0
    gaps = [(positions[(index + 1) % len(positions)] - positions[index]) % len(sequence) for index in range(len(positions))]
    return sum(max(0, 6 - gap) for gap in gaps)


def repair_scatter_gaps(sequence: list[str], rng: random.Random) -> list[str]:
    best = list(sequence)
    best_penalty = scatter_gap_penalty(best)
    for _ in range(30000):
        if best_penalty == 0:
            break
        scatter_positions = [index for index, symbol in enumerate(best) if symbol == "C1"]
        source = rng.choice(scatter_positions)
        target = rng.randrange(len(best))
        if best[target] == "C1":
            continue
        candidate = list(best)
        candidate[source], candidate[target] = candidate[target], candidate[source]
        rates = run_distribution(candidate)
        if any(size > 3 and rate > 0 for size, rate in rates.items()):
            continue
        penalty = scatter_gap_penalty(candidate)
        if penalty < best_penalty:
            best, best_penalty = candidate, penalty
    if best_penalty:
        raise ValueError("Unable to enforce C1 circular gap >= 6")
    return best


def run_distribution(sequence: list[str]) -> dict[int, float]:
    n = len(sequence)
    seen = [False] * n
    cells = Counter()
    for start in range(n):
        if seen[start]:
            continue
        symbol = sequence[start]
        run = []
        index = start
        while not seen[index] and sequence[index] == symbol:
            seen[index] = True
            run.append(index)
            index = (index + 1) % n
        cells[len(run)] += len(run)
    return {size: cells[size] / n for size in range(1, 6)}


def set_strip(strip: dict, scene: str, initial: dict, drops: dict, code_to_id: dict[str, int], seed: int) -> None:
    length = 300
    reels = []
    for reel_index, reel in enumerate(REELS):
        counts = allocate_symbol_counts(initial[scene][reel], length)
        sequence = arrange_runs(counts, STACK_TARGET[scene], seed + reel_index)
        reels.append([code_to_id[code] for code in sequence])
    strip["symbols"] = [[reels[reel][row] for reel in range(6)] for row in range(length)]
    strip["weights"] = [[1] * 6 for _ in range(length)]
    strip["reel_lengths"] = [length] * 6
    drop_weights = [[0] * 6 for _ in range(12)]
    for reel_index, reel in enumerate(REELS):
        probabilities = [drops[scene][reel].get(code, 0.0) for code in SYMBOL_ORDER]
        weights = largest_remainder(probabilities, 1_000_000)
        for code, weight in zip(SYMBOL_ORDER, weights):
            drop_weights[code_to_id[code] - 1][reel_index] = weight
    strip["drop_weights"] = drop_weights


def multiplier_weights(levels: list[int], scene: str, total: int = 10000) -> list[int]:
    target_by_value = dict(zip(MULTIPLIERS, MULTIPLIER_TARGET[scene]))
    weights = largest_remainder([target_by_value.get(value, 0.0) for value in levels], total)
    return weights


def cumulative(values: list[int]) -> list[int]:
    result, running = [], 0
    for value in values:
        running += int(value)
        result.append(running)
    return result


def update_multiplier_blocks(cfg: dict) -> None:
    levels = list(cfg["multiplier_levels"])
    scene_by_table = {"BG_Symbol": "BG", "BG_Symbol (2)": "BF", "FG_Symbol": "FG", "FG_Symbol (2)": "BF"}
    for profile_name in ("normal", "featurebuy"):
        profile = cfg["parameter"][profile_name]
        profile["use_super_multiplier"]["weights_by_initial_ball_count"] = {
            table: [0, 0, 0, 0, 0, 0] for table in profile["use_super_multiplier"]["table_names"]
        }
        profile["c2"]["multipliers"] = levels
        for table in profile["c2"]["table_names"]:
            weights = multiplier_weights(levels, scene_by_table[table])
            profile["c2"]["weights"][table] = weights
            profile["c2"]["weights_cum"][table] = cumulative(weights)


def set_table_roles(cfg: dict) -> None:
    normal = cfg["parameter"]["normal"]
    feature = cfg["parameter"]["featurebuy"]
    normal["base_reel_weights"] = [1, 0]
    normal["base_reel_weights_cum"] = [1, 1]
    feature["base_reel_weights"] = [0, 1]
    feature["base_reel_weights_cum"] = [0, 1]
    normal["free_table"]["initial"] = [15, 0]
    normal["free_table"]["retrigger"] = [5, 0]
    feature["free_table"]["initial"] = [0, 15]
    feature["free_table"]["retrigger"] = [0, 5]


def sync_physical(base: dict, target: dict) -> None:
    for key in ("strip_names", "strips", "multiplier_levels"):
        target[key] = copy.deepcopy(base[key])
    target["parameter"]["super_multiplier"] = copy.deepcopy(base["parameter"]["super_multiplier"])
    for profile_name in ("normal", "featurebuy"):
        for key in ("base_reel_names", "base_reel_weights", "base_reel_weights_cum", "free_table", "use_super_multiplier", "c2", "c3"):
            target["parameter"][profile_name][key] = copy.deepcopy(base["parameter"][profile_name][key])


def validate(cfg: dict, initial: dict) -> None:
    code_to_id = dict(zip(cfg["symbol_codes"], cfg["symbol_ids"]))
    id_to_code = {value: key for key, value in code_to_id.items()}
    for name, strip in zip(cfg["strip_names"], cfg["strips"]):
        if len(strip["symbols"]) != 300 or any(len(row) != 6 for row in strip["symbols"]):
            raise ValueError(f"{name}: invalid symbol shape")
        if any(value != 1 for row in strip["weights"] for value in row):
            raise ValueError(f"{name}: Symbol Weight must remain 1")
        scene = STRIP_SCENE[name]
        for reel_index, reel in enumerate(REELS):
            seq = [id_to_code[row[reel_index]] for row in strip["symbols"]]
            if max(run_distribution(seq)) > 5:
                raise ValueError(f"{name} {reel}: invalid run")
            if any(size > 3 and rate > 0 for size, rate in run_distribution(seq).items()):
                raise ValueError(f"{name} {reel}: stack exceeds 3")
            expected = allocate_symbol_counts(initial[scene][reel], 300)
            actual = Counter(seq)
            if any(actual[code] != expected[code] for code in SYMBOL_ORDER):
                raise ValueError(f"{name} {reel}: symbol count mismatch")
        for reel_index in range(6):
            if sum(row[reel_index] for row in strip["drop_weights"]) != 1_000_000:
                raise ValueError(f"{name} R{reel_index + 1}: drop weights do not sum to 1,000,000")
        c1 = code_to_id["C1"]
        for reel_index in range(6):
            positions = [row for row, values in enumerate(strip["symbols"]) if values[reel_index] == c1]
            if len(positions) > 1:
                gaps = [(positions[(i + 1) % len(positions)] - positions[i]) % 300 for i in range(len(positions))]
                if min(gaps) < 6:
                    raise ValueError(f"{name} R{reel_index + 1}: C1 gap below 6")


def summarize(cfg: dict) -> None:
    id_to_code = dict(zip(cfg["symbol_ids"], cfg["symbol_codes"]))
    for name, strip in zip(cfg["strip_names"], cfg["strips"]):
        scene = STRIP_SCENE[name]
        rows = []
        for reel_index in range(6):
            seq = [id_to_code[row[reel_index]] for row in strip["symbols"]]
            rates = run_distribution(seq)
            rows.append("/".join(f"S{size}:{rates.get(size, 0):.1%}" for size in (1, 2, 3)))
        print(f"{name} ({scene})", " | ".join(rows))


def apply() -> None:
    initial, drops = read_targets()
    loaded = [load_js(path) for path in CONFIGS]
    base, base_prefix = loaded[0]
    code_to_id = dict(zip(base["symbol_codes"], base["symbol_ids"]))
    strip_by_name = dict(zip(base["strip_names"], base["strips"]))
    for index, (name, scene) in enumerate(STRIP_SCENE.items()):
        set_strip(strip_by_name[name], scene, initial, drops, code_to_id, 27000 + index * 100)
    set_table_roles(base)
    update_multiplier_blocks(base)
    validate(base, initial)
    write_js(CONFIGS[0], base, base_prefix)
    for path, (target, prefix) in zip(CONFIGS[1:], loaded[1:]):
        sync_physical(base, target)
        validate(target, initial)
        write_js(path, target, prefix)
    summarize(base)
    print("Updated config.js, config_92A.js, config_94A.js; XLSX files were not modified.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        raise SystemExit("Use --apply to update config files.")
    apply()


if __name__ == "__main__":
    main()
