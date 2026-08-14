from __future__ import annotations

import argparse
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


WEIGHT_TOTAL = 1_000_000_000
TARGET_SF_RTP = 0.925
SUPER_PRICE = 250.0
MIN_SF_WEIGHTED_INDEX = 15  # (30, 35] is the first interval that guarantees > 30x.
SF_MID_RTP_INDICES = (27, 28, 29, 30, 31)  # (160,180] ... (300,350]
SF_HIGH_RTP_INDEX = 47  # (3000, 4000]
SF_MID_RTP_SHARE = 0.50
SF_HIGH_RTP_SHARE = 0.05
PROJECT_DIR = Path(__file__).resolve().parents[2]


def base_info(workbook) -> dict[str, Any]:
    return {
        str(row[0]): row[1]
        for row in workbook["Base Info"].iter_rows(min_row=2, values_only=True)
        if row[0] is not None
    }


def load_sf_report(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path, read_only=True, data_only=True, keep_links=False)
    try:
        fields = base_info(workbook)
        rows = list(workbook["Multiplier Line"].iter_rows(min_row=1, max_row=65, values_only=True))
        if len(rows) != 65:
            raise ValueError(f"{path.name}: expected header plus 64 multiplier buckets")
        header = {str(value): index for index, value in enumerate(rows[0]) if value is not None}
        required = {"Interval", "free_game_cnt_SF", "free_game_pay_SF"}
        missing = required.difference(header)
        if missing:
            raise ValueError(f"{path.name}: missing Multiplier Line columns {sorted(missing)}")
        count_column = header["free_game_cnt_SF"]
        pay_column = header["free_game_pay_SF"]
        data = rows[1:]
        result = {
            "path": str(path.resolve()),
            "rounds": int(fields["total_rounds"]),
            "coin_in": float(fields["coin_in"]),
            "rtp_total": float(fields["rtp_total"]),
            "rtp_fg": float(fields["rtp_fg"]),
            "bet_mode": str(fields["bet_mode"]),
            "card_system": str(fields["card_system"]),
            "intervals": [str(row[header["Interval"]]) for row in data],
            "sf_count": [int(row[count_column] or 0) for row in data],
            "sf_pay": [float(row[pay_column] or 0) for row in data],
        }
    finally:
        workbook.close()

    if result["bet_mode"] != "Buy Super Feature":
        raise ValueError(f"{path.name}: expected Buy Super Feature, got {result['bet_mode']!r}")
    if result["card_system"].lower() != "off":
        raise ValueError(f"{path.name}: SF natural report must have Card System off")
    if sum(result["sf_count"]) != result["rounds"]:
        raise ValueError(f"{path.name}: SF bucket count does not equal total rounds")
    observed_rtp = sum(result["sf_pay"]) / result["rounds"] / result["coin_in"]
    if abs(observed_rtp - result["rtp_total"]) > 1e-10:
        raise ValueError(
            f"{path.name}: SF bucket pay RTP {observed_rtp} differs from Base Info {result['rtp_total']}"
        )
    return result


def workbook_labels(path: Path) -> list[str]:
    workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
    try:
        labels = [str(workbook["Detail"].cell(row, 1).value or "").strip() for row in range(234, 298)]
    finally:
        workbook.close()
    if len(labels) != 64 or any(not label for label in labels):
        raise ValueError(f"{path.name}: Detail SF range labels are incomplete")
    return labels


def fix_numbers(weights: list[int], counts: list[int]) -> list[float]:
    total = sum(counts)
    result: list[float] = []
    for weight, count in zip(weights, counts):
        if count <= 0:
            if weight:
                raise ValueError("Positive SF weight assigned to a range absent from the 10^8 report")
            result.append(0.0)
        else:
            result.append((weight / WEIGHT_TOTAL) / (count / total))
    return result


def tilted_probabilities(raw: list[int], means: list[float], target_mean: float) -> list[float]:
    active = [index for index, value in enumerate(raw) if value > 0]
    if not active:
        raise ValueError("No supported SF ranges remain")
    low = min(means[index] for index in active)
    high = max(means[index] for index in active)
    if not low <= target_mean <= high:
        raise ValueError(f"SF target mean {target_mean} is outside supported range {low}..{high}")

    def probabilities(lam: float) -> list[float]:
        logs = [math.log(raw[index]) + lam * means[index] for index in active]
        pivot = max(logs)
        values = [math.exp(value - pivot) for value in logs]
        denominator = sum(values)
        result = [0.0] * len(raw)
        for index, value in zip(active, values):
            result[index] = value / denominator
        return result

    lower, upper = -1.0, 1.0
    while sum(p * m for p, m in zip(probabilities(lower), means)) > target_mean:
        lower *= 2
    while sum(p * m for p, m in zip(probabilities(upper), means)) < target_mean:
        upper *= 2
    for _ in range(180):
        middle = (lower + upper) / 2
        observed = sum(p * m for p, m in zip(probabilities(middle), means))
        if observed < target_mean:
            lower = middle
        else:
            upper = middle
    return probabilities((lower + upper) / 2)


def integerize_probabilities(probabilities: list[float]) -> list[int]:
    exact = [value * WEIGHT_TOTAL for value in probabilities]
    result = [math.floor(value) for value in exact]
    remainder = WEIGHT_TOTAL - sum(result)
    order = sorted(range(len(result)), key=lambda index: exact[index] - result[index], reverse=True)
    for index in order[:remainder]:
        result[index] += 1
    return result


def recalibrate_sf(
    baseline: dict[str, Any], labels: list[str], counts: list[int], pays: list[float], base_bet: float
) -> dict[str, Any]:
    baseline_weights = [int(value) for value in baseline["weights"]]
    if len(baseline_weights) != 64 or sum(baseline_weights) != WEIGHT_TOTAL:
        raise ValueError("Previous SF weights must contain 64 rows summing to 1,000,000,000")
    means = [pay / count / base_bet if count else 0.0 for count, pay in zip(counts, pays)]
    supported_paying = [
        index for index in range(1, 64)
        if baseline_weights[index] > 0 and counts[index] > 0 and means[index] > 0
    ]
    if not supported_paying:
        raise ValueError("The SF report has no supported paying buckets from the approved line")
    before = sum(baseline_weights[index] / WEIGHT_TOTAL * means[index] for index in supported_paying)
    target_scene_rtp = TARGET_SF_RTP * SUPER_PRICE

    # SF is guaranteed above 30x, so every interval below (30, 35] is disabled.
    # The two requested RTP groups are locked first; the remaining 45% keeps the
    # closest possible approved Hit Rate shape through a minimum-KL tilt.
    mid_indices = list(SF_MID_RTP_INDICES)
    high_index = SF_HIGH_RTP_INDEX
    remaining_indices = [
        index for index in range(MIN_SF_WEIGHTED_INDEX, 64)
        if index not in mid_indices
        and index != high_index
        and baseline_weights[index] > 0
        and counts[index] > 0
        and means[index] > 0
    ]
    if any(counts[index] <= 0 or means[index] <= 0 for index in (*mid_indices, high_index)):
        raise ValueError("The SF source report does not support every requested RTP interval")
    if not remaining_indices:
        raise ValueError("No supported SF intervals remain for the residual 45% RTP share")

    target_mid_rtp = target_scene_rtp * SF_MID_RTP_SHARE
    target_high_rtp = target_scene_rtp * SF_HIGH_RTP_SHARE
    target_remaining_rtp = target_scene_rtp - target_mid_rtp - target_high_rtp
    mid_denominator = sum(baseline_weights[index] * means[index] for index in mid_indices)
    if mid_denominator <= 0:
        raise ValueError("Previous SF weights cannot establish the requested five-range shape")

    probabilities = [0.0] * 64
    for index in mid_indices:
        probabilities[index] = baseline_weights[index] * target_mid_rtp / mid_denominator
    probabilities[high_index] = target_high_rtp / means[high_index]
    remaining_mass = 1.0 - sum(probabilities)
    if remaining_mass <= 0:
        raise ValueError("Requested SF RTP groups consume all available card probability")
    remaining_mean = target_remaining_rtp / remaining_mass
    remaining_raw = [
        baseline_weights[index] if index in remaining_indices else 0
        for index in range(64)
    ]
    remaining_shape = tilted_probabilities(remaining_raw, means, remaining_mean)
    for index in remaining_indices:
        probabilities[index] = remaining_mass * remaining_shape[index]

    weights = integerize_probabilities(probabilities)
    after = sum(weight / WEIGHT_TOTAL * mean for weight, mean in zip(weights, means))
    mid_after = sum(weights[index] / WEIGHT_TOTAL * means[index] for index in mid_indices)
    high_after = weights[high_index] / WEIGHT_TOTAL * means[high_index]
    remaining_after = after - mid_after - high_after
    if abs(after - target_scene_rtp) > 0.00075:
        raise ValueError(f"SF integerized target mismatch: {after} vs {target_scene_rtp}")
    if abs(mid_after / after - SF_MID_RTP_SHARE) > 0.0000001:
        raise ValueError(f"SF five-range RTP share mismatch: {mid_after / after}")
    if abs(high_after / after - SF_HIGH_RTP_SHARE) > 0.0000001:
        raise ValueError(f"SF (3000,4000] RTP share mismatch: {high_after / after}")
    if any(weights[index] for index in range(MIN_SF_WEIGHTED_INDEX)):
        raise ValueError("SF guarantee failed: an interval below (30,35] still has weight")

    audits = []
    total = sum(counts)
    for index, label in enumerate(labels):
        after_rtp = weights[index] / WEIGHT_TOTAL * means[index]
        audits.append({
            "index": index,
            "range": label,
            "rule": (
                "SF minimum 30x: disabled below (30,35]"
                if index < MIN_SF_WEIGHTED_INDEX
                else "Requested five-range group: 50% of total SF RTP"
                if index in mid_indices
                else "Requested (3000,4000] cap: 5% of total SF RTP"
                if index == high_index
                else "Residual 45%: minimum-KL adjustment from approved SF Hit Rate shape"
                if index in remaining_indices
                else "No approved/supported SF weight"
            ),
            "natural_rate": counts[index] / total,
            "natural_count": counts[index],
            "natural_mean": means[index],
            "before_weight": baseline_weights[index],
            "after_weight": weights[index],
            "target_scene_rtp": after_rtp,
            "target_rtp": after_rtp,
            "after_hit_rate": weights[index] / WEIGHT_TOTAL,
            "after_rtp": after_rtp,
            "after_rtp_share": after_rtp / after if after else 0.0,
            "shape_scale": (
                weights[index] / baseline_weights[index]
                if baseline_weights[index] > 0 and index in supported_paying
                else None
            ),
        })
    return {
        "weights": weights,
        "fix": fix_numbers(weights, counts),
        "audit": audits,
        "zero_bucket_before": baseline_weights[0],
        "zero_bucket_after": weights[0],
        "unrequested_mass_factor": 1.0,
        "calibration": (
            "SF >30x guarantee; five requested 160x-350x ranges take 50% of SF RTP; "
            "(3000,4000] takes 5%; residual 45% uses minimum-KL Hit Rate shaping"
        ),
        "minimum_weighted_index": MIN_SF_WEIGHTED_INDEX,
        "minimum_weighted_range": labels[MIN_SF_WEIGHTED_INDEX],
        "group_rtp": {
            "five_ranges_target_share": SF_MID_RTP_SHARE,
            "five_ranges_scene_rtp": mid_after,
            "five_ranges_actual_share": mid_after / after,
            "3000_4000_target_share": SF_HIGH_RTP_SHARE,
            "3000_4000_scene_rtp": high_after,
            "3000_4000_actual_share": high_after / after,
            "remaining_target_share": 1.0 - SF_MID_RTP_SHARE - SF_HIGH_RTP_SHARE,
            "remaining_scene_rtp": remaining_after,
            "remaining_actual_share": remaining_after / after,
        },
        "target_scene_rtp": target_scene_rtp,
        "scene_rtp_before": before,
        "scene_rtp_after": after,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recalculate H016 SF multiplier weights from a card-off SF report")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--previous-payload", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    report = load_sf_report(args.report.resolve())
    previous = json.loads(args.previous_payload.read_text(encoding="utf-8"))
    labels = workbook_labels(PROJECT_DIR / "Source" / "H016192A.xlsx")
    base_bet = report["coin_in"] / SUPER_PRICE
    if not math.isclose(base_bet, 100.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"Unexpected SF base bet: {base_bet}")

    payload = deepcopy(previous)
    for key in ("92", "94"):
        sf = recalibrate_sf(
            payload["versions"][key]["sf"], labels, report["sf_count"], report["sf_pay"], base_bet
        )
        payload["versions"][key]["sf"] = sf
        payload["versions"][key]["metrics"]["sf_rtp"] = sf["scene_rtp_after"] / SUPER_PRICE
    payload.setdefault("rules", {})["sf_rule"] = (
        "SF uses the H016 card-off 10^8 report at 92.5% RTP: no weight below (30,35], "
        "the five ranges (160,180] through (300,350] contribute 50% of SF RTP, "
        "(3000,4000] contributes 5%, and the residual 45% uses minimum-KL Hit Rate shaping"
    )
    payload["rules"]["sf_minimum_weighted_range"] = "(30,35]"
    payload["rules"]["sf_rtp_share_constraints"] = {
        "(160,180]..(300,350]": SF_MID_RTP_SHARE,
        "(3000,4000]": SF_HIGH_RTP_SHARE,
    }
    payload["rules"].setdefault("targets", {})["sf"] = TARGET_SF_RTP
    payload["sf_source_report"] = {
        "path": report["path"],
        "rounds": report["rounds"],
        "coin_in": report["coin_in"],
        "base_bet": base_bet,
        "observed_rtp": report["rtp_total"],
        "sf_count": report["sf_count"],
        "sf_pay": report["sf_pay"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output.resolve()),
        "source_rounds": report["rounds"],
        "source_rtp": report["rtp_total"],
        "target_sf_rtp": TARGET_SF_RTP,
        "versions": {
            key: {
                "scene_rtp_before": payload["versions"][key]["sf"]["scene_rtp_before"],
                "scene_rtp_after": payload["versions"][key]["sf"]["scene_rtp_after"],
                "sf_rtp_after": payload["versions"][key]["metrics"]["sf_rtp"],
                "zero_weight_after": payload["versions"][key]["sf"]["zero_bucket_after"],
                "weight_sum": sum(payload["versions"][key]["sf"]["weights"]),
            }
            for key in ("92", "94")
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
