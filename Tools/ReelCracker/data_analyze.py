import argparse
import ast
import json
import time
from pathlib import Path

import pandas as pd


DEFAULT_INPUT_FILE = "spin_responses_lucky_neko.xlsx"
REQUIRED_COLUMNS = [
    "si_sid",
    "si_psid",
    "si_st",
    "si_nst",
    "si_tb",
    "si_tbb",
    "si_aw",
    "si_tw",
    "si_fs",
]
MULTIPLIER_BINS = [
    (-1, 0),
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (8, 9),
    (9, 10),
    (10, 15),
    (15, 20),
    (20, 25),
    (25, 30),
    (30, 35),
    (35, 40),
    (40, 45),
    (45, 50),
    (50, 60),
    (60, 70),
    (70, 80),
    (80, 90),
    (90, 100),
    (100, 120),
    (120, 140),
    (140, 160),
    (160, 180),
    (180, 200),
    (200, 250),
    (250, 300),
    (300, 350),
    (350, 400),
    (400, 450),
    (450, 500),
    (500, 550),
    (550, 600),
    (600, 650),
    (650, 700),
    (700, 750),
    (750, 800),
    (800, 850),
    (850, 900),
    (900, 950),
    (950, 1000),
    (1000, 2000),
    (2000, 3000),
    (3000, 4000),
    (4000, 5000),
    (5000, 6000),
    (6000, 7000),
    (7000, 8000),
    (8000, 9000),
    (9000, 10000),
    (10000, 20000),
    (20000, 30000),
    (30000, 40000),
    (40000, 50000),
    (50000, 60000),
    (60000, 70000),
    (70000, 80000),
    (80000, 90000),
    (90000, 100000),
    (100000, 9999999),
]


STATE_NAME_MAP = {
    1: "base_spin",
    4: "cascade",
    21: "free_spin",
    22: "free_spin_cascade",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze Lucky Neko spin response data exported to Excel."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default=DEFAULT_INPUT_FILE,
        help="Path to the Excel file to analyze.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional directory for generated CSV/JSON reports.",
    )
    args, _unknown_args = parser.parse_known_args()
    return args


def validate_columns(df):
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing_text}")


def parse_cell(value):
    if pd.isna(value):
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value

    text = str(value).strip()
    if not text:
        return None

    for loader in (json.loads, ast.literal_eval):
        try:
            return loader(text)
        except Exception:
            continue

    return text


def to_int(value):
    if pd.isna(value):
        return None
    try:
        return int(value)
    except Exception:
        return None


def to_float(value):
    if pd.isna(value):
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


def root_spin_id(row):
    psid = row.get("si_psid")
    sid = row.get("si_sid")
    return str(int(psid if pd.notna(psid) else sid))


def state_name(state):
    return STATE_NAME_MAP.get(state, f"state_{state}")


def extract_free_spin_total(fs_value):
    payload = parse_cell(fs_value)
    if not isinstance(payload, dict):
        return 0

    candidates = []
    for key in ("ts", "s", "nosa"):
        value = payload.get(key)
        if isinstance(value, (int, float)):
            candidates.append(int(value))

    return max(candidates, default=0)


def is_state(row, value):
    return row["row_state"] == value


def format_bin_label(lower, upper):
    return f"({lower}, {upper}]"


def classify_multiplier(multiplier):
    for lower, upper in MULTIPLIER_BINS:
        if multiplier > lower and multiplier <= upper:
            return format_bin_label(lower, upper)
    return None


def build_multiplier_distribution(series):
    counts = {format_bin_label(lower, upper): 0 for lower, upper in MULTIPLIER_BINS}

    for value in series:
        bucket = classify_multiplier(float(value))
        if bucket is not None:
            counts[bucket] += 1

    return [
        {
            "range": label,
            "count": count,
            "rate": 0.0 if len(series) == 0 else round(count / len(series), 6),
        }
        for label, count in counts.items()
    ]


def count_distinct_symbols(board_value):
    board = parse_cell(board_value)
    if not isinstance(board, list):
        return 0
    return len(set(board))


def count_total_symbols(nowpr_value):
    nowpr = parse_cell(nowpr_value)
    if not isinstance(nowpr, list):
        return 0
    total = 0
    for value in nowpr:
        try:
            total += int(value)
        except Exception:
            continue
    return total


def normalize_nowpr(nowpr_value, reel_count=6):
    nowpr = parse_cell(nowpr_value)
    if not isinstance(nowpr, list):
        return [0] * reel_count

    normalized = []
    for value in nowpr[:reel_count]:
        try:
            normalized.append(int(value))
        except Exception:
            normalized.append(0)

    while len(normalized) < reel_count:
        normalized.append(0)

    return normalized


def analyze_round(round_df):
    round_df = round_df.copy()
    round_df["parsed_si_fs"] = round_df["si_fs"].apply(parse_cell)
    round_df["row_state"] = round_df["si_st"].apply(to_int)
    round_df["next_row_state"] = round_df["si_nst"].apply(to_int)

    first_row = round_df.iloc[0]
    last_row = round_df.iloc[-1]

    state_counts = (
        round_df["row_state"]
        .fillna(-1)
        .astype(int)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    state_counts = {
        state_name(state): count for state, count in state_counts.items() if state != -1
    }

    free_spin_total = max(round_df["si_fs"].apply(extract_free_spin_total), default=0)
    derived_rows = int((round_df["si_sid"] != round_df["si_psid"]).sum())
    cascade_rows = int((round_df["row_state"] == 4).sum() + (round_df["row_state"] == 22).sum())
    free_spin_rows = int((round_df["row_state"] == 21).sum())
    fg_rows = round_df[round_df["row_state"].isin([21, 22])]

    fg_total_win = float(fg_rows["si_tw"].sum()) if len(fg_rows) else 0.0
    bg_total_win = float(round_df["si_aw"].max()) - fg_total_win
    if bg_total_win < 0:
        bg_total_win = 0.0

    base_bet = to_float(first_row.get("si_tbb")) or to_float(first_row.get("si_tb"))
    bg_multiplier = 0.0 if base_bet == 0 else bg_total_win / base_bet
    fg_multiplier = 0.0 if base_bet == 0 else fg_total_win / base_bet
    bg_cascade_count = int((round_df["row_state"] == 4).sum())
    fg_cascade_count = int((round_df["row_state"] == 22).sum())
    distinct_symbol_count = count_distinct_symbols(first_row.get("si_orl"))
    nowpr_counts = normalize_nowpr(first_row.get("si_nowpr"))
    total_symbol_count = sum(nowpr_counts)

    return {
        "root_spin_id": root_spin_id(first_row),
        "row_count": int(len(round_df)),
        "derived_row_count": derived_rows,
        "base_spin_state": state_name(to_int(first_row.get("si_st"))),
        "final_state": state_name(to_int(last_row.get("si_st"))),
        "has_line_win": bool(round_df["si_lw"].notna().any()),
        "has_cascade": derived_rows > 0,
        "cascade_row_count": cascade_rows,
        "has_free_spin_trigger": free_spin_total > 0 or free_spin_rows > 0,
        "free_spin_awarded": free_spin_total,
        "free_spin_row_count": free_spin_rows,
        "total_bet": to_float(first_row.get("si_tb")),
        "base_bet": base_bet,
        "total_win": float(round_df["si_aw"].max()),
        "base_game_win": bg_total_win,
        "free_game_win": fg_total_win,
        "bg_multiplier": bg_multiplier,
        "fg_multiplier": fg_multiplier,
        "bg_cascade_count": bg_cascade_count,
        "fg_cascade_count": fg_cascade_count,
        "distinct_symbol_count": distinct_symbol_count,
        "total_symbol_count": total_symbol_count,
        "reel_symbol_counts": json.dumps(nowpr_counts, ensure_ascii=True),
        "ending_balance": to_float(last_row.get("si_bl")),
        "balance_before_spin": to_float(first_row.get("si_blb")),
        "balance_after_bet": to_float(first_row.get("si_blab")),
        "state_counts": json.dumps(state_counts, ensure_ascii=True),
    }


def build_round_dataframe(df):
    ordered = df.copy()
    ordered["root_spin_id"] = ordered.apply(root_spin_id, axis=1)
    ordered["row_order"] = range(len(ordered))

    round_rows = []
    for _, group in ordered.groupby("root_spin_id", sort=False):
        group = group.sort_values("row_order")
        round_rows.append(analyze_round(group))

    return pd.DataFrame(round_rows)


def summarize(df, round_df):
    total_bet = round_df["total_bet"].sum()
    total_win = round_df["total_win"].sum()
    bg_total_win = round_df["base_game_win"].sum()
    fg_total_win = round_df["free_game_win"].sum()
    fg_triggered = round_df[round_df["has_free_spin_trigger"]].copy()

    summary = {
        "source_file": str(df.attrs.get("source_file", "")),
        "total_rows": int(len(df)),
        "total_root_spins": int(len(round_df)),
        "rows_per_spin_avg": round(len(df) / len(round_df), 4) if len(round_df) else 0.0,
        "total_bet": round(float(total_bet), 4),
        "total_win": round(float(total_win), 4),
        "total_rtp": round(float(total_win / total_bet), 6) if total_bet else 0.0,
        "bg_rtp": round(float(bg_total_win / total_bet), 6) if total_bet else 0.0,
        "fg_rtp": round(float(fg_total_win / total_bet), 6) if total_bet else 0.0,
        "winning_spins": int((round_df["total_win"] > 0).sum()),
        "winning_spin_rate": round(
            float((round_df["total_win"] > 0).mean()), 6
        ) if len(round_df) else 0.0,
        "spins_with_cascade": int(round_df["has_cascade"].sum()),
        "cascade_trigger_rate": round(
            float(round_df["has_cascade"].mean()), 6
        ) if len(round_df) else 0.0,
        "spins_with_free_spin_trigger": int(round_df["has_free_spin_trigger"].sum()),
        "free_spin_trigger_rate": round(
            float(round_df["has_free_spin_trigger"].mean()), 6
        ) if len(round_df) else 0.0,
        "total_free_spins_awarded": int(round_df["free_spin_awarded"].sum()),
        "avg_free_spins_per_trigger": round(
            float(fg_triggered["free_spin_awarded"].mean()), 6
        ) if len(fg_triggered) else 0.0,
        "total_free_spin_rows": int(round_df["free_spin_row_count"].sum()),
        "max_single_spin_win": round(float(round_df["total_win"].max()), 4)
        if len(round_df)
        else 0.0,
    }

    return summary


def build_distribution_payload(round_df):
    bg_distribution = build_multiplier_distribution(round_df["bg_multiplier"].tolist())
    fg_triggered = round_df[round_df["has_free_spin_trigger"]].copy()
    fg_distribution = build_multiplier_distribution(fg_triggered["fg_multiplier"].tolist())

    return {
        "bg": {
            "sample_count": int(len(round_df)),
            "distribution": bg_distribution,
        },
        "fg": {
            "sample_count": int(len(fg_triggered)),
            "distribution": fg_distribution,
        },
    }


def build_cascade_distribution(round_df):
    bg_total_spins = len(round_df)
    fg_triggered = round_df[round_df["has_free_spin_trigger"]].copy()
    fg_total_spins = len(fg_triggered)

    def build_counts(series, denominator):
        result = []
        for count_value in range(10):
            count = int((series == count_value).sum())
            result.append(
                {
                    "cascade_count": count_value,
                    "count": count,
                    "rate": 0.0 if denominator == 0 else round(count / denominator, 6),
                }
            )
        return result

    return {
        "bg": {
            "sample_count": int(bg_total_spins),
            "distribution": build_counts(round_df["bg_cascade_count"], bg_total_spins),
        },
        "fg": {
            "sample_count": int(fg_total_spins),
            "distribution": build_counts(fg_triggered["fg_cascade_count"], fg_total_spins),
        },
    }


def build_symbol_count_distribution(round_df):
    total_spins = len(round_df)
    counts = (
        round_df["total_symbol_count"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    distribution = []
    for symbol_count, count in counts.items():
        distribution.append(
            {
                "symbol_count": int(symbol_count),
                "count": int(count),
                "rate": 0.0 if total_spins == 0 else round(int(count) / total_spins, 6),
            }
        )

    return {
        "sample_count": int(total_spins),
        "distribution": distribution,
    }


def build_reel_symbol_count_distribution(round_df, reel_count=6, symbol_counts=None):
    if symbol_counts is None:
        symbol_counts = [2, 3, 4, 5, 6]

    total_spins = len(round_df)
    matrix = {symbol_count: {} for symbol_count in symbol_counts}

    parsed_counts = round_df["reel_symbol_counts"].apply(parse_cell).tolist()
    for reel_index in range(reel_count):
        reel_name = f"R{reel_index + 1}"
        reel_values = []
        for row in parsed_counts:
            if isinstance(row, list) and reel_index < len(row):
                reel_values.append(row[reel_index])
            else:
                reel_values.append(0)

        for symbol_count in symbol_counts:
            count = sum(1 for value in reel_values if value == symbol_count)
            matrix[symbol_count][reel_name] = 0.0 if total_spins == 0 else round(count / total_spins, 6)

    return {
        "sample_count": int(total_spins),
        "rows": matrix,
    }


def infer_game_id(input_path):
    return input_path.stem


def infer_bet_mode(round_df):
    return "Normal Bet"


def infer_bet_multi(round_df):
    if "si_ml" not in round_df.columns:
        return "-"
    values = [str(int(value)) for value in round_df["si_ml"].dropna().unique()]
    return ",".join(values) if values else "-"


def infer_coin_in(round_df):
    if "base_bet" not in round_df.columns or round_df.empty:
        return 0
    return round(float(round_df["base_bet"].iloc[0]), 6)


def format_metric_block(summary, round_df, input_path, duration_sec):
    fg_triggered = round_df[round_df["has_free_spin_trigger"]].copy()
    fg_hit_rate = (
        float((round_df["free_game_win"] > 0).sum() / len(round_df)) if len(round_df) else 0.0
    )
    bg_hit_rate = float((round_df["base_game_win"] > 0).mean()) if len(round_df) else 0.0
    total_hit_rate = float((round_df["total_win"] > 0).mean()) if len(round_df) else 0.0
    retrigger_rate = (
        float((fg_triggered["free_spin_awarded"] > 10).mean()) if len(fg_triggered) else 0.0
    )
    avg_fg_multiplier = (
        float(fg_triggered["fg_multiplier"].mean()) if len(fg_triggered) else 0.0
    )

    rows = [
        ("total_rounds", summary["total_root_spins"]),
        ("fg_count", int(round_df["has_free_spin_trigger"].sum())),
        ("rtp_total", f'{summary["total_rtp"]:.6f}'),
        ("rtp_bg", f'{summary["bg_rtp"]:.6f}'),
        ("rtp_fg", f'{summary["fg_rtp"]:.6f}'),
        ("hit_rate_bg", f"{bg_hit_rate:.6f}"),
        ("hit_rate_fg", f"{fg_hit_rate:.6f}"),
        ("hit_rate_total", f"{total_hit_rate:.6f}"),
        ("fg_trigger_rate", f'{summary["free_spin_trigger_rate"]:.6f}'),
        ("retrigger_rate", f"{retrigger_rate:.6f}"),
        ("avg_fg_multiplier", f"{avg_fg_multiplier:.6f}"),
        ("avg_free_spins", f'{summary["avg_free_spins_per_trigger"]:.6f}'),
    ]

    label_width = max(len(label) for label, _ in rows if label)
    lines = []
    for label, value in rows:
        if not label:
            lines.append("")
            continue
        lines.append(f"{label:<{label_width}} : {value}")
    return "\n".join(lines)


def format_multiplier_distribution(title, payload):
    lines = [title]
    for item in payload["distribution"]:
        lower, upper = item["range"][1:-1].split(", ")
        lines.append(f"{lower} < x <= {upper:<7}: {item['rate']:.6f}")
    return "\n".join(lines)


def format_cascade_distribution(title, payload):
    lines = [title]
    for item in payload["distribution"]:
        count_value = item["cascade_count"]
        lines.append(f"{count_value} cascades : {item['rate']:.6f}")
    return "\n".join(lines)


def format_symbol_count_distribution(title, payload):
    lines = [title]
    for item in payload["distribution"]:
        lines.append(f"{item['symbol_count']} symbols : {item['rate']:.6f}")
    return "\n".join(lines)


def format_reel_symbol_count_distribution(title, payload):
    reel_names = [f"R{index}" for index in range(1, 7)]
    header = "     " + " ".join(f"{name:>8}" for name in reel_names)
    lines = [title, header]
    for symbol_count in sorted(payload["rows"].keys()):
        values = " ".join(f"{payload['rows'][symbol_count][name]:>8.6f}" for name in reel_names)
        lines.append(f"{symbol_count}顆  {values}")
    return "\n".join(lines)


def format_multiplier_bin_list(title):
    lines = [title]
    for lower, upper in MULTIPLIER_BINS:
        lines.append(f"{lower} < x <= {upper}")
    return "\n".join(lines)


def main():
    started_at = time.perf_counter()
    args = parse_args()
    input_path = Path(args.input_file).resolve()

    df = pd.read_excel(input_path)
    validate_columns(df)
    df.attrs["source_file"] = str(input_path)

    round_df = build_round_dataframe(df)
    summary = summarize(df, round_df)
    distributions = build_distribution_payload(round_df)
    cascade_distribution = build_cascade_distribution(round_df)
    symbol_count_distribution = build_symbol_count_distribution(round_df)
    reel_symbol_count_distribution = build_reel_symbol_count_distribution(round_df)
    duration_sec = time.perf_counter() - started_at

    print(format_metric_block(summary, round_df, input_path, duration_sec))
    print("")
    print(format_multiplier_distribution("bg_multiplier_distribution", distributions["bg"]))
    print("")
    print(format_multiplier_distribution("fg_multiplier_distribution", distributions["fg"]))
    print("")
    print(format_symbol_count_distribution("round_symbol_count_distribution", symbol_count_distribution))
    print("")
    print(format_reel_symbol_count_distribution("reel_symbol_count_distribution", reel_symbol_count_distribution))
    print("")
    print(format_multiplier_bin_list("multiplier_bins"))

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        summary_path = output_dir / f"{input_path.stem}_summary.json"
        round_path = output_dir / f"{input_path.stem}_rounds.csv"
        distribution_path = output_dir / f"{input_path.stem}_multiplier_distribution.json"
        cascade_path = output_dir / f"{input_path.stem}_cascade_distribution.json"
        symbol_count_path = output_dir / f"{input_path.stem}_symbol_count_distribution.json"
        reel_symbol_count_path = output_dir / f"{input_path.stem}_reel_symbol_count_distribution.json"

        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        distribution_path.write_text(
            json.dumps(distributions, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        cascade_path.write_text(
            json.dumps(cascade_distribution, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        symbol_count_path.write_text(
            json.dumps(symbol_count_distribution, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        reel_symbol_count_path.write_text(
            json.dumps(reel_symbol_count_distribution, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        round_df.to_csv(round_path, index=False, encoding="utf-8-sig")

        print(f"Saved round report: {round_path}")
        print(f"Saved summary report: {summary_path}")
        print(f"Saved multiplier distribution: {distribution_path}")
        print(f"Saved cascade distribution: {cascade_path}")
        print(f"Saved symbol count distribution: {symbol_count_path}")
        print(f"Saved reel symbol count distribution: {reel_symbol_count_path}")


if __name__ == "__main__":
    main()
