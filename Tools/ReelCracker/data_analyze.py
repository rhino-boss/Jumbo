import argparse
import ast
import json
import time
from pathlib import Path
from datetime import timedelta

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_FILE = str((BASE_DIR / "spin_responses_lucky_neko_all.xlsx").resolve())
DEFAULT_SHEET_NAME = "spin_data_new"
DEFAULT_MAX_ROWS = 69779  # 69779
DEFAULT_OUTPUT_DIR = str((BASE_DIR / "analysis_output").resolve())
SHOW_OVERVIEW = True
SHOW_MULTIPLIER_RANGE = True
SHOW_COMBO_RATE = True
SHOW_REEL_HIGH_DISTRIBUTION = True
SHOW_SILVER_DISTRIBUTION = True
SHOW_EXTRA_REEL = True
SHOW_SYMBOL_SIZE_DISTRIBUTION = True
SHOW_M1_METRICS = True
SHOW_RTP_HIT_RATE = True
SHOW_SYMBOL_OCCURRENCE_RATE = True
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
    parser = argparse.ArgumentParser(description="Analyze Lucky Neko spin response data exported to Excel.")
    parser.add_argument(
        "input_file",
        nargs="?",
        default=DEFAULT_INPUT_FILE,
        help="Path to the Excel file to analyze.",
    )
    parser.add_argument(
        "--sheet-name",
        default=DEFAULT_SHEET_NAME,
        help="Worksheet name to analyze.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=DEFAULT_MAX_ROWS,
        help="Maximum number of rows to analyze from the worksheet.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the generated analysis workbook.",
    )
    args, _unknown_args = parser.parse_known_args()
    return args


def resolve_path(path_value):
    path = Path(path_value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


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


def iter_free_spin_segments(group):
    ordered_group = group.reset_index(drop=True)
    index = 0
    while index < len(ordered_group):
        if to_int(ordered_group.iloc[index].get("si_st")) != 21:
            index += 1
            continue

        end = index + 1
        while end < len(ordered_group) and to_int(ordered_group.iloc[end].get("si_st")) == 22:
            end += 1

        segment = ordered_group.iloc[index:end].copy()
        last_next_state = to_int(segment.iloc[-1].get("si_nst"))
        if last_next_state in (1, 21):
            yield segment

        index = end


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


def build_reel_ranges(nowpr_counts):
    ranges = []
    start = 0
    for count in nowpr_counts:
        end = start + max(int(count), 0)
        ranges.append((start, end))
        start = end
    return ranges


def get_reel_index(position, reel_ranges):
    for reel_index, (start, end) in enumerate(reel_ranges):
        if start <= position < end:
            return reel_index
    return None


def get_frame_kind(item):
    if not isinstance(item, dict):
        return None

    bt = to_int(item.get("bt"))
    ls = to_int(item.get("ls"))
    if bt == 1 and ls == 2:
        return "silver"
    if bt == 1 and ls == 1:
        return "gold"
    if bt == 2 and ls == 1:
        return "normal"
    return None


def count_silver_frames(eb_value, nowpr_counts):
    eb = parse_cell(eb_value)
    if not isinstance(eb, dict):
        return [0] * len(nowpr_counts)

    reel_ranges = build_reel_ranges(nowpr_counts)
    silver_counts = [0] * len(nowpr_counts)

    for item in eb.values():
        if get_frame_kind(item) != "silver":
            continue
        fp = item.get("fp")
        if not isinstance(fp, int):
            continue
        reel_index = get_reel_index(fp, reel_ranges)
        if reel_index is not None:
            silver_counts[reel_index] += 1

    return silver_counts


def extract_silver_positions(eb_value):
    eb = parse_cell(eb_value)
    if not isinstance(eb, dict):
        return set()

    positions = set()
    for item in eb.values():
        if get_frame_kind(item) != "silver":
            continue
        fp = item.get("fp")
        lp = item.get("lp")
        if not isinstance(fp, int) or not isinstance(lp, int):
            continue
        for position in range(fp, lp + 1):
            positions.add(position)
    return positions


def count_new_drop_silver_frames(current_eb, nowpr_counts, previous_orl, current_orl):
    prev_board = parse_cell(previous_orl)
    curr_board = parse_cell(current_orl)
    if not isinstance(prev_board, list) or not isinstance(curr_board, list):
        return [0] * len(nowpr_counts)

    eb = parse_cell(current_eb)
    if not isinstance(eb, dict):
        return [0] * len(nowpr_counts)

    reel_ranges = build_reel_ranges(nowpr_counts)
    silver_counts = [0] * len(nowpr_counts)

    max_len = min(len(prev_board), len(curr_board))

    for item in eb.values():
        if get_frame_kind(item) != "silver":
            continue
        fp = item.get("fp")
        lp = item.get("lp")
        if not isinstance(fp, int) or not isinstance(lp, int):
            continue

        has_drop_change = False
        for position in range(fp, min(lp, max_len - 1) + 1):
            if prev_board[position] != curr_board[position]:
                has_drop_change = True
                break

        if not has_drop_change:
            continue

        reel_index = get_reel_index(fp, reel_ranges)
        if reel_index is not None:
            silver_counts[reel_index] += 1

    return silver_counts


def analyze_round(round_df):
    round_df = round_df.copy()
    round_df["parsed_si_fs"] = round_df["si_fs"].apply(parse_cell)
    round_df["row_state"] = round_df["si_st"].apply(to_int)
    round_df["next_row_state"] = round_df["si_nst"].apply(to_int)

    first_row = round_df.iloc[0]
    last_row = round_df.iloc[-1]

    state_counts = round_df["row_state"].fillna(-1).astype(int).value_counts().sort_index().to_dict()
    state_counts = {state_name(state): count for state, count in state_counts.items() if state != -1}

    free_spin_total = max(round_df["si_fs"].apply(extract_free_spin_total), default=0)
    derived_rows = int((round_df["si_sid"] != round_df["si_psid"]).sum())
    cascade_rows = int((round_df["row_state"] == 4).sum() + (round_df["row_state"] == 22).sum())
    free_spin_rows = int((round_df["row_state"] == 21).sum())
    fg_rows = round_df[round_df["row_state"].isin([21, 22])]
    fg_segments = list(iter_free_spin_segments(round_df))
    free_spin_count = len(fg_segments)
    free_spin_hit_count = sum(1 for segment in fg_segments if float(segment["si_tw"].apply(to_float).sum()) > 0)

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
    silver_frame_counts = count_silver_frames(first_row.get("si_eb"), nowpr_counts)

    return {
        "root_spin_id": root_spin_id(first_row),
        "row_count": int(len(round_df)),
        "derived_row_count": derived_rows,
        "base_spin_state": state_name(to_int(first_row.get("si_st"))),
        "final_state": state_name(to_int(last_row.get("si_st"))),
        "has_line_win": bool(round_df["si_lw"].notna().any()) if "si_lw" in round_df.columns else False,
        "has_cascade": derived_rows > 0,
        "cascade_row_count": cascade_rows,
        "has_free_spin_trigger": free_spin_total > 0 or free_spin_rows > 0 or free_spin_count > 0,
        "free_spin_awarded": free_spin_total,
        "free_spin_count": free_spin_count,
        "free_spin_hit_count": free_spin_hit_count,
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
        "reel_silver_counts": json.dumps(silver_frame_counts, ensure_ascii=True),
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
        group = group.sort_values("row_order").reset_index(drop=True)
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
        "winning_spin_rate": round(float((round_df["total_win"] > 0).mean()), 6) if len(round_df) else 0.0,
        "spins_with_cascade": int(round_df["has_cascade"].sum()),
        "cascade_trigger_rate": round(float(round_df["has_cascade"].mean()), 6) if len(round_df) else 0.0,
        "spins_with_free_spin_trigger": int(round_df["has_free_spin_trigger"].sum()),
        "free_spin_trigger_rate": round(float(round_df["has_free_spin_trigger"].mean()), 6) if len(round_df) else 0.0,
        "total_free_spins_awarded": int(round_df["free_spin_count"].sum()),
        "avg_free_spins_per_trigger": round(float(fg_triggered["free_spin_count"].mean()), 6) if len(fg_triggered) else 0.0,
        "total_free_spin_rows": int(round_df["free_spin_row_count"].sum()),
        "max_single_spin_win": round(float(round_df["total_win"].max()), 4) if len(round_df) else 0.0,
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


def build_combo_rate_rows(combo_counts, denominator):
    rows = []
    for combo_value in range(1, 10):
        count = sum(1 for value in combo_counts if value == combo_value)
        rate = 0.0 if denominator == 0 else round(count / denominator, 6)
        rows.append(
            {
                "label": f"Combo {combo_value}",
                "combo_count": combo_value,
                "hit_count": count,
                "rate": rate,
            }
        )

    combo_10_plus_count = sum(1 for value in combo_counts if value >= 10)
    combo_10_plus_rate = 0.0 if denominator == 0 else round(combo_10_plus_count / denominator, 6)
    rows.append(
        {
            "label": "Combo 10+",
            "combo_count": "10+",
            "hit_count": combo_10_plus_count,
            "rate": combo_10_plus_rate,
        }
    )
    rows.append(
        {
            "label": "Max Hit",
            "combo_count": max(combo_counts, default=0),
            "hit_count": "",
            "rate": "",
        }
    )
    return rows


def build_combo_rate_payload(df):
    ordered = df.copy()
    ordered["root_spin_id"] = ordered.apply(root_spin_id, axis=1)
    ordered["row_order"] = range(len(ordered))
    ordered["row_state"] = ordered["si_st"].apply(to_int)
    ordered["row_tw"] = ordered["si_tw"].apply(to_float)

    bg_combo_counts = []
    fg_combo_counts = []

    for _, group in ordered.groupby("root_spin_id", sort=False):
        group = group.sort_values("row_order").reset_index(drop=True)
        if group.empty:
            continue

        first_state = to_int(group.iloc[0].get("si_st"))
        if first_state == 1:
            bg_end = 1
            while bg_end < len(group) and to_int(group.iloc[bg_end].get("si_st")) == 4:
                bg_end += 1

            bg_segment = group.iloc[:bg_end]
            bg_combo = 0 if bg_segment["row_tw"].sum() <= 0 else 1 + int((bg_segment["row_state"] == 4).sum())
            bg_combo_counts.append(bg_combo)

        for fg_segment in iter_free_spin_segments(group):
            fg_combo = 0 if fg_segment["row_tw"].sum() <= 0 else 1 + int((fg_segment["row_state"] == 22).sum())
            fg_combo_counts.append(fg_combo)

    return {
        "bg": {
            "sample_count": int(len(bg_combo_counts)),
            "distribution": build_combo_rate_rows(bg_combo_counts, len(bg_combo_counts)),
        },
        "fg": {
            "sample_count": int(len(fg_combo_counts)),
            "distribution": build_combo_rate_rows(fg_combo_counts, len(fg_combo_counts)),
        },
    }


def build_extra_reel_same_symbol_payload(df):
    working = df.copy()
    working["row_state"] = working["si_st"].apply(to_int)

    def build_for_states(states):
        symbol_counts = {}
        symbol_counts_more2 = {}
        valid_row_count = 0
        subset = working[working["row_state"].isin(states)]

        for value in subset.get("si_trl", []):
            trl = parse_cell(value)
            if not isinstance(trl, list) or len(trl) != 4:
                continue

            normalized = []
            for item in trl:
                item_int = to_int(item)
                if item_int is None:
                    normalized = []
                    break
                normalized.append(item_int)

            if len(normalized) != 4:
                continue

            valid_row_count += 1
            if len(set(normalized)) != 1:
                if normalized[0] == normalized[1]:
                    symbol_id = normalized[0]
                    symbol_counts_more2[symbol_id] = symbol_counts_more2.get(symbol_id, 0) + 1
                continue

            symbol_id = normalized[0]
            symbol_counts[symbol_id] = symbol_counts.get(symbol_id, 0) + 1
            symbol_counts_more2[symbol_id] = symbol_counts_more2.get(symbol_id, 0) + 1

        return valid_row_count, symbol_counts, symbol_counts_more2

    bg_sample_count, bg_symbol_counts, bg_symbol_counts_more2 = build_for_states([1])
    fg_sample_count, fg_symbol_counts, fg_symbol_counts_more2 = build_for_states([21, 22])
    all_symbol_ids = sorted(set(bg_symbol_counts.keys()) | set(fg_symbol_counts.keys()) | set(bg_symbol_counts_more2.keys()) | set(fg_symbol_counts_more2.keys()))

    rows = []
    for symbol_id in all_symbol_ids:
        hit_count_bg = bg_symbol_counts.get(symbol_id, 0)
        hit_count_fg = fg_symbol_counts.get(symbol_id, 0)
        hit_count_bg_more2 = bg_symbol_counts_more2.get(symbol_id, 0)
        hit_count_fg_more2 = fg_symbol_counts_more2.get(symbol_id, 0)
        rows.append(
            {
                "symbol_id": symbol_id,
                "hit_count_BG": hit_count_bg,
                "hit_count_BG_more2": hit_count_bg_more2,
                "rate_BG": 0.0 if bg_sample_count == 0 else round(hit_count_bg / bg_sample_count, 6),
                "hit_count_FG": hit_count_fg,
                "hit_count_FG_more2": hit_count_fg_more2,
                "rate_FG": 0.0 if fg_sample_count == 0 else round(hit_count_fg / fg_sample_count, 6),
            }
        )

    return {
        "sample_count_BG": int(bg_sample_count),
        "sample_count_FG": int(fg_sample_count),
        "distribution": rows,
    }


def iter_symbol_runs(board_value, nowpr_value):
    board = parse_cell(board_value)
    nowpr_counts = normalize_nowpr(nowpr_value)
    if not isinstance(board, list):
        return

    start = 0
    for reel_count in nowpr_counts:
        end = start + max(int(reel_count), 0)
        reel_symbols = board[start:end]
        start = end
        if not reel_symbols:
            continue

        run_symbol = reel_symbols[0]
        run_length = 1
        for symbol in reel_symbols[1:]:
            if symbol == run_symbol:
                run_length += 1
                continue
            yield run_symbol, run_length
            run_symbol = symbol
            run_length = 1
        yield run_symbol, run_length


def build_symbol_size_distribution_payload(df):
    working = df.copy()
    working["row_state"] = working["si_st"].apply(to_int)

    def build_for_states(states):
        symbol_size_counts = {}
        subset = working[working["row_state"].isin(states)]
        for _, row in subset.iterrows():
            for symbol_id, run_length in iter_symbol_runs(row.get("si_orl"), row.get("si_nowpr")):
                symbol_id = to_int(symbol_id)
                if symbol_id is None:
                    continue
                if run_length not in (1, 2, 3, 4):
                    continue
                size_counts = symbol_size_counts.setdefault(symbol_id, {1: 0, 2: 0, 3: 0, 4: 0})
                size_counts[run_length] += 1

        rows = []
        for symbol_id in sorted(symbol_size_counts.keys()):
            size_counts = symbol_size_counts[symbol_id]
            total = sum(size_counts.values())
            rows.append(
                {
                    "symbol_id": symbol_id,
                    "1x1": size_counts[1],
                    "2x1": size_counts[2],
                    "3x1": size_counts[3],
                    "4x1": size_counts[4],
                    "symbol_total_count": total,
                }
            )
        return rows

    return {
        "bg": build_for_states([1]),
        "fg": build_for_states([21]),
    }


def build_m1_metrics_payload(df, symbol_id=2):
    ordered = df.copy()
    ordered["root_spin_id"] = ordered.apply(root_spin_id, axis=1)
    ordered["row_order"] = range(len(ordered))
    ordered["row_state"] = ordered["si_st"].apply(to_int)

    bg_total_spins = 0
    fg_total_spins = 0
    bg_spins_with_m1 = 0
    fg_spins_with_m1 = 0
    bg_spins_with_m1_and_win = 0
    fg_spins_with_m1_and_win = 0

    for _, group in ordered.groupby("root_spin_id", sort=False):
        group = group.sort_values("row_order")

        bg_rows = []
        index = 0
        while index < len(group) and group.iloc[index]["row_state"] in (1, 4):
            bg_rows.append(group.iloc[index])
            index += 1

        if bg_rows:
            bg_total_spins += 1
            bg_board = parse_cell(bg_rows[0].get("si_orl"))
            bg_has_m1 = isinstance(bg_board, list) and any(to_int(symbol) == symbol_id for symbol in bg_board)
            if bg_has_m1:
                bg_spins_with_m1 += 1
                bg_has_win = any(to_float(row.get("si_tw")) > 0 for row in bg_rows)
                if bg_has_win:
                    bg_spins_with_m1_and_win += 1

        for fg_segment in iter_free_spin_segments(group):
            fg_total_spins += 1
            fg_board = parse_cell(fg_segment.iloc[0].get("si_orl"))
            fg_has_m1 = isinstance(fg_board, list) and any(to_int(symbol) == symbol_id for symbol in fg_board)
            if fg_has_m1:
                fg_spins_with_m1 += 1
                fg_has_win = any(to_float(row.get("si_tw")) > 0 for _, row in fg_segment.iterrows())
                if fg_has_win:
                    fg_spins_with_m1_and_win += 1

    bg_appearance_rate = 0.0 if bg_total_spins == 0 else round(bg_spins_with_m1 / bg_total_spins, 6)
    fg_appearance_rate = 0.0 if fg_total_spins == 0 else round(fg_spins_with_m1 / fg_total_spins, 6)
    bg_usage_rate = 0.0 if bg_spins_with_m1 == 0 else round(bg_spins_with_m1_and_win / bg_spins_with_m1, 6)
    fg_usage_rate = 0.0 if fg_spins_with_m1 == 0 else round(fg_spins_with_m1_and_win / fg_spins_with_m1, 6)
    bucket_labels = [f"{count}顆" for count in range(1, 16)] + ["15顆+"]
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    distribution_counts = {bucket: {column: 0 for column in distribution_columns} for bucket in bucket_labels}
    sample_counts = {column: 0 for column in distribution_columns}

    for _, group in ordered.groupby("root_spin_id", sort=False):
        group = group.sort_values("row_order").reset_index(drop=True)
        free_spin_index = 0

        if not group.empty and group.iloc[0]["row_state"] == 1:
            board = parse_cell(group.iloc[0].get("si_orl"))
            if isinstance(board, list):
                sample_counts["BG"] += 1
                symbol_count = sum(1 for symbol in board if to_int(symbol) == symbol_id)
                if symbol_count > 0:
                    bucket = "15顆+" if symbol_count >= 15 else f"{symbol_count}顆"
                    distribution_counts[bucket]["BG"] += 1

        for fg_segment in iter_free_spin_segments(group):
            free_spin_index += 1
            if free_spin_index > 10:
                continue
            board = parse_cell(fg_segment.iloc[0].get("si_orl"))
            if isinstance(board, list):
                column = f"F{free_spin_index}"
                sample_counts[column] += 1
                symbol_count = sum(1 for symbol in board if to_int(symbol) == symbol_id)
                if symbol_count > 0:
                    bucket = "15顆+" if symbol_count >= 15 else f"{symbol_count}顆"
                    distribution_counts[bucket][column] += 1

    distribution_rows = []
    for bucket in bucket_labels:
        row = {"num": bucket}
        for column in distribution_columns:
            denominator = sample_counts[column]
            hit_count = distribution_counts[bucket][column]
            row[column] = 0.0 if denominator == 0 else round(hit_count / denominator, 6)
        distribution_rows.append(row)

    return {
        "symbol_id": symbol_id,
        "bg_total_spins": bg_total_spins,
        "fg_total_spins": fg_total_spins,
        "bg_spins_with_symbol": bg_spins_with_m1,
        "fg_spins_with_symbol": fg_spins_with_m1,
        "bg_spins_with_symbol_and_win": bg_spins_with_m1_and_win,
        "fg_spins_with_symbol_and_win": fg_spins_with_m1_and_win,
        "bg_appearance_rate": bg_appearance_rate,
        "fg_appearance_rate": fg_appearance_rate,
        "bg_usage_rate": bg_usage_rate,
        "fg_usage_rate": fg_usage_rate,
        "sample_counts": sample_counts,
        "distribution_rows": distribution_rows,
    }


def extract_symbol_line_entries(row):
    bwp = parse_cell(row.get("si_bwp"))
    snww = parse_cell(row.get("si_snww"))
    rwsp = parse_cell(row.get("si_rwsp"))
    twp = parse_cell(row.get("si_twp"))
    row_ctw = to_float(row.get("si_ctw"))

    if not isinstance(bwp, dict) or not isinstance(snww, dict) or not isinstance(rwsp, dict):
        return []

    entries = []
    raw_total = 0.0
    for symbol_key, groups in bwp.items():
        if not isinstance(groups, list):
            continue
        symbol_id = to_int(symbol_key)
        ways = to_float(snww.get(symbol_key)) if isinstance(snww, dict) else 0.0
        payout = to_float(rwsp.get(symbol_key)) if isinstance(rwsp, dict) else 0.0
        extra_groups = 0
        if isinstance(twp, dict):
            twp_value = twp.get(symbol_key)
            if isinstance(twp_value, list):
                extra_groups = len(twp_value)

        line_count = len(groups) + extra_groups
        if line_count < 3:
            continue
        if line_count > 6:
            line_count = 6

        raw_value = payout * ways
        if symbol_id is None or raw_value <= 0:
            continue
        raw_total += raw_value
        entries.append(
            {
                "symbol_id": symbol_id,
                "line_count": line_count,
                "raw_value": raw_value,
            }
        )

    if raw_total <= 0 or row_ctw <= 0:
        return []

    for entry in entries:
        entry["win_value"] = row_ctw * (entry["raw_value"] / raw_total)
    return entries


def build_symbol_line_rtp_hit_payload(df):
    working = df.copy()
    working["root_spin_id"] = working.apply(root_spin_id, axis=1)
    working["row_order"] = range(len(working))
    working["row_state"] = working["si_st"].apply(to_int)

    symbol_ids = set()
    for board_value in working["si_orl"].tolist():
        board = parse_cell(board_value)
        if isinstance(board, list):
            for symbol in board:
                symbol_id = to_int(symbol)
                if symbol_id is not None:
                    symbol_ids.add(symbol_id)
    symbol_ids = sorted(symbol_ids)
    line_keys = [3, 4, 5, 6]

    bg_rtp_wins = {(symbol_id, line_count): 0.0 for symbol_id in symbol_ids for line_count in line_keys}
    fg_rtp_wins = {(symbol_id, line_count): 0.0 for symbol_id in symbol_ids for line_count in line_keys}
    bg_hit_counts = {(symbol_id, line_count): 0 for symbol_id in symbol_ids for line_count in line_keys}
    fg_hit_counts = {(symbol_id, line_count): 0 for symbol_id in symbol_ids for line_count in line_keys}

    total_rounds = 0
    total_free_spins = 0

    for _, group in working.groupby("root_spin_id", sort=False):
        group = group.sort_values("row_order").reset_index(drop=True)
        total_rounds += 1

        bg_hits_this_round = set()
        bg_end = 0
        while bg_end < len(group) and to_int(group.iloc[bg_end].get("si_st")) in (1, 4):
            bg_end += 1
        bg_segment = group.iloc[:bg_end]
        for _, row in bg_segment.iterrows():
            for entry in extract_symbol_line_entries(row):
                key = (entry["symbol_id"], entry["line_count"])
                if key in bg_rtp_wins:
                    bg_rtp_wins[key] += entry["win_value"]
                    bg_hits_this_round.add(key)
        for key in bg_hits_this_round:
            bg_hit_counts[key] += 1

        for fg_segment in iter_free_spin_segments(group):
            total_free_spins += 1
            fg_hits_this_spin = set()
            for _, row in fg_segment.iterrows():
                for entry in extract_symbol_line_entries(row):
                    key = (entry["symbol_id"], entry["line_count"])
                    if key in fg_rtp_wins:
                        fg_rtp_wins[key] += entry["win_value"]
                        fg_hits_this_spin.add(key)
            for key in fg_hits_this_spin:
                fg_hit_counts[key] += 1

    def build_rows(win_map, hit_map, rtp_denominator, hit_denominator):
        rows = []
        for symbol_id in symbol_ids:
            row = {"symbol_id": symbol_id}
            for line_count in line_keys:
                rtp_key = f"{line_count}line_rtp"
                hit_key = f"{line_count}line_hit_rate"
                key = (symbol_id, line_count)
                row[rtp_key] = 0.0 if rtp_denominator == 0 else round(win_map[key] / rtp_denominator, 6)
                row[hit_key] = 0.0 if hit_denominator == 0 else round(hit_map[key] / hit_denominator, 6)
            rows.append(row)
        return rows

    return {
        "rtp_bg": build_rows(bg_rtp_wins, bg_hit_counts, total_rounds, total_rounds),
        "rtp_fg": build_rows(fg_rtp_wins, fg_hit_counts, total_free_spins, total_free_spins),
        "hit_bg": build_rows(bg_rtp_wins, bg_hit_counts, total_rounds, total_rounds),
        "hit_fg": build_rows(fg_rtp_wins, fg_hit_counts, total_free_spins, total_free_spins),
        "total_rounds": total_rounds,
        "total_free_spins": total_free_spins,
    }


def build_symbol_occurrence_payload(df, reel_count=6):
    working = df.copy()
    working["row_state"] = working["si_st"].apply(to_int)

    def empty_counts():
        return {}

    def count_initial(states):
        counts = empty_counts()
        totals = [0] * reel_count
        subset = working[working["row_state"].isin(states)]
        for _, row in subset.iterrows():
            board = parse_cell(row.get("si_orl"))
            nowpr_counts = normalize_nowpr(row.get("si_nowpr"), reel_count=reel_count)
            if not isinstance(board, list):
                continue

            start = 0
            for reel_index, visible_count in enumerate(nowpr_counts):
                end = start + max(int(visible_count), 0)
                reel_symbols = board[start:end]
                start = end
                for symbol in reel_symbols:
                    symbol_id = to_int(symbol)
                    if symbol_id is None:
                        continue
                    totals[reel_index] += 1
                    counts.setdefault(symbol_id, [0] * reel_count)[reel_index] += 1
        return counts, totals

    def count_drop(states):
        counts = empty_counts()
        totals = [0] * reel_count
        subset = working[working["row_state"].isin(states)]
        for _, row in subset.iterrows():
            rs = parse_cell(row.get("si_rs"))
            if not isinstance(rs, dict):
                continue
            rns = rs.get("rns")
            if not isinstance(rns, list):
                continue
            for reel_index, dropped_symbols in enumerate(rns[:reel_count]):
                if not isinstance(dropped_symbols, list):
                    continue
                for symbol in dropped_symbols:
                    symbol_id = to_int(symbol)
                    if symbol_id is None:
                        continue
                    totals[reel_index] += 1
                    counts.setdefault(symbol_id, [0] * reel_count)[reel_index] += 1
        return counts, totals

    def to_rows(counts, totals):
        rows = []
        for symbol_id in sorted(counts.keys()):
            row = {"symbol_id": symbol_id}
            for reel_index in range(reel_count):
                denominator = totals[reel_index]
                value = counts[symbol_id][reel_index]
                row[f"R{reel_index + 1}"] = 0.0 if denominator == 0 else round(value / denominator, 6)
            rows.append(row)
        return rows

    bg_initial_counts, bg_initial_totals = count_initial([1])
    bg_drop_counts, bg_drop_totals = count_drop([4])
    fg_initial_counts, fg_initial_totals = count_initial([21])
    fg_drop_counts, fg_drop_totals = count_drop([22])

    return {
        "bg_initial": to_rows(bg_initial_counts, bg_initial_totals),
        "bg_drop": to_rows(bg_drop_counts, bg_drop_totals),
        "fg_initial": to_rows(fg_initial_counts, fg_initial_totals),
        "fg_drop": to_rows(fg_drop_counts, fg_drop_totals),
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


def build_reel_high_distribution_payload(df):
    working = df.copy()
    working["row_state"] = working["si_st"].apply(to_int)
    working["nowpr_counts"] = working["si_nowpr"].apply(normalize_nowpr)
    working["reel_symbol_counts"] = working["nowpr_counts"].apply(lambda value: json.dumps(value, ensure_ascii=True))

    def from_states(states):
        subset = working[working["row_state"].isin(states)].copy()
        return build_reel_symbol_count_distribution(subset)

    return {
        "bg_initial": from_states([1]),
        "fg_initial": from_states([21]),
    }


def build_reel_occurrence_distribution(round_df, source_column, count_values, reel_count=6):
    total_spins = len(round_df)
    matrix = {count_value: {} for count_value in count_values}
    parsed_counts = round_df[source_column].apply(parse_cell).tolist()

    for reel_index in range(reel_count):
        reel_name = f"R{reel_index + 1}"
        reel_values = []
        for row in parsed_counts:
            if isinstance(row, list) and reel_index < len(row):
                reel_values.append(row[reel_index])
            else:
                reel_values.append(0)

        for count_value in count_values:
            count = sum(1 for value in reel_values if value == count_value)
            matrix[count_value][reel_name] = 0.0 if total_spins == 0 else round(count / total_spins, 6)

    return {
        "sample_count": int(total_spins),
        "rows": matrix,
    }


def build_silver_distribution_payload(df):
    working = df.copy()
    working["row_state"] = working["si_st"].apply(to_int)
    working["nowpr_counts"] = working["si_nowpr"].apply(normalize_nowpr)
    working["silver_initial_counts"] = working.apply(
        lambda row: count_silver_frames(row.get("si_eb"), row["nowpr_counts"]),
        axis=1,
    )
    working["previous_orl"] = working["si_orl"].shift(1)
    working["silver_drop_counts"] = working.apply(
        lambda row: count_new_drop_silver_frames(
            row.get("si_eb"),
            row["nowpr_counts"],
            row.get("previous_orl"),
            row.get("si_orl"),
        ),
        axis=1,
    )

    def from_states(states, source_column):
        subset = working[working["row_state"].isin(states)].copy()
        subset["reel_silver_counts"] = subset[source_column].apply(lambda value: json.dumps(value, ensure_ascii=True))
        return build_reel_occurrence_distribution(
            subset,
            "reel_silver_counts",
            count_values=[0, 1, 2, 3, 4, 5, 6],
        )

    return {
        "bg_initial": from_states([1], "silver_initial_counts"),
        "bg_drop": from_states([4], "silver_drop_counts"),
        "fg_initial": from_states([21], "silver_initial_counts"),
        "fg_drop": from_states([22], "silver_drop_counts"),
    }


def build_silver_init_count_distribution_payload(df):
    ordered = df.copy()
    ordered["root_spin_id"] = ordered.apply(root_spin_id, axis=1)
    ordered["row_order"] = range(len(ordered))
    ordered["row_state"] = ordered["si_st"].apply(to_int)

    bucket_labels = [f"{count}顆" for count in range(1, 16)] + ["15顆+"]
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    distribution_counts = {bucket: {column: 0 for column in distribution_columns} for bucket in bucket_labels}
    sample_counts = {column: 0 for column in distribution_columns}

    for _, group in ordered.groupby("root_spin_id", sort=False):
        group = group.sort_values("row_order").reset_index(drop=True)
        free_spin_index = 0

        if not group.empty and group.iloc[0]["row_state"] == 1:
            nowpr_counts = normalize_nowpr(group.iloc[0].get("si_nowpr"))
            silver_count = sum(count_silver_frames(group.iloc[0].get("si_eb"), nowpr_counts))
            sample_counts["BG"] += 1
            if silver_count > 0:
                bucket = "15顆+" if silver_count >= 15 else f"{silver_count}顆"
                distribution_counts[bucket]["BG"] += 1

        for fg_segment in iter_free_spin_segments(group):
            free_spin_index += 1
            if free_spin_index > 10:
                continue
            first_row = fg_segment.iloc[0]
            nowpr_counts = normalize_nowpr(first_row.get("si_nowpr"))
            silver_count = sum(count_silver_frames(first_row.get("si_eb"), nowpr_counts))
            column = f"F{free_spin_index}"
            sample_counts[column] += 1
            if silver_count <= 0:
                continue
            bucket = "15顆+" if silver_count >= 15 else f"{silver_count}顆"
            distribution_counts[bucket][column] += 1

    distribution_rows = []
    for bucket in bucket_labels:
        row = {"num": bucket}
        for column in distribution_columns:
            denominator = sample_counts[column]
            hit_count = distribution_counts[bucket][column]
            row[column] = 0.0 if denominator == 0 else round(hit_count / denominator, 6)
        distribution_rows.append(row)

    return {
        "sample_counts": sample_counts,
        "distribution_rows": distribution_rows,
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


def build_metric_rows(summary, round_df, df, duration_sec, max_rows):
    fg_triggered = round_df[round_df["has_free_spin_trigger"]].copy()
    bg_hit_rate = float((round_df["base_game_win"] > 0).mean()) if len(round_df) else 0.0
    total_hit_rate = float((round_df["total_win"] > 0).mean()) if len(round_df) else 0.0
    retrigger_rate = float((fg_triggered["free_spin_count"] > 10).mean()) if len(fg_triggered) else 0.0
    avg_fg_multiplier = float(fg_triggered["fg_multiplier"].mean()) if len(fg_triggered) else 0.0
    median_fg_multiplier = float(fg_triggered["fg_multiplier"].median()) if len(fg_triggered) else 0.0
    total_free_spins = int(round_df["free_spin_count"].sum()) if "free_spin_count" in round_df.columns else 0
    total_free_spin_hits = int(round_df["free_spin_hit_count"].sum()) if "free_spin_hit_count" in round_df.columns else 0
    fg_hit_rate = float(total_free_spin_hits / total_free_spins) if total_free_spins else 0.0
    formatted_duration = str(timedelta(seconds=round(duration_sec)))

    rows = [
        ("source_rows_limit", max_rows if max_rows is not None else "all"),
        ("total_rounds", summary["total_root_spins"]),
        ("fg_count", total_free_spins),
        ("rtp_total", f'{summary["total_rtp"]:.6f}'),
        ("rtp_bg", f'{summary["bg_rtp"]:.6f}'),
        ("rtp_fg", f'{summary["fg_rtp"]:.6f}'),
        ("hit_rate_bg", f"{bg_hit_rate:.6f}"),
        ("hit_rate_fg", f"{fg_hit_rate:.6f}"),
        ("hit_rate_total", f"{total_hit_rate:.6f}"),
        ("fg_trigger_rate", f'{summary["free_spin_trigger_rate"]:.6f}'),
        ("retrigger_rate", f"{retrigger_rate:.6f}"),
        ("avg_fg_multiplier", f"{avg_fg_multiplier:.6f}"),
        ("median_fg_multiplier", f"{median_fg_multiplier:.6f}"),
        ("avg_free_spins", f'{summary["avg_free_spins_per_trigger"]:.6f}'),
        ("execution_time_sec", f"{duration_sec:.3f}"),
        ("execution_time", formatted_duration),
    ]
    return rows


def format_metric_block(summary, round_df, df, duration_sec, max_rows):
    rows = build_metric_rows(summary, round_df, df, duration_sec, max_rows)

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


def format_combo_rate_distribution(title, payload):
    lines = [title, f"sample_count : {payload['sample_count']}", "label       combo_count  hit_count    rate"]
    for item in payload["distribution"]:
        rate_text = "" if item["rate"] == "" else f"{item['rate']:.6f}"
        lines.append(f"{item['label']:<11} {str(item['combo_count']):<12} {str(item['hit_count']):<12} {rate_text}")
    return "\n".join(lines)


def format_combo_rate_frame(title, frame):
    sample_count = frame["sample_count"].iloc[0] if not frame.empty else 0
    lines = [title, f"sample_count : {sample_count}", "label       combo_count  hit_count    rate"]
    for _, row in frame.iterrows():
        rate_text = "" if row["rate"] == "" else f"{float(row['rate']):.6f}"
        lines.append(f"{row['label']:<11} {str(row['combo_count']):<12} {str(row['hit_count']):<12} {rate_text}")
    return "\n".join(lines)


def format_reel_symbol_count_distribution(title, payload):
    reel_names = [f"R{index}" for index in range(1, 7)]
    header = "     " + " ".join(f"{name:>8}" for name in reel_names)
    lines = [title, header]
    for symbol_count in sorted(payload["rows"].keys()):
        values = " ".join(f"{payload['rows'][symbol_count][name]:>8.6f}" for name in reel_names)
        lines.append(f"{symbol_count}顆  {values}")
    return "\n".join(lines)


def format_reel_silver_distribution(title, payload):
    reel_names = [f"R{index}" for index in range(1, 7)]
    header = "     " + " ".join(f"{name:>8}" for name in reel_names)
    lines = [title, header]
    for silver_count in sorted(payload["rows"].keys()):
        values = " ".join(f"{payload['rows'][silver_count][name]:>8.6f}" for name in reel_names)
        lines.append(f"{silver_count}銀框 {values}")
    return "\n".join(lines)


def format_silver_init_count_distribution(title, payload):
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    lines = [
        title,
        "sample_count " + " ".join(f"{column}:{payload['sample_counts'][column]}" for column in distribution_columns),
        "num        " + " ".join(f"{column:>8}" for column in distribution_columns),
    ]
    for item in payload["distribution_rows"]:
        values = " ".join(f"{item[column]:>8.6f}" for column in distribution_columns)
        lines.append(f"{item['num']:<10} {values}")
    return "\n".join(lines)


def format_extra_reel_distribution(title, payload):
    lines = [
        title,
        f"sample_count_BG : {payload['sample_count_BG']}",
        f"sample_count_FG : {payload['sample_count_FG']}",
        "symbol_id   hit_count_BG  hit_count_BG_more2  rate_BG     hit_count_FG  hit_count_FG_more2  rate_FG",
    ]
    for item in payload["distribution"]:
        lines.append(f"{item['symbol_id']:<11} {item['hit_count_BG']:<13} {item['hit_count_BG_more2']:<19} {item['rate_BG']:<11.6f} {item['hit_count_FG']:<13} {item['hit_count_FG_more2']:<19} {item['rate_FG']:.6f}")
    return "\n".join(lines)


def format_symbol_size_distribution(title, rows):
    lines = [title, "symbol_id   1x1        2x1        3x1        4x1        symbol_total_count"]
    for item in rows:
        lines.append(f"{item['symbol_id']:<11} {item['1x1']:<10} {item['2x1']:<10} {item['3x1']:<10} {item['4x1']:<10} {item['symbol_total_count']}")
    return "\n".join(lines)


def format_m1_metrics(title, payload):
    rows = [
        ("symbol_id", payload["symbol_id"], payload["symbol_id"]),
        ("total_spins", payload["bg_total_spins"], payload["fg_total_spins"]),
        ("spins_with_symbol", payload["bg_spins_with_symbol"], payload["fg_spins_with_symbol"]),
        ("spins_with_symbol_and_win", payload["bg_spins_with_symbol_and_win"], payload["fg_spins_with_symbol_and_win"]),
        ("appearance_rate", f'{payload["bg_appearance_rate"]:.6f}', f'{payload["fg_appearance_rate"]:.6f}'),
        ("usage_rate", f'{payload["bg_usage_rate"]:.6f}', f'{payload["fg_usage_rate"]:.6f}'),
    ]
    label_width = max(len(label) for label, _, _ in rows)
    lines = [title]
    lines.append(f"{'metric':<{label_width}}   {'BG':>12}   {'FG':>12}")
    for label, bg_value, fg_value in rows:
        lines.append(f"{label:<{label_width}}   {str(bg_value):>12}   {str(fg_value):>12}")

    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    lines.extend(
        [
            "",
            "M1 Count Distribution Rate",
            "sample_count " + " ".join(f"{column}:{payload['sample_counts'][column]}" for column in distribution_columns),
            "num        " + " ".join(f"{column:>8}" for column in distribution_columns),
        ]
    )
    for item in payload["distribution_rows"]:
        values = " ".join(f"{item[column]:>8.6f}" for column in distribution_columns)
        lines.append(f"{item['num']:<10} {values}")
    return "\n".join(lines)


def format_symbol_line_table(title, rows, value_suffix):
    lines = [title, f"symbol_id   3line{value_suffix}  4line{value_suffix}  5line{value_suffix}  6line{value_suffix}"]
    for item in rows:
        value_3 = item[f"3line_{value_suffix}"]
        value_4 = item[f"4line_{value_suffix}"]
        value_5 = item[f"5line_{value_suffix}"]
        value_6 = item[f"6line_{value_suffix}"]
        lines.append(f"{item['symbol_id']:<11} {value_3:<12.6f} {value_4:<12.6f} {value_5:<12.6f} {value_6:<12.6f}")
    return "\n".join(lines)


def format_symbol_occurrence_table(title, rows):
    lines = [title, "symbol_id   R1         R2         R3         R4         R5         R6"]
    for item in rows:
        lines.append(f"{item['symbol_id']:<11} {item['R1']:<10.6f} {item['R2']:<10.6f} {item['R3']:<10.6f} {item['R4']:<10.6f} {item['R5']:<10.6f} {item['R6']:<10.6f}")
    return "\n".join(lines)


def build_metric_dataframe(summary, round_df, df, duration_sec, max_rows):
    return pd.DataFrame(build_metric_rows(summary, round_df, df, duration_sec, max_rows), columns=["metric", "value"])


def build_multiplier_distribution_dataframe(payload):
    return pd.DataFrame(payload["distribution"])[["range", "count", "rate"]]


def build_multiplier_comparison_dataframe(bg_payload, fg_payload):
    bg_frame = pd.DataFrame(bg_payload["distribution"])[["range", "count", "rate"]].rename(columns={"count": "count_BG", "rate": "rate_BG"})
    fg_frame = pd.DataFrame(fg_payload["distribution"])[["range", "count", "rate"]].rename(columns={"count": "count_FG", "rate": "rate_FG"})
    return bg_frame.merge(fg_frame, on="range", how="outer")


def build_cascade_distribution_dataframe(payload):
    return pd.DataFrame(payload["distribution"])[["cascade_count", "count", "rate"]]


def build_extra_reel_same_symbol_dataframe(payload):
    frame = pd.DataFrame(
        payload["distribution"],
        columns=[
            "symbol_id",
            "hit_count_BG",
            "hit_count_BG_more2",
            "rate_BG",
            "hit_count_FG",
            "hit_count_FG_more2",
            "rate_FG",
        ],
    )
    frame.insert(0, "sample_count_BG", payload["sample_count_BG"])
    frame.insert(1, "sample_count_FG", payload["sample_count_FG"])
    return frame


def build_symbol_size_distribution_dataframe(rows):
    return pd.DataFrame(rows, columns=["symbol_id", "1x1", "2x1", "3x1", "4x1", "symbol_total_count"])


def build_m1_metrics_dataframe(payload):
    return pd.DataFrame(
        [
            ("symbol_id", payload["symbol_id"], payload["symbol_id"]),
            ("total_spins", payload["bg_total_spins"], payload["fg_total_spins"]),
            ("spins_with_symbol", payload["bg_spins_with_symbol"], payload["fg_spins_with_symbol"]),
            ("spins_with_symbol_and_win", payload["bg_spins_with_symbol_and_win"], payload["fg_spins_with_symbol_and_win"]),
            ("appearance_rate", payload["bg_appearance_rate"], payload["fg_appearance_rate"]),
            ("usage_rate", payload["bg_usage_rate"], payload["fg_usage_rate"]),
        ],
        columns=["metric", "BG", "FG"],
    )


def build_m1_distribution_sample_count_dataframe(payload):
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    row = {column: payload["sample_counts"][column] for column in distribution_columns}
    row["num"] = "sample_count"
    return pd.DataFrame([row], columns=["num"] + distribution_columns)


def build_m1_distribution_dataframe(payload):
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    return pd.DataFrame(payload["distribution_rows"], columns=["num"] + distribution_columns)


def build_silver_init_count_sample_count_dataframe(payload):
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    row = {column: payload["sample_counts"][column] for column in distribution_columns}
    row["num"] = "sample_count"
    return pd.DataFrame([row], columns=["num"] + distribution_columns)


def build_silver_init_count_distribution_dataframe(payload):
    distribution_columns = ["BG"] + [f"F{index}" for index in range(1, 11)]
    return pd.DataFrame(payload["distribution_rows"], columns=["num"] + distribution_columns)


def build_symbol_line_rtp_dataframe(rows):
    return pd.DataFrame(rows, columns=["symbol_id", "3line_rtp", "4line_rtp", "5line_rtp", "6line_rtp"])


def build_symbol_line_hit_dataframe(rows):
    return pd.DataFrame(rows, columns=["symbol_id", "3line_hit_rate", "4line_hit_rate", "5line_hit_rate", "6line_hit_rate"])


def build_symbol_occurrence_dataframe(rows):
    return pd.DataFrame(rows, columns=["symbol_id", "R1", "R2", "R3", "R4", "R5", "R6"])


def build_named_distribution_dataframe(payload, name):
    frame = pd.DataFrame(payload["distribution"]).copy()
    frame.insert(0, "section", name)
    return frame


def build_combo_rate_dataframe(payload, cascade_payload, apply_cascade_distribution=True):
    frame = pd.DataFrame(payload["distribution"])[["label", "combo_count", "hit_count", "rate"]].copy()
    if apply_cascade_distribution:
        cascade_count_map = {int(item["cascade_count"]): item["count"] for item in cascade_payload["distribution"]}
        cascade_rate_map = {int(item["cascade_count"]): item["rate"] for item in cascade_payload["distribution"]}
        for row_index, row in frame.iterrows():
            combo_count = row["combo_count"]
            if isinstance(combo_count, int):
                frame.at[row_index, "hit_count"] = cascade_count_map.get(combo_count - 1, row["hit_count"])
                frame.at[row_index, "rate"] = cascade_rate_map.get(combo_count - 1, row["rate"])
    frame.insert(0, "sample_count", payload["sample_count"])
    return frame


def write_stacked_frames(writer, sheet_name, sections, blank_rows=1):
    current_row = 0
    for title, frame in sections:
        pd.DataFrame([[title]], columns=[title]).to_excel(
            writer,
            sheet_name=sheet_name,
            index=False,
            header=False,
            startrow=current_row,
        )
        current_row += 1
        frame.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False,
            startrow=current_row,
        )
        current_row += len(frame) + 1 + blank_rows


def build_occurrence_distribution_dataframe(payload, index_label):
    frame = pd.DataFrame(payload["rows"]).T
    frame.index.name = index_label
    return frame.reset_index()


def main():
    started_at = time.perf_counter()
    args = parse_args()
    input_path = resolve_path(args.input_file)

    read_kwargs = {"sheet_name": args.sheet_name}
    if args.max_rows is not None and args.max_rows > 0:
        read_kwargs["nrows"] = args.max_rows
    df = pd.read_excel(input_path, **read_kwargs)
    validate_columns(df)
    df.attrs["source_file"] = str(input_path)

    round_df = build_round_dataframe(df)
    summary = summarize(df, round_df)
    distributions = build_distribution_payload(round_df)
    cascade_distribution = build_cascade_distribution(round_df)
    combo_rate_payload = build_combo_rate_payload(df)
    extra_reel_same_symbol_payload = build_extra_reel_same_symbol_payload(df)
    symbol_size_distribution_payload = build_symbol_size_distribution_payload(df)
    m1_metrics_payload = build_m1_metrics_payload(df, symbol_id=2)
    symbol_line_rtp_hit_payload = build_symbol_line_rtp_hit_payload(df)
    symbol_occurrence_payload = build_symbol_occurrence_payload(df)
    reel_high_distribution_payload = build_reel_high_distribution_payload(df)
    silver_distribution_payload = build_silver_distribution_payload(df)
    silver_init_count_distribution_payload = build_silver_init_count_distribution_payload(df)
    duration_sec = time.perf_counter() - started_at

    output_sections = []

    if SHOW_OVERVIEW:
        output_sections.append("=== Overview ===\n" + format_metric_block(summary, round_df, df, duration_sec, args.max_rows))

    if SHOW_MULTIPLIER_RANGE:
        multiplier_parts = [
            "=== Multiplier Range ===",
            format_multiplier_distribution("Multiplier Range BG", distributions["bg"]),
            format_multiplier_distribution("Multiplier Range FG", distributions["fg"]),
        ]
        output_sections.append("\n\n".join(multiplier_parts))

    if SHOW_COMBO_RATE:
        combo_rate_bg_frame = build_combo_rate_dataframe(combo_rate_payload["bg"], cascade_distribution["bg"])
        combo_rate_fg_frame = build_combo_rate_dataframe(
            combo_rate_payload["fg"],
            cascade_distribution["fg"],
            apply_cascade_distribution=False,
        )
        combo_parts = [
            "=== Combo Rate ===",
            format_combo_rate_frame("Combo Rate BG", combo_rate_bg_frame),
            format_combo_rate_frame("Combo Rate FG", combo_rate_fg_frame),
        ]
        output_sections.append("\n\n".join(combo_parts))

    if SHOW_REEL_HIGH_DISTRIBUTION:
        reel_parts = [
            "=== Reel High Distribution ===",
            format_reel_symbol_count_distribution(
                "Reel High Distribution BG Initial",
                reel_high_distribution_payload["bg_initial"],
            ),
            format_reel_symbol_count_distribution(
                "Reel High Distribution FG Initial",
                reel_high_distribution_payload["fg_initial"],
            ),
        ]
        output_sections.append("\n\n".join(reel_parts))

    if SHOW_SILVER_DISTRIBUTION:
        silver_parts = [
            "=== Silver Distribution ===",
            format_reel_silver_distribution(
                "Silver Distribution BG Initial",
                silver_distribution_payload["bg_initial"],
            ),
            format_reel_silver_distribution(
                "Silver Distribution BG Drop",
                silver_distribution_payload["bg_drop"],
            ),
            format_reel_silver_distribution(
                "Silver Distribution FG Initial",
                silver_distribution_payload["fg_initial"],
            ),
            format_reel_silver_distribution(
                "Silver Distribution FG Drop",
                silver_distribution_payload["fg_drop"],
            ),
            format_silver_init_count_distribution(
                "Silver Init Count Distribution",
                silver_init_count_distribution_payload,
            ),
        ]
        output_sections.append("\n\n".join(silver_parts))

    if SHOW_EXTRA_REEL:
        output_sections.append(
            "=== Extra Reel ===\n"
            + format_extra_reel_distribution(
                "Extra Reel Same Symbol Rate",
                extra_reel_same_symbol_payload,
            )
        )

    if SHOW_SYMBOL_SIZE_DISTRIBUTION:
        output_sections.append(
            "=== Symbol Size Distribution ===\n"
            + "\n\n".join(
                [
                    format_symbol_size_distribution("BG Initial Symbol Size", symbol_size_distribution_payload["bg"]),
                    format_symbol_size_distribution("FG Initial Symbol Size", symbol_size_distribution_payload["fg"]),
                ]
            )
        )

    if SHOW_M1_METRICS:
        output_sections.append(
            "=== M1 Metrics ===\n"
            + format_m1_metrics(
                "M1 Appearance And Usage",
                m1_metrics_payload,
            )
        )

    if SHOW_RTP_HIT_RATE:
        output_sections.append(
            "=== RTP / Hit Rate ===\n"
            + "\n\n".join(
                [
                    format_symbol_line_table("RTP BG", symbol_line_rtp_hit_payload["rtp_bg"], "rtp"),
                    format_symbol_line_table("RTP FG", symbol_line_rtp_hit_payload["rtp_fg"], "rtp"),
                    format_symbol_line_table("Hit Rate BG", symbol_line_rtp_hit_payload["hit_bg"], "hit_rate"),
                    format_symbol_line_table("Hit Rate FG", symbol_line_rtp_hit_payload["hit_fg"], "hit_rate"),
                ]
            )
        )

    if SHOW_SYMBOL_OCCURRENCE_RATE:
        output_sections.append(
            "=== Symbol Occurrence Rate ===\n"
            + "\n\n".join(
                [
                    format_symbol_occurrence_table("BG Initial Symbols", symbol_occurrence_payload["bg_initial"]),
                    format_symbol_occurrence_table("BG Drop Symbols", symbol_occurrence_payload["bg_drop"]),
                    format_symbol_occurrence_table("FG Initial Symbols", symbol_occurrence_payload["fg_initial"]),
                    format_symbol_occurrence_table("FG Drop Symbols", symbol_occurrence_payload["fg_drop"]),
                ]
            )
        )

    print("\n\n".join(output_sections))

    if args.output_dir:
        output_dir = resolve_path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        workbook_path = output_dir / f"{input_path.stem}_analysis.xlsx"

        with pd.ExcelWriter(workbook_path) as writer:
            build_metric_dataframe(summary, round_df, df, duration_sec, args.max_rows).to_excel(
                writer,
                sheet_name="Overview",
                index=False,
            )
            build_multiplier_comparison_dataframe(distributions["bg"], distributions["fg"]).to_excel(
                writer,
                sheet_name="Multiplier",
                index=False,
            )
            write_stacked_frames(
                writer,
                "ComboRate",
                [
                    ("BG", build_combo_rate_dataframe(combo_rate_payload["bg"], cascade_distribution["bg"])),
                    (
                        "FG",
                        build_combo_rate_dataframe(
                            combo_rate_payload["fg"],
                            cascade_distribution["fg"],
                            apply_cascade_distribution=False,
                        ),
                    ),
                ],
            )
            build_extra_reel_same_symbol_dataframe(extra_reel_same_symbol_payload).to_excel(
                writer,
                sheet_name="ExtraReelSame",
                index=False,
            )
            write_stacked_frames(
                writer,
                "SymbolSize",
                [
                    ("BG", build_symbol_size_distribution_dataframe(symbol_size_distribution_payload["bg"])),
                    ("FG", build_symbol_size_distribution_dataframe(symbol_size_distribution_payload["fg"])),
                ],
            )
            write_stacked_frames(
                writer,
                "M1Metrics",
                [
                    ("Summary", build_m1_metrics_dataframe(m1_metrics_payload)),
                    ("SampleCount", build_m1_distribution_sample_count_dataframe(m1_metrics_payload)),
                    ("Distribution", build_m1_distribution_dataframe(m1_metrics_payload)),
                ],
            )
            write_stacked_frames(
                writer,
                "RTP",
                [
                    ("BG", build_symbol_line_rtp_dataframe(symbol_line_rtp_hit_payload["rtp_bg"])),
                    ("FG", build_symbol_line_rtp_dataframe(symbol_line_rtp_hit_payload["rtp_fg"])),
                ],
            )
            write_stacked_frames(
                writer,
                "HitRate",
                [
                    ("BG", build_symbol_line_hit_dataframe(symbol_line_rtp_hit_payload["hit_bg"])),
                    ("FG", build_symbol_line_hit_dataframe(symbol_line_rtp_hit_payload["hit_fg"])),
                ],
            )
            write_stacked_frames(
                writer,
                "SymbolOcc_Init",
                [
                    ("BG", build_symbol_occurrence_dataframe(symbol_occurrence_payload["bg_initial"])),
                    ("FG", build_symbol_occurrence_dataframe(symbol_occurrence_payload["fg_initial"])),
                ],
            )
            write_stacked_frames(
                writer,
                "SymbolOcc_Drop",
                [
                    ("BG", build_symbol_occurrence_dataframe(symbol_occurrence_payload["bg_drop"])),
                    ("FG", build_symbol_occurrence_dataframe(symbol_occurrence_payload["fg_drop"])),
                ],
            )
            write_stacked_frames(
                writer,
                "ReelHigh_Init",
                [
                    (
                        "BG",
                        build_occurrence_distribution_dataframe(
                            reel_high_distribution_payload["bg_initial"],
                            "symbol_count",
                        ),
                    ),
                    (
                        "FG",
                        build_occurrence_distribution_dataframe(
                            reel_high_distribution_payload["fg_initial"],
                            "symbol_count",
                        ),
                    ),
                ],
            )
            write_stacked_frames(
                writer,
                "Silver_Init",
                [
                    (
                        "BG",
                        build_occurrence_distribution_dataframe(
                            silver_distribution_payload["bg_initial"],
                            "silver_count",
                        ),
                    ),
                    (
                        "FG",
                        build_occurrence_distribution_dataframe(
                            silver_distribution_payload["fg_initial"],
                            "silver_count",
                        ),
                    ),
                    ("SampleCount", build_silver_init_count_sample_count_dataframe(silver_init_count_distribution_payload)),
                    ("Distribution", build_silver_init_count_distribution_dataframe(silver_init_count_distribution_payload)),
                ],
            )
            write_stacked_frames(
                writer,
                "Silver_Drop",
                [
                    (
                        "BG",
                        build_occurrence_distribution_dataframe(
                            silver_distribution_payload["bg_drop"],
                            "silver_count",
                        ),
                    ),
                    (
                        "FG",
                        build_occurrence_distribution_dataframe(
                            silver_distribution_payload["fg_drop"],
                            "silver_count",
                        ),
                    ),
                ],
            )
            round_df.to_excel(
                writer,
                sheet_name="Rounds",
                index=False,
            )

        print(f"Saved analysis workbook: {workbook_path}")


if __name__ == "__main__":
    main()
