"""H032 亡靈派對 (Calavera Party) simulator.

盤面 5x4、1024 Ways、Cascade（重力掉落）；黃底（金色符號，出現軸依 Config；v2 為 R2~R4，不帶倍數）中獎時變成 WW，
原格沒有框就留下 1X 框；框留在格子上，每一段連消全盤所有框 +1（本消新留的框從下一消起才 +1）；
每一消得分 ×（1 ＋ 消除前的框倍數總和），算完分才更新框（2026-11-11 規則改版）。
FG 開場沒有框、框整場保留到 FG 結束（BG 每轉清空）；每場 FG 依 FG 隱性控制（Good Spin Slots、Retrigger Boost、Dead Streak、
Frame Tier）決定抽表權重。玩法定義見 ``game_rule.md``；執行參數一律來自 Config，不在本程式內重複維護輪帶、權重、
Paytable 或 Feature 參數。

Runner、BATCH_RUNS、Console 欄位與 Excel 報表版面依 ``專案需知/開發規範/模擬程式規範.md``。
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# ===== User Settings =====

CONFIG_FILE = "config.js"
CONFIG_RTP_FILE = "AUTO"   # AUTO＝依押注檔位自動選（模擬程式規範 §1.2.3）；明寫檔名即 override
# 檔位對應表（2026-10-22）：老手 小 Bet < $2 → 94A、中 Bet $2～$100 → 92A、大 Bet > $100 → 92A_Bet100；
# 小 Bet：NB／EB 用實際押注判；大 Bet：一律用基礎押注判（對齊 SPS isHighBet()，2026-10-27）；BF 皆用基礎押注。Newbie 各版共用 → 固定 92A。最大押注 $5000。
RTP_SERIES = os.environ.get("H032_RTP_SERIES", "A")   # A／B 版（2026-10-27 加 B 版）；--series 可覆寫
TIER_CONFIG = {"small_bet": "config_94{s}.js", "medium_bet": "config_92{s}.js", "big_bet": "config_92{s}_Bet100.js"}
NEWBIE_CONFIG = "config_92{s}.js"
TOTAL_ROUNDS = 100_000
BASE_BET_SETTING = 1.0
BET_MODE = 0  # 0 = Normal Bet, 2 = Buy Feature
CARD_SYSTEM_ENABLED = False
CARD_SYSTEM_IS_NEWBIE = False

RUN_ALL_COMBINATIONS = True
BATCH_RUNS = [
    # --- 階段 7：小場次 Debug ---
    {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 0,
     "total_rounds": 10**5, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # --- 階段 8：自然機率正式報表（卡片權重校準用）---
    # 2026-10-06 使用者決議：純 Python 無 Numba（1e6≈76 秒），本機改跑 NB 1e8／BF 1e7（規範預設 1e9／1e8）
    # {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 0,
    #  "total_rounds": 10**8, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
    # {"config_file": "config.js", "config_rtp_file": "AUTO", "bet_mode": 2,
    #  "total_rounds": 10**7, "card_system_enabled": False, "card_system_is_newbie": False, "base_bet": 1.0},
]
THREADS = max(1, min(12, os.cpu_count() or 1))   # 多程序；本機 i7-12700H 20 執行緒
OUTPUT_REPORT = True
SHOW_CONSOLE_SUMMARY = True
RUN_SINGLE_SPIN_DEBUG = False
DEBUG_ROUNDS = 1
CARD_RETRY_LIMIT = 10_000
RNG_SEED = 45_045

COIN_BASE = 100.0                      # Credit 基準，與 Overview!A7 一致
MODE_NORMALBET = 0
MODE_EXTRABET = 1                      # 本作目前無 Extra Bet（保留常數供共用欄位判斷）
MODE_FEATUREBUY = 2
SUPPORTED_BET_MODES = (MODE_NORMALBET, MODE_FEATUREBUY)

WW = 0
C1 = 2
SCORE_SYMBOLS = tuple(range(3, 11))
EMPTY = -1

YELLOW_RATE_SCALE = 100_000            # Yellow_Rate／Yellow_Drop_Rate 單位：/100,000
BIG_FRAME_TOTAL = 10                   # 觀察指標：開局框總和 ≥ 10 視為「大框」
RETRIGGER_WATCH_SPINS = 2              # 觀察指標：retrigger 後幾局的得分

MULTIPLIER_THRESHOLDS = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50,
    60, 70, 80, 90, 100, 120, 140, 160, 180, 200, 250, 300, 350, 400, 450,
    500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
    2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
    20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 9999999,
)

CFG: dict[str, Any] = {}
CFG_RTP: dict[str, Any] = {}


# ===== Config =====

def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_base_dir() -> Path:
    base = Path(__file__).resolve().parent
    if not (base / CONFIG_FILE).exists():
        raise FileNotFoundError(f"找不到 {CONFIG_FILE}，請在 H032 專案資料夾執行。")
    return base


BASE_DIR = resolve_base_dir()


def load_js_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])


def _version_major(value: Any) -> str:
    return str(value).split(".")[0]


def validate_config_pair(natural: dict[str, Any], rtp: dict[str, Any] | None,
                         natural_name: str, rtp_name: str) -> None:
    if natural.get("game_id") != "H032":
        raise ValueError(f"{natural_name} 的 game_id 必須為 H032")
    version = str(natural.get("excel_version", ""))
    if not version.isdigit() or len(version) != 1:
        raise ValueError(f"{natural_name} 的 excel_version 必須為 1 碼，目前為 {version!r}")
    if rtp is None:
        return
    if rtp.get("game_id") != natural.get("game_id"):
        raise ValueError(f"{rtp_name} 與 {natural_name} 的 game_id 不一致")
    rtp_version = str(rtp.get("excel_version", ""))
    parts = rtp_version.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        raise ValueError(f"{rtp_name} 的 excel_version 必須為 4 碼，目前為 {rtp_version!r}")
    if parts[0] != version:
        raise ValueError(
            f"{rtp_name} 的版本第 1 碼 {parts[0]} 必須等於基礎模型版本 {version}")


# ===== 遊戲核心 =====

@dataclass
class Reel:
    symbols: list[int]
    cumulative: list[float]
    total: float

    def stop(self, rng: random.Random) -> int:
        position = rng.random() * self.total
        return min(bisect.bisect_right(self.cumulative, position), len(self.cumulative) - 1)

    def window(self, rng: random.Random, size: int) -> list[int]:
        start = self.stop(rng)
        length = len(self.symbols)
        return [self.symbols[(start + offset) % length] for offset in range(size)]


@dataclass
class Table:
    reels: list[Reel]
    drop_values: list[list[int]]
    drop_cumulative: list[list[float]]
    drop_total: list[float]
    yellow_rate: list[float]                 # 初始盤面每格成為黃底的機率（各軸）
    yellow_drop_rate: list[float]            # 補牌符號成為黃底的機率（各軸）
    yellow_values: list[int]
    yellow_cumulative: list[float]
    yellow_total: float
    yellow_symbol_factor: dict[int, float]   # 各符號係數（1.0＝軸機率）


def _cumulative(weights: list[float]) -> tuple[list[float], float]:
    out, running = [], 0.0
    for weight in weights:
        running += max(0.0, float(weight))
        out.append(running)
    return out, running


def _pick(rng: random.Random, values: list[Any], cumulative: list[float], total: float) -> Any:
    if total <= 0:
        raise ValueError("權重總和必須大於 0")
    position = rng.random() * total
    return values[min(bisect.bisect_right(cumulative, position), len(values) - 1)]


def prepare_table(raw: dict[str, Any]) -> Table:
    reels = []
    for symbols, weights in zip(raw["reels"], raw["symbol_weight"]):
        cumulative, total = _cumulative(weights)
        reels.append(Reel(list(map(int, symbols)), cumulative, total))

    drop_values, drop_cumulative, drop_total = [], [], []
    drop = {int(k): v for k, v in raw["drop_weight"].items()}
    for reel in range(5):
        values = [sid for sid in sorted(drop) if float(drop[sid][reel]) > 0]
        cumulative, total = _cumulative([float(drop[sid][reel]) for sid in values])
        drop_values.append(values)
        drop_cumulative.append(cumulative)
        drop_total.append(total)

    y_values = sorted(int(k) for k in raw["yellow_value_weight"])
    y_cumulative, y_total = _cumulative([float(raw["yellow_value_weight"][str(v)]) for v in y_values])
    return Table(reels, drop_values, drop_cumulative, drop_total,
                 [float(v) / YELLOW_RATE_SCALE for v in raw["yellow_rate"]],
                 [float(v) / YELLOW_RATE_SCALE for v in raw["yellow_drop_rate"]],
                 y_values, y_cumulative, y_total,
                 {int(k): float(v) / 100.0 for k, v in raw["yellow_symbol_weight"].items()})


@dataclass
class SpinResult:
    pay: float = 0.0
    scatter_count: int = 0
    cascades: int = 0
    yellow_seen: bool = False                    # 初始或補牌出現過黃底
    yellow_used: int = 0                         # 中獎留框、變 WILD 的黃底顆數
    yellow_values: Counter = field(default_factory=Counter)   # 被使用黃底的倍數分布
    peak_frame: int = 0                          # 本轉框倍數總和的最大值
    end_frame: int = 0
    max_mult: int = 1                            # 本轉計分用過的最大框總和
    symbol_hits: Counter = field(default_factory=Counter)
    symbol_pay: Counter = field(default_factory=Counter)
    symbol_length_hits: Counter = field(default_factory=Counter)
    symbol_length_pay: Counter = field(default_factory=Counter)
    initial_symbols: Counter = field(default_factory=Counter)
    drop_symbols: Counter = field(default_factory=Counter)
    initial_board: list[list[int]] = field(default_factory=list)
    final_board: list[list[int]] = field(default_factory=list)


@dataclass
class RoundResult:
    pay_bg: float = 0.0
    pay_fg: float = 0.0
    fg_triggered: bool = False
    fg_spins: int = 0
    retriggers: int = 0
    cascades_bg: int = 0
    cascades_fg: int = 0
    capped: bool = False
    bg_hit_spins: int = 0
    fg_hit_spins: int = 0
    bg_yellow_seen: int = 0
    fg_yellow_seen: int = 0
    bg_yellow_used: int = 0
    fg_yellow_used: int = 0
    yellow_values: Counter = field(default_factory=Counter)
    bg_peak_frame: int = 0
    fg_end_frame: int = 0                         # FG 結束時框總和
    max_mult: int = 1
    special_symbol_cnt: int = 0
    bg_trigger_fg_cnt: int = 0
    bg_trigger_fg_pay: float = 0.0
    bg_cascade_count: int = 0
    combo_fg: Counter = field(default_factory=Counter)
    # FG 隱性控制觀察（同一份統計輸出到 Console 與報表）
    fg_index_spins: Counter = field(default_factory=Counter)   # 第 i 局（1 起算）
    fg_index_hits: Counter = field(default_factory=Counter)
    fg_index_pay: Counter = field(default_factory=Counter)
    fg_rule_spins: Counter = field(default_factory=Counter)    # 本局採用的規則
    fg_rule_hits: Counter = field(default_factory=Counter)
    fg_rule_pay: Counter = field(default_factory=Counter)
    fg_table_spins: Counter = field(default_factory=Counter)
    fg_bigframe_spins: int = 0                    # 開局框總和 ≥ BIG_FRAME_TOTAL 的局
    fg_bigframe_dead: int = 0
    fg_dead_runs: Counter = field(default_factory=Counter)     # 連續未中的長度分布
    fg_post_retrigger_spins: int = 0              # retrigger 後 RETRIGGER_WATCH_SPINS 局內
    fg_post_retrigger_hits: int = 0
    fg_post_retrigger_pay: float = 0.0
    symbol_hits: Counter = field(default_factory=Counter)
    symbol_pay: Counter = field(default_factory=Counter)
    bg_symbol_length_hits: Counter = field(default_factory=Counter)
    fg_symbol_length_hits: Counter = field(default_factory=Counter)
    bg_symbol_length_pay: Counter = field(default_factory=Counter)
    fg_symbol_length_pay: Counter = field(default_factory=Counter)
    bg_initial_symbols: Counter = field(default_factory=Counter)
    bg_drop_symbols: Counter = field(default_factory=Counter)
    fg_initial_symbols: Counter = field(default_factory=Counter)
    fg_drop_symbols: Counter = field(default_factory=Counter)

    @property
    def pay(self) -> float:
        return self.pay_bg + self.pay_fg


def _grid(value: int = 0) -> list[list[int]]:
    return [[value] * 4 for _ in range(5)]


def _frame_sum(frames: list[list[int]]) -> int:
    return sum(sum(column) for column in frames)


class CalaveraParty:
    """H032 遊戲核心。單一實例持有自己的 RNG，供單一 Worker 使用。"""

    def __init__(self, config: dict[str, Any], rtp_config: dict[str, Any] | None,
                 seed: int, bet_amount: float, card_enabled: bool, newbie: bool):
        self.config = config
        self.rtp_config = rtp_config or {}
        self.rng = random.Random(seed)
        self.bet = bet_amount
        self.card_enabled = bool(card_enabled and (self.rtp_config.get("card_system") or {}).get("enabled"))
        self.profile = "newbie" if newbie else "oldhand"
        self.tables = {name: prepare_table(raw) for name, raw in config["tables"].items()}
        self.pays = {int(k): v for k, v in config["pays"].items()}
        self.max_fs = int(config["max_free_spins"])
        self.fs_retrigger = int(config["free_spins_retrigger"])
        self.min_scatter = int(config["min_scatter"])
        self.weights = {group: (list(w), *_cumulative([float(w[n]) for n in w]))
                        for group, w in config["table_weight"].items()}
        self.good_slots = config["fg_good_slots"]
        self.boost_spins = int(config["retrigger_boost"]["spins"])
        self.frame_tiers = config["fg_frame_tier_weight"]
        self.dead_tiers = config["fg_dead_streak_weight"]
        self.priority = list(config["fg_weight_priority"])
        # FG 後段黃底：依盤面有框的格數，黃底機率乘上係數、倍數改抽這一段的權重（隱性控制）
        self.late_yellow = []
        for row in config.get("fg_late_yellow", []):
            values = sorted(int(k) for k in row["value_weight"])
            self.late_yellow.append((int(row["min"]), int(row["max"]), float(row["rate_scale"]) / 100.0, values,
                                     *_cumulative([float(row["value_weight"][str(v)]) for v in values])))
        # Max Win 由卡片系統的倍率上限決定；Card System Off 時不套上限
        self.max_win = self._card_multiplier_cap()
        self.fs_table = {int(k): v for k, v in config["free_spins"].items()}
        self.retry_total = 0
        self.retry_limit_exceeded = 0
        self.retry_limit_bg_range = 0
        self.retry_limit_bg_freegame = 0
        self.retry_limit_fg = 0
        self.card_draws: Counter = Counter()

    def _card_section_cap(self, section: str) -> float:
        """該 Profile 某卡組「最高有權重 range 卡」的上限；Card System Off 回傳無限大。"""
        if not self.card_enabled:
            return math.inf
        cards = ((self.rtp_config.get("card_system") or {}).get("profiles") or {}) \
            .get(self.profile, {}).get(section) or []
        caps = [float(c["max"]) for c in cards
                if str(c.get("type")) == "range" and float(c.get("weight", 0)) > 0 and "max" in c]
        return max(caps) if caps else math.inf

    def _card_multiplier_cap(self) -> float:
        """Max Win（單局上限）取 base_game／free_game 卡組最高有權重區間上限的較大者；BG Trigger Cap 由 base_game 卡組決定。"""
        self.bg_trigger_cap = self._card_section_cap("base_game")
        self.fg_cap = self._card_section_cap("free_game")
        self.bf_cap = self._card_section_cap("buy_feature")
        self.trigger_cap = self.bg_trigger_cap
        return max(self.fg_cap, self.bg_trigger_cap)

    # --- 盤面 ---

    def _pick_table(self, group: str) -> str:
        names, cumulative, total = self.weights[group]
        return str(_pick(self.rng, names, cumulative, total))

    def _pick_from(self, weights: dict[str, Any]) -> str:
        names = list(weights)
        cumulative, total = _cumulative([float(weights[n]) for n in names])
        return str(_pick(self.rng, names, cumulative, total))

    def late_tier(self, frames: list[list[int]]):
        """FG 後段黃底：盤面有框的格數落在哪一段；沒有對應段回傳 None。"""
        cells = sum(value > 0 for column in frames for value in column)
        for tier in self.late_yellow:
            if tier[0] <= cells <= tier[1]:
                return tier
        return None

    def roll_yellow(self, table: Table, reel: int, symbol: int, refill: bool, late=None) -> int:
        """黃底只套在一般符號（不套 C1／WW）；機率＝該表該軸機率 × 符號係數，倍數依 Yellow_Value_Weight。
        late（FG 後段段位）：機率再乘 rate_scale，倍數改抽該段的權重。"""
        if symbol in (WW, C1):
            return 0
        rate = (table.yellow_drop_rate if refill else table.yellow_rate)[reel] * table.yellow_symbol_factor.get(symbol, 0.0)
        if late:
            rate *= late[2]
        if rate <= 0 or self.rng.random() >= rate:
            return 0
        if late:
            return int(_pick(self.rng, late[3], late[4], late[5]))
        return int(_pick(self.rng, table.yellow_values, table.yellow_cumulative, table.yellow_total))

    def evaluate(self, symbols: list[list[int]]):
        """1024 Ways：WW 替代除 C1 外所有符號。回傳 (raw_pay, hit_positions, details)。"""
        total = 0.0
        hits: set[tuple[int, int]] = set()
        details: list[tuple[int, int, int, float]] = []
        for target in SCORE_SYMBOLS:
            counts: list[int] = []
            positions: list[list[tuple[int, int]]] = []
            for reel in range(5):
                matched = [(reel, row) for row, symbol in enumerate(symbols[reel]) if symbol == WW or symbol == target]
                if not matched:
                    break
                counts.append(len(matched))
                positions.append(matched)
            length = len(counts)
            if length < 3:
                continue
            ways = 1
            for count in counts:
                ways *= count
            raw = float(self.pays[target][length - 3]) * ways
            if raw <= 0:
                continue
            for group in positions:
                hits.update(group)
            total += raw
            details.append((target, length, ways, raw))
        return total, hits, details

    def spin(self, table_name: str, frames: list[list[int]], free_game: bool = False) -> SpinResult:
        """一轉（BG 局或一場 FG）。frames 由呼叫端傳入並就地更新（FG 整場保留、BG 每轉新的空盤）。

        game_rule §5（2026-11-11 改版）：每一消依「消除 → 加倍數 → 算分」：先更新框
        （全盤所有框 +1；黃底在沒有框的格子消除時留下 1X 新框，新框本消不 +1），再以更新後的框總和計分（乘數＝1＋框總和）；黃底符號變 WW 不消除，其餘中獎符號消除後重力掉落、上方補牌。
        """
        table = self.tables[table_name]
        symbols = [table.reels[reel].window(self.rng, 4) for reel in range(5)]
        late = self.late_tier(frames) if free_game else None
        yellow = [[self.roll_yellow(table, reel, symbols[reel][row], False, late) for row in range(4)] for reel in range(5)]
        result = SpinResult(initial_board=[reel[:] for reel in symbols])
        result.initial_symbols.update((reel, symbol) for reel, column in enumerate(symbols) for symbol in column)
        result.yellow_seen = any(any(column) for column in yellow)
        result.peak_frame = _frame_sum(frames)
        cap = self.max_win * self.bet
        while True:
            raw_pay, hits, details = self.evaluate(symbols)
            if raw_pay <= 0:
                break
            # 2026-11-11 規則改版：每一段連消，全盤所有框 +1；
            # 黃底（不帶倍數）在沒有框的格子消除 → 留下 1X 新框（本消新留的框從下一消起才 +1）
            for reel in range(5):
                for row in range(4):
                    if frames[reel][row] > 0:
                        frames[reel][row] += 1
            for reel, row in hits:
                if yellow[reel][row] > 0 and frames[reel][row] == 0:
                    frames[reel][row] = 1
            total_frame = _frame_sum(frames)
            # 2026-11-11 使用者：流程「消除 → 加倍數 → 算分」——乘數＝1＋本消「更新後」的框總和
            mult = 1 + total_frame
            gained = raw_pay * mult * self.bet
            result.pay += gained
            result.max_mult = max(result.max_mult, mult)
            result.cascades += 1
            for symbol, length, ways, symbol_raw in details:
                result.symbol_hits[symbol] += ways
                result.symbol_pay[symbol] += symbol_raw * mult * self.bet
                result.symbol_length_hits[(symbol, length)] += 1
                result.symbol_length_pay[(symbol, length)] += symbol_raw * mult * self.bet
            for reel, row in hits:
                if yellow[reel][row] > 0:
                    result.yellow_used += 1
                    result.yellow_values[yellow[reel][row]] += 1
                    yellow[reel][row] = 0
                    symbols[reel][row] = WW
                else:
                    symbols[reel][row] = EMPTY
            result.peak_frame = max(result.peak_frame, total_frame)
            late = self.late_tier(frames) if free_game else None
            # 重力掉落：row 0 在最下面（同 Demogame），剩下的符號連同黃底往下掉，上方補新符號；框留在原格
            for reel in range(5):
                keep = [(symbols[reel][row], yellow[reel][row]) for row in range(4) if symbols[reel][row] != EMPTY]
                if len(keep) == 4:
                    continue
                for row in range(4):
                    if row < len(keep):
                        symbols[reel][row], yellow[reel][row] = keep[row]
                    else:
                        symbol = int(_pick(self.rng, table.drop_values[reel], table.drop_cumulative[reel], table.drop_total[reel]))
                        symbols[reel][row] = symbol
                        yellow[reel][row] = self.roll_yellow(table, reel, symbol, True, late)
                        result.yellow_seen |= yellow[reel][row] > 0
                        result.drop_symbols[(reel, symbol)] += 1
            if result.pay >= cap:
                break
        result.scatter_count = sum(symbol == C1 for column in symbols for symbol in column)
        result.end_frame = _frame_sum(frames)
        result.final_board = [reel[:] for reel in symbols]
        return result

    # --- Card System ---

    def pick_card(self, section: str) -> dict[str, Any]:
        cards = self.rtp_config["card_system"]["profiles"][self.profile][section]
        weights = [float(card["weight"]) for card in cards]
        cumulative, total = _cumulative(weights)
        index = min(bisect.bisect_right(cumulative, self.rng.random() * total), len(cards) - 1)
        self.card_draws[(self.profile, section, index)] += 1
        return dict(cards[index])

    def card_matches(self, card: dict[str, Any], pay: float) -> bool:
        ratio = pay / self.bet
        return float(card["min"]) < ratio <= float(card["max"])

    # --- Round ---

    def natural_base_spin(self) -> SpinResult:
        return self.spin(self._pick_table("bg"), _grid(0))

    def card_spin(self, card: dict[str, Any]) -> SpinResult:
        want_fg = card.get("type") == "free_game"
        spin = None
        for _ in range(CARD_RETRY_LIMIT):
            spin = self.natural_base_spin()
            if want_fg:
                # 數學模型規範 §2.3：free_game 卡須同時滿足「觸發 FG」且 BG 得分 ≤ BG Trigger Cap，否則整把重骰
                if spin.scatter_count >= self.min_scatter and spin.pay / self.bet <= self.trigger_cap:
                    return spin
            elif spin.scatter_count < self.min_scatter and self.card_matches(card, spin.pay):
                return spin
            self.retry_total += 1
        self.retry_limit_exceeded += 1
        if want_fg:
            self.retry_limit_bg_freegame += 1
        else:
            self.retry_limit_bg_range += 1
        return spin

    def _draw_slot(self, slot: dict[str, Any], total: int, after: int = 0) -> set[int]:
        """依 FG Good Spin Slots 抽好局位置（1 起算）；只抽 after 之後的局。"""
        lo, hi = int(slot["from"]), int(slot["to"])
        if slot["anchor"] == "end":
            lo, hi = total - hi + 1, total - lo + 1
        candidates = [i for i in range(max(1, lo, after + 1), min(total, hi) + 1)]
        self.rng.shuffle(candidates)
        return set(candidates[:int(slot["count"])])

    @staticmethod
    def _tier(rows: list[dict[str, Any]], value: int) -> dict[str, Any] | None:
        for row in rows:
            if int(row["min"]) <= value <= int(row["max"]):
                return row["weights"]
        return None

    def _fg_weights(self, index: int, good: set[int], boost_left: int, dead: int, frame_total: int,
                    buy: bool) -> tuple[str, dict[str, Any] | str]:
        """FG 隱性控制：依 fg_weight_priority 取第一個成立的規則；回傳 (規則, 權重群組名或權重表)。"""
        for rule in self.priority:
            if rule == "good_slot" and index in good:
                return rule, "bf_fg_good" if buy else "fg_good"
            if rule == "retrigger_boost" and boost_left > 0:
                return rule, "fg_retrigger_boost"
            if rule == "dead_streak":
                weights = self._tier(self.dead_tiers, dead)
                if weights:
                    return rule, weights
            if rule == "frame_tier":
                weights = self._tier(self.frame_tiers, frame_total)
                if weights:
                    return rule, weights
            if rule == "normal":
                return rule, "bf_fg_normal" if buy else "fg_normal"
        return "normal", "bf_fg_normal" if buy else "fg_normal"

    def free_session(self, initial_spins: int, budget: float, buy: bool = False) -> RoundResult:
        result = RoundResult(fg_triggered=True)
        frames = _grid(0)                         # game_rule §6：FG 開場沒有框（2026-11-11 起），框整場保留到結束
        total = min(int(initial_spins), self.max_fs)
        good: set[int] = set()
        for slot in self.good_slots:
            good |= self._draw_slot(slot, total)
        boost_left, dead, watch_left, index = 0, 0, 0, 0
        cap = self.max_win * self.bet
        while index < total:
            index += 1
            frame_total = _frame_sum(frames)
            rule, weights = self._fg_weights(index, good, boost_left, dead, frame_total, buy)
            table_name = self._pick_table(weights) if isinstance(weights, str) else self._pick_from(weights)
            boost_left = max(0, boost_left - 1)
            spin = self.spin(table_name, frames, free_game=True)
            hit = spin.pay > 0
            result.pay_fg += spin.pay
            result.fg_spins += 1
            result.cascades_fg += spin.cascades
            result.fg_hit_spins += int(hit)
            result.fg_yellow_seen += int(spin.yellow_seen)
            result.fg_yellow_used += spin.yellow_used
            result.yellow_values.update(spin.yellow_values)
            result.max_mult = max(result.max_mult, spin.max_mult)
            result.special_symbol_cnt += int(spin.scatter_count > 0)
            result.combo_fg[min(spin.cascades, 5)] += 1
            result.fg_index_spins[index] += 1
            result.fg_index_hits[index] += int(hit)
            result.fg_index_pay[index] += spin.pay
            result.fg_rule_spins[rule] += 1
            result.fg_rule_hits[rule] += int(hit)
            result.fg_rule_pay[rule] += spin.pay
            result.fg_table_spins[table_name] += 1
            if frame_total >= BIG_FRAME_TOTAL:
                result.fg_bigframe_spins += 1
                result.fg_bigframe_dead += int(not hit)
            if watch_left > 0:
                watch_left -= 1
                result.fg_post_retrigger_spins += 1
                result.fg_post_retrigger_hits += int(hit)
                result.fg_post_retrigger_pay += spin.pay
            if hit:
                if dead:
                    result.fg_dead_runs[dead] += 1
                dead = 0
            else:
                dead += 1
            result.symbol_hits.update(spin.symbol_hits)
            result.symbol_pay.update(spin.symbol_pay)
            result.fg_symbol_length_hits.update(spin.symbol_length_hits)
            result.fg_symbol_length_pay.update(spin.symbol_length_pay)
            result.fg_initial_symbols.update(spin.initial_symbols)
            result.fg_drop_symbols.update(spin.drop_symbols)
            if budget + result.pay_fg >= cap:
                result.capped = True
                break
            if spin.scatter_count >= self.min_scatter and total < self.max_fs:
                add = min(self.fs_retrigger, self.max_fs - total)
                total += add
                result.retriggers += 1
                boost_left = self.boost_spins
                watch_left = RETRIGGER_WATCH_SPINS
                late = [slot for slot in self.good_slots if slot["anchor"] == "end"]
                for slot in late:                 # 新增的局數再抽一次尾段好局
                    good |= self._draw_slot(slot, total, after=index)
        if dead:
            result.fg_dead_runs[dead] += 1
        result.fg_end_frame = _frame_sum(frames)
        return result

    def card_feature(self, section: str, initial_spins: int, budget: float, buy: bool = False) -> RoundResult:
        card = self.pick_card(section)
        result = None
        for _ in range(CARD_RETRY_LIMIT):
            result = self.free_session(initial_spins, budget, buy)
            if self.card_matches(card, result.pay_fg):
                return result
            self.retry_total += 1
        self.retry_limit_exceeded += 1
        self.retry_limit_fg += 1
        return result

    @staticmethod
    def merge(target: RoundResult, source: RoundResult) -> None:
        for name in ("pay_fg", "fg_spins", "retriggers", "cascades_fg", "fg_hit_spins", "fg_yellow_seen", "fg_yellow_used",
                     "special_symbol_cnt", "fg_bigframe_spins", "fg_bigframe_dead", "fg_post_retrigger_spins",
                     "fg_post_retrigger_hits", "fg_post_retrigger_pay"):
            setattr(target, name, getattr(target, name) + getattr(source, name))
        target.fg_triggered |= source.fg_triggered
        target.capped |= source.capped
        target.max_mult = max(target.max_mult, source.max_mult)
        target.fg_end_frame = source.fg_end_frame
        for name in ("yellow_values", "combo_fg", "fg_index_spins", "fg_index_hits", "fg_index_pay", "fg_rule_spins",
                     "fg_rule_hits", "fg_rule_pay", "fg_table_spins", "fg_dead_runs", "symbol_hits", "symbol_pay",
                     "fg_symbol_length_hits", "fg_symbol_length_pay", "fg_initial_symbols", "fg_drop_symbols"):
            getattr(target, name).update(getattr(source, name))

    def round(self, bet_mode: int) -> RoundResult:
        if self.card_enabled:   # Max Win 依模式取 buy_feature 卡組上限，或 base_game／free_game 兩者上限的較大者
            self.max_win = self.bf_cap if bet_mode == MODE_FEATUREBUY else max(self.fg_cap, self.bg_trigger_cap)
            self.trigger_cap = self.bg_trigger_cap
        if bet_mode == MODE_FEATUREBUY:
            entry = self.tables[self.config["bet_modes"]["buy_feature"]["entry_table"]]
            entry_symbols = [entry.reels[reel].window(self.rng, 4) for reel in range(5)]
            scatter = sum(symbol == C1 for column in entry_symbols for symbol in column)
            if scatter < self.min_scatter:
                raise RuntimeError("BF_Symbol 權重必須保證進場盤至少 3 顆 C1")
            spins = int(self.fs_table[min(scatter, max(self.fs_table))]["initial"])
            result = (self.card_feature("buy_feature", spins, 0.0, buy=True)
                      if self.card_enabled else self.free_session(spins, 0.0, buy=True))
            result.special_symbol_cnt += 1   # 進場盤本身含 SC
            result.pay_fg = min(result.pay_fg, self.max_win * self.bet)
            return result

        result = RoundResult()
        spin = self.card_spin(self.pick_card("base_game")) if self.card_enabled else self.natural_base_spin()
        result.pay_bg = spin.pay
        result.cascades_bg = spin.cascades
        result.bg_cascade_count = spin.cascades
        result.bg_hit_spins = int(spin.pay > 0)
        result.bg_yellow_seen = int(spin.yellow_seen)
        result.bg_yellow_used = spin.yellow_used
        result.yellow_values.update(spin.yellow_values)
        result.bg_peak_frame = spin.peak_frame
        result.max_mult = spin.max_mult
        result.special_symbol_cnt = int(spin.scatter_count > 0)
        result.symbol_hits.update(spin.symbol_hits)
        result.symbol_pay.update(spin.symbol_pay)
        result.bg_symbol_length_hits.update(spin.symbol_length_hits)
        result.bg_symbol_length_pay.update(spin.symbol_length_pay)
        result.bg_initial_symbols.update(spin.initial_symbols)
        result.bg_drop_symbols.update(spin.drop_symbols)

        if spin.scatter_count >= self.min_scatter:
            result.bg_trigger_fg_cnt = 1
            result.bg_trigger_fg_pay = spin.pay
            initial = self.fs_table[min(spin.scatter_count, max(self.fs_table))]["initial"]
            feature = (self.card_feature("free_game", initial, result.pay_bg)
                       if self.card_enabled else self.free_session(initial, result.pay_bg))
            self.merge(result, feature)

        cap = self.max_win * self.bet
        if result.pay > cap:                      # 達上限即截斷
            overflow = result.pay - cap
            result.pay_fg = max(0.0, result.pay_fg - overflow)
            if result.pay > cap:
                result.pay_bg = min(result.pay_bg, cap)
            result.capped = True
        return result


# ===== 統計 =====

def wager_for_mode(mode: int, base_bet: float) -> float:
    if mode == MODE_NORMALBET:
        return base_bet
    return base_bet * float(CFG["bet_modes"]["buy_feature"]["cost_multiplier"])


def bet_tier_name(bet_tier_amount: float, big_amount: float | None = None) -> str:
    """數學模型規範 §1.7.1（2026-10-27）：小 Bet（< $2）看 bet_tier_amount（NB／EB 實際押注、BF／SF 基礎押注）；
    大 Bet（> $100）看基礎押注 big_amount（對齊 SPS isHighBet()）。未給 big_amount 時同 bet_tier_amount。"""
    big_amount = bet_tier_amount if big_amount is None else big_amount
    if bet_tier_amount < 2.0:
        return "small_bet"
    if big_amount <= 100.0:
        return "medium_bet"
    return "big_bet"


def threshold_index(multiplier: float) -> int:
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if multiplier <= upper:
            return index
    return len(MULTIPLIER_THRESHOLDS) - 1


def _empty_stats() -> dict[str, Any]:
    buckets = len(MULTIPLIER_THRESHOLDS)
    return {
        "rounds": 0, "coin_in": 0.0, "pay_bg": 0.0, "pay_fg": 0.0,
        "win_x_sum": 0.0, "win_x_square": 0.0, "max_win_x": 0.0, "capped_rounds": 0,
        "bg_hit_spins": 0, "fg_hit_spins": 0, "fg_spins": 0, "fg_triggers": 0,
        "retriggers": 0, "cascades_bg": 0, "cascades_fg": 0,
        "special_symbol_cnt": 0, "bg_trigger_fg_cnt": 0, "bg_trigger_fg_pay": 0.0,
        "bg_yellow_seen": 0, "fg_yellow_seen": 0, "bg_yellow_used": 0, "fg_yellow_used": 0,
        "yellow_values": Counter(), "bg_peak_frame_sum": 0, "bg_peak_frame_max": 0,
        "fg_end_frame_sum": 0, "fg_end_frame_max": 0, "max_mult": 1,
        "fg_index_spins": Counter(), "fg_index_hits": Counter(), "fg_index_pay": Counter(),
        "fg_rule_spins": Counter(), "fg_rule_hits": Counter(), "fg_rule_pay": Counter(), "fg_table_spins": Counter(),
        "fg_bigframe_spins": 0, "fg_bigframe_dead": 0, "fg_dead_runs": Counter(),
        "fg_post_retrigger_spins": 0, "fg_post_retrigger_hits": 0, "fg_post_retrigger_pay": 0.0,
        "combo_bg": Counter(), "combo_fg": Counter(),
        "bg_symbol_length_pay": Counter(), "fg_symbol_length_pay": Counter(),
        "symbol_hits": Counter(), "symbol_pay": Counter(),
        "bg_symbol_length_hits": Counter(), "fg_symbol_length_hits": Counter(),
        "bg_initial_symbols": Counter(), "bg_drop_symbols": Counter(),
        "fg_initial_symbols": Counter(), "fg_drop_symbols": Counter(),
        "retry_total": 0, "retry_limit_exceeded": 0, "retry_limit_bg_range": 0,
        "retry_limit_bg_freegame": 0, "retry_limit_fg": 0,
        "card_draws": Counter(),
        # Multiplier Line 分桶
        "bucket_bg_cnt": [0] * buckets, "bucket_bg_pay": [0.0] * buckets,
        "bucket_fg_cnt": [0] * buckets, "bucket_fg_pay": [0.0] * buckets,
        "bucket_bf_cnt": [0] * buckets, "bucket_bf_pay": [0.0] * buckets,
        "bucket_trigger_cnt": [0] * buckets, "bucket_trigger_pay": [0.0] * buckets,
        "bucket_fg_hit": [0] * buckets, "bucket_fg_spins": [0] * buckets,
        "bucket_fg_end_frame": [0] * buckets, "bucket_bg_yellow": [0] * buckets,
        "bucket_bg_combo": [[0] * 5 for _ in range(buckets)],
        "bucket_fg_combo": [[0] * 5 for _ in range(buckets)],
    }


def _accumulate(stats: dict[str, Any], result: RoundResult, wager: float,
                base_bet: float, bet_mode: int) -> None:
    stats["rounds"] += 1
    stats["coin_in"] += wager
    stats["pay_bg"] += result.pay_bg
    stats["pay_fg"] += result.pay_fg
    win_x = result.pay / wager
    stats["win_x_sum"] += win_x
    stats["win_x_square"] += win_x * win_x
    stats["max_win_x"] = max(stats["max_win_x"], win_x)
    stats["capped_rounds"] += int(result.capped)
    for key in ("bg_hit_spins", "fg_hit_spins", "fg_spins", "retriggers", "cascades_bg", "cascades_fg",
                "special_symbol_cnt", "bg_trigger_fg_cnt", "bg_trigger_fg_pay", "bg_yellow_seen", "fg_yellow_seen",
                "bg_yellow_used", "fg_yellow_used", "fg_bigframe_spins", "fg_bigframe_dead",
                "fg_post_retrigger_spins", "fg_post_retrigger_hits", "fg_post_retrigger_pay"):
        stats[key] += getattr(result, key)
    stats["fg_triggers"] += int(result.fg_triggered)
    stats["max_mult"] = max(stats["max_mult"], result.max_mult)
    if bet_mode != MODE_FEATUREBUY:
        stats["combo_bg"][min(result.bg_cascade_count, 5)] += 1
        stats["bg_peak_frame_sum"] += result.bg_peak_frame
        stats["bg_peak_frame_max"] = max(stats["bg_peak_frame_max"], result.bg_peak_frame)
    if result.fg_triggered:
        stats["fg_end_frame_sum"] += result.fg_end_frame
        stats["fg_end_frame_max"] = max(stats["fg_end_frame_max"], result.fg_end_frame)
    for key in ("yellow_values", "combo_fg", "fg_index_spins", "fg_index_hits", "fg_index_pay", "fg_rule_spins",
                "fg_rule_hits", "fg_rule_pay", "fg_table_spins", "fg_dead_runs", "symbol_hits", "symbol_pay",
                "bg_symbol_length_hits", "fg_symbol_length_hits", "bg_symbol_length_pay", "fg_symbol_length_pay",
                "bg_initial_symbols", "bg_drop_symbols", "fg_initial_symbols", "fg_drop_symbols"):
        stats[key].update(getattr(result, key))

    if bet_mode == MODE_FEATUREBUY:
        # 數學模型規範 §2.5：BF 的倍率判定分母是 Normal Bet 基準成本，不是購買價
        index = threshold_index(result.pay_fg / base_bet)
        stats["bucket_bf_cnt"][index] += 1
        stats["bucket_bf_pay"][index] += result.pay_fg
    elif result.fg_triggered:
        # 規範：觸發 FG 的局屬 FG 卡口徑，其 BG 得分只進 bg_trigger_fg_*_lte_upper
        index = threshold_index(result.bg_trigger_fg_pay / base_bet)
        stats["bucket_trigger_cnt"][index] += 1
        stats["bucket_trigger_pay"][index] += result.bg_trigger_fg_pay
        fg_index = threshold_index(result.pay_fg / base_bet)
        stats["bucket_fg_cnt"][fg_index] += 1
        stats["bucket_fg_pay"][fg_index] += result.pay_fg
        stats["bucket_fg_spins"][fg_index] += result.fg_spins
        stats["bucket_fg_hit"][fg_index] += result.fg_hit_spins
        stats["bucket_fg_end_frame"][fg_index] += result.fg_end_frame
        for combo, count in result.combo_fg.items():
            stats["bucket_fg_combo"][fg_index][min(max(combo, 1), 5) - 1] += count
    else:
        index = threshold_index(result.pay_bg / base_bet)
        stats["bucket_bg_cnt"][index] += 1
        stats["bucket_bg_pay"][index] += result.pay_bg
        stats["bucket_bg_yellow"][index] += result.bg_yellow_used
        stats["bucket_bg_combo"][index][min(max(result.bg_cascade_count, 1), 5) - 1] += 1


def _merge_stats(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, Counter):
            target[key].update(value)
        elif key in ("max_win_x", "max_mult", "bg_peak_frame_max", "fg_end_frame_max"):
            target[key] = max(target[key], value)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, Counter):
                    target[key][index].update(item)
                elif isinstance(item, list):
                    for sub, subvalue in enumerate(item):
                        target[key][index][sub] += subvalue
                else:
                    target[key][index] += item
        else:
            target[key] += value


def _simulate_chunk(rounds: int, bet_mode: int, base_bet: float, seed: int,
                    card_enabled: bool, newbie: bool) -> dict[str, Any]:
    wager = wager_for_mode(bet_mode, base_bet)
    engine = CalaveraParty(CFG, CFG_RTP or None, seed, base_bet, card_enabled, newbie)
    stats = _empty_stats()
    for _ in range(rounds):
        _accumulate(stats, engine.round(bet_mode), wager, base_bet, bet_mode)
    stats["retry_total"] = engine.retry_total
    stats["retry_limit_exceeded"] = engine.retry_limit_exceeded
    stats["retry_limit_bg_range"] = engine.retry_limit_bg_range
    stats["retry_limit_bg_freegame"] = engine.retry_limit_bg_freegame
    stats["retry_limit_fg"] = engine.retry_limit_fg
    stats["card_draws"].update(engine.card_draws)
    return stats


def _init_worker(cfg: dict[str, Any], cfg_rtp: dict[str, Any]) -> None:
    """多程序 worker 初始化：Windows 以 spawn 啟動，需把主程序載入的 config 傳進來。"""
    global CFG, CFG_RTP
    CFG, CFG_RTP = cfg, cfg_rtp


def run_simulation(total_rounds: int, bet_mode: int, base_bet: float, threads: int,
                   card_enabled: bool, newbie: bool) -> dict[str, Any]:
    per_thread = [total_rounds // threads] * threads
    for index in range(total_rounds % threads):
        per_thread[index] += 1
    assert sum(per_thread) == total_rounds

    # Warm-up（不計時）
    _simulate_chunk(min(200, max(1, total_rounds)), bet_mode, base_bet,
                    RNG_SEED - 1, card_enabled, newbie)

    started = time.perf_counter()
    merged = _empty_stats()
    if threads == 1:
        merged = _simulate_chunk(total_rounds, bet_mode, base_bet, RNG_SEED, card_enabled, newbie)
    else:
        # 2026-10-06：ThreadPool 受 GIL 限制實際只用 1 核（1e8 跑 3.5 小時）；改多程序，worker 以 initializer 接收 config
        with ProcessPoolExecutor(max_workers=threads, initializer=_init_worker, initargs=(CFG, CFG_RTP)) as pool:
            futures = [
                pool.submit(_simulate_chunk, count, bet_mode, base_bet,
                            RNG_SEED + index * 7919, card_enabled, newbie)
                for index, count in enumerate(per_thread) if count > 0
            ]
            for future in futures:
                _merge_stats(merged, future.result())
    duration = time.perf_counter() - started
    return {"stats": merged, "duration": duration}


# ===== 報表 / Console =====

def mode_name(mode: int) -> str:
    return {MODE_NORMALBET: "Normal Bet", MODE_EXTRABET: "Extra Bet"}.get(mode, "Buy Feature")


def calculated_metrics(result: dict[str, Any]) -> dict[str, Any]:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    coin_in = max(1e-12, s["coin_in"])
    pay_total = s["pay_bg"] + s["pay_fg"]
    mean = s["win_x_sum"] / rounds
    variance = max(0.0, s["win_x_square"] / rounds - mean * mean)
    fg_triggers = s["fg_triggers"]
    fg_spins = s["fg_spins"]
    special = int(s["special_symbol_cnt"])
    return {
        "rounds": s["rounds"],
        "coin_in_per_round": s["coin_in"] / rounds,
        "rtp_total": pay_total / coin_in,
        "rtp_link": 0.0,
        "rtp_bonus": 0.0,
        "rtp_game": pay_total / coin_in,
        "rtp_bg": s["pay_bg"] / coin_in,
        "rtp_fg": s["pay_fg"] / coin_in,
        "hit_rate_bg": s["bg_hit_spins"] / rounds,
        "hit_rate_fg": s["fg_hit_spins"] / max(1, fg_spins),
        "fg_trigger_rate": fg_triggers / rounds,
        "fg_trigger_cycle": rounds / fg_triggers if fg_triggers else math.inf,
        "retrigger_trigger_rate": s["retriggers"] / max(1, fg_spins),
        "retrigger_trigger_cycle": fg_spins / s["retriggers"] if s["retriggers"] else math.inf,
        "avg_fg_spins": fg_spins / fg_triggers if fg_triggers else 0.0,
        "special_symbol_cnt": special,
        "SCR": special / rounds * 10_000_000_000,
        "max_win_x": s["max_win_x"],
        "capped_rounds": s["capped_rounds"],
        "volatility_std": math.sqrt(variance),
        "standard_error": math.sqrt(variance) / math.sqrt(rounds),
    }


def _trigger_within_cap(s: dict[str, Any], profile: str, section: str) -> tuple[int, float]:
    """自然機率（Card Off）下，BG 觸發 FG 那把得分 ≤ 該 Profile BG Trigger Cap（base_game 卡組最高有權重區間上限）的次數與得分。"""
    cards = (CFG_RTP or {}).get("card_system", {}).get("profiles", {}).get(profile, {}).get(section) or []
    caps = [float(c["max"]) for c in cards if c.get("type") == "range" and float(c.get("weight", 0)) > 0]
    cap = max(caps) if caps else math.inf
    idx = [i for i, upper in enumerate(MULTIPLIER_THRESHOLDS) if upper <= cap]
    return (int(sum(s["bucket_trigger_cnt"][i] for i in idx)), float(sum(s["bucket_trigger_pay"][i] for i in idx)))


def common_summary_sections(result: dict[str, Any]) -> list[list[tuple[str, Any]]]:
    s = result["stats"]
    m = calculated_metrics(result)
    # 2026-10-21：自然機率報表的觸發 FG 那把依新老手 BG Trigger Cap 分開統計（新手上限 ≤ 老手，較多大倍數被擋）
    trigger_rows: list[tuple[str, Any]] = [("bg_trigger_fg_cnt", s["bg_trigger_fg_cnt"]),
                                           ("bg_trigger_fg_pay", s["bg_trigger_fg_pay"])]
    if not result["card_system_enabled"] and result["bet_mode"] != MODE_FEATUREBUY:
        section = "base_game"
        old_cnt, old_pay = _trigger_within_cap(s, "oldhand", section)
        new_cnt, new_pay = _trigger_within_cap(s, "newbie", section)
        trigger_rows = [("bg_trigger_fg_cnt", old_cnt), ("bg_trigger_fg_pay", old_pay),
                        ("bg_trigger_fg_cnt_newbie", new_cnt), ("bg_trigger_fg_pay_newbie", new_pay)]
    sections: list[list[tuple[str, Any]]] = [
        [("game_name", result["game_name"]), ("game_id", result["game_id"])],
        [("config_file", result["config_file"]),
         ("config_rtp_file", result["config_rtp_file"]),
         ("math_version", result["math_version"]),
         ("card_system", "on" if result["card_system_enabled"] else "off")],
        [("bet_mode", mode_name(result["bet_mode"])),
         ("bet_multi", result["bet_multi"]),
         ("feature_price_multiplier", result["feature_price_multiplier"]),
         ("base_bet", result["base_bet"]),
         ("bet_amount", result["bet_amount"]),
         ("bet_tier_amount", result["bet_tier_amount"]),
         ("bet_tier", result["bet_tier"]),
         ("jackpot", result["jackpot"]),
         ("coin_in", m["coin_in_per_round"]),
         ("total_rounds", s["rounds"]),
         ("duration", result["duration"])],
        [("rtp_total", m["rtp_total"]), ("rtp_link", m["rtp_link"]),
         ("rtp_bonus", m["rtp_bonus"]), ("rtp_game", m["rtp_game"]),
         ("rtp_bg", m["rtp_bg"]), ("rtp_fg", m["rtp_fg"]),
         ("hit_rate_bg", m["hit_rate_bg"]), ("hit_rate_fg", m["hit_rate_fg"]),
         ("fg_trigger_rate", (m["fg_trigger_rate"], m["fg_trigger_cycle"])),
         ("retrigger_trigger_rate", (m["retrigger_trigger_rate"], m["retrigger_trigger_cycle"])),
         ("avg_fg_spins", m["avg_fg_spins"])],
        [*trigger_rows,
         ("special_symbol_cnt", m["special_symbol_cnt"]),
         ("SCR", m["SCR"])],
        [("max_win_x", m["max_win_x"]), ("capped_rounds", m["capped_rounds"]),
         ("volatility_std", m["volatility_std"]), ("standard_error", m["standard_error"])],
    ]
    if result["card_system_enabled"]:
        sections.extend([
            [("card_system_profile", result["card_system_profile"]),
             ("card_retry_limit", CARD_RETRY_LIMIT),
             ("retry_total", s["retry_total"]),
             ("avg_retry", s["retry_total"] / max(1, s["rounds"]))],
            [("retry_limit_exceeded", s["retry_limit_exceeded"]),
             ("retry_limit_bg_range", s["retry_limit_bg_range"]),
             ("retry_limit_bg_freegame", s["retry_limit_bg_freegame"]),
             ("retry_limit_fg", s["retry_limit_fg"])],
        ])
    return sections


def game_info_rows(result: dict[str, Any]) -> list[tuple[str, Any]]:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    fg_spins = max(1, s["fg_spins"])
    fg_triggers = max(1, s["fg_triggers"])
    rows: list[tuple[str, Any]] = [
        ("avg_cascades_bg", s["cascades_bg"] / rounds),
        ("avg_cascades_fg", s["cascades_fg"] / fg_spins),
        ("yellow_seen_bg_rate", s["bg_yellow_seen"] / rounds),
        ("yellow_seen_fg_rate", s["fg_yellow_seen"] / fg_spins),
        ("yellow_used_per_spin_bg", s["bg_yellow_used"] / rounds),
        ("yellow_used_per_spin_fg", s["fg_yellow_used"] / fg_spins),
        ("avg_peak_frame_bg", s["bg_peak_frame_sum"] / rounds),
        ("max_peak_frame_bg", s["bg_peak_frame_max"]),
        ("avg_end_frame_fg", s["fg_end_frame_sum"] / fg_triggers),
        ("max_end_frame_fg", s["fg_end_frame_max"]),
        ("max_frame_multiplier", s["max_mult"]),
        ("bigframe_dead_fg_rate", s["fg_bigframe_dead"] / max(1, s["fg_bigframe_spins"])),
        ("post_retrigger_hit_rate", s["fg_post_retrigger_hits"] / max(1, s["fg_post_retrigger_spins"])),
        ("post_retrigger_avg_win_x", s["fg_post_retrigger_pay"] / max(1, s["fg_post_retrigger_spins"]) / max(1e-12, result["base_bet"])),
        ("fg_spin_avg_win_x", s["pay_fg"] / fg_spins / max(1e-12, result["base_bet"])),
    ]
    short = {"good_slot": "good", "retrigger_boost": "boost", "dead_streak": "dead", "frame_tier": "tier", "normal": "normal"}
    for rule, name in short.items():
        spins = s["fg_rule_spins"][rule]
        rows.append((f"fg_{name}_share", spins / fg_spins))
        rows.append((f"fg_{name}_hit_rate", s["fg_rule_hits"][rule] / max(1, spins)))
        rows.append((f"fg_{name}_avg_win_x", s["fg_rule_pay"][rule] / max(1, spins) / max(1e-12, result["base_bet"])))
    return rows


COUNT_KEYS = {
    "total_rounds", "bg_trigger_fg_cnt", "bg_trigger_fg_cnt_newbie", "special_symbol_cnt", "SCR", "retry_total",
    "retry_limit_exceeded", "retry_limit_bg_range", "retry_limit_bg_freegame",
    "retry_limit_fg", "capped_rounds", "max_peak_frame_bg", "max_end_frame_fg", "max_frame_multiplier",
}


def _display_value(key: str, value: Any) -> str:
    if key == "duration":
        return f"{float(value):05.2f} sec"
    if key in COUNT_KEYS:
        return f"{int(value):,}"
    if key == "card_retry_limit":
        return str(int(value))
    if key in {"bg_trigger_fg_pay", "bg_trigger_fg_pay_newbie"}:
        return f"{float(value):,.0f}"
    if key in {"coin_in", "base_bet", "bet_amount", "bet_tier_amount"}:
        return f"{float(value):.2f}"
    if key in {"fg_trigger_rate", "retrigger_trigger_rate"}:
        rate, cycle = value
        unit = "spins" if key == "fg_trigger_rate" else "free spins"
        cycle_text = "N/A" if not math.isfinite(float(cycle)) else f"{float(cycle):.2f} {unit}"
        return f"{float(rate):.4%} (cycle {cycle_text})"
    if key.startswith("rtp_") or key in {"hit_rate_bg", "hit_rate_fg"} or key.endswith("_share"):
        return f"{float(value):.4%}"
    if key.endswith("_rate"):
        return f"{float(value):.6%}"
    if key == "avg_fg_spins":
        return f"{float(value):.2f} spins"
    if key == "max_win_x":
        return f"{float(value):,.2f} x"
    if key in {"avg_retry", "volatility_std", "standard_error"} or key.endswith("_win_x") or key.startswith("avg_"):
        return f"{float(value):05.2f}"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def overview_rows(result: dict[str, Any]) -> list[tuple[str, str]]:
    flat = [row for section in common_summary_sections(result) for row in section]
    return [(key, _display_value(key, value)) for key, value in flat + game_info_rows(result)]


def print_console(result: dict[str, Any]) -> None:
    for section in common_summary_sections(result):
        for key, value in section:
            print(f"{key:<28}{_display_value(key, value)}")
        print()
    print("<< By Game Info >>")
    for key, value in game_info_rows(result):
        print(f"{key:<28}{_display_value(key, value)}")
    print()


def multiplier_line_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    rows = []
    trigger_cnt_cum = 0
    trigger_pay_cum = 0.0
    has_bf = result["bet_mode"] == MODE_FEATUREBUY
    for index, upper in enumerate(MULTIPLIER_THRESHOLDS):
        if index == 0:
            interval = "0"
        else:
            interval = f"{float(MULTIPLIER_THRESHOLDS[index - 1]):.1f} < X <= {float(upper):.1f}"
        trigger_cnt_cum += s["bucket_trigger_cnt"][index]
        trigger_pay_cum += s["bucket_trigger_pay"][index]
        row: dict[str, Any] = {
            "Interval": interval,
            "base_game_cnt": s["bucket_bg_cnt"][index],
            "base_game_pay": s["bucket_bg_pay"][index],
            "free_game_cnt": s["bucket_fg_cnt"][index],
            "free_game_pay": s["bucket_fg_pay"][index],
        }
        if has_bf:
            row["free_game_cnt_BF"] = s["bucket_bf_cnt"][index]
            row["free_game_pay_BF"] = s["bucket_bf_pay"][index]
        row["Interval_Upper"] = upper
        row["bg_trigger_fg_cnt_lte_upper"] = trigger_cnt_cum
        row["bg_trigger_fg_pay_lte_upper"] = trigger_pay_cum
        fg_spins = s["bucket_fg_spins"][index]
        row["FG_Hit_Rate"] = s["bucket_fg_hit"][index] / fg_spins if fg_spins else 0.0
        row["FG_Spin_Count"] = fg_spins
        bg_cnt = s["bucket_bg_cnt"][index]
        row["BG_Avg_Yellow_Used"] = s["bucket_bg_yellow"][index] / bg_cnt if bg_cnt else 0.0
        row["FG_Avg_End_Frame"] = s["bucket_fg_end_frame"][index] / s["bucket_fg_cnt"][index] if s["bucket_fg_cnt"][index] else 0.0

        bg_combo_total = max(1, sum(s["bucket_bg_combo"][index]))
        for combo in range(5):
            label = f"BG_Combo_{combo + 1}{'+' if combo == 4 else ''}_Rate"
            row[label] = s["bucket_bg_combo"][index][combo] / bg_combo_total
        fg_combo_total = max(1, sum(s["bucket_fg_combo"][index]))
        for combo in range(5):
            label = f"FG_Combo_{combo + 1}{'+' if combo == 4 else ''}_Rate"
            row[label] = s["bucket_fg_combo"][index][combo] / fg_combo_total
        rows.append(row)
    return pd.DataFrame(rows)


def symbol_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    names = CFG["symbol_names"]
    total_hits = max(1, sum(s["symbol_hits"].values()))
    total_pay = max(1e-12, sum(s["symbol_pay"].values()))
    rows = []
    for symbol in SCORE_SYMBOLS:
        rows.append({
            "symbol_id": symbol,
            "symbol": names[str(symbol)],
            "ways_hits": s["symbol_hits"][symbol],
            "hit_share": s["symbol_hits"][symbol] / total_hits,
            "pay": s["symbol_pay"][symbol],
            "pay_share": s["symbol_pay"][symbol] / total_pay,
            "hits_3": s["bg_symbol_length_hits"][(symbol, 3)] + s["fg_symbol_length_hits"][(symbol, 3)],
            "hits_4": s["bg_symbol_length_hits"][(symbol, 4)] + s["fg_symbol_length_hits"][(symbol, 4)],
            "hits_5": s["bg_symbol_length_hits"][(symbol, 5)] + s["fg_symbol_length_hits"][(symbol, 5)],
        })
    return pd.DataFrame(rows)


def feature_frame(result: dict[str, Any]) -> pd.DataFrame:
    s = result["stats"]
    rounds = max(1, s["rounds"])
    fg_spins = max(1, s["fg_spins"])
    used = max(1, sum(s["yellow_values"].values()))
    rows = [
        ("yellow_seen_spins_bg", s["bg_yellow_seen"]), ("yellow_seen_spins_fg", s["fg_yellow_seen"]),
        ("yellow_used_bg", s["bg_yellow_used"]), ("yellow_used_fg", s["fg_yellow_used"]),
        ("avg_peak_frame_bg", s["bg_peak_frame_sum"] / rounds), ("max_peak_frame_bg", s["bg_peak_frame_max"]),
        ("avg_end_frame_fg", s["fg_end_frame_sum"] / max(1, s["fg_triggers"])), ("max_end_frame_fg", s["fg_end_frame_max"]),
        ("max_frame_multiplier", s["max_mult"]),
        ("bigframe_spins_fg", s["fg_bigframe_spins"]), ("bigframe_dead_fg", s["fg_bigframe_dead"]),
        ("bigframe_dead_rate_fg", s["fg_bigframe_dead"] / max(1, s["fg_bigframe_spins"])),
        ("post_retrigger_spins", s["fg_post_retrigger_spins"]), ("post_retrigger_hits", s["fg_post_retrigger_hits"]),
        ("post_retrigger_pay", s["fg_post_retrigger_pay"]),
        ("max_win_x", s["max_win_x"]), ("capped_rounds", s["capped_rounds"]),
        ("avg_cascades_bg", s["cascades_bg"] / rounds), ("avg_cascades_fg", s["cascades_fg"] / fg_spins),
    ]
    rows += [(f"yellow_used_x{v}_share", s["yellow_values"][v] / used) for v in sorted(s["yellow_values"])]
    rows += [(f"fg_table_{name}_share", s["fg_table_spins"][name] / fg_spins) for name in sorted(s["fg_table_spins"])]
    rows += [(f"fg_dead_run_{n}", s["fg_dead_runs"][n]) for n in sorted(s["fg_dead_runs"])]
    return pd.DataFrame(rows, columns=["Index", "Value"])


def fg_spin_index_frame(result: dict[str, Any]) -> pd.DataFrame:
    """FG 第 i 局的得分率與平均得分（看前 3 局、最後 5 局的好事節奏）。"""
    s = result["stats"]
    base = max(1e-12, result["base_bet"])
    rows = []
    for index in sorted(s["fg_index_spins"]):
        spins = s["fg_index_spins"][index]
        rows.append({"fg_spin": index, "spins": spins, "hit_rate": s["fg_index_hits"][index] / spins,
                     "avg_win_x": s["fg_index_pay"][index] / spins / base})
    return pd.DataFrame(rows, columns=["fg_spin", "spins", "hit_rate", "avg_win_x"])


def fg_rule_frame(result: dict[str, Any]) -> pd.DataFrame:
    """FG 隱性控制各規則的使用率、得分率與平均得分。"""
    s = result["stats"]
    base = max(1e-12, result["base_bet"])
    total = max(1, s["fg_spins"])
    rows = []
    for rule in ("good_slot", "retrigger_boost", "dead_streak", "frame_tier", "normal"):
        spins = s["fg_rule_spins"][rule]
        rows.append({"rule": rule, "spins": spins, "share": spins / total,
                     "hit_rate": s["fg_rule_hits"][rule] / spins if spins else 0.0,
                     "avg_win_x": s["fg_rule_pay"][rule] / spins / base if spins else 0.0})
    return pd.DataFrame(rows, columns=["rule", "spins", "share", "hit_rate", "avg_win_x"])


# ===== 報表檔名 =====

def format_rounds_tag(total_rounds: int) -> str:
    exponent = round(math.log10(total_rounds)) if total_rounds > 0 else 0
    if 10 ** exponent == total_rounds:
        return f"10{exponent}"
    return str(total_rounds)


def format_base_version_tag(version: Any) -> str:
    text = str(version)
    if not text.isdigit() or len(text) != 1:
        raise ValueError(f"基礎版本必須為 1 碼，目前為 {version!r}")
    return text.zfill(2)


def format_rtp_version_tag(version: Any) -> str:
    parts = str(version).split(".")
    if len(parts) != 4:
        raise ValueError(f"RTP／Variant 版本必須為四段，目前為 {version!r}")
    out = ""
    for part in parts:
        if not part.isdigit() or len(part) > 2:
            raise ValueError(f"版本段位 {part!r} 超過 2 位數，請修正版本後再輸出報表")
        out += part.zfill(2)
    return out


def format_rtp_tag(rtp_ratio: float) -> str:
    return f"{rtp_ratio * 100:.4f}".replace(".", "")[:4]


def report_filename(result: dict[str, Any], timestamp: datetime | None = None) -> str:
    stamp = (timestamp or datetime.now()).strftime("%y%m%d%H%M")
    rounds_tag = format_rounds_tag(result["stats"]["rounds"])
    bet_mode = result["bet_mode"]
    if not result["card_system_enabled"]:
        game_id = f"{CFG['parsheet_id']}"
        version_tag = format_base_version_tag(CFG["excel_version"])
        return f"{game_id}_{version_tag}_{stamp}_betmode{bet_mode}_{rounds_tag}.xlsx"
    rtp_game_id = str(CFG_RTP.get("parsheet_id") or CFG_RTP.get("game_id"))
    version_tag = format_rtp_version_tag(CFG_RTP["excel_version"])
    rtp_tag = format_rtp_tag(calculated_metrics(result)["rtp_total"])
    profile = result["card_system_profile"]
    parts = [rtp_game_id, version_tag, stamp, f"betmode{bet_mode}", rounds_tag, rtp_tag, profile]
    if profile == "oldhand":
        parts.append(result["bet_tier"])
    parts.append("card")
    return "_".join(parts) + ".xlsx"


def output_report(result: dict[str, Any], output_dir: Path | None = None) -> Path:
    directory = output_dir or (BASE_DIR / "Record")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / report_filename(result)
    overview = pd.DataFrame(overview_rows(result), columns=["Index", "Value"])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        overview.to_excel(writer, sheet_name="Overview", index=False)
        multiplier_line_frame(result).to_excel(writer, sheet_name="Multiplier Line", index=False)
        feature_frame(result).to_excel(writer, sheet_name="Feature", index=False)
        fg_spin_index_frame(result).to_excel(writer, sheet_name="FG Spin Index", index=False)
        fg_rule_frame(result).to_excel(writer, sheet_name="FG Rule", index=False)
        symbol_frame(result).to_excel(writer, sheet_name="Symbol", index=False)
        eliminate_frame(result).to_excel(writer, sheet_name="Eliminate", index=False)
        symbol_length_frame(result).to_excel(writer, sheet_name="Symbol Length", index=False)
    return path


def eliminate_frame(result: dict[str, Any]) -> pd.DataFrame:
    """消除次數分布（同 H016 報表 Eliminate 頁）：BG 每局、FG 每次免費轉。"""
    s = result["stats"]
    rows = [(("5+" if k == 5 else str(k)), s["combo_bg"].get(k, 0), s["combo_fg"].get(k, 0)) for k in range(6)]
    return pd.DataFrame(rows, columns=["combo", "BG", "FG"])


def symbol_length_frame(result: dict[str, Any]) -> pd.DataFrame:
    """各符號 3／4／5 連線命中數與派彩（同 H016 報表 Symbol Length 頁）。"""
    s = result["stats"]
    names = CFG["symbol_names"]
    rows = []
    for scene, hits_key, pay_key in (("BG", "bg_symbol_length_hits", "bg_symbol_length_pay"),
                                     ("FG", "fg_symbol_length_hits", "fg_symbol_length_pay")):
        for symbol in SCORE_SYMBOLS:
            for length in (3, 4, 5):
                rows.append((scene, names[str(symbol)], length,
                             s[hits_key][(symbol, length)], s[pay_key][(symbol, length)]))
    return pd.DataFrame(rows, columns=["scene", "symbol", "length", "hits", "pay"])


# ===== Runner =====

def build_result(stats_bundle: dict[str, Any], combo: dict[str, Any]) -> dict[str, Any]:
    bet_mode = int(combo["bet_mode"])
    base_bet = float(combo["base_bet"])
    bet_amount = wager_for_mode(bet_mode, base_bet)
    if bet_mode == MODE_FEATUREBUY:
        price = float(CFG["bet_modes"]["buy_feature"]["cost_multiplier"])
        bet_tier_amount = bet_amount / price
        feature_price = price
    else:
        bet_tier_amount = bet_amount
        feature_price = "n/a"
    jackpot_on = bool((CFG.get("jackpot") or {}).get("enabled"))
    return {
        "stats": stats_bundle["stats"],
        "duration": stats_bundle["duration"],
        "game_name": CFG["name_zh"],
        "game_id": CFG["online_game_id"],
        "parsheet_id": CFG["parsheet_id"],
        "config_file": combo["config_file"],
        "config_rtp_file": combo["config_rtp_file"] if CFG_RTP else f"{combo['config_rtp_file']} (not found)",
        "math_version": CFG_RTP.get("excel_version", CFG["excel_version"]),
        "card_system_enabled": bool(combo["card_system_enabled"]) and bool(CFG_RTP),
        "card_system_profile": "newbie" if combo["card_system_is_newbie"] else "oldhand",
        "bet_mode": bet_mode,
        "bet_multi": int(round(bet_amount / base_bet)),
        "feature_price_multiplier": feature_price,
        "base_bet": base_bet,
        "bet_amount": bet_amount,
        "bet_tier_amount": bet_tier_amount,
        "bet_tier": bet_tier_name(bet_tier_amount, base_bet),
        "jackpot": "on" if jackpot_on else "off",
    }


def load_batch_configs(combo: dict[str, Any]) -> None:
    global CFG, CFG_RTP
    CFG = load_js_config(BASE_DIR / combo["config_file"])
    if str(combo.get("config_rtp_file", "AUTO")).upper() == "AUTO":
        mode, base_bet = int(combo["bet_mode"]), float(combo["base_bet"])
        tier_amount = base_bet if mode == MODE_FEATUREBUY else wager_for_mode(mode, base_bet)
        tpl = NEWBIE_CONFIG if combo.get("card_system_is_newbie") else TIER_CONFIG[bet_tier_name(tier_amount, base_bet)]
        combo["config_rtp_file"] = tpl.format(s=RTP_SERIES)
        print(f"[auto] bet_mode {mode}、base_bet {base_bet:g}（檔位金額 ${tier_amount:g}）→ {combo['config_rtp_file']}")
    rtp_path = BASE_DIR / combo["config_rtp_file"]
    CFG_RTP = load_js_config(rtp_path) if rtp_path.exists() else {}
    validate_config_pair(CFG, CFG_RTP or None, combo["config_file"], combo["config_rtp_file"])
    if not CFG_RTP and combo["card_system_enabled"]:
        print(f"[warn] 找不到 {combo['config_rtp_file']}，本批改以 Card System Off 執行。")


def validate_batch_run(combo: dict[str, Any]) -> dict[str, Any]:
    required = {"config_file", "config_rtp_file", "bet_mode", "total_rounds",
                "card_system_enabled", "card_system_is_newbie", "base_bet"}
    missing = required - set(combo)
    if missing:
        raise ValueError(f"BATCH_RUNS 缺少必要欄位：{sorted(missing)}")
    if int(combo["bet_mode"]) not in SUPPORTED_BET_MODES:
        raise ValueError(f"不支援的 bet_mode {combo['bet_mode']}；本作只有 0 / 2")
    if int(combo["total_rounds"]) <= 0:
        raise ValueError("total_rounds 必須為正整數")
    if float(combo["base_bet"]) <= 0:
        raise ValueError("base_bet 必須大於 0")
    return combo


def format_board(symbols: list[list[int]], mults: list[list[int]] | None = None) -> str:
    names = CFG["symbol_names"]
    lines = []
    for row in range(4):
        cells = []
        for reel in range(5):
            text = names[str(symbols[reel][row])]
            if mults and mults[reel][row]:
                text += f"x{mults[reel][row]}"
            cells.append(f"{text:>7}")
        lines.append(" ".join(cells))
    return "\n".join(lines)


def run_single_spin_debug() -> None:
    engine = CalaveraParty(CFG, CFG_RTP or None, RNG_SEED, 1.0, False, False)
    for index in range(DEBUG_ROUNDS):
        result = engine.round(MODE_NORMALBET)
        print(f"--- debug round {index + 1} ---")
        print(f"pay_bg={result.pay_bg:.4f} pay_fg={result.pay_fg:.4f} "
              f"cascades_bg={result.cascades_bg} fg_spins={result.fg_spins} "
              f"yellow_used={result.bg_yellow_used + result.fg_yellow_used} max_mult={result.max_mult} "
              f"fg_end_frame={result.fg_end_frame} capped={result.capped}")


def run_batch(combo: dict[str, Any], index: int, total: int) -> None:
    validate_batch_run(combo)
    load_batch_configs(combo)
    print(f"=== Batch {index}/{total}: {combo} ===")
    card_enabled = bool(combo["card_system_enabled"]) and bool(CFG_RTP)
    bundle = run_simulation(int(combo["total_rounds"]), int(combo["bet_mode"]),
                            float(combo["base_bet"]), THREADS,
                            card_enabled, bool(combo["card_system_is_newbie"]))
    result = build_result(bundle, combo)
    if SHOW_CONSOLE_SUMMARY:
        print_console(result)
    if OUTPUT_REPORT:
        path = output_report(result)
        print(f"report -> {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H032 亡靈派對 simulator")
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--bet-mode", type=int, default=None)
    parser.add_argument("--base-bet", type=float, default=None)
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--no-report", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--card-on", action="store_true", help="Card System On（需 config_rtp_file）")
    parser.add_argument("--card-off", action="store_true", help="Card System Off")
    parser.add_argument("--newbie", action="store_true", help="Profile 改為 Newbie")
    parser.add_argument("--config-rtp", default=None, help="覆寫 config_rtp_file，例如 config_92A.js")
    parser.add_argument("--config", default=None, help="覆寫 config_file（調參試驗用）")
    parser.add_argument("--seed", type=int, default=None, help="覆寫 RNG_SEED（複驗用不同種子）")
    parser.add_argument("--series", choices=["A", "B"], default=None, help="AUTO 選組用 A／B 版")
    return parser.parse_args()


def main() -> None:
    global RNG_SEED, RTP_SERIES
    global THREADS, OUTPUT_REPORT
    args = parse_args()
    if args.seed is not None:
        RNG_SEED = args.seed
    if args.series:
        RTP_SERIES = args.series
    if args.threads:
        THREADS = max(1, args.threads)
    if args.no_report:
        OUTPUT_REPORT = False

    runs = [dict(run) for run in BATCH_RUNS] if RUN_ALL_COMBINATIONS else [{
        "config_file": CONFIG_FILE, "config_rtp_file": CONFIG_RTP_FILE,
        "bet_mode": BET_MODE, "total_rounds": TOTAL_ROUNDS,
        "card_system_enabled": CARD_SYSTEM_ENABLED,
        "card_system_is_newbie": CARD_SYSTEM_IS_NEWBIE,
        "base_bet": BASE_BET_SETTING,
    }]
    for run in runs:
        if args.rounds:
            run["total_rounds"] = args.rounds
        if args.bet_mode is not None:
            run["bet_mode"] = args.bet_mode
        if args.base_bet:
            run["base_bet"] = args.base_bet
        if args.card_on:
            run["card_system_enabled"] = True
        if args.card_off:
            run["card_system_enabled"] = False
        if args.newbie:
            run["card_system_is_newbie"] = True
        if args.config_rtp:
            run["config_rtp_file"] = args.config_rtp
        if args.config:
            run["config_file"] = args.config

    if args.debug or RUN_SINGLE_SPIN_DEBUG:
        load_batch_configs(runs[0])
        run_single_spin_debug()
        return

    for index, run in enumerate(runs, start=1):
        run_batch(run, index, len(runs))


if __name__ == "__main__":
    main()
