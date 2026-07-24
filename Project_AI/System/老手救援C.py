"""老手救援 C 模擬器。

目前使用 Fixed Weight 倍率線型：

* 自然 Spin 依倍率區間與 Fixed Weight 抽樣。
* 自然 FG 以獨立機率抽樣；預設 1%，可由 ``--natural-fg-rate`` 修改。
* 救援固定為 FG，倍率直接落在指定 Tier 區間。
* 遊戲層透過 GameAdapter 隔離，日後可加入其他獨立遊戲模型。

預設每 50 轉檢查一次。這是尚未定案的模擬參數，可由
``--check-interval`` 修改。

範例：

    python 老手救援C.py --players 1000 --spins 1000
    python 老手救援C.py --players 100 --natural-fg-rate 0.01
"""

from __future__ import annotations

import argparse
import sys
import time
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd


def _locate_script_dir() -> Path:
    """定位本程式資料夾；避免 Jupyter 沿用其他檔案的 __file__。"""

    candidates: list[Path] = []
    try:
        file_path = Path(__file__).resolve()
        if file_path.name == "老手救援C.py":
            candidates.append(file_path.parent)
    except NameError:
        pass

    current = Path.cwd().resolve()
    for base in (current, *current.parents):
        candidates.extend((base / "Project_AI" / "System", base / "System", base))

    for candidate in candidates:
        if (candidate / "老手救援C.py").is_file():
            return candidate.resolve()

    raise FileNotFoundError("無法定位 Project_AI/System/老手救援C.py；請先將 Jupyter 工作目錄切到 2_Program")


SCRIPT_DIR = _locate_script_dir()
DEFAULT_REPORT_DIR = SCRIPT_DIR / "Record"

NEWBIE_LAST_SPIN = 200

WINDOW_SHORT = 50
WINDOW_MID = 200
WINDOW_LONG = 500
NO_FG_LIMIT = 100

STAGE_MID_RTP = {
    "A": 0.60,
    "B": 0.50,
    "C": 0.40,
    "D": 0.50,
}

TIER_RANGES = {
    "T1": (80.0, 85.0),
    "T2": (50.0, 55.0),
    "T3": (30.0, 35.0),
    "T4": (25.0, 30.0),
    "T5": (15.0, 20.0),
    "T6": (10.0, 15.0),
}

# Fixed Weight 只決定自然 Spin 倍率區間；
# 是否觸發 FG 由獨立的可調機率決定。
FIXED_WEIGHT_MULTIPLIER_CURVE = (
    (-1.0, 0.0, 886736787, 0.0),
    (0.0, 1.0, 11694229, 0.8),
    (1.0, 2.0, 16256897, 1.7),
    (2.0, 3.0, 11555104, 2.7),
    (3.0, 4.0, 12298861, 3.7),
    (4.0, 5.0, 10019810, 4.8),
    (5.0, 6.0, 7927665, 5.9),
    (6.0, 7.0, 2020123, 6.5),
    (7.0, 8.0, 8363309, 7.7),
    (8.0, 9.0, 3070235, 8.9),
    (9.0, 10.0, 6145390, 9.8),
    (10.0, 15.0, 9801988, 12.9),
    (15.0, 20.0, 5837980, 18.1),
    (20.0, 25.0, 2443119, 23.4),
    (25.0, 30.0, 2129736, 28.7),
    (30.0, 35.0, 405781, 32.6),
    (35.0, 40.0, 951038, 38.4),
    (40.0, 45.0, 219578, 43.7),
    (45.0, 50.0, 1102108, 48.4),
    (50.0, 60.0, 428617, 57.2),
    (60.0, 70.0, 44267, 65.8),
    (70.0, 80.0, 189364, 76.4),
    (80.0, 90.0, 73075, 86.9),
    (90.0, 100.0, 137368, 97.2),
    (100.0, 120.0, 86777, 113.1),
    (120.0, 140.0, 21079, 132.3),
    (140.0, 160.0, 14053, 152.1),
    (160.0, 180.0, 12647, 173.2),
    (180.0, 200.0, 5621, 194.8),
    (200.0, 250.0, 5972, 226.4),
    (250.0, 300.0, 702, 277.7),
    (300.0, 350.0, 351, 325.7),
    (350.0, 400.0, 0, 379.3),
    (400.0, 450.0, 0, 428.2),
    (450.0, 500.0, 0, 479.9),
    (500.0, 550.0, 0, 526.2),
    (550.0, 600.0, 0, 580.0),
    (600.0, 650.0, 0, 629.5),
    (650.0, 700.0, 0, 678.6),
    (700.0, 750.0, 0, 726.0),
    (750.0, 800.0, 0, 786.5),
    (800.0, 850.0, 0, 828.9),
    (850.0, 900.0, 0, 880.3),
    (900.0, 950.0, 0, 925.9),
    (950.0, 1000.0, 351, 985.6),
    (1000.0, 2000.0, 0, 1454.7),
    (2000.0, 3000.0, 0, 2485.8),
    (3000.0, 4000.0, 0, 3535.5),
    (4000.0, 5000.0, 0, 4520.7),
    (5000.0, 6000.0, 0, 5555.5),
    (6000.0, 7000.0, 0, 6489.4),
    (7000.0, 8000.0, 0, 7562.8),
    (8000.0, 9000.0, 0, 8559.2),
    (9000.0, 10000.0, 0, 9552.3),
    (10000.0, 20000.0, 0, 12787.0),
    (20000.0, 30000.0, 0, 23082.8),
    (30000.0, 100000.0, 0, 35529.0),
    (100000.0, 999999.0, 0, 0.0),
)


@dataclass(frozen=True)
class SpinOutcome:
    multiplier: float
    triggered_fg: bool


@dataclass(frozen=True)
class RescueDecision:
    stage: str
    rule_id: str
    rule_description: str
    tier: str | None
    short_rtp: float
    mid_rtp: float
    long_rtp: float | None
    no_fg_spins: int
    mid_bad: bool
    long_bad: bool | None

    @property
    def triggered(self) -> bool:
        return self.tier is not None


class GameAdapter(ABC):
    """遊戲模擬介面；救援規則只依賴這個介面。"""

    game_key: str

    @abstractmethod
    def natural_spin(self, is_newbie: bool) -> SpinOutcome:
        """產生一個自然付費 Spin（含完整 FG 結果）。"""

    @abstractmethod
    def rescue_fg(self, tier: str) -> SpinOutcome:
        """產生符合指定 Tier 的 FG 救援結果。"""

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """回傳報表用遊戲設定。"""

    def multiplier_curve_rows(self) -> list[dict[str, Any]]:
        return []


class FixedWeightAdapter(GameAdapter):
    game_key = "FIXED_WEIGHT"

    def __init__(self, seed: int, natural_fg_rate: float):
        if not 0.0 <= natural_fg_rate <= 1.0:
            raise ValueError("--natural-fg-rate 必須介於 0 與 1")
        self.seed = int(seed)
        self.natural_fg_rate = float(natural_fg_rate)
        self.rng = np.random.default_rng(self.seed)

        curve = np.asarray(FIXED_WEIGHT_MULTIPLIER_CURVE, dtype=np.float64)
        self._curve_lower = curve[:, 0]
        self._curve_upper = curve[:, 1]
        curve_weights = curve[:, 2]
        self._curve_multiplier = curve[:, 3]
        self._curve_total_weight = int(curve_weights.sum())
        self._curve_cdf = np.cumsum(curve_weights / curve_weights.sum())
        self._curve_expected_rtp = float(
            np.sum(self._curve_multiplier * curve_weights) / curve_weights.sum()
        )

    def _sample_natural_multiplier(self) -> float:
        draw = float(self.rng.random())
        index = min(
            int(np.searchsorted(self._curve_cdf, draw, side="right")),
            len(self._curve_cdf) - 1,
        )
        return float(self._curve_multiplier[index])

    def natural_spin(self, is_newbie: bool) -> SpinOutcome:
        del is_newbie
        multiplier = self._sample_natural_multiplier()
        triggered_fg = bool(self.rng.random() < self.natural_fg_rate)
        return SpinOutcome(multiplier=multiplier, triggered_fg=triggered_fg)

    def rescue_fg(self, tier: str) -> SpinOutcome:
        if tier not in TIER_RANGES:
            raise KeyError(f"未知 Tier：{tier}")
        low, high = TIER_RANGES[tier]
        return SpinOutcome(
            multiplier=float(self.rng.uniform(low, high)),
            triggered_fg=True,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "game": self.game_key,
            "natural_multiplier_model": "fixed-weight",
            "fixed_weight_total": self._curve_total_weight,
            "fixed_weight_expected_rtp_%": self._curve_expected_rtp * 100.0,
            "natural_fg_rate_%": self.natural_fg_rate * 100.0,
            "fg_and_multiplier_relation": "獨立抽樣",
            "rescue_result": "Tier 區間內均勻抽樣 FG",
        }

    def multiplier_curve_rows(self) -> list[dict[str, Any]]:
        total = float(self._curve_total_weight)
        rows: list[dict[str, Any]] = []
        for lower, upper, weight, multiplier in FIXED_WEIGHT_MULTIPLIER_CURVE:
            rows.append(
                {
                    "Lower": lower,
                    "Upper": upper,
                    "Fixed Weight": weight,
                    "Probability_%": weight / total * 100.0,
                    "Multi_X": multiplier,
                    "RTP_Contribution_%": multiplier * weight / total * 100.0,
                }
            )
        return rows


GameFactory = Callable[[argparse.Namespace], GameAdapter]


def _create_fixed_weight(args: argparse.Namespace) -> GameAdapter:
    return FixedWeightAdapter(
        seed=args.seed,
        natural_fg_rate=args.natural_fg_rate,
    )


GAME_ADAPTERS: dict[str, GameFactory] = {
    "FIXED_WEIGHT": _create_fixed_weight,
}


def get_stage(spin_no: int) -> str | None:
    if 201 <= spin_no <= 300:
        return "A"
    if 301 <= spin_no <= 400:
        return "B"
    if 401 <= spin_no <= 500:
        return "C"
    if spin_no >= 501:
        return "D"
    return None


def is_checkpoint(spin_no: int, check_interval: int) -> bool:
    return spin_no > NEWBIE_LAST_SPIN and (spin_no - NEWBIE_LAST_SPIN) % check_interval == 0


def _window_rtp(history: list[float], size: int) -> float | None:
    if len(history) < size:
        return None
    return float(np.mean(history[-size:]))


def decide_rescue(history: list[float], no_fg_spins: int, stage: str) -> RescueDecision:
    short_rtp = _window_rtp(history, WINDOW_SHORT)
    mid_rtp = _window_rtp(history, WINDOW_MID)
    long_rtp = _window_rtp(history, WINDOW_LONG)
    if short_rtp is None or mid_rtp is None:
        raise ValueError("救援判定前沒有足夠的短期／中期資料")

    no_fg_bad = no_fg_spins > NO_FG_LIMIT
    mid_bad = mid_rtp < STAGE_MID_RTP[stage]
    long_bad: bool | None = None if long_rtp is None else long_rtp < 1.0

    if stage in {"A", "B", "C"}:
        if mid_bad and no_fg_bad:
            return RescueDecision(stage, "AC_COMBINED", "中期 RTP 低於門檻且超過 100 轉未進 FG", "T2", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
        if no_fg_bad:
            return RescueDecision(stage, "AC_NO_FG", "超過 100 轉未進 FG", "T5", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
        if mid_bad:
            return RescueDecision(stage, "AC_MID_RTP", "中期 RTP 低於階段門檻", "T5", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
        return RescueDecision(stage, "NO_RESCUE", "未符合救援條件", None, short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)

    if long_rtp is None:
        return RescueDecision(stage, "D_NO_LONG_WINDOW", "長期資料尚未滿 500 轉", None, short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    if mid_bad and no_fg_bad and bool(long_bad):
        return RescueDecision(stage, "D_COMBINED", "中期 RTP、未進 FG 與長期 RTP 三項皆符合", "T1", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    if mid_bad and bool(long_bad):
        return RescueDecision(stage, "D_MID_LONG", "中期 RTP 與長期 RTP 符合", "T3", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    if no_fg_bad and bool(long_bad):
        return RescueDecision(stage, "D_NO_FG_LONG", "未進 FG 與長期 RTP 符合", "T6", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    return RescueDecision(stage, "NO_RESCUE", "未符合救援條件", None, short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)


def _pct(value: float | None) -> float | None:
    return None if value is None else value * 100.0


def run_simulation(args: argparse.Namespace, adapter: GameAdapter) -> dict[str, Any]:
    started = time.perf_counter()
    checkpoints: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    players: list[dict[str, Any]] = []

    stage_check_counts: Counter[str] = Counter()
    stage_trigger_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()

    natural_win_total = 0.0
    actual_win_total = 0.0
    natural_fg_total = 0
    actual_fg_total = 0

    for player_id in range(1, args.players + 1):
        history: list[float] = []
        no_fg_spins = 0
        player_natural_total = 0.0
        player_actual_total = 0.0
        player_trigger_counts: Counter[str] = Counter()

        for spin_no in range(1, args.spins + 1):
            natural = adapter.natural_spin(is_newbie=spin_no <= NEWBIE_LAST_SPIN)
            player_natural_total += natural.multiplier
            natural_win_total += natural.multiplier
            natural_fg_total += int(natural.triggered_fg)

            stage = get_stage(spin_no)
            decision: RescueDecision | None = None
            if stage is not None and is_checkpoint(spin_no, args.check_interval):
                decision = decide_rescue(history, no_fg_spins, stage)
                stage_check_counts[stage] += 1
                rule_counts[decision.rule_id] += 1

            actual = natural
            if decision is not None and decision.triggered:
                actual = adapter.rescue_fg(decision.tier or "")
                stage_trigger_counts[stage or ""] += 1
                tier_counts[decision.tier or ""] += 1
                player_trigger_counts[decision.tier or ""] += 1
                trigger_row = {
                    "Player": player_id,
                    "Spin": spin_no,
                    "Stage": stage,
                    "Rule_ID": decision.rule_id,
                    "Rule": decision.rule_description,
                    "Tier": decision.tier,
                    "Short_RTP_%": _pct(decision.short_rtp),
                    "Mid_RTP_%": _pct(decision.mid_rtp),
                    "Long_RTP_%": _pct(decision.long_rtp),
                    "No_FG_Spins": decision.no_fg_spins,
                    "Natural_X": natural.multiplier,
                    "Rescue_FG_X": actual.multiplier,
                    "Delta_X": actual.multiplier - natural.multiplier,
                }
                triggers.append(trigger_row)

            if decision is not None:
                checkpoints.append(
                    {
                        "Player": player_id,
                        "Spin": spin_no,
                        "Stage": stage,
                        "Mid_Threshold_%": STAGE_MID_RTP[stage or ""] * 100.0,
                        "Short_RTP_%": _pct(decision.short_rtp),
                        "Mid_RTP_%": _pct(decision.mid_rtp),
                        "Long_RTP_%": _pct(decision.long_rtp),
                        "No_FG_Spins": decision.no_fg_spins,
                        "Mid_Bad": decision.mid_bad,
                        "Long_Bad": decision.long_bad,
                        "Rule_ID": decision.rule_id,
                        "Tier": decision.tier or "",
                        "Triggered": decision.triggered,
                    }
                )

            history.append(actual.multiplier)
            player_actual_total += actual.multiplier
            actual_win_total += actual.multiplier
            actual_fg_total += int(actual.triggered_fg)
            no_fg_spins = 0 if actual.triggered_fg else no_fg_spins + 1

        player_row: dict[str, Any] = {
            "Player": player_id,
            "Spins": args.spins,
            "Natural_RTP_%": player_natural_total / args.spins * 100.0,
            "Rescue_RTP_%": player_actual_total / args.spins * 100.0,
            "RTP_Delta_pp": (player_actual_total - player_natural_total) / args.spins * 100.0,
            "Trigger_Count": sum(player_trigger_counts.values()),
        }
        for tier in TIER_RANGES:
            player_row[tier] = player_trigger_counts[tier]
        players.append(player_row)

        if args.progress_every > 0 and (player_id % args.progress_every == 0 or player_id == args.players):
            print(f"進度：{player_id:,}/{args.players:,} 位玩家", flush=True)

    total_paid_spins = args.players * args.spins
    total_checks = sum(stage_check_counts.values())
    total_triggers = sum(tier_counts.values())
    duration = time.perf_counter() - started

    stage_rows = []
    for stage in ("A", "B", "C", "D"):
        checks = stage_check_counts[stage]
        trigger_count = stage_trigger_counts[stage]
        row: dict[str, Any] = {
            "Stage": stage,
            "Spin_Range": {"A": "201～300", "B": "301～400", "C": "401～500", "D": "501+"}[stage],
            "Mid_RTP_Threshold_%": STAGE_MID_RTP[stage] * 100.0,
            "Checkpoint_Count": checks,
            "Trigger_Count": trigger_count,
            "Trigger_Rate_%": (trigger_count / checks * 100.0) if checks else 0.0,
        }
        for tier in TIER_RANGES:
            row[tier] = sum(1 for item in triggers if item["Stage"] == stage and item["Tier"] == tier)
        stage_rows.append(row)

    tier_rows = []
    for tier, (low, high) in TIER_RANGES.items():
        tier_rows.append(
            {
                "Tier": tier,
                "Low_X": low,
                "High_X": high,
                "Trigger_Count": tier_counts[tier],
                "Share_of_Triggers_%": (tier_counts[tier] / total_triggers * 100.0) if total_triggers else 0.0,
            }
        )

    rule_descriptions = {
        "AC_COMBINED": "A～C：中期 RTP 低於門檻且超過 100 轉未進 FG",
        "AC_NO_FG": "A～C：超過 100 轉未進 FG",
        "AC_MID_RTP": "A～C：中期 RTP 低於階段門檻",
        "D_COMBINED": "D：中期 RTP、未進 FG、長期 RTP 皆符合",
        "D_MID_LONG": "D：中期 RTP 與長期 RTP 符合",
        "D_NO_FG_LONG": "D：未進 FG 與長期 RTP 符合",
        "D_NO_LONG_WINDOW": "D：長期資料未滿 500 轉",
        "NO_RESCUE": "未符合救援條件",
    }
    rule_rows = [{"Rule_ID": rule_id, "Description": rule_descriptions.get(rule_id, rule_id), "Count": count} for rule_id, count in sorted(rule_counts.items())]

    summary = {
        **adapter.metadata(),
        "players": args.players,
        "spins_per_player": args.spins,
        "total_paid_spins": total_paid_spins,
        "check_interval": args.check_interval,
        "checkpoint_count": total_checks,
        "rescue_trigger_count": total_triggers,
        "rescue_trigger_rate_per_checkpoint_%": (total_triggers / total_checks * 100.0) if total_checks else 0.0,
        "players_with_rescue": sum(1 for row in players if row["Trigger_Count"] > 0),
        "natural_rtp_%": natural_win_total / total_paid_spins * 100.0,
        "rescue_rtp_%": actual_win_total / total_paid_spins * 100.0,
        "rtp_delta_pp": (actual_win_total - natural_win_total) / total_paid_spins * 100.0,
        "natural_fg_count": natural_fg_total,
        "actual_fg_count": actual_fg_total,
        "duration_sec": duration,
        "seed": args.seed,
    }

    return {
        "summary": summary,
        "stage_rows": stage_rows,
        "tier_rows": tier_rows,
        "rule_rows": rule_rows,
        "checkpoint_rows": checkpoints,
        "trigger_rows": triggers,
        "player_rows": players,
        "multiplier_curve_rows": adapter.multiplier_curve_rows(),
    }


def _summary_frame(summary: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame([{"Metric": key, "Value": value} for key, value in summary.items()])


def _safe_frame(rows: list[dict[str, Any]], columns: list[str] | None = None) -> pd.DataFrame:
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=columns or [])


def _format_excel(writer: pd.ExcelWriter) -> None:
    for worksheet in writer.book.worksheets:
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for column_cells in worksheet.columns:
            values = [str(cell.value) if cell.value is not None else "" for cell in column_cells]
            width = min(60, max(10, max((len(value) for value in values), default=0) + 2))
            worksheet.column_dimensions[column_cells[0].column_letter].width = width


def write_report(result: dict[str, Any], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        _summary_frame(result["summary"]).to_excel(writer, sheet_name="總覽", index=False)
        _safe_frame(result["stage_rows"]).to_excel(writer, sheet_name="階段統計", index=False)
        _safe_frame(result["tier_rows"]).to_excel(writer, sheet_name="Tier統計", index=False)
        _safe_frame(result["rule_rows"]).to_excel(writer, sheet_name="規則統計", index=False)
        _safe_frame(result["checkpoint_rows"]).to_excel(writer, sheet_name="判定明細", index=False)
        _safe_frame(result["trigger_rows"]).to_excel(writer, sheet_name="觸發明細", index=False)
        _safe_frame(result["player_rows"]).to_excel(writer, sheet_name="玩家統計", index=False)
        _safe_frame(result["multiplier_curve_rows"]).to_excel(writer, sheet_name="倍率線型", index=False)
        _format_excel(writer)
    return report_path


def _default_report_path(args: argparse.Namespace) -> Path:
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    filename = f"老手救援C_{args.players}p_{args.spins}s_{timestamp}.xlsx"
    return Path(args.report_dir) / filename


def print_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("\n=== 老手救援 C 模擬結果 ===")
    print(f"遊戲模型：{summary['game']}")
    print(f"玩家／每人轉數：{summary['players']:,} / {summary['spins_per_player']:,}")
    print(f"判定次數：{summary['checkpoint_count']:,}")
    print(f"救援觸發次數：{summary['rescue_trigger_count']:,}")
    print(f"有觸發玩家：{summary['players_with_rescue']:,}")
    print(f"自然 RTP：{summary['natural_rtp_%']:.4f}%")
    print(f"救援後 RTP：{summary['rescue_rtp_%']:.4f}%")
    print(f"RTP 增量：{summary['rtp_delta_pp']:.4f} 個百分點")
    print("Tier 觸發：" + ", ".join(f"{row['Tier']}={row['Trigger_Count']:,}" for row in result["tier_rows"]))
    print(f"耗時：{summary['duration_sec']:.2f} 秒")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="老手救援 C Fixed Weight 模擬器")
    parser.add_argument("--game", default="FIXED_WEIGHT", choices=sorted(GAME_ADAPTERS), help="遊戲模型")
    parser.add_argument("--players", type=int, default=10000, help="模擬玩家數")
    parser.add_argument("--spins", type=int, default=1000, help="每位玩家付費 Spin 數")
    parser.add_argument(
        "--natural-fg-rate",
        type=float,
        default=0.01,
        help="自然 Spin 進入 FG 的獨立機率，預設 0.01（1%）",
    )
    parser.add_argument("--check-interval", type=int, default=50, help="老手期判定間隔，預設每 50 轉")
    parser.add_argument("--seed", type=int, default=20260721, help="亂數種子")
    parser.add_argument("--progress-every", type=int, default=100, help="每幾位玩家顯示進度；0 表示關閉")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR), help="Excel 報表資料夾")
    parser.add_argument("--report", help="指定 Excel 報表完整路徑")
    parser.add_argument("--no-report", action="store_true", help="只輸出主控台，不建立 Excel")
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.players <= 0:
        raise ValueError("--players 必須大於 0")
    if args.spins <= 0:
        raise ValueError("--spins 必須大於 0")
    if args.check_interval <= 0:
        raise ValueError("--check-interval 必須大於 0")
    if not 0.0 <= args.natural_fg_rate <= 1.0:
        raise ValueError("--natural-fg-rate 必須介於 0 與 1")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None and Path(sys.argv[0]).stem == "ipykernel_launcher":
        # 直接在 Jupyter / VS Code Interactive Window 執行整份程式時，
        # 不解析 kernel 自動加入的 -f/--f=... 連線參數。
        argv = []
    args = parser.parse_args(argv)
    try:
        validate_args(args)
        adapter = GAME_ADAPTERS[args.game](args)
        result = run_simulation(args, adapter)
        print_summary(result)
        if not args.no_report:
            report_path = Path(args.report) if args.report else _default_report_path(args)
            output = write_report(result, report_path.resolve())
            print(f"報表：{output}")
        return 0
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
