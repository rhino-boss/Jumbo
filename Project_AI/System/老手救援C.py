"""老手救援 C 模擬器。

目前提供 H026 遊戲 Adapter：

* 每個自然 Spin 直接使用 H026 Simulator，且卡片系統保持開啟。
* 前 200 轉使用 H026 newbie Profile，201 轉後使用 oldhand Profile。
* 救援結果固定為 FG，使用 H026 BG／FG 盤面邏輯重骰至指定 Tier。
* 遊戲層透過 GameAdapter 隔離；新增遊戲時只需實作 Adapter 並加入
  GAME_ADAPTERS，不需修改老手救援規則。

預設每 50 轉檢查一次。這是尚未定案的模擬參數，可由
``--check-interval`` 修改。

範例：

    python 老手救援C.py --game H026 --players 1000 --spins 1000
    python 老手救援C.py --game H026 --config config_94A.js --players 100
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from abc import ABC, abstractmethod
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from numba import njit


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_AI_DIR = SCRIPT_DIR.parent
DEFAULT_REPORT_DIR = SCRIPT_DIR / "Record"
H026_DIR = PROJECT_AI_DIR / "Slots" / "H026_彩罐熱舞 1000"
H026_SIMULATOR = H026_DIR / "Simulator.py"

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


@njit
def _seed_numba(seed: int) -> None:
    np.random.seed(seed)


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


@dataclass(frozen=True)
class ForcedFGSample:
    multiplier: float
    target_attempts: int
    bg_attempts: int


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

    def rescue_pool_rows(self) -> list[dict[str, Any]]:
        return []


@contextmanager
def _temporary_environment(values: dict[str, str]):
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _load_h026_module(config_file: str, is_newbie: bool) -> Any:
    if not H026_SIMULATOR.exists():
        raise FileNotFoundError(f"找不到 H026 Simulator：{H026_SIMULATOR}")
    config_path = H026_DIR / config_file
    if not config_path.exists():
        raise FileNotFoundError(f"找不到 H026 config：{config_path}")

    profile_name = "newbie" if is_newbie else "oldhand"
    module_name = f"_oldhand_c_h026_{profile_name}_{config_path.stem}_{time.time_ns()}"
    env = {
        "H026_CONFIG_FILE": config_file,
        "H026_CARD_SYSTEM_ENABLED": "true",
        "H026_CARD_SYSTEM_IS_NEWBIE": "true" if is_newbie else "false",
        "H026_RUN_ALL_COMBINATIONS": "false",
        "H026_BET_MODE": "0",
        "H026_TOTAL_ROUNDS": "1",
    }
    with _temporary_environment(env):
        spec = importlib.util.spec_from_file_location(module_name, H026_SIMULATOR)
        if spec is None or spec.loader is None:
            raise ImportError(f"無法載入 H026 Simulator：{H026_SIMULATOR}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return module


class _H026Runtime:
    def __init__(self, module: Any, bet_mode: int, bet_multi: int):
        self.module = module
        self.bet_mode = int(bet_mode)
        self.bet_multi = int(bet_multi)
        self.coin_in = int(module.calc_coin_in(self.bet_mode, self.bet_multi))
        self.card_system_coin_in = int(module.calc_card_system_coin_in(self.bet_mode, self.bet_multi))
        self.record_buffer = np.zeros(module.RECORD_SIZE, dtype=np.int64)
        self._scratch = self._create_scratch()

    def _create_scratch(self) -> dict[str, np.ndarray]:
        m = self.module
        return {
            "board": np.zeros(m.LAYOUT_SHAPE, np.int64),
            "board_initial": np.zeros(m.LAYOUT_SHAPE, np.int64),
            "gold_mask": np.zeros(m.LAYOUT_SHAPE, np.int64),
            "multi_mask": np.zeros(m.LAYOUT_SHAPE, np.int64),
            "hit_mask": np.zeros(m.LAYOUT_SHAPE, np.int64),
            "spin_hits": np.zeros((3, m.SYMBOLS_COUNT), np.int64),
            "spin_pay": np.zeros((3, m.SYMBOLS_COUNT), np.int64),
            "spin_eliminate": np.zeros((3, m.SYMBOLS_COUNT), np.int64),
            "gold_pos": np.zeros((m.DISPLAY_WINDOW_SIZE * m.REEL_NUM, 2), np.int64),
            "keep_symbol": np.zeros(m.DISPLAY_WINDOW_SIZE, np.int64),
            "keep_gold": np.zeros(m.DISPLAY_WINDOW_SIZE, np.int64),
            "keep_multi": np.zeros(m.DISPLAY_WINDOW_SIZE, np.int64),
            "next_above_idx": np.zeros(m.REEL_NUM, np.int64),
            "spin_multiplier_seen": np.zeros(m.VALUE_MULTIPLIER_COUNT, np.int64),
            "reel_stop_idx": np.zeros(m.REEL_NUM, np.int64),
            "fg_record": np.zeros(m.RECORD_SIZE, np.int64),
        }

    def natural_spin(self) -> SpinOutcome:
        m = self.module
        self.record_buffer.fill(0)
        result = m.simulator_chunk(
            self.record_buffer,
            1,
            self.bet_mode,
            self.bet_multi,
            self.coin_in,
            self.card_system_coin_in,
        )
        multiplier = float(result[m.R_ALL, m.RA_X_SUM]) / 1_000_000.0
        triggered_fg = bool(result[m.R_ALL, m.RA_TRIGGER_FREEGAME] > 0)
        return SpinOutcome(multiplier=multiplier, triggered_fg=triggered_fg)

    def forced_fg(self, low: float, high: float, retry_limit: int) -> ForcedFGSample:
        """用 H026 盤面與 FG 邏輯重骰到目標總倍數。"""

        m = self.module
        s = self._scratch
        total_bg_attempts = 0
        bg_retry_limit = max(1, int(getattr(m, "CARD_RETRY_LIMIT", retry_limit) or retry_limit))

        for target_attempt in range(1, retry_limit + 1):
            bg_result = None
            for _ in range(bg_retry_limit):
                total_bg_attempts += 1
                candidate = m.run_spin(
                    m.SCENE_BG,
                    0,
                    self.bet_multi,
                    s["board"],
                    s["board_initial"],
                    s["gold_mask"],
                    s["multi_mask"],
                    s["hit_mask"],
                    s["spin_hits"],
                    s["spin_pay"],
                    s["spin_eliminate"],
                    s["gold_pos"],
                    s["keep_symbol"],
                    s["keep_gold"],
                    s["keep_multi"],
                    s["next_above_idx"],
                    s["spin_multiplier_seen"],
                    s["reel_stop_idx"],
                )
                if candidate[1] >= 3:
                    bg_result = candidate
                    break
            if bg_result is None:
                raise RuntimeError(f"H026 在 {bg_retry_limit} 次內無法產生 FG 觸發盤面")

            s["fg_record"].fill(0)
            free_spins = int(m.calc_free_spins(bg_result[1], 0))
            pay_fg = int(
                m.run_free_game_session(
                    s["fg_record"],
                    free_spins,
                    self.bet_multi,
                    self.coin_in,
                    s["board"],
                    s["board_initial"],
                    s["gold_mask"],
                    s["multi_mask"],
                    s["hit_mask"],
                    s["spin_hits"],
                    s["spin_pay"],
                    s["spin_eliminate"],
                    s["gold_pos"],
                    s["keep_symbol"],
                    s["keep_gold"],
                    s["keep_multi"],
                    s["next_above_idx"],
                    s["spin_multiplier_seen"],
                )
            )
            multiplier = (float(bg_result[0]) + pay_fg) / self.coin_in
            if low <= multiplier <= high:
                return ForcedFGSample(
                    multiplier=multiplier,
                    target_attempts=target_attempt,
                    bg_attempts=total_bg_attempts,
                )

        raise RuntimeError(
            f"H026 無法在 {retry_limit} 次 FG 重骰內產生 {low:g}～{high:g}× 結果"
        )


class H026Adapter(GameAdapter):
    game_key = "H026"

    def __init__(
        self,
        config_file: str,
        bet_mode: int,
        bet_multi: int,
        seed: int,
        rescue_pool_size: int,
        rescue_retry_limit: int,
    ):
        if bet_mode not in (0, 1):
            raise ValueError("老手救援 C 目前只支援 H026 bet mode 0（Normal）或 1（Extra）")
        self.config_file = config_file
        self.bet_mode = int(bet_mode)
        self.bet_multi = int(bet_multi)
        self.seed = int(seed)
        self.rescue_pool_size = max(1, int(rescue_pool_size))
        self.rescue_retry_limit = max(1, int(rescue_retry_limit))
        self.rng = np.random.default_rng(self.seed)
        self._rescue_pools: dict[str, list[ForcedFGSample]] = {}

        print("載入 H026 newbie 卡片 Profile…", flush=True)
        newbie_module = _load_h026_module(config_file, is_newbie=True)
        print("載入 H026 oldhand 卡片 Profile…", flush=True)
        oldhand_module = _load_h026_module(config_file, is_newbie=False)
        if not bool(newbie_module.CARD_SYSTEM_ENABLED) or not bool(oldhand_module.CARD_SYSTEM_ENABLED):
            raise RuntimeError("H026 config 的 card_system 未啟用")

        self.newbie = _H026Runtime(newbie_module, self.bet_mode, self.bet_multi)
        self.oldhand = _H026Runtime(oldhand_module, self.bet_mode, self.bet_multi)
        _seed_numba(self.seed)

    def natural_spin(self, is_newbie: bool) -> SpinOutcome:
        runtime = self.newbie if is_newbie else self.oldhand
        return runtime.natural_spin()

    def _ensure_rescue_pool(self, tier: str) -> None:
        if tier in self._rescue_pools:
            return
        low, high = TIER_RANGES[tier]
        print(f"建立 {tier} H026 FG 樣本池（{low:g}～{high:g}×）…", flush=True)
        samples = [
            self.oldhand.forced_fg(low, high, self.rescue_retry_limit)
            for _ in range(self.rescue_pool_size)
        ]
        self._rescue_pools[tier] = samples

    def rescue_fg(self, tier: str) -> SpinOutcome:
        if tier not in TIER_RANGES:
            raise KeyError(f"未知 Tier：{tier}")
        self._ensure_rescue_pool(tier)
        samples = self._rescue_pools[tier]
        sample = samples[int(self.rng.integers(0, len(samples)))]
        return SpinOutcome(multiplier=sample.multiplier, triggered_fg=True)

    def metadata(self) -> dict[str, Any]:
        module = self.oldhand.module
        return {
            "game": self.game_key,
            "game_id": str(getattr(module, "GAME_ID", "H026")),
            "config": self.config_file,
            "version": str(getattr(module, "CONFIG_VERSION", "")),
            "bet_mode": self.bet_mode,
            "bet_multi": self.bet_multi,
            "coin_in": self.oldhand.coin_in,
            "card_system": "on",
            "newbie_profile_spins": f"1～{NEWBIE_LAST_SPIN}",
            "oldhand_profile_spins": f"{NEWBIE_LAST_SPIN + 1}+",
            "rescue_pool_size_per_tier": self.rescue_pool_size,
            "rescue_retry_limit": self.rescue_retry_limit,
        }

    def rescue_pool_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for tier, samples in sorted(self._rescue_pools.items()):
            low, high = TIER_RANGES[tier]
            for index, sample in enumerate(samples, start=1):
                rows.append(
                    {
                        "Tier": tier,
                        "Sample": index,
                        "Low_X": low,
                        "High_X": high,
                        "Result_X": sample.multiplier,
                        "FG_Target_Attempts": sample.target_attempts,
                        "BG_Attempts": sample.bg_attempts,
                    }
                )
        return rows


GameFactory = Callable[[argparse.Namespace], GameAdapter]


def _create_h026(args: argparse.Namespace) -> GameAdapter:
    return H026Adapter(
        config_file=args.config,
        bet_mode=args.bet_mode,
        bet_multi=args.bet_multi,
        seed=args.seed,
        rescue_pool_size=args.rescue_pool_size,
        rescue_retry_limit=args.rescue_retry_limit,
    )


GAME_ADAPTERS: dict[str, GameFactory] = {
    "H026": _create_h026,
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
    rule_rows = [
        {"Rule_ID": rule_id, "Description": rule_descriptions.get(rule_id, rule_id), "Count": count}
        for rule_id, count in sorted(rule_counts.items())
    ]

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
        "rescue_pool_rows": adapter.rescue_pool_rows(),
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
        _safe_frame(result["rescue_pool_rows"]).to_excel(writer, sheet_name="FG樣本池", index=False)
        _format_excel(writer)
    return report_path


def _default_report_path(args: argparse.Namespace) -> Path:
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    config_tag = Path(args.config).stem
    filename = f"老手救援C_{args.game}_{config_tag}_{args.players}p_{args.spins}s_{timestamp}.xlsx"
    return Path(args.report_dir) / filename


def print_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("\n=== 老手救援 C 模擬結果 ===")
    print(f"遊戲／設定：{summary['game']} / {summary['config']}")
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
    parser = argparse.ArgumentParser(description="老手救援 C 模擬器（可切換遊戲 Adapter）")
    parser.add_argument("--game", default="H026", choices=sorted(GAME_ADAPTERS), help="遊戲 Adapter")
    parser.add_argument("--config", default="config_92A.js", help="遊戲設定檔；H026 使用 config_*.js")
    parser.add_argument("--players", type=int, default=1000, help="模擬玩家數")
    parser.add_argument("--spins", type=int, default=1000, help="每位玩家付費 Spin 數")
    parser.add_argument("--bet-mode", type=int, default=0, choices=(0, 1), help="H026：0 Normal、1 Extra")
    parser.add_argument("--bet-multi", type=int, default=1, help="投注倍率")
    parser.add_argument("--check-interval", type=int, default=50, help="老手期判定間隔，預設每 50 轉")
    parser.add_argument("--rescue-pool-size", type=int, default=32, help="每個有使用 Tier 的 H026 FG 樣本數")
    parser.add_argument("--rescue-retry-limit", type=int, default=5000, help="單筆 FG 樣本的目標區間重骰上限")
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
    if args.bet_multi <= 0:
        raise ValueError("--bet-multi 必須大於 0")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
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
