"""Dry-run-first H016 config-only calibrator; never reads or writes XLSX/MD.

Token swapping keeps every exact symbol/gold-token count.  ``--write`` is the
only mode that replaces config_92.js, and it does so only after validation.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE.parent / "config_92.js"
ROOTS = (
    Path("C:/Users/rhinshen/Mine/個人工作區/市場資訊/H5/遊戲資源/JILI/JILI - Super Ace"),
    Path("C:/Users/rhinshen/Mine/個人工作區/市場資訊/H5/遊戲資源/JILI/JILI - Super Ace - m"),
)
WINDOW, NREELS, C1 = 4, 5, 2
SCORES, GOLDS = tuple(range(3, 11)), set(range(11, 19))
STACK_SYMBOLS = (C1, *SCORES)
SYMBOL_MAP = {"Bonus": 2, **{f"Symbol{i}": i + 2 for i in range(1, 9)}}
PRIMARY = {"BG": "bg_1", "FG": "fg_1"}
VARIANTS = {"BG": ("bg_1", "bg_2", "bg_3"), "FG": ("fg_1", "fg_2", "fg_3")}
ALIASES = {
    "bg_high": "bg_1", "bg_low": "bg_2", "buy": "bg_3",
    "fg_high_a": "fg_1", "fg_high_j": "fg_1", "fg_low": "fg_1",
    "fg_high_k": "fg_2", "super": "fg_2", "fg_high_q": "fg_3",
}
NO_SC = {"bg_1": (2, 4), "bg_2": (0, 3)}
W2_CONDITIONAL = (1401, 235, 18)
BG_MULTIPLIERS = [1, 1, 2, 3]


def canonical(symbol: int) -> int:
    return symbol - 8 if symbol in GOLDS else symbol


def load_config(path: Path) -> tuple[dict[str, Any], str, str]:
    text = path.read_text(encoding="utf-8-sig")
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"No JSON object in {path}")
    return json.loads(text[start:end + 1]), text[:start], text[end + 1:]


def data_dir(explicit: Path | None) -> Path:
    for root in ((explicit,) if explicit else ROOTS):
        if root is None:
            continue
        root = root.expanduser().resolve()
        for candidate in (root / "遊戲資料", root):
            if candidate.is_dir() and any(candidate.glob("*.jsonl")):
                return candidate
    raise FileNotFoundError("No Super Ace JSONL directory found")


def input_files(folder: Path) -> list[Path]:
    indexed = {p.name.lower(): p for p in folder.glob("*.jsonl")}
    preferred = [
        indexed[name.lower()] for name in (
            "SuperAce_BG_Combined_NoJP.jsonl", "SuperAce_BG_3.jsonl", "Super_Ace_BG_4.jsonl"
        ) if name.lower() in indexed
    ]
    if preferred:
        return preferred
    files = [p for p in folder.glob("*.jsonl") if "bg" in p.stem.lower() and not any(x in p.stem.lower() for x in ("bigwin", "feature", "buy"))]
    combined = [p for p in files if "combined" in p.stem.lower()]
    if not (combined or files):
        raise FileNotFoundError(f"No usable captures in {folder}")
    return combined or sorted(files)


def runs(window: list[int]) -> Counter[tuple[int, int]]:
    result: Counter[tuple[int, int]] = Counter()
    if not window:
        return result
    value, length = window[0], 1
    for item in window[1:]:
        if item == value:
            length += 1
        else:
            if length >= 2:
                result[(value, length)] += 1
            value, length = item, 1
    if length >= 2:
        result[(value, length)] += 1
    return result


def read_competitor(files: list[Path], cap: int) -> dict[str, Any]:
    scenes = {s: {"spins": 0, "hits": 0, "stack": [Counter() for _ in range(5)], "drop": [Counter() for _ in range(5)]} for s in ("BG", "FG")}
    records = 0
    for path in files:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if cap and records >= cap:
                    break
                records += 1
                obj = json.loads(line)
                for plate_index, plate in enumerate(obj.get("plate", {}).get("plate", [])):
                    scene = "BG" if plate_index == 0 else "FG"
                    data = scenes[scene]
                    data["spins"] += 1
                    data["hits"] += int(float(plate.get("win", 0) or 0) > 0)
                    for reel, column in enumerate(plate.get("column", [])[:5]):
                        window = [SYMBOL_MAP[x] for x in column.get("row", []) if x in SYMBOL_MAP]
                        data["stack"][reel].update(runs(window))
                    for combo in plate.get("combo", []):
                        for change in combo.get("change", []):
                            name = change.get("symbol")
                            reel = int(change.get("column", 0) or 0)
                            if name not in SYMBOL_MAP or not 0 <= reel < 5:
                                continue
                            symbol = SYMBOL_MAP[name]
                            if change.get("isGold") in (1, 2) and symbol in SCORES:
                                symbol += 8
                            data["drop"][reel][symbol] += 1
            if cap and records >= cap:
                break
    if not scenes["BG"]["spins"] or not scenes["FG"]["spins"]:
        raise ValueError("Samples must include both BG and FG plates")
    return {"records": records, "scenes": scenes}


def target_stack(comp: dict[str, Any], scene: str, reel: int) -> dict[tuple[int, int], float]:
    data = comp["scenes"][scene]
    return {(s, n): data["stack"][reel][(s, n)] / data["spins"] for s in STACK_SYMBOLS for n in (2, 3, 4)}


def stack_rates(symbols: list[int], weights: list[int]) -> dict[tuple[int, int], float]:
    counts: Counter[tuple[int, int]] = Counter()
    total, size = 0, len(symbols)
    symbols = [canonical(x) for x in symbols]
    for stop, weight in enumerate(weights):
        if weight <= 0:
            continue
        for key, amount in runs([symbols[(stop + row) % size] for row in range(4)]).items():
            counts[key] += amount * weight
        total += weight
    return {(s, n): counts[(s, n)] / max(1, total) for s in STACK_SYMBOLS for n in (2, 3, 4)}


def score(rates: dict[tuple[int, int], float], target: dict[tuple[int, int], float]) -> float:
    return sum((rates[key] - target[key]) ** 2 for key in target) / len(target)


def sc_gap_ok(symbols: list[int]) -> bool:
    positions = [i for i, x in enumerate(symbols) if canonical(x) == C1]
    if len(positions) < 2:
        return True
    return all(((b - a - 1) % len(symbols)) >= 4 for a, b in zip(positions, positions[1:] + positions[:1]))


def max_run(symbols: list[int]) -> int:
    values = [canonical(x) for x in symbols]
    if len(set(values)) == 1:
        return len(values)
    boundary = next(i for i in range(len(values)) if values[i] != values[i - 1])
    values = values[boundary:] + values[:boundary]
    best = current = 1
    for i in range(1, len(values)):
        current = current + 1 if values[i] == values[i - 1] else 1
        best = max(best, current)
    return best


def rules_ok(symbols: list[int]) -> bool:
    return len(symbols) == 200 and sc_gap_ok(symbols) and max_run(symbols) <= 4


def optimize_reel(symbols: list[int], weights: list[int], target: dict[tuple[int, int], float], iterations: int, temperature: float, rng: random.Random) -> tuple[list[int], dict[str, Any]]:
    current = list(symbols)
    if not rules_ok(current):
        raise ValueError("Input reel violates cyclic SC gap or max stack")
    current_score = before = score(stack_rates(current, weights), target)
    best, best_score, accepted = current[:], current_score, 0
    for step in range(max(0, iterations)):
        left, right = rng.sample(range(200), 2)
        if current[left] == current[right]:
            continue
        current[left], current[right] = current[right], current[left]
        if not rules_ok(current):
            current[left], current[right] = current[right], current[left]
            continue
        candidate = score(stack_rates(current, weights), target)
        heat = max(1e-12, temperature * (1 - step / max(1, iterations)))
        if candidate <= current_score or rng.random() < math.exp((current_score - candidate) / heat):
            current_score, accepted = candidate, accepted + 1
            if candidate < best_score:
                best, best_score = current[:], candidate
        else:
            current[left], current[right] = current[right], current[left]
    return best, {"before_rmse_pp": math.sqrt(before) * 100, "after_rmse_pp": math.sqrt(best_score) * 100, "accepted": accepted}


def has_sc(symbols: list[int], stop: int) -> bool:
    return any(canonical(symbols[(stop + row) % 200]) == C1 for row in range(4))


def enforce_stops(name: str, table: dict[str, Any]) -> None:
    """Use uniform positive stops; zero exists only for a hard visibility rule."""
    table["weights"] = [[1] * 200 for _ in range(5)]
    for reel in range(5):
        refresh_stop_reel(name, table, reel)


def refresh_stop_reel(name: str, table: dict[str, Any], reel: int) -> None:
    if reel in NO_SC.get(name, ()):
        table["weights"][reel] = [
            0 if has_sc(table["reels"][reel], stop) else 1 for stop in range(200)
        ]
    elif name == "bg_3" and reel < 3:
        table["weights"][reel] = [
            1 if has_sc(table["reels"][reel], stop) else 0 for stop in range(200)
        ]
    else:
        table["weights"][reel] = [1] * 200


def window_mask(symbols: list[int], stop: int) -> int:
    mask = 0
    for row in range(4):
        symbol = symbols[(stop + row) % 200]
        if symbol in (0, 1):
            return (1 << len(SCORES)) - 1
        symbol = canonical(symbol)
        if symbol in SCORES:
            mask |= 1 << (symbol - SCORES[0])
    return mask


def exact_hit_rate(table: dict[str, Any]) -> float:
    histograms: list[Counter[int]] = []
    for reel in range(3):
        histogram: Counter[int] = Counter()
        for stop, weight in enumerate(table["weights"][reel]):
            if weight > 0:
                histogram[window_mask(table["reels"][reel], stop)] += weight
        histograms.append(histogram)
    pair: Counter[int] = Counter()
    for left, left_weight in histograms[0].items():
        for right, right_weight in histograms[1].items():
            pair[left & right] += left_weight * right_weight
    wins = sum(
        pair_weight * third_weight
        for pair_mask, pair_weight in pair.items()
        for third_mask, third_weight in histograms[2].items()
        if pair_mask & third_mask
    )
    denominator = math.prod(sum(histogram.values()) for histogram in histograms)
    return wins / max(1, denominator)


def scene_stack_score(table: dict[str, Any], comp: dict[str, Any], scene: str) -> float:
    return sum(score(stack_rates(table["reels"][r], table["weights"][r]), target_stack(comp, scene, r)) for r in range(5)) / 5


def selection_items(config: dict[str, Any], scene: str) -> list[tuple[str, float]]:
    group = "base" if scene == "BG" else "free"
    return [
        (str(row["table"]), float(row["weight"]))
        for row in config["table_selection"][group]
        if float(row["weight"]) > 0
    ]


def mixed_hit_rate(config: dict[str, Any], scene: str) -> float:
    items = selection_items(config, scene)
    total = sum(weight for _, weight in items)
    return sum(exact_hit_rate(config["tables"][name]) * weight for name, weight in items) / total


def mixed_stack_score(config: dict[str, Any], comp: dict[str, Any], scene: str) -> float:
    items = selection_items(config, scene)
    total = sum(weight for _, weight in items)
    return sum(
        scene_stack_score(config["tables"][name], comp, scene) * weight
        for name, weight in items
    ) / total


def greedy_hit(config: dict[str, Any], comp: dict[str, Any], scene: str, iterations: int, tolerance: float, rng: random.Random) -> dict[str, Any]:
    """Swap exact tokens on R1-R3; never tune marginal stop exposure."""
    target = comp["scenes"][scene]["hits"] / comp["scenes"][scene]["spins"]
    current = before = mixed_hit_rate(config, scene)
    before_stack_rmse = math.sqrt(mixed_stack_score(config, comp, scene)) * 100
    limit_rmse = before_stack_rmse + max(0.0, tolerance)
    names = VARIANTS[scene]
    accepted = 0
    for _ in range(max(0, iterations)):
        reel = rng.randrange(3)
        left, right = rng.sample(range(200), 2)
        primary = config["tables"][PRIMARY[scene]]["reels"][reel]
        if primary[left] == primary[right]:
            continue
        for name in names:
            strip = config["tables"][name]["reels"][reel]
            strip[left], strip[right] = strip[right], strip[left]
            refresh_stop_reel(name, config["tables"][name], reel)
        if not rules_ok(config["tables"][PRIMARY[scene]]["reels"][reel]):
            candidate = math.inf
        else:
            candidate = mixed_hit_rate(config, scene)
        improves = abs(candidate - target) < abs(current - target)
        stack_rmse = math.inf
        if improves:
            stack_rmse = math.sqrt(mixed_stack_score(config, comp, scene)) * 100
        if improves and stack_rmse <= limit_rmse:
            current, accepted = candidate, accepted + 1
            if abs(current - target) <= 1e-7:
                break
        else:
            for name in names:
                strip = config["tables"][name]["reels"][reel]
                strip[left], strip[right] = strip[right], strip[left]
                refresh_stop_reel(name, config["tables"][name], reel)
    return {
        "target": target, "before": before, "after": current, "accepted": accepted,
        "stack_rmse_before_pp": before_stack_rmse,
        "stack_rmse_after_pp": math.sqrt(mixed_stack_score(config, comp, scene)) * 100,
        "stack_rmse_limit_pp": limit_rmse,
    }


def distribute(values: list[int], counts: Counter[int], total: int = 1_000_000) -> list[int]:
    denominator = sum(max(0, counts[value]) for value in values)
    if denominator <= 0:
        raise ValueError("Competitor drop reel has no observations")
    raw = [total * max(0, counts[value]) / denominator for value in values]
    result = [math.floor(x) for x in raw]
    order = sorted(range(len(values)), key=lambda i: raw[i] - result[i], reverse=True)
    for index in order[:total - sum(result)]:
        result[index] += 1
    return result


def remove_c1(values: list[int], weights: list[int]) -> list[int]:
    counts = Counter({value: weight for value, weight in zip(values, weights) if value != C1})
    return distribute(values, counts, sum(weights))


def calibrate_drops(config: dict[str, Any], comp: dict[str, Any]) -> None:
    tables = config["tables"]
    for scene in ("BG", "FG"):
        base = tables[PRIMARY[scene]]
        base["drop_weights"] = [distribute(base["drop_values"][r], comp["scenes"][scene]["drop"][r]) for r in range(5)]
        for name in VARIANTS[scene]:
            table = tables[name]
            table["drop_values"] = copy.deepcopy(base["drop_values"])
            table["drop_weights"] = copy.deepcopy(base["drop_weights"])
            for reel in NO_SC.get(name, ()):
                table["drop_weights"][reel] = remove_c1(table["drop_values"][reel], table["drop_weights"][reel])


def scaled_conditional(total: int) -> list[int]:
    denominator = sum(W2_CONDITIONAL)
    raw = [total * x / denominator for x in W2_CONDITIONAL]
    result = [math.floor(x) for x in raw]
    for index in sorted(range(3), key=lambda i: raw[i] - result[i], reverse=True)[:total - sum(result)]:
        result[index] += 1
    return result


def calibrate_wild(config: dict[str, Any]) -> None:
    for name in ("bg_1", "bg_2"):
        wild = config["tables"][name]["random_wild"]
        nonzero = max(1, sum(map(int, wild["weights"][1:])))
        wild["values"] = [0, 2, 3, 4]
        wild["weights"] = [int(wild["weights"][0]), *scaled_conditional(nonzero)]
    for name in ("fg_1", "fg_2", "fg_3"):
        config["tables"][name]["random_wild"] = {"values": [0, 2, 3, 4], "weights": [1, 0, 0, 0]}


def sync_aliases(config: dict[str, Any]) -> None:
    for alias, primary in ALIASES.items():
        config["tables"][alias] = copy.deepcopy(config["tables"][primary])


def calibrate_multipliers(config: dict[str, Any]) -> None:
    """Final RTP guardrail; it leaves every probability and reel invariant."""
    for name in VARIANTS["BG"]:
        config["tables"][name]["multipliers"] = list(BG_MULTIPLIERS)


def atomic_write(path: Path, prefix: str, suffix: str, config: dict[str, Any]) -> None:
    serialized = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(prefix + serialized + suffix)
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate(config: dict[str, Any], original: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tables = config["tables"]
    for scene in ("BG", "FG"):
        for name in VARIANTS[scene]:
            table = tables[name]
            for reel in range(5):
                symbols, weights = table["reels"][reel], table["weights"][reel]
                label = f"{name}.R{reel + 1}"
                if len(symbols) != 200 or len(weights) != 200:
                    errors.append(f"{label}: length != 200")
                if Counter(symbols) != Counter(original["tables"][name]["reels"][reel]):
                    errors.append(f"{label}: exact symbol/gold-token multiset changed")
                if not sc_gap_ok(symbols):
                    errors.append(f"{label}: SC cyclic gap < 4")
                if max_run(symbols) > 4:
                    errors.append(f"{label}: canonical stack > 4")
                if any(type(x) is not int or x < 0 for x in weights):
                    errors.append(f"{label}: invalid stop weight")
                positive = [x for x in weights if x > 0]
                if not positive or max(positive) > 10 * min(positive):
                    errors.append(f"{label}: positive max/min > 10x or empty")
                if reel in NO_SC.get(name, ()):
                    if any(x > 0 and has_sc(symbols, stop) for stop, x in enumerate(weights)):
                        errors.append(f"{label}: initial SC is reachable")
                    if sum(x for value, x in zip(table["drop_values"][reel], table["drop_weights"][reel]) if value == C1):
                        errors.append(f"{label}: C1 drop != 0")
                if name == "bg_3" and reel < 3 and any(x > 0 and not has_sc(symbols, stop) for stop, x in enumerate(weights)):
                    errors.append(f"{label}: BG3 does not guarantee SC")
                drops = table["drop_weights"][reel]
                if any(type(x) is not int or x < 0 for x in drops) or sum(drops) <= 0:
                    errors.append(f"{label}: invalid drop weights")
    for alias, primary in ALIASES.items():
        if tables.get(alias) != tables.get(primary):
            errors.append(f"{alias}: alias differs from {primary}")
    for name in ("fg_1", "fg_2", "fg_3"):
        if any(tables[name]["random_wild"]["weights"][1:]):
            errors.append(f"{name}: FG Random Wild nonzero")
    return errors


def stack_summary(config: dict[str, Any], comp: dict[str, Any], scene: str) -> dict[str, float]:
    table, differences = config["tables"][PRIMARY[scene]], []
    for reel in range(5):
        actual, target = stack_rates(table["reels"][reel], table["weights"][reel]), target_stack(comp, scene, reel)
        differences += [(actual[key] - target[key]) * 100 for key in target]
    return {
        "mae_pp": sum(map(abs, differences)) / len(differences),
        "rmse_pp": math.sqrt(sum(x * x for x in differences) / len(differences)),
        "max_abs_pp": max(map(abs, differences)),
    }


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H016 config-only stack/hit calibrator (dry-run by default)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--competitor-root", type=Path)
    parser.add_argument("--iterations", type=int, default=1000, help="pair-swap SA attempts per reel")
    parser.add_argument("--temperature", type=float, default=0.00002)
    parser.add_argument("--hit-iterations", type=int, default=50_000)
    parser.add_argument("--hit-samples", type=int, default=0, help="deprecated; exact Hit Rate is enumerated")
    parser.add_argument("--stack-tolerance", type=float, default=0.75, help="maximum additive mixed stack RMSE, percentage points")
    parser.add_argument("--seed", type=int, default=16016)
    parser.add_argument("--max-records", type=int, default=0, help="smoke cap; zero reads all selected JSONL")
    parser.add_argument("--multipliers-only", action="store_true", help="apply only the tested BG RTP guardrail")
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    path = args.config.expanduser().resolve()
    original, prefix, suffix = load_config(path)
    candidate, rng = copy.deepcopy(original), random.Random(args.seed)
    if args.multipliers_only:
        calibrate_multipliers(candidate)
        sync_aliases(candidate)
        errors = validate(candidate, original)
        report = {
            "mode": "write" if args.write else "dry-run",
            "scope": "BG multipliers only",
            "config": str(path),
            "bg_multipliers": BG_MULTIPLIERS,
            "validation": {"ok": not errors, "errors": errors},
            "written": False,
        }
        if args.write:
            if errors:
                raise ValueError("Refusing --write:\n- " + "\n- ".join(errors))
            atomic_write(path, prefix, suffix, candidate)
            report["written"] = True
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    folder = data_dir(args.competitor_root)
    files = input_files(folder)
    comp = read_competitor(files, max(0, args.max_records))
    before = {scene: stack_summary(original, comp, scene) for scene in ("BG", "FG")}
    sa: dict[str, list[dict[str, Any]]] = {"BG": [], "FG": []}
    for scene in ("BG", "FG"):
        table = candidate["tables"][PRIMARY[scene]]
        enforce_stops(PRIMARY[scene], table)
        optimized = []
        for reel in range(5):
            strip, metric = optimize_reel(table["reels"][reel], table["weights"][reel], target_stack(comp, scene, reel), args.iterations, args.temperature, rng)
            optimized.append(strip)
            sa[scene].append(metric)
        for name in VARIANTS[scene]:
            candidate["tables"][name]["reels"] = copy.deepcopy(optimized)
    for scene in ("BG", "FG"):
        for name in VARIANTS[scene]:
            enforce_stops(name, candidate["tables"][name])
    hit = {
        scene: greedy_hit(candidate, comp, scene, args.hit_iterations, args.stack_tolerance, rng)
        for scene in ("BG", "FG")
    }
    calibrate_drops(candidate, comp)
    calibrate_wild(candidate)
    calibrate_multipliers(candidate)
    sync_aliases(candidate)
    errors = validate(candidate, original)
    report = {
        "mode": "write" if args.write else "dry-run", "config": str(path),
        "competitor_dir": str(folder), "competitor_files": [x.name for x in files], "records": comp["records"],
        "samples": {scene: {"spins": comp["scenes"][scene]["spins"], "hit_rate": comp["scenes"][scene]["hits"] / comp["scenes"][scene]["spins"]} for scene in ("BG", "FG")},
        "stack": {scene: {"before": before[scene], "after": stack_summary(candidate, comp, scene), "sa": sa[scene]} for scene in ("BG", "FG")},
        "initial_hit_greedy": hit, "validation": {"ok": not errors, "errors": errors}, "written": False,
    }
    if args.write:
        if errors:
            raise ValueError("Refusing --write:\n- " + "\n- ".join(errors))
        atomic_write(path, prefix, suffix, candidate)
        report["written"] = True
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
