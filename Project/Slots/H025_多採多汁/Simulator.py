"""H025 多採多汁 Simulator。

外層執行與報表結構以 H026 Simulator 為模板；盤面、Cluster、Wild、Mega、
Scatter 與 Free Game 行為由 Source/H025_game_logic.py（101013 核心）提供。
"""

import argparse
import importlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


# ===== User Settings =====

CONFIG_FILE = "config_92B.js"
TOTAL_ROUNDS = 10**5
BET_MODE = 0
BET_MULTI = 1
RUN_ALL_COMBINATIONS = False
BATCH_RUNS = [
    {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**9, "card_system_enabled": False, "card_system_is_newbie": False},
    {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_92A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_92A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_92A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_94A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_94A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_94A.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_94A.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_92B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_92B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_92B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_92B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_94B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_94B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": True},
    {"config_file": "config_94B.js", "bet_mode": 0, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_94B.js", "bet_mode": 1, "total_rounds": 10**8, "card_system_enabled": True, "card_system_is_newbie": False},
    {"config_file": "config_92A.js", "bet_mode": 2, "total_rounds": 10**7, "card_system_enabled": True, "card_system_is_newbie": False},
]

DEFAULT_THREADS = max(1, min(8, os.cpu_count() or 1))
COIN_IN = 100
GAME_ID = "H025"
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
SHOW_CONSOLE_DETAIL = False
ENABLE_MULTIPLIER = True
FG_SPIN_CAP = 10000
CARD_SYSTEM_ENABLED = True
CARD_SYSTEM_IS_NEWBIE = False  # True: 新手；False: 老手


def parse_env_bool(name, default):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return bool(default)
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def early_cli_value(name):
    try:
        index = sys.argv.index(name)
    except ValueError:
        return None
    return sys.argv[index + 1] if index + 1 < len(sys.argv) else None


CONFIG_FILE = os.environ.get("H025_CONFIG_FILE", early_cli_value("--config") or CONFIG_FILE)
TOTAL_ROUNDS = int(os.environ.get("H025_TOTAL_ROUNDS", str(TOTAL_ROUNDS)))
BET_MODE = int(os.environ.get("H025_BET_MODE", early_cli_value("--bet-mode") or str(BET_MODE)))
BET_MULTI = int(os.environ.get("H025_BET_MULTI", early_cli_value("--bet-multi") or str(BET_MULTI)))
THREADS = max(1, int(os.environ.get("H025_THREADS", str(DEFAULT_THREADS))))
RUN_ALL_COMBINATIONS = parse_env_bool("H025_RUN_ALL_COMBINATIONS", RUN_ALL_COMBINATIONS)
OUTPUT_REPORT = parse_env_bool("H025_OUTPUT_REPORT", OUTPUT_REPORT)
SHOW_CONSOLE_SUMMARY = parse_env_bool("H025_SHOW_CONSOLE_SUMMARY", SHOW_CONSOLE_SUMMARY)
SHOW_CONSOLE_DETAIL = parse_env_bool("H025_SHOW_CONSOLE_DETAIL", SHOW_CONSOLE_DETAIL)
ENABLE_MULTIPLIER = parse_env_bool("H025_ENABLE_MULTIPLIER", ENABLE_MULTIPLIER)
FG_SPIN_CAP = max(1, int(os.environ.get("H025_MAX_FG_SPINS", str(FG_SPIN_CAP))))
CARD_SYSTEM_ENABLED = parse_env_bool("H025_CARD_SYSTEM_ENABLED", CARD_SYSTEM_ENABLED)
CARD_SYSTEM_IS_NEWBIE = parse_env_bool("H025_CARD_SYSTEM_IS_NEWBIE", CARD_SYSTEM_IS_NEWBIE)
if "--no-card" in sys.argv:
    CARD_SYSTEM_ENABLED = False
if "--newbie" in sys.argv:
    CARD_SYSTEM_IS_NEWBIE = True
SEED_BASE = int(os.environ.get("H025_SEED", str(int.from_bytes(os.urandom(4), "little"))))


def resolve_base_dir():
    cwd = Path.cwd().resolve()
    candidates = []
    override = os.environ.get("H025_BASE_DIR")
    if override:
        candidates.append(Path(override).expanduser().resolve())
    file_value = globals().get("__file__")
    file_parent = Path(file_value).resolve().parent if file_value else None
    if file_parent is not None:
        candidates.append(file_parent)
    candidates.append(cwd)
    anchors = [cwd, *cwd.parents]
    if file_parent is not None:
        anchors.extend([file_parent, *file_parent.parents])
    for anchor in anchors:
        search_roots = [anchor, anchor / "Slots", anchor / "Project_AI" / "Slots"]
        for search_root in search_roots:
            candidates.extend([
                search_root / "H025_多採多汁",
                search_root / "H025_多採多汁 (未完成)",
            ])
            if search_root.is_dir():
                candidates.extend(search_root.glob("H025_多採多汁*"))
    checked = []
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        key = os.path.normcase(str(candidate))
        if key in seen:
            continue
        seen.add(key)
        checked.append(str(candidate / CONFIG_FILE))
        if (candidate / CONFIG_FILE).is_file() and (candidate / "Source" / "H025_game_logic.py").is_file():
            return candidate
    raise FileNotFoundError(f"Cannot locate H025 {CONFIG_FILE}. Checked: " + " | ".join(checked))


BASE_DIR = resolve_base_dir()
SIMULATOR_PATH = BASE_DIR / "Simulator.py"
OUTPUT_DIR = BASE_DIR / "Record"
os.environ["H025_BASE_DIR"] = str(BASE_DIR)
os.environ["H025_CONFIG_FILE"] = CONFIG_FILE
SOURCE_DIR = BASE_DIR / "Source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

if "H025_game_logic" in sys.modules:
    logic = importlib.reload(sys.modules["H025_game_logic"])
else:
    logic = importlib.import_module("H025_game_logic")
if logic.GAME_DATA is None:
    raise RuntimeError(f"H025 game config failed to load: {BASE_DIR / CONFIG_FILE}")

CARD_SYSTEM = logic.GAME_DATA.get("card_system", {})
CARD_SYSTEM_ENABLED = CARD_SYSTEM_ENABLED and bool(CARD_SYSTEM.get("enabled", False))
CARD_RETRY_LIMIT = max(1, int(CARD_SYSTEM.get("retry_limit", 5000)))


def get_card_profile_cards(player, segment):
    player_data = CARD_SYSTEM.get(player, {})
    normal_bet = player_data.get("normal_bet", {}) if isinstance(player_data, dict) else {}
    return list(normal_bet.get(segment, [])) if isinstance(normal_bet, dict) else []


CARD_BG = get_card_profile_cards("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand", "weight_bg")
CARD_FG = get_card_profile_cards("newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand", "weight_fg")


def pick_card(cards):
    total_weight = sum(max(0, int(card.get("weight", 0))) for card in cards)
    if total_weight <= 0:
        return None
    value = int(np.random.randint(0, total_weight))
    running = 0
    for card in cards:
        running += max(0, int(card.get("weight", 0)))
        if value < running:
            return card
    return cards[-1]


def is_card_match(card, score, coin_in, triggered_free_game=False):
    if card is None:
        return True
    if card.get("type") == "free_game":
        return bool(triggered_free_game)
    multiplier = float(score) / float(coin_in)
    return multiplier > float(card.get("min", 0.0)) and multiplier <= float(card.get("max", 0.0))


# ===== Record Layout =====

RETRIGGER_SPINS = np.array([0, 0, 0, 8, 10, 15, 20, 30], dtype=np.int64)
CASCADE_OVERFLOW = 21
WIN_LABELS = ["0x", "(0,1)x", "[1,2)x", "[2,5)x", "[5,10)x", "[10,20)x", "[20,50)x", "[50,100)x", "[100,500)x", "500x+"]
WIN_BOUNDS = np.array([1, 2, 5, 10, 20, 50, 100, 500], dtype=np.float64)


def new_record():
    return {
        "rounds": 0,
        "bg_pay": 0,
        "fg_pay": 0,
        "total_pay_square": 0.0,
        "bg_hit_rounds": 0,
        "fg_hit_spins": 0,
        "fg_trigger_count": 0,
        "fg_retrigger_count": 0,
        "fg_spins": 0,
        "fg_truncated_sessions": 0,
        "retry_total": 0,
        "retry_limit_exceeded": 0,
        "retry_fail_bg_range": 0,
        "retry_fail_bg_freegame": 0,
        "retry_fail_fg": 0,
        "max_round_pay": 0,
        "max_bg_pay": 0,
        "max_fg_session_pay": 0,
        "bg_mega_checks": 0,
        "bg_mega_success": 0,
        "bg_mega_fail": 0,
        "fg_mega_checks": 0,
        "fg_mega_success": 0,
        "fg_mega_fail": 0,
        "bg_initial_scatter": np.zeros(8, dtype=np.int64),
        "bg_final_scatter": np.zeros(8, dtype=np.int64),
        "fg_final_scatter": np.zeros(8, dtype=np.int64),
        "bg_cascade": np.zeros(CASCADE_OVERFLOW + 1, dtype=np.int64),
        "fg_cascade": np.zeros(CASCADE_OVERFLOW + 1, dtype=np.int64),
        "bg_multiplier": np.zeros(101, dtype=np.int64),
        "fg_multiplier": np.zeros(101, dtype=np.int64),
        "win_distribution": np.zeros(len(WIN_LABELS), dtype=np.int64),
    }


def scatter_spins(c1_count):
    return int(RETRIGGER_SPINS[c1_count]) if 0 <= c1_count < len(RETRIGGER_SPINS) else 0


def cascade_bucket(value):
    return min(max(0, int(value)), CASCADE_OVERFLOW)


def win_bucket(pay):
    multiplier = float(pay) / COIN_IN
    if multiplier == 0:
        return 0
    return int(np.searchsorted(WIN_BOUNDS, multiplier, side="right") + 1)


def record_scene_spin(record, scene, result):
    final_c1 = min(int(result["final_c1"]), 7)
    cascade = cascade_bucket(result["cascade"])
    multiplier = min(int(result["multiplier"]), 100)
    if scene == "BG":
        record["bg_final_scatter"][final_c1] += 1
        record["bg_cascade"][cascade] += 1
        record["bg_multiplier"][multiplier] += 1
        record["bg_mega_checks"] += result["mega_checks"]
        record["bg_mega_success"] += result["mega_success"]
        record["bg_mega_fail"] += result["mega_fail"]
    else:
        record["fg_final_scatter"][final_c1] += 1
        record["fg_cascade"][cascade] += 1
        record["fg_multiplier"][multiplier] += 1
        record["fg_mega_checks"] += result["mega_checks"]
        record["fg_mega_success"] += result["mega_success"]
        record["fg_mega_fail"] += result["mega_fail"]


def run_free_game_session(game, initial_spins, record, spin_cap):
    game.wild_eliminate_count = 0
    game.mega_level = 0
    game.mega_eliminate_count = 0
    remaining = int(initial_spins)
    session_pay = 0
    session_spins = 0
    while remaining > 0 and session_spins < spin_cap:
        result = logic._play_spin(game, keep_multipliers=True)
        remaining -= 1
        session_spins += 1
        session_pay += result["score"]
        record["fg_spins"] += 1
        record["fg_hit_spins"] += int(result["score"] > 0)
        record_scene_spin(record, "FG", result)
        extra = scatter_spins(result["final_c1"])
        if extra:
            record["fg_retrigger_count"] += 1
            remaining += extra
    if remaining > 0:
        record["fg_truncated_sessions"] += 1
    record["max_fg_session_pay"] = max(record["max_fg_session_pay"], session_pay)
    return session_pay


# ===== Simulation =====

def simulate_bg_spin(bg_game):
    attempt = new_record()
    bg = logic._play_spin(bg_game, keep_multipliers=False)
    bg_pay = int(bg["score"])
    attempt["rounds"] = 1
    attempt["bg_pay"] = bg_pay
    attempt["bg_hit_rounds"] = int(bg_pay > 0)
    attempt["max_bg_pay"] = bg_pay
    attempt["bg_initial_scatter"][min(int(bg["initial_c1"]), 7)] += 1
    record_scene_spin(attempt, "BG", bg)
    initial_spins = scatter_spins(bg["final_c1"])
    return attempt, bg_pay, initial_spins


def simulate_fg_session(fg_game, initial_spins, fg_spin_cap):
    attempt = new_record()
    attempt["fg_trigger_count"] = 1
    fg_pay = run_free_game_session(fg_game, initial_spins, attempt, fg_spin_cap)
    attempt["fg_pay"] = fg_pay
    return attempt, fg_pay


def finalize_paid_round(attempt, bg_pay, fg_pay):
    total_pay = bg_pay + fg_pay
    attempt["total_pay_square"] = float(total_pay) ** 2
    attempt["max_round_pay"] = total_pay
    attempt["win_distribution"][win_bucket(total_pay)] += 1
    return attempt


def simulator_chunk(args):
    total_round, seed, enable_multiplier, fg_spin_cap = args
    logic._seed_all(seed)
    record = new_record()
    bg_game = logic.Game7x7(enable_multiplier=enable_multiplier)
    fg_game = logic.Game7x7(is_free_game=True, enable_multiplier=enable_multiplier)
    for _ in range(int(total_round)):
        bg_card = pick_card(CARD_BG) if CARD_SYSTEM_ENABLED else None
        retry_count = 0
        while True:
            bg_attempt, bg_pay, initial_spins = simulate_bg_spin(bg_game)
            triggered_free_game = bool(initial_spins)
            accepted = True
            fail_key = None
            if CARD_SYSTEM_ENABLED and bg_card is not None:
                if bg_card.get("type") == "free_game":
                    if not triggered_free_game:
                        accepted = False
                        fail_key = "retry_fail_bg_freegame"
                elif triggered_free_game or not is_card_match(bg_card, bg_pay, COIN_IN, False):
                    accepted = False
                    fail_key = "retry_fail_bg_range"
            if accepted:
                break
            record["retry_total"] += 1
            record[fail_key] += 1
            retry_count += 1
            if retry_count >= CARD_RETRY_LIMIT:
                record["retry_limit_exceeded"] += 1
                break

        fg_pay = 0
        attempt = bg_attempt
        if triggered_free_game:
            fg_card = pick_card(CARD_FG) if CARD_SYSTEM_ENABLED and bg_card and bg_card.get("type") == "free_game" else None
            fg_retry_count = 0
            while True:
                fg_attempt, fg_pay = simulate_fg_session(fg_game, initial_spins, fg_spin_cap)
                if is_card_match(fg_card, fg_pay, COIN_IN, True):
                    break
                record["retry_total"] += 1
                record["retry_fail_fg"] += 1
                fg_retry_count += 1
                if fg_retry_count >= CARD_RETRY_LIMIT:
                    record["retry_limit_exceeded"] += 1
                    break
            attempt = merge_record_data((attempt, fg_attempt))

        attempt = finalize_paid_round(attempt, bg_pay, fg_pay)
        record = merge_record_data((record, attempt))
    return record


def build_chunk_rounds(total_round, threads):
    threads = max(1, min(int(threads), int(total_round) if total_round > 0 else 1))
    base, extra = divmod(int(total_round), threads)
    return [base + (1 if index < extra else 0) for index in range(threads)]


def merge_record_data(chunks):
    merged = new_record()
    maximum_keys = {"max_round_pay", "max_bg_pay", "max_fg_session_pay"}
    for chunk in chunks:
        for key, value in chunk.items():
            if isinstance(value, np.ndarray):
                merged[key] += value
            elif key in maximum_keys:
                merged[key] = max(merged[key], value)
            else:
                merged[key] += value
    return merged


def run_simulation(total_round=TOTAL_ROUNDS, threads=THREADS, seed_base=SEED_BASE, enable_multiplier=ENABLE_MULTIPLIER):
    total_round = int(total_round)
    if total_round <= 0:
        raise ValueError("total_round must be greater than zero")

    # H026 pattern: warm up once before timing.
    print("Numba warm-up: compiling H025 game functions...", flush=True)
    simulator_chunk((1, 0, enable_multiplier, FG_SPIN_CAP))
    chunk_rounds = build_chunk_rounds(total_round, threads)
    jobs = [
        (rounds, (int(seed_base) + index * 7919) & 0xFFFFFFFF, enable_multiplier, FG_SPIN_CAP)
        for index, rounds in enumerate(chunk_rounds)
    ]
    print(
        f"Simulation: config={CONFIG_FILE}, rounds={total_round:,}, "
        f"threads={len(jobs)}, seed={seed_base}",
        flush=True,
    )
    start = time.perf_counter()
    if len(jobs) == 1:
        record_data = simulator_chunk(jobs[0])
    else:
        with ThreadPoolExecutor(max_workers=len(jobs), thread_name_prefix="H025") as executor:
            record_data = merge_record_data(list(executor.map(simulator_chunk, jobs)))
    return record_data, time.perf_counter() - start, COIN_IN


# ===== Report =====

def config_tag():
    stem = Path(CONFIG_FILE).stem
    match = re.search(r"(\d{2}[A-Za-z])$", stem)
    return match.group(1).upper() if match else stem.replace("config", "").strip("_") or "101013"


def bet_mode_label():
    return {0: "Normal Bet", 1: "Extra Bet", 2: "Feature Buy"}.get(BET_MODE, f"Bet Mode {BET_MODE}")


def build_result_frames(record_data, total_round, duration, coin_in, threads=THREADS, seed_base=SEED_BASE):
    total_pay = record_data["bg_pay"] + record_data["fg_pay"]
    total_coin_in = total_round * coin_in
    fg_spins = record_data["fg_spins"]
    total_hits = total_round - int(record_data["win_distribution"][0])
    rtp_total = total_pay / total_coin_in
    rtp_bg = record_data["bg_pay"] / total_coin_in
    rtp_fg = record_data["fg_pay"] / total_coin_in
    mean_x = total_pay / total_coin_in
    second_moment = record_data["total_pay_square"] / total_round / (coin_in ** 2)
    summary = {
        "rtp_total": rtp_total,
        "rtp_bg": rtp_bg,
        "rtp_fg": rtp_fg,
        "hit_rate_total": total_hits / total_round,
        "hit_rate_bg": record_data["bg_hit_rounds"] / total_round,
        "hit_rate_fg": record_data["fg_hit_spins"] / fg_spins if fg_spins else 0.0,
        "fg_trigger_rate": record_data["fg_trigger_count"] / total_round,
        "fg_trigger_count": record_data["fg_trigger_count"],
        "retrigger_rate": record_data["fg_retrigger_count"] / fg_spins if fg_spins else 0.0,
        "avg_fg_spins": fg_spins / record_data["fg_trigger_count"] if record_data["fg_trigger_count"] else 0.0,
        "volatility_std": float(np.sqrt(max(0.0, second_moment - mean_x ** 2))),
        "max_win_x": record_data["max_round_pay"] / coin_in,
        "card_system": "on" if CARD_SYSTEM_ENABLED else "off",
        "card_system_profile": "newbie" if CARD_SYSTEM_IS_NEWBIE else "oldhand",
        "retry_total": record_data["retry_total"],
        "avg_retry": record_data["retry_total"] / total_round,
    }
    base_rows = [
        ("game_id", GAME_ID),
        ("config", CONFIG_FILE),
        ("config_tag", config_tag()),
        ("bet_mode", bet_mode_label()),
        ("bet_multi", BET_MULTI),
        ("coin_in", coin_in),
        ("total_rounds", total_round),
        ("threads", threads),
        ("seed_base", seed_base),
        ("duration_sec", round(duration, 3)),
        ("rtp_total", rtp_total),
        ("rtp_bg", rtp_bg),
        ("rtp_fg", rtp_fg),
        ("hit_rate_total", summary["hit_rate_total"]),
        ("hit_rate_bg", summary["hit_rate_bg"]),
        ("hit_rate_fg", summary["hit_rate_fg"]),
        ("fg_trigger_rate", summary["fg_trigger_rate"]),
        ("fg_trigger_count", summary["fg_trigger_count"]),
        ("retrigger_rate", summary["retrigger_rate"]),
        ("fg_spins", fg_spins),
        ("avg_fg_spins", summary["avg_fg_spins"]),
        ("volatility_std", summary["volatility_std"]),
        ("max_win_x", summary["max_win_x"]),
        ("fg_truncated_sessions", record_data["fg_truncated_sessions"]),
        ("card_system", summary["card_system"]),
        ("card_system_profile", summary["card_system_profile"] if CARD_SYSTEM_ENABLED else "off"),
        ("retry_limit", CARD_RETRY_LIMIT if CARD_SYSTEM_ENABLED else 0),
        ("retry_total", summary["retry_total"]),
        ("avg_retry", summary["avg_retry"]),
        ("retry_limit_exceeded", record_data["retry_limit_exceeded"]),
        ("retry_fail_bg_range", record_data["retry_fail_bg_range"]),
        ("retry_fail_bg_freegame", record_data["retry_fail_bg_freegame"]),
        ("retry_fail_fg", record_data["retry_fail_fg"]),
    ]
    df_base = pd.DataFrame(base_rows, columns=["Index", "Value"])
    df_rtp_hit = pd.DataFrame([
        ("Total Paid Round", total_round, total_hits, summary["hit_rate_total"], total_pay, rtp_total),
        ("Base Game", total_round, record_data["bg_hit_rounds"], summary["hit_rate_bg"], record_data["bg_pay"], rtp_bg),
        ("Free Game Spin", fg_spins, record_data["fg_hit_spins"], summary["hit_rate_fg"], record_data["fg_pay"], rtp_fg),
    ], columns=["Scene", "Sample Count", "Hit Count", "Hit Rate", "Pay", "RTP Contribution"])
    df_win = pd.DataFrame({
        "Interval": WIN_LABELS,
        "Count": record_data["win_distribution"],
        "Rate": record_data["win_distribution"] / total_round,
    })
    df_scatter = pd.DataFrame({
        "C1 Count": range(8),
        "BG Initial Count": record_data["bg_initial_scatter"],
        "BG Initial Rate": record_data["bg_initial_scatter"] / total_round,
        "BG Final Count": record_data["bg_final_scatter"],
        "BG Final Rate": record_data["bg_final_scatter"] / total_round,
        "FG Final Count": record_data["fg_final_scatter"],
        "FG Final Rate": record_data["fg_final_scatter"] / fg_spins if fg_spins else np.zeros(8),
    })
    cascade_labels = [str(value) for value in range(CASCADE_OVERFLOW)] + [f"{CASCADE_OVERFLOW}+"]
    df_cascade = pd.DataFrame({
        "Cascades": cascade_labels,
        "BG Count": record_data["bg_cascade"],
        "BG Rate": record_data["bg_cascade"] / total_round,
        "FG Count": record_data["fg_cascade"],
        "FG Rate": record_data["fg_cascade"] / fg_spins if fg_spins else np.zeros(CASCADE_OVERFLOW + 1),
    })
    indexes = np.flatnonzero(record_data["bg_multiplier"] + record_data["fg_multiplier"])
    df_multiplier = pd.DataFrame({
        "Multiplier": indexes,
        "BG Count": record_data["bg_multiplier"][indexes],
        "FG Count": record_data["fg_multiplier"][indexes],
    })
    df_mega = pd.DataFrame([
        ("BG", record_data["bg_mega_checks"], record_data["bg_mega_success"], record_data["bg_mega_fail"]),
        ("FG", record_data["fg_mega_checks"], record_data["fg_mega_success"], record_data["fg_mega_fail"]),
    ], columns=["Scene", "Trigger Checks", "Placement Success", "Placement Fail"])
    raw_rows = [(key, json.dumps(value.tolist()) if isinstance(value, np.ndarray) else value) for key, value in record_data.items()]
    df_record = pd.DataFrame(raw_rows, columns=["Metric", "Value"])
    return {
        "Base Info": df_base,
        "RTP Hit Rate": df_rtp_hit,
        "Win Distribution": df_win,
        "Scatter Distribution": df_scatter,
        "Cascade Distribution": df_cascade,
        "Wild Multiplier": df_multiplier,
        "Mega Feature": df_mega,
        "Record Data": df_record,
    }, summary


def print_console_result(frames):
    if SHOW_CONSOLE_SUMMARY:
        print("\n=== Fixed Result ===")
        rows = list(frames["Base Info"].itertuples(index=False))
        width = max(len(str(row.Index)) for row in rows)
        for row in rows:
            print(f"{str(row.Index):<{width}} : {row.Value}")
    if SHOW_CONSOLE_DETAIL:
        for name, frame in frames.items():
            if name not in {"Base Info", "Record Data"}:
                print(f"\n=== {name} ===")
                print(frame.to_string(index=False))


def format_rounds_tag(total_round):
    value = int(total_round)
    exponent = 0
    while value > 0 and value % 10 == 0:
        value //= 10
        exponent += 1
    return f"10{exponent}" if value == 1 and exponent else str(total_round)


def print_batch_summary(duration, summary):
    print(f"* game_id: {GAME_ID}", flush=True)
    print(f"* config: {CONFIG_FILE}", flush=True)
    print(f"* bet_mode: {bet_mode_label()}", flush=True)
    print(f"* duration: {duration:.2f}s", flush=True)
    print(f"* rtp_total: {summary['rtp_total'] * 100:.4f}%", flush=True)
    print(f"* rtp_bg: {summary['rtp_bg'] * 100:.4f}%", flush=True)
    print(f"* rtp_fg: {summary['rtp_fg'] * 100:.4f}%", flush=True)
    print(f"* hit_rate_total: {summary['hit_rate_total']:.6f}", flush=True)
    print(f"* hit_rate_bg: {summary['hit_rate_bg']:.6f}", flush=True)
    print(f"* hit_rate_fg: {summary['hit_rate_fg']:.6f}", flush=True)
    print(f"* fg_trigger_rate: {summary['fg_trigger_rate']:.6f} ({summary['fg_trigger_count']} rounds)", flush=True)
    print(f"* retrigger_rate: {summary['retrigger_rate']:.6f}", flush=True)
    print(f"* avg_fg_spins: {summary['avg_fg_spins']:.4f}", flush=True)
    profile = f" ({summary['card_system_profile']})" if CARD_SYSTEM_ENABLED else ""
    print(f"* card_system: {summary['card_system']}{profile}", flush=True)
    print(f"* retry_total: {summary['retry_total']} (avg {summary['avg_retry']:.6f})", flush=True)


def output_report(frames, summary, total_round):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    profile_suffix = f"_{summary['card_system_profile']}_card" if CARD_SYSTEM_ENABLED else ""
    filename = f"{GAME_ID}_{config_tag()}_{timestamp}_betmode{BET_MODE}_{format_rounds_tag(total_round)}{profile_suffix}.xlsx"
    path = OUTPUT_DIR / filename
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in frames.items():
            frame.to_excel(writer, sheet_name=name[:31], index=False)
            worksheet = writer.sheets[name[:31]]
            worksheet.freeze_panes = "A2"
            for cells in worksheet.columns:
                width = min(48, max(12, max(len(str(cell.value or "")) for cell in cells) + 2))
                worksheet.column_dimensions[cells[0].column_letter].width = width
            if name == "RTP Hit Rate":
                for row in range(2, worksheet.max_row + 1):
                    worksheet[f"D{row}"].number_format = "0.0000%"
                    worksheet[f"F{row}"].number_format = "0.0000%"
    return path


# ===== Batch / Main =====

def run_all_combinations(total_round, threads, seed_base, output_report_enabled):
    for index, combo in enumerate(BATCH_RUNS, start=1):
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["H025_CONFIG_FILE"] = combo["config_file"]
        env["H025_TOTAL_ROUNDS"] = str(total_round if total_round != TOTAL_ROUNDS else combo["total_rounds"])
        env["H025_BET_MODE"] = str(combo["bet_mode"])
        env["H025_BET_MULTI"] = str(BET_MULTI)
        env["H025_THREADS"] = str(threads)
        env["H025_SEED"] = str(seed_base)
        env["H025_OUTPUT_REPORT"] = "true" if output_report_enabled else "false"
        env["H025_CARD_SYSTEM_ENABLED"] = "true" if combo["card_system_enabled"] else "false"
        env["H025_CARD_SYSTEM_IS_NEWBIE"] = "true" if combo["card_system_is_newbie"] else "false"
        env["H025_RUN_ALL_COMBINATIONS"] = "false"
        env["H025_BATCH_CHILD"] = "1"
        print(
            f"\n=== Batch {index}/{len(BATCH_RUNS)}: config={combo['config_file']}, "
            f"bet_mode={combo['bet_mode']}, total_rounds={env['H025_TOTAL_ROUNDS']}, "
            f"card_system_enabled={combo['card_system_enabled']}, "
            f"card_system_is_newbie={combo['card_system_is_newbie']} ===",
            flush=True,
        )
        subprocess.run([sys.executable, str(SIMULATOR_PATH)], check=True, env=env)


def parse_arguments():
    parser = argparse.ArgumentParser(description="H025 Simulator (H026 framework / 101013 game logic)")
    parser.add_argument("-r", "--rounds", type=int, default=TOTAL_ROUNDS)
    parser.add_argument("-w", "--workers", type=int, default=THREADS)
    parser.add_argument("--seed", type=int, default=SEED_BASE)
    parser.add_argument("--config", default=CONFIG_FILE)
    parser.add_argument("--bet-mode", type=int, default=BET_MODE)
    parser.add_argument("--bet-multi", type=int, default=BET_MULTI)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--no-multiplier", action="store_true")
    parser.add_argument("--no-card", action="store_true")
    parser.add_argument("--newbie", action="store_true")
    parser.add_argument("--detail", action="store_true")
    if "ipykernel" in sys.modules:
        return parser.parse_known_args()[0]
    return parser.parse_args()


def main():
    global SHOW_CONSOLE_DETAIL
    args = parse_arguments()
    SHOW_CONSOLE_DETAIL = SHOW_CONSOLE_DETAIL or args.detail
    output_enabled = OUTPUT_REPORT and not args.no_report
    if (RUN_ALL_COMBINATIONS or args.all) and os.environ.get("H025_BATCH_CHILD") != "1":
        run_all_combinations(args.rounds, args.workers, args.seed, output_enabled)
        return
    record_data, duration, coin_in = run_simulation(
        total_round=args.rounds,
        threads=args.workers,
        seed_base=args.seed,
        enable_multiplier=ENABLE_MULTIPLIER and not args.no_multiplier,
    )
    frames, summary = build_result_frames(record_data, args.rounds, duration, coin_in, args.workers, args.seed)
    print_console_result(frames)
    print_batch_summary(duration, summary)
    if output_enabled:
        path = output_report(frames, summary, args.rounds)
        print(f"\nReport: {path}")


if __name__ == "__main__":
    main()
