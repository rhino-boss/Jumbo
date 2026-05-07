from __future__ import annotations

import argparse
import importlib
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

PROJECT_DIR_NAME = "H026_彩罐熱舞"


def detect_script_dir() -> Path:
    candidates: list[Path] = []
    if "__file__" in globals():
        try:
            candidates.append(Path(__file__).resolve().parent)
        except Exception:
            pass
    cwd = Path.cwd().resolve()
    candidates.extend(
        [
            cwd,
            cwd / PROJECT_DIR_NAME,
            cwd / "Project_AI" / PROJECT_DIR_NAME,
        ]
    )
    for parent in [cwd, *cwd.parents]:
        candidates.append(parent / "Project_AI" / PROJECT_DIR_NAME)

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "config.js").exists() or (candidate / "config.json").exists():
            return candidate
    return candidates[0]


SCRIPT_DIR = detect_script_dir()
WORKSPACE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.js"
DEFAULT_RECORD_DIR = SCRIPT_DIR / "Record"

# Interactive / 直接執行時的預設設定
INTERACTIVE_BET = 1
INTERACTIVE_ROUNDS = 10**5
INTERACTIVE_BET_MODE = "normal"  # "normal" or "featurebuy"
INTERACTIVE_OUTPUT_XLSX = ""

DEFAULT_BET = INTERACTIVE_BET
DEFAULT_ROUNDS = INTERACTIVE_ROUNDS
DEFAULT_MODE = INTERACTIVE_BET_MODE

if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))


def default_output_xlsx_path(mode: str | None = None) -> Path:
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    mode_name = mode or INTERACTIVE_BET_MODE
    bet_mode = 2 if mode_name == "featurebuy" else 0
    return DEFAULT_RECORD_DIR / f"{SCRIPT_DIR.name}_{timestamp}_betmode{bet_mode}.xlsx"


def load_config(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").strip()
    if path.suffix.lower() == ".js":
        if raw.startswith("window.") and "=" in raw:
            raw = raw.split("=", 1)[1].strip()
        if raw.endswith(";"):
            raw = raw[:-1].strip()
    return json.loads(raw)


def run_original_h026_simulation(rounds: int, bet: int, mode: str, output_xlsx: str) -> tuple[dict[str, Any], Path]:
    simulator_module = importlib.import_module("Project.Slots.H026_Simulator")
    box_module = importlib.import_module("Project.Slots.Source.H026_Box")

    simulator_module.bet_multi = int(bet)
    simulator_module.bet_mode = box_module.mode_featurebuy if mode == "featurebuy" else box_module.mode_normalbet
    simulator_module.total_round = int(rounds)
    simulator_module.debug_spin_trace = False

    if simulator_module.bet_mode == box_module.mode_normalbet:
        simulator_module.coin_in = simulator_module.bet_multi * box_module.default_coin_in * box_module.normalbet
    else:
        simulator_module.coin_in = simulator_module.bet_multi * box_module.default_coin_in * box_module.normalbet * box_module.featurebuy

    output_path = Path(output_xlsx).resolve() if output_xlsx else default_output_xlsx_path(mode).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    original_output_path = box_module.path_output_data
    try:
        box_module.path_output_data = lambda add_info="": str(output_path)
        simulator_module.run_simulation(int(rounds))
        df_base, result = simulator_module.simulater_result(False, False, False, True, True)
    finally:
        box_module.path_output_data = original_output_path

    return {
        "base_info": df_base,
        "summary": result["summary"],
        "hits": result["hits"],
        "pay": result["pay"],
        "eliminate": result["eliminate"],
    }, output_path


def weighted_choice(weight_map: dict[str, float], rng: random.Random) -> str:
    total = float(sum(weight_map.values()))
    roll = rng.uniform(0.0, total)
    running = 0.0
    for key, weight in weight_map.items():
        running += float(weight)
        if roll <= running:
            return key
    return next(reversed(weight_map))


def weighted_choice_list(values: list[int], weights: list[float], rng: random.Random) -> int:
    total = float(sum(weights))
    roll = rng.uniform(0.0, total)
    running = 0.0
    for value, weight in zip(values, weights):
        running += float(weight)
        if roll <= running:
            return int(value)
    return int(values[-1])


def empty_cell() -> dict[str, Any]:
    return {"code": "", "is_gold": False, "multiplier": 0}


class Engine:
    def __init__(self, config: dict[str, Any], seed: int | None = None) -> None:
        self.config = config
        self.rng = random.Random(seed)
        self.rows = int(config["rows"])
        self.cols = int(config["cols"])
        self.symbols = config["symbols"]
        self.gold_reels = set(int(value) for value in config["gold_reels"])
        self.line_patterns = config["line_patterns"]

    def make_symbol(self, reel_index: int, scene: str) -> dict[str, Any]:
        code = weighted_choice(self.config["reel_symbol_weights"][scene][reel_index], self.rng)
        cell = {"code": code, "is_gold": False, "multiplier": 0}
        symbol_info = self.symbols[code]
        goldable = bool(symbol_info.get("goldable"))
        gold_rate = float(self.config["gold_chance"][scene])

        if scene in {"FG", "BF"} and reel_index == 2 and goldable:
            cell["is_gold"] = True
        elif reel_index in self.gold_reels and goldable and self.rng.random() < gold_rate:
            cell["is_gold"] = True

        if cell["is_gold"]:
            cell["multiplier"] = weighted_choice_list(
                self.config["multiplier_values"],
                self.config["multiplier_weights"],
                self.rng,
            )
        return cell

    def new_board(self, scene: str) -> list[list[dict[str, Any]]]:
        return [[self.make_symbol(col, scene) for col in range(self.cols)] for _ in range(self.rows)]

    def scatter_count(self, board: list[list[dict[str, Any]]]) -> int:
        return sum(1 for row in board for cell in row if cell["code"] == "C1")

    def evaluate_line(self, board: list[list[dict[str, Any]]], pattern: list[int]) -> tuple[float, str, list[tuple[int, int]]]:
        cells = [board[pattern[col]][col] for col in range(self.cols)]
        target = ""
        for cell in cells:
            if cell["code"] not in {"WW", "C1", ""}:
                target = cell["code"]
                break
        if not target:
            target = "WW" if all(cell["code"] == "WW" for cell in cells[:3]) else ""
        if not target or target == "C1":
            return 0.0, "", []

        positions: list[tuple[int, int]] = []
        count = 0
        for col, cell in enumerate(cells):
            code = cell["code"]
            if code in {target, "WW"}:
                positions.append((pattern[col], col))
                count += 1
            else:
                break
        if count < 3:
            return 0.0, "", []
        pay = float(self.symbols[target]["pays"].get(str(count), 0.0))
        return pay, target, positions

    def find_wins(self, board: list[list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], set[tuple[int, int]]]:
        line_wins: list[dict[str, Any]] = []
        hit_positions: set[tuple[int, int]] = set()
        for index, pattern in enumerate(self.line_patterns, start=1):
            pay, symbol, positions = self.evaluate_line(board, pattern)
            if pay <= 0:
                continue
            line_wins.append(
                {
                    "line": index,
                    "symbol": symbol,
                    "count": len(positions),
                    "pay": pay,
                    "positions": positions,
                }
            )
            hit_positions.update(positions)
        return line_wins, hit_positions

    def drop_board(self, board: list[list[dict[str, Any]]], hit_positions: set[tuple[int, int]], scene: str) -> tuple[list[list[dict[str, Any]]], list[tuple[int, int]], int]:
        multi_gain = 0
        converted: list[tuple[int, int]] = []
        next_board = [[empty_cell() for _ in range(self.cols)] for _ in range(self.rows)]

        for row, col in hit_positions:
            hit_cell = board[row][col]
            if hit_cell["is_gold"]:
                multi_gain += int(hit_cell["multiplier"])
                converted.append((row, col))

        for col in range(self.cols):
            survivors = [board[row][col] for row in range(self.rows) if (row, col) not in hit_positions]
            write_row = self.rows - 1
            for cell in reversed(survivors):
                next_board[write_row][col] = cell
                write_row -= 1
            while write_row >= 0:
                next_board[write_row][col] = self.make_symbol(col, scene)
                write_row -= 1

        for row, col in converted:
            next_board[row][col] = {"code": "WW", "is_gold": False, "multiplier": 0}
        return next_board, converted, multi_gain

    def play_single_spin(self, scene: str, carry_multiplier: int = 0, board: list[list[dict[str, Any]]] | None = None) -> dict[str, Any]:
        board = board or self.new_board(scene)
        scatter = self.scatter_count(board)
        steps: list[dict[str, Any]] = []
        raw_win = 0.0
        spin_multi = 0
        working = [[dict(cell) for cell in row] for row in board]

        while True:
            line_wins, hit_positions = self.find_wins(working)
            if not line_wins:
                break
            cascade_pay = sum(item["pay"] for item in line_wins)
            raw_win += cascade_pay
            after_drop, converted, multi_gain = self.drop_board(working, hit_positions, scene)
            spin_multi += multi_gain
            steps.append(
                {
                    "board_before": working,
                    "line_wins": line_wins,
                    "hit_positions": sorted(list(hit_positions)),
                    "cascade_pay": cascade_pay,
                    "converted_positions": converted,
                    "added_multiplier": multi_gain,
                    "board_after": after_drop,
                }
            )
            working = after_drop

        applied_multiplier = max(1, carry_multiplier + spin_multi)
        final_win = raw_win * applied_multiplier
        return {
            "scene": scene,
            "board_initial": board,
            "board_final": working,
            "steps": steps,
            "scatter_count": scatter,
            "raw_win": raw_win,
            "added_multiplier": spin_multi,
            "carry_multiplier_after": carry_multiplier + spin_multi,
            "applied_multiplier": applied_multiplier,
            "final_win": final_win,
        }

    def play_round(self, bet: int, mode: str) -> dict[str, Any]:
        if mode == "featurebuy":
            scene = "BF"
            cost = bet * int(self.config["buy_feature_cost"])
            free_left = int(self.config["fg_awards"]["3"])
        else:
            scene = "BG"
            cost = bet
            free_left = 0

        base_spin = self.play_single_spin(scene)
        total_win = base_spin["final_win"] * bet
        carry_multiplier = 0
        fg_spins: list[dict[str, Any]] = []

        if mode == "normal":
            award = self.config["fg_awards"].get(str(base_spin["scatter_count"]))
            free_left = int(award) if award else 0

        while free_left > 0:
            fg_spin = self.play_single_spin("FG", carry_multiplier=carry_multiplier)
            carry_multiplier = int(fg_spin["carry_multiplier_after"])
            fg_spins.append(fg_spin)
            total_win += fg_spin["final_win"] * bet
            extra = self.config["fg_awards"].get(str(fg_spin["scatter_count"]))
            free_left += int(extra) if extra else 0
            free_left -= 1

        return {
            "bet": bet,
            "mode": mode,
            "cost": cost,
            "base_spin": base_spin,
            "fg_spins": fg_spins,
            "total_win": total_win,
            "profit": total_win - cost,
        }


def print_summary(config: dict[str, Any], rounds: int, bet: int, mode: str, duration: float, results: list[dict[str, Any]]) -> dict[str, Any]:
    total_cost = sum(item["cost"] for item in results)
    total_win = sum(item["total_win"] for item in results)
    hit_rounds = sum(1 for item in results if item["total_win"] > 0)
    fg_rounds = sum(1 for item in results if item["fg_spins"])
    max_win = max((item["total_win"] for item in results), default=0.0)
    rtp = (total_win / total_cost) if total_cost else 0.0
    hit_rate = hit_rounds / rounds if rounds else 0.0
    fg_rate = fg_rounds / rounds if rounds else 0.0

    print("----- Base -----")
    print()
    print(f"Duration    : {duration:.2f}s")
    print()
    print(f"PARsheet ID : {config['game_id']}")
    print(f"Bet         : x{bet}")
    print(f"Rounds      : {rounds:,}")
    print(f"Bet Mode    : {'Buy Feature' if mode == 'featurebuy' else 'Normal Bet'}")
    print()
    print(f"RTP         : {rtp:.6f}")
    print(f"Hit Rate    : {hit_rate:.6f}")
    print(f"FG Trigger  : {fg_rate:.6f}")
    print(f"Max Win (x) : {max_win / bet if bet else 0:.2f}")

    return {
        "game_id": config["game_id"],
        "bet": bet,
        "rounds": rounds,
        "bet_mode": mode,
        "duration_sec": duration,
        "rtp": rtp,
        "hit_rate": hit_rate,
        "fg_trigger_rate": fg_rate,
        "max_win": max_win,
        "max_win_x": max_win / bet if bet else 0.0,
        "total_cost": total_cost,
        "total_win": total_win,
    }


def export_xlsx(path: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    if pd is None:
        raise RuntimeError("pandas is required for xlsx export")
    path.parent.mkdir(parents=True, exist_ok=True)
    df_base = pd.DataFrame(
        [
            {
                "game_id": summary["game_id"],
                "bet": summary["bet"],
                "rounds": summary["rounds"],
                "bet_mode": summary["bet_mode"],
                "duration_sec": summary["duration_sec"],
                "rtp": summary["rtp"],
                "hit_rate": summary["hit_rate"],
                "fg_trigger_rate": summary["fg_trigger_rate"],
                "max_win": summary["max_win"],
                "max_win_x": summary["max_win_x"],
                "total_cost": summary["total_cost"],
                "total_win": summary["total_win"],
            }
        ]
    )

    multiplier_rows: list[dict[str, Any]] = []
    hit_rows: list[dict[str, Any]] = []
    pay_rows: list[dict[str, Any]] = []
    eliminate_rows: list[dict[str, Any]] = []
    record_rows: list[dict[str, Any]] = []

    for round_index, item in enumerate(results, start=1):
        all_spins = [item["base_spin"], *item["fg_spins"]]
        record_rows.append(
            {
                "round": round_index,
                "mode": item["mode"],
                "bet": item["bet"],
                "cost": item["cost"],
                "total_win": item["total_win"],
                "profit": item["profit"],
                "fg_spins": len(item["fg_spins"]),
                "base_scatter": item["base_spin"]["scatter_count"],
            }
        )
        for spin_index, spin in enumerate(all_spins, start=1):
            multiplier_rows.append(
                {
                    "round": round_index,
                    "spin": spin_index,
                    "scene": spin["scene"],
                    "added_multiplier": spin["added_multiplier"],
                    "applied_multiplier": spin["applied_multiplier"],
                    "raw_win": spin["raw_win"],
                    "final_win": spin["final_win"],
                }
            )
            hit_rows.append(
                {
                    "round": round_index,
                    "spin": spin_index,
                    "scene": spin["scene"],
                    "hit_lines": sum(len(step["line_wins"]) for step in spin["steps"]),
                    "scatter_count": spin["scatter_count"],
                    "cascade_count": len(spin["steps"]),
                }
            )
            pay_rows.append(
                {
                    "round": round_index,
                    "spin": spin_index,
                    "scene": spin["scene"],
                    "raw_win": spin["raw_win"],
                    "final_win": spin["final_win"],
                }
            )
            for cascade_index, step in enumerate(spin["steps"], start=1):
                eliminate_rows.append(
                    {
                        "round": round_index,
                        "spin": spin_index,
                        "scene": spin["scene"],
                        "cascade_index": cascade_index,
                        "hit_count": len(step["hit_positions"]),
                        "cascade_pay": step["cascade_pay"],
                        "added_multiplier": step["added_multiplier"],
                        "converted_count": len(step["converted_positions"]),
                    }
                )

    df_multiplier = pd.DataFrame(multiplier_rows or [{"round": 0}])
    df_hits = pd.DataFrame(hit_rows or [{"round": 0}])
    df_pay = pd.DataFrame(pay_rows or [{"round": 0}])
    df_eliminate = pd.DataFrame(eliminate_rows or [{"round": 0}])
    df_record = pd.DataFrame(record_rows or [{"round": 0}])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df_base.to_excel(writer, sheet_name="Base Info", index=False)
        df_multiplier.to_excel(writer, sheet_name="Multiplier Line", index=False)
        df_hits.to_excel(writer, sheet_name="Hits", index=False)
        df_pay.to_excel(writer, sheet_name="Pay", index=False)
        df_eliminate.to_excel(writer, sheet_name="Eliminate", index=False)
        df_record.to_excel(writer, sheet_name="Record Data", index=False)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone H026 simulator")
    parser.add_argument("command", nargs="?", default="simulate", choices=("simulate", "spin"))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--bet", type=int, default=DEFAULT_BET)
    parser.add_argument("--mode", choices=("normal", "featurebuy"), default=DEFAULT_MODE)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--xlsx", default="")
    args, _unknown = parser.parse_known_args(argv)
    return args


def normalize_argv(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    skip_next = False
    for index, token in enumerate(argv):
        if skip_next:
            skip_next = False
            continue
        if token == "-f":
            skip_next = True
            continue
        if token.startswith("--f="):
            continue
        if index == 0 and token not in {"simulate", "spin"} and not token.startswith("-"):
            continue
        normalized.append(token)
    return normalized


def default_args_for_interactive() -> list[str]:
    args = [
        "simulate",
        "--config",
        str(DEFAULT_CONFIG_PATH),
        "--rounds",
        str(INTERACTIVE_ROUNDS),
        "--bet",
        str(INTERACTIVE_BET),
        "--mode",
        str(INTERACTIVE_BET_MODE),
    ]
    output_xlsx = INTERACTIVE_OUTPUT_XLSX.strip()
    if output_xlsx:
        args.extend(["--xlsx", output_xlsx])
    else:
        args.extend(["--xlsx", str(default_output_xlsx_path(INTERACTIVE_BET_MODE))])
    return args


def main() -> None:
    normalized_argv = normalize_argv(sys.argv[1:])
    if not normalized_argv:
        normalized_argv = default_args_for_interactive()
    args = parse_args(normalized_argv)
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    engine = Engine(config=config, seed=args.seed)

    print(f"[Simulator] Script Dir : {SCRIPT_DIR}")
    print(f"[Simulator] Config Path: {config_path}")
    if args.command == "simulate":
        print(f"[Simulator] Rounds     : {args.rounds:,}")
        print(f"[Simulator] Bet Mode   : {args.mode}")
        print(f"[Simulator] Bet        : x{args.bet}")
        if args.xlsx:
            print(f"[Simulator] Output XLSX: {Path(args.xlsx).resolve()}")

    if args.command == "spin":
        result = engine.play_round(args.bet, args.mode)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print("[Simulator] Engine     : Project/Slots/H026_Simulator.py (Numba)")
    report, written_xlsx = run_original_h026_simulation(args.rounds, args.bet, args.mode, args.xlsx)
    summary = report["summary"]
    print("----- Base -----")
    print()
    print(f"Duration    : {float(report['base_info'].loc[report['base_info']['Index'] == 'durning', 'Value'].iloc[0].replace('s', '')):.2f}s")
    print()
    print(f"PARsheet ID : {config['game_id']}")
    print(f"Bet         : x{args.bet}")
    print(f"Rounds      : {args.rounds:,}")
    print(f"Bet Mode    : {'Buy Feature' if args.mode == 'featurebuy' else 'Normal Bet'}")
    print()
    print(f"RTP         : {summary['rtp_overall']:.6f}")
    print(f"RTP BG/FG   : {summary['rtp_bg']:.6f} / {summary['rtp_fg']:.6f}")
    print(f"Hit BG/FG   : {summary['hit_rate_bg']:.6f} / {summary['hit_rate_fg']:.6f}")
    print(f"Hit Overall : {summary['hit_rate_overall']:.6f}")
    print(f"FG Trigger  : {summary['fg_trigger_rate']:.6f}")
    print(f"Retrigger   : {summary['retrigger_rate']:.6f}")
    print(f"Gold Usage  : {summary['gold_usage_rate']:.6f}")
    print(f"Multi Usage : {summary['multiplier_usage_rate']:.6f}")
    print(f"Volatility  : {summary['volatility_std']:.6f}")
    print(f"Max Win (x) : {summary['max_win_x']:.2f}")
    print(f"Max Multi   : x{summary['max_multiplier']}")
    print(f"Output XLSX : {written_xlsx}")


if __name__ == "__main__":
    main()
