import json
import math
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
from numba import njit


# ===== User Settings =====

CONFIG_FILE = "config.js"
TOTAL_ROUNDS = 10**7
BET_MULTI = 1
BET_MODE = 0  # 0 Normal, 1 Extra, 2 Feature Buy, 3 Super Feature Buy
THREADS = max(1, min(8, os.cpu_count() or 1))

OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false, got {value!r}")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.environ.get("H013_CONFIG_FILE", CONFIG_FILE)
TOTAL_ROUNDS = int(os.environ.get("H013_TOTAL_ROUNDS", TOTAL_ROUNDS))
BET_MULTI = int(os.environ.get("H013_BET_MULTI", BET_MULTI))
BET_MODE = int(os.environ.get("H013_BET_MODE", BET_MODE))
THREADS = int(os.environ.get("H013_THREADS", THREADS))
OUTPUT_REPORT = _env_bool("H013_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = _env_bool("H013_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = _env_bool("H013_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
RUN_SINGLE_SPIN_DEBUG = _env_bool("H013_RUN_SINGLE_SPIN_DEBUG", RUN_SINGLE_SPIN_DEBUG)

THRESHOLD_RECORD = np.asarray(
    [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
        15, 20, 25, 30, 35, 40, 45, 50,
        60, 70, 80, 90, 100, 120, 140, 160, 180,
        200, 250, 300, 350, 400, 450, 500, 550, 600, 650,
        700, 750, 800, 850, 900, 950, 1000,
        2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
        20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000,
        9999999,
    ],
    dtype=np.float64,
)


def _load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])


CFG = _load_config(os.path.join(BASE_DIR, CONFIG_FILE))
GAME_ID = str(CFG["game_id"])
PARSHEET_ID = str(CFG["parsheet_id"])
GAME_NAME = str(CFG["display_name"])
GAME_VERSION = str(CFG["game_version"])

MODE_NORMALBET = int(CFG["mode_normalbet"])
MODE_EXTRABET = int(CFG["mode_extrabet"])
MODE_FEATUREBUY = int(CFG["mode_featurebuy"])
MODE_SUPERFEATUREBUY = int(CFG["mode_superfeaturebuy"])
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_EXTRABET, MODE_FEATUREBUY, MODE_SUPERFEATUREBUY)
MODE_NAMES = {0: "Normal Bet", 1: "Extra Bet", 2: "Feature Buy", 3: "Super Feature Buy"}

WINDOW_SIZE = int(CFG["window_size"])
REEL_NUM = int(CFG["reel_num"])
DEFAULT_COIN_IN = int(CFG["default_coin_in"])
BET_FACTORS = np.asarray(
    [CFG["normalbet"], CFG["extrabet"], CFG["featurebuy"], CFG["superfeaturebuy"]],
    dtype=np.float64,
)
MAX_FREE_SPINS = int(CFG["max_spin_free_game"])
INITIAL_LOW = int(CFG["initial_free_spins_low"])
INITIAL_HIGH = int(CFG["initial_free_spins_high"])
RETRIGGER_LOW = int(CFG["retrigger_free_spins_low"])
RETRIGGER_HIGH = int(CFG["retrigger_free_spins_high"])

ARR_REELS = np.asarray(CFG["arr_reels"], dtype=np.int64)
ARR_REELS_WEIGHT_CUM = np.asarray(CFG["arr_reels_weight_cum"], dtype=np.int64)
REELS_LEN = np.asarray(CFG["reels_len"], dtype=np.int64)
PAY_TABLE = np.asarray(CFG["pay_table"], dtype=np.int64)
SYMBOL_STR = {int(key): value for key, value in CFG["symbol_str"].items()}
SYMBOL_COUNT = len(SYMBOL_STR)
SYMBOLS_SCORE = np.asarray(CFG["symbols_score"], dtype=np.int64)
VALUE_MULTIPLIER = np.asarray(CFG["value_multiplier"], dtype=np.int64)

WEIGHT_TABLE_NORMAL = np.asarray(CFG["weight_table_normal_bet"], dtype=np.int64)
WEIGHT_TABLE_EXTRA = np.asarray(CFG["weight_table_extra_bet"], dtype=np.int64)
MULTI_WEIGHTS = np.asarray(
    [
        CFG["weight_multiplier_fg_low"], CFG["weight_multiplier_fg_high"],
        CFG["weight_multiplier_fb_low"], CFG["weight_multiplier_fb_high"],
        CFG["weight_multiplier_sb_low"], CFG["weight_multiplier_sb_high"],
    ],
    dtype=np.int64,
)

C1 = next(sid for sid, code in SYMBOL_STR.items() if code == "C1")
C2 = next(sid for sid, code in SYMBOL_STR.items() if code == "C2")

S_TOTAL_WIN = 0
S_BG_PAY = 1
S_SCATTER_PAY = 2
S_FG_PAY = 3
S_BG_HITS = 4
S_FG_HITS = 5
S_FG_TRIGGER = 6
S_RETRIGGER = 7
S_FREE_SPINS = 8
S_MAX_WIN = 9
S_X_SUM = 10
S_X_SQUARE = 11
S_BG_CASCADES = 12
S_FG_CASCADES = 13
S_FG_MULTI_SUM = 14
S_FG_MULTI_MAX = 15
STAT_COUNT = 16


def _validate_settings():
    if BET_MODE not in SUPPORTED_BET_MODES:
        raise ValueError(f"Unsupported H013 bet mode {BET_MODE}; valid modes: 0, 1, 2, 3")
    if TOTAL_ROUNDS <= 0:
        raise ValueError("TOTAL_ROUNDS must be positive")
    if BET_MULTI <= 0:
        raise ValueError("BET_MULTI must be positive")
    if THREADS <= 0:
        raise ValueError("THREADS must be positive")


@njit(nogil=True)
def _weighted_index(weights):
    total = 0
    for value in weights:
        if value > 0:
            total += value
    if total <= 0:
        return 0
    pick = np.random.randint(0, total)
    running = 0
    for idx in range(weights.shape[0]):
        if weights[idx] > 0:
            running += weights[idx]
            if pick < running:
                return idx
    return weights.shape[0] - 1


@njit(nogil=True)
def _weighted_cumulative_index(cumulative):
    total = cumulative[-1]
    if total <= 0:
        return 0
    pick = np.random.randint(0, total)
    for idx in range(cumulative.shape[0]):
        if pick < cumulative[idx]:
            return idx
    return cumulative.shape[0] - 1


@njit(nogil=True)
def _threshold_index(multiplier):
    for idx in range(THRESHOLD_RECORD.shape[0]):
        if multiplier <= THRESHOLD_RECORD[idx]:
            return idx
    return THRESHOLD_RECORD.shape[0] - 1


@njit(nogil=True)
def _generate_board(table_id):
    board = np.zeros((WINDOW_SIZE, REEL_NUM), dtype=np.int64)
    stops = np.zeros(REEL_NUM, dtype=np.int64)
    for reel in range(REEL_NUM):
        stops[reel] = _weighted_cumulative_index(ARR_REELS_WEIGHT_CUM[table_id, :, reel])
        reel_len = REELS_LEN[table_id, reel]
        for row in range(WINDOW_SIZE):
            board[row, reel] = ARR_REELS[table_id, (stops[reel] + row) % reel_len, reel]
    return board, stops


@njit(nogil=True)
def _pay_bin(count):
    if count >= 12:
        return 2
    if count >= 10:
        return 1
    if count >= 8:
        return 0
    return -1


@njit(nogil=True)
def _cascade(table_id, board, stops, multiplier, scene, collect, hits, pays, eliminates):
    total_pay = 0.0
    cascade_count = 0
    remove_counts = np.zeros(REEL_NUM, dtype=np.int64)
    while True:
        counts = np.zeros(SYMBOL_COUNT, dtype=np.int64)
        for row in range(WINDOW_SIZE):
            for reel in range(REEL_NUM):
                symbol = board[row, reel]
                if 0 <= symbol < SYMBOL_COUNT:
                    counts[symbol] += 1

        remove_symbols = np.zeros(SYMBOL_COUNT, dtype=np.int64)
        any_win = False
        for idx in range(SYMBOLS_SCORE.shape[0]):
            symbol = SYMBOLS_SCORE[idx]
            pay_bin = _pay_bin(counts[symbol])
            if pay_bin >= 0:
                pay = PAY_TABLE[symbol, pay_bin + 3] * multiplier
                if pay > 0:
                    any_win = True
                    remove_symbols[symbol] = 1
                    total_pay += pay
                    if collect:
                        hits[scene, symbol, pay_bin] += 1
                        pays[scene, symbol, pay_bin] += pay
                        eliminates[scene, symbol, pay_bin] += counts[symbol]
        if not any_win:
            break

        cascade_count += 1
        for reel in range(REEL_NUM):
            kept = np.empty(WINDOW_SIZE, dtype=np.int64)
            kept_count = 0
            for row in range(WINDOW_SIZE):
                symbol = board[row, reel]
                if remove_symbols[symbol] == 0:
                    kept[kept_count] = symbol
                    kept_count += 1
            missing = WINDOW_SIZE - kept_count
            for pos in range(kept_count - 1, -1, -1):
                board[pos + missing, reel] = kept[pos]
            for row in range(missing - 1, -1, -1):
                while True:
                    remove_counts[reel] += 1
                    reel_len = REELS_LEN[table_id, reel]
                    source = (stops[reel] - (remove_counts[reel] % reel_len)) % reel_len
                    symbol = ARR_REELS[table_id, source, reel]
                    duplicate = False
                    if symbol == C1 or symbol == C2:
                        for check_row in range(row + 1, WINDOW_SIZE):
                            if board[check_row, reel] == symbol:
                                duplicate = True
                                break
                    if not duplicate:
                        board[row, reel] = symbol
                        break
    return total_pay, cascade_count


@njit(nogil=True)
def _count_symbol(board, symbol):
    count = 0
    for row in range(WINDOW_SIZE):
        for reel in range(REEL_NUM):
            if board[row, reel] == symbol:
                count += 1
    return count


@njit(nogil=True)
def _base_table(mode):
    if mode == MODE_NORMALBET:
        return _weighted_index(WEIGHT_TABLE_NORMAL)
    if mode == MODE_EXTRABET:
        return 4 + _weighted_index(WEIGHT_TABLE_EXTRA)
    return 3


@njit(nogil=True)
def _fg_tables_and_profile(mode):
    if mode == MODE_FEATUREBUY:
        return 9, 10, 2
    if mode == MODE_SUPERFEATUREBUY:
        return 11, 12, 4
    return 7, 8, 0


@njit(nogil=True)
def _draw_multiplier(profile_row, count):
    if count <= 0:
        return 1
    total = 0
    weights = MULTI_WEIGHTS[profile_row]
    for _ in range(count):
        total += VALUE_MULTIPLIER[_weighted_index(weights)]
    return total


@njit(nogil=True)
def _simulate_chunk(rounds, mode, bet_multi):
    stats = np.zeros(STAT_COUNT, dtype=np.float64)
    hits = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
    pays = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
    eliminates = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
    multiplier_line = np.zeros((3, THRESHOLD_RECORD.shape[0]), dtype=np.float64)
    coin_in = DEFAULT_COIN_IN * BET_FACTORS[mode] * bet_multi

    for _ in range(rounds):
        table_id = _base_table(mode)
        board, stops = _generate_board(table_id)
        bg_regular, bg_cascades = _cascade(table_id, board, stops, bet_multi, 0, True, hits, pays, eliminates)
        scatter_count = _count_symbol(board, C1)
        scatter_pay = 0.0
        if 4 <= scatter_count <= 6:
            scatter_pay = PAY_TABLE[C1, scatter_count - 4] * bet_multi

        bg_pay = bg_regular + scatter_pay
        fg_pay = 0.0
        fg_spins = 0
        retriggers = 0
        fg_hit_spins = 0
        fg_cascades = 0
        fg_multiplier_sum = 0
        fg_multiplier_max = 0

        if scatter_pay > 0:
            low_table, high_table, profile = _fg_tables_and_profile(mode)
            low_total = INITIAL_LOW
            high_total = INITIAL_HIGH
            low_done = 0
            high_done = 0
            while high_done < high_total or low_done < low_total:
                is_high = high_done < high_total
                if is_high:
                    fg_table = high_table
                    high_done += 1
                else:
                    fg_table = low_table
                    low_done += 1

                fg_board, fg_stops = _generate_board(fg_table)
                preview = fg_board.copy()
                dummy_hits = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
                dummy_pays = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
                dummy_eliminates = np.zeros((2, SYMBOL_COUNT, 3), dtype=np.float64)
                _cascade(fg_table, preview, fg_stops, 1, 1, False, dummy_hits, dummy_pays, dummy_eliminates)

                final_scatter = _count_symbol(preview, C1)
                if low_total + high_total < MAX_FREE_SPINS and 3 <= final_scatter <= 6:
                    low_total += RETRIGGER_LOW
                    high_total += RETRIGGER_HIGH
                    retriggers += 1

                multiplier = _draw_multiplier(profile + (1 if is_high else 0), _count_symbol(preview, C2))
                spin_pay, cascades = _cascade(
                    fg_table, fg_board, fg_stops, multiplier * bet_multi, 1, True, hits, pays, eliminates
                )
                fg_pay += spin_pay
                fg_spins += 1
                fg_cascades += cascades
                fg_multiplier_sum += multiplier
                if multiplier > fg_multiplier_max:
                    fg_multiplier_max = multiplier
                if spin_pay > 0:
                    fg_hit_spins += 1

        total_win = bg_pay + fg_pay
        stats[S_TOTAL_WIN] += total_win
        stats[S_BG_PAY] += bg_regular
        stats[S_SCATTER_PAY] += scatter_pay
        stats[S_FG_PAY] += fg_pay
        if bg_pay > 0:
            stats[S_BG_HITS] += 1
        stats[S_FG_HITS] += fg_hit_spins
        if scatter_pay > 0:
            stats[S_FG_TRIGGER] += 1
        stats[S_RETRIGGER] += retriggers
        stats[S_FREE_SPINS] += fg_spins
        stats[S_BG_CASCADES] += bg_cascades
        stats[S_FG_CASCADES] += fg_cascades
        stats[S_FG_MULTI_SUM] += fg_multiplier_sum
        if fg_multiplier_max > stats[S_FG_MULTI_MAX]:
            stats[S_FG_MULTI_MAX] = fg_multiplier_max
        if total_win > stats[S_MAX_WIN]:
            stats[S_MAX_WIN] = total_win
        x = total_win / coin_in
        stats[S_X_SUM] += x
        stats[S_X_SQUARE] += x * x
        multiplier_line[0, _threshold_index(bg_pay / coin_in)] += 1
        if scatter_pay > 0:
            multiplier_line[1, _threshold_index(fg_pay / coin_in)] += 1
        multiplier_line[2, _threshold_index(x)] += 1

    return stats, hits, pays, eliminates, multiplier_line


def _run_parallel(total_rounds, threads, mode, bet_multi):
    workers = min(threads, total_rounds)
    chunks = [total_rounds // workers] * workers
    for idx in range(total_rounds % workers):
        chunks[idx] += 1
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda count: _simulate_chunk(count, mode, bet_multi), chunks))
    stats = sum((item[0] for item in results), np.zeros(STAT_COUNT))
    hits = sum((item[1] for item in results), np.zeros((2, SYMBOL_COUNT, 3)))
    pays = sum((item[2] for item in results), np.zeros((2, SYMBOL_COUNT, 3)))
    eliminates = sum((item[3] for item in results), np.zeros((2, SYMBOL_COUNT, 3)))
    multiplier_line = sum(
        (item[4] for item in results), np.zeros((3, THRESHOLD_RECORD.shape[0]))
    )
    return stats, hits, pays, eliminates, multiplier_line, time.perf_counter() - started


def _safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def _build_outputs(stats, hits, pays, eliminates, multiplier_line, rounds, duration):
    coin_in = DEFAULT_COIN_IN * BET_FACTORS[BET_MODE] * BET_MULTI
    total_coin_in = coin_in * rounds
    fg_spins = stats[S_FREE_SPINS]
    triggers = stats[S_FG_TRIGGER]
    mean = stats[S_X_SUM] / rounds
    variance = max(0.0, stats[S_X_SQUARE] / rounds - mean * mean)
    base_rows = [
        ("Game ID", GAME_ID, ""),
        ("PARsheet ID", PARSHEET_ID, ""),
        ("Game Version", GAME_VERSION, ""),
        ("Bet Mode", BET_MODE, MODE_NAMES[BET_MODE]),
        ("Coin In / Round", coin_in, "credit"),
        ("Total Rounds", rounds, ""),
        ("Threads", min(THREADS, rounds), ""),
        ("Duration", duration, "seconds"),
        ("RTP", _safe_div(stats[S_TOTAL_WIN], total_coin_in), ""),
        ("RTP - Base", _safe_div(stats[S_BG_PAY], total_coin_in), ""),
        ("RTP - Scatter", _safe_div(stats[S_SCATTER_PAY], total_coin_in), ""),
        ("RTP - Free Game", _safe_div(stats[S_FG_PAY], total_coin_in), ""),
        ("Hit Rate - Paid Round", _safe_div(stats[S_BG_HITS], rounds), ""),
        ("Hit Rate - FG Spin", _safe_div(stats[S_FG_HITS], fg_spins), ""),
        ("FG Trigger Rate", _safe_div(triggers, rounds), f"1 / {_safe_div(rounds, triggers):.2f}" if triggers else "N/A"),
        ("Average FG Spins", _safe_div(fg_spins, triggers), ""),
        ("Retrigger / Feature", _safe_div(stats[S_RETRIGGER], triggers), ""),
        ("Average FG Multiplier", _safe_div(stats[S_FG_MULTI_SUM], fg_spins), ""),
        ("Max FG Multiplier", stats[S_FG_MULTI_MAX], "x"),
        ("Average BG Cascades", _safe_div(stats[S_BG_CASCADES], rounds), ""),
        ("Average FG Cascades", _safe_div(stats[S_FG_CASCADES], fg_spins), ""),
        ("Max Win", _safe_div(stats[S_MAX_WIN], coin_in), "x Bet"),
        ("Standard Deviation", math.sqrt(variance), ""),
    ]
    df_base = pd.DataFrame(base_rows, columns=["Index", "Value", "Value2"])

    detail_rows = []
    bins = ["8-9", "10-11", "12+"]
    for scene, scene_name in enumerate(("BG", "FG")):
        for symbol in SYMBOLS_SCORE:
            for pay_bin, label in enumerate(bins):
                detail_rows.append(
                    {
                        "Scene": scene_name,
                        "Symbol": SYMBOL_STR[int(symbol)],
                        "Count": label,
                        "Hits": hits[scene, symbol, pay_bin],
                        "Pay": pays[scene, symbol, pay_bin],
                        "RTP": pays[scene, symbol, pay_bin] / total_coin_in,
                        "Eliminate": eliminates[scene, symbol, pay_bin],
                    }
                )
    df_detail = pd.DataFrame(detail_rows)

    labels = []
    for idx, upper in enumerate(THRESHOLD_RECORD):
        labels.append("0" if idx == 0 else f"({THRESHOLD_RECORD[idx - 1]:g}, {upper:g}]")
    df_multiplier = pd.DataFrame(
        {
            "Interval": labels,
            "Base Game": multiplier_line[0],
            "Free Game": multiplier_line[1],
            "Over All": multiplier_line[2],
        }
    )
    df_record = pd.DataFrame({"Stat Index": np.arange(STAT_COUNT), "Value": stats})
    return df_base, df_detail, df_multiplier, df_record


def _print_outputs(df_base, df_detail):
    print("\n=== H013 Fixed Result ===")
    for row in df_base.itertuples(index=False):
        if isinstance(row.Value, float):
            value = f"{row.Value:.6f}"
        else:
            value = str(row.Value)
        print(f"{row.Index:<27} {value:<14} {row.Value2}")
    if SHOW_CONSOLE_DETAIL:
        print("\n=== H013 By-Game Result ===")
        grouped = df_detail.groupby(["Scene", "Symbol"], as_index=False)[["Hits", "Pay", "Eliminate"]].sum()
        print(grouped.to_string(index=False))


def _write_report(df_base, df_detail, df_multiplier, df_record):
    output_dir = os.path.join(BASE_DIR, "Record")
    os.makedirs(output_dir, exist_ok=True)
    stamp = datetime.now().strftime("%y%m%d%H%M")
    filename = f"{PARSHEET_ID}_{GAME_VERSION}_{stamp}_betmode{BET_MODE}_{TOTAL_ROUNDS}.xlsx"
    path = os.path.join(output_dir, filename)
    with pd.ExcelWriter(path) as writer:
        df_base.to_excel(writer, sheet_name="Base Info", index=False)
        df_detail[["Scene", "Symbol", "Count", "Hits"]].to_excel(writer, sheet_name="Hits", index=False)
        df_detail[["Scene", "Symbol", "Count", "Pay", "RTP"]].to_excel(writer, sheet_name="Pay", index=False)
        df_detail[["Scene", "Symbol", "Count", "Eliminate"]].to_excel(writer, sheet_name="Eliminate", index=False)
        df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
        df_record.to_excel(writer, sheet_name="Record Data", index=False)
    print(f"Report: {path}")
    return path


def main():
    _validate_settings()
    rounds = DEBUG_ROUNDS if RUN_SINGLE_SPIN_DEBUG else TOTAL_ROUNDS
    stats, hits, pays, eliminates, multiplier_line, duration = _run_parallel(
        rounds, 1 if RUN_SINGLE_SPIN_DEBUG else THREADS, BET_MODE, BET_MULTI
    )
    df_base, df_detail, df_multiplier, df_record = _build_outputs(
        stats, hits, pays, eliminates, multiplier_line, rounds, duration
    )
    if SHOW_CONSOLE_SUMMARY:
        _print_outputs(df_base, df_detail)
    else:
        rtp = _safe_div(stats[S_TOTAL_WIN], DEFAULT_COIN_IN * BET_FACTORS[BET_MODE] * BET_MULTI * rounds)
        print(f"{GAME_ID} {PARSHEET_ID} mode={BET_MODE} rounds={rounds} duration={duration:.2f}s RTP={rtp:.6f}")
    if OUTPUT_REPORT and not RUN_SINGLE_SPIN_DEBUG:
        _write_report(df_base, df_detail, df_multiplier, df_record)


if __name__ == "__main__":
    main()
