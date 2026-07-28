"""老手救援 C 模擬器。

目前使用固定自然遊戲 Row Data：

* 可切換超級寶石與彩罐熱舞的 1000 人 × 1000 轉固定 CSV.GZ 資料。
* 超級寶石沒有自然 FG；彩罐熱舞由 BG Free Game 卡觸發後另抽 FG 卡。
* 前 200 轉套用新手體驗 D，第 50／150 轉依累積 RTP 改寫得分。
* 救援固定為 FG，倍率直接落在指定 Tier 區間。
* 遊戲層透過 GameAdapter 隔離。

老手 A、B、C 各自在 100 轉區間內隨機安排 2 次判定；
老手 D 自第 501 轉起，每 100 轉區間重新隨機安排 2 次判定。
同一區間若已觸發救援，剩餘判定取消。

範例：

    python simulator_system.py --players 1000 --spins 1000
    python simulator_system.py --players 100 --spins 1000
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
        if file_path.name == "simulator_system.py":
            candidates.append(file_path.parent)
    except NameError:
        pass

    current = Path.cwd().resolve()
    for base in (current, *current.parents):
        candidates.extend((base / "Project_AI" / "System", base / "System", base))

    for candidate in candidates:
        if (candidate / "simulator_system.py").is_file():
            return candidate.resolve()

    raise FileNotFoundError("無法定位 Project_AI/System/simulator_system.py；" "請先將 Jupyter 工作目錄切到 2_Program")


SCRIPT_DIR = _locate_script_dir()
DEFAULT_REPORT_DIR = SCRIPT_DIR / "Record"
BASE_GAME_DATA = {
    "超級寶石": SCRIPT_DIR / "Data" / "超級寶石_基礎遊戲_1000人_1000轉.csv.gz",
    "彩罐熱舞": SCRIPT_DIR / "Data" / "彩罐熱舞_基礎遊戲_1000人_1000轉.csv.gz",
}
DEFAULT_BASE_GAME = "超級寶石"
SYSTEM_VERSION = "b06c.4"

SUMMARY_FIELD_INFO = {
    "game": ("遊戲模型", "模擬器使用的遊戲資料模型。"),
    "base_game": ("基礎遊戲", "本次使用的固定逐轉資料遊戲。"),
    "system_version": ("系統版本", "老手救援系統版本。"),
    "base_data": ("基礎資料路徑", "固定自然遊戲逐轉資料的檔案路徑。"),
    "base_data_players": ("基礎資料玩家數", "固定資料包含的玩家總數。"),
    "base_data_spins_per_player": ("每位玩家基礎轉數", "固定資料中每位玩家的轉數。"),
    "base_data_rows": ("基礎資料總筆數", "固定逐轉資料的資料列總數。"),
    "base_data_rtp_%": ("基礎資料 RTP", "整份固定資料的自然 RTP。"),
    "base_data_natural_fg_count": ("基礎資料自然 FG 次數", "整份固定資料中的自然 FG 次數。"),
    "natural_multiplier_model": ("自然倍率模型", "自然倍率的來源方式，目前讀取固定逐轉資料。"),
    "fixed_weight_total": ("固定權重總和", "超級寶石倍率線型的權重總和。"),
    "fixed_weight_expected_rtp_%": ("固定權重理論 RTP", "超級寶石倍率線型計算出的理論 RTP。"),
    "rescue_result": ("救援結果方式", "老手救援獎勵倍率的產生方式。"),
    "players": ("模擬玩家數", "本次實際模擬的玩家數。"),
    "spins_per_player": ("每位玩家模擬轉數", "本次每位玩家執行的付費轉數。"),
    "total_paid_spins": ("付費轉數總計", "玩家數乘以每位玩家轉數。"),
    "checks_per_100_spin_block": ("每百轉預定判定次數", "每個 100 轉區間預定安排的判定點數。"),
    "scheduled_checkpoint_count": ("預定判定點總數", "所有玩家原先安排的判定點總數。"),
    "checkpoint_count": ("實際判定次數", "扣除取消後實際執行規則判斷的次數。"),
    "cancelled_checkpoint_count": ("取消判定次數", "同區間已觸發救援而取消的剩餘判定數。"),
    "rescue_trigger_count": ("老手 C 觸發次數", "老手 C 救援的觸發總次數。"),
    "rescue_trigger_rate_per_checkpoint_%": ("判定點救援觸發率", "老手 C 觸發次數占實際判定次數的比例。"),
    "players_with_rescue": ("使用老手救援玩家數", "至少觸發一次老手 C 的玩家數。"),
    "players_with_any_mechanism": ("使用任一機制玩家數", "至少觸發一次新手 D 或老手 C 的玩家數。"),
    "player_any_mechanism_rate_%": ("任一機制玩家比例", "使用過新手 D 或老手 C 的玩家比例。"),
    "players_with_newbie_d": ("使用新手 D 玩家數", "至少觸發一次新手 D 的玩家數。"),
    "player_newbie_d_rate_%": ("新手 D 玩家比例", "觸發新手 D 的玩家比例。"),
    "players_with_oldhand_c": ("使用老手 C 玩家數", "至少觸發一次老手 C 的玩家數。"),
    "player_oldhand_c_rate_%": ("老手 C 玩家比例", "觸發老手 C 的玩家比例。"),
    "natural_rtp_%": ("自然 RTP", "完全沒有新手 D 與老手 C 時的 RTP。"),
    "newbie_d_rtp_%": ("新手 D 後 RTP", "只套用新手 D 後的 RTP。"),
    "newbie_d_rtp_delta_pp": ("新手 D RTP 增量", "新手 D 相對自然 RTP 增加的百分點。"),
    "newbie_d_trigger_count": ("新手 D 觸發次數", "新手 D 的觸發總次數。"),
    "rescue_rtp_%": ("最終救援後 RTP", "新手 D 與老手 C 全部套用後的最終 RTP。"),
    "oldhand_c_rtp_delta_pp": ("老手 C RTP 增量", "老手 C 相對新手 D 後 RTP 增加的百分點。"),
    "rtp_delta_pp": ("總 RTP 增量", "最終 RTP 相對自然 RTP 增加的總百分點。"),
    "natural_fg_count": ("本次自然 FG 次數", "本次模擬範圍內固定逐轉資料的自然 FG 次數。"),
    "actual_fg_count": ("本次實際 FG 總數", "自然 FG 加上老手救援 FG 後的實際 FG 次數。"),
    "duration_sec": ("執行時間（秒）", "本次模擬所需時間。"),
    "seed": ("亂數種子", "判定點與救援倍率使用的固定亂數種子。"),
}

REPORT_COLUMN_NAMES = {
    "Stage": "階段",
    "Spin_Range": "轉數區間",
    "Short_RTP_Threshold_%": "短期RTP門檻(%)",
    "Mid_RTP_Threshold_%": "中期RTP門檻(%)",
    "Scheduled_Checkpoint_Count": "預定判定點數",
    "Evaluated_Checkpoint_Count": "實際判定次數",
    "Cancelled_Checkpoint_Count": "取消判定次數",
    "Trigger_Count": "觸發次數",
    "Trigger_Rate_%": "觸發率(%)",
    "Tier": "獎項級別",
    "Low_X": "最低倍率",
    "High_X": "最高倍率",
    "Share_of_Triggers_%": "觸發占比(%)",
    "Rule_ID": "規則",
    "Description": "說明",
    "Count": "次數",
    "Scope": "範圍",
    "Mechanism": "機制",
    "Players_Used_Rescue": "使用救援玩家數",
    "Total_Players": "總玩家數",
    "Player_Usage_Rate_%": "玩家使用率(%)",
    "Players_With_FG_有機制": "有機制遇到FG或機制玩家數",
    "Avg_Exit_Spin_有機制": "有機制平均離開轉數",
    "RTP_有機制遇到FG就走_%": "有機制遇到FG或機制就走RTP(%)",
    "Players_With_FG_無機制": "無機制遇到FG玩家數",
    "Avg_Exit_Spin_無機制": "無機制平均離開轉數",
    "RTP_無機制遇到FG就走_%": "無機制遇到FG就走RTP(%)",
    "RTP_完整階段_%": "完整階段RTP(%)",
    "Player": "玩家",
    "Spin": "轉數",
    "RTP_Before_%": "判定前RTP(%)",
    "Triggered": "是否觸發",
    "Natural_X": "自然倍率",
    "Newbie_D_X": "新手D倍率",
    "Delta_X": "倍率差",
    "Natural_FG": "是否自然FG",
    "Block": "判定區間",
    "Status": "狀態",
    "Short_Threshold_%": "短期門檻(%)",
    "Mid_Threshold_%": "中期門檻(%)",
    "Short_RTP_%": "短期RTP(%)",
    "Mid_RTP_%": "中期RTP(%)",
    "Long_RTP_%": "長期RTP(%)",
    "No_FG_Spins": "連續未進FG轉數",
    "Short_Bad": "短期是否符合",
    "Mid_Bad": "中期是否符合",
    "Long_Bad": "長期是否符合",
    "Display_Range": "顯示區間",
    "Actual_Spin_Range": "實際轉數區間",
    "Rule": "規則說明",
    "Rescue_FG_X": "救援FG倍率",
    "Stop_After_Rescue_Block_RTP_%": "救援後區間RTP(%)",
    "Stop_After_Rescue_Cumulative_RTP_%": "救援後累積RTP(%)",
    "Spins": "總轉數",
    "Natural_RTP_%": "自然RTP(%)",
    "Newbie_D_RTP_%": "新手D後RTP(%)",
    "Rescue_RTP_%": "最終救援後RTP(%)",
    "Newbie_D_Delta_pp": "新手D增量(百分點)",
    "Oldhand_C_Delta_pp": "老手C增量(百分點)",
    "RTP_Delta_pp": "總增量(百分點)",
    "Newbie_D_Trigger_Count": "新手D觸發次數",
    "Lower": "區間下限",
    "Upper": "區間上限",
    "Fixed Weight": "固定權重",
    "Probability_%": "抽中率(%)",
    "Multi_X": "平均倍率",
    "RTP_Contribution_%": "RTP貢獻(%)",
}

RULE_NAMES_ZH = {
    "AC_COMBINED": "A～C：短期＋中期＋未進FG",
    "AC_NO_FG": "A～C：短期＋未進FG",
    "AC_MID_RTP": "A～C：短期＋中期",
    "D_COMBINED": "D：短期＋中期＋未進FG＋長期",
    "D_MID_LONG": "D：短期＋中期＋長期",
    "D_NO_FG_LONG": "D：短期＋未進FG＋長期",
    "D_NO_LONG_WINDOW": "D：長期資料不足",
    "NO_RESCUE": "不救援",
    "D1_RTP_LT_50": "第一次：RTP低於50%",
    "D1_RTP_50_70": "第一次：RTP為50%～70%",
    "D1_RTP_70_100": "第一次：RTP為70%～100%",
    "D1_NO_RESCUE": "第一次：不介入",
    "D2_RTP_LT_65": "第二次：RTP低於65%",
    "D2_RTP_65_85": "第二次：RTP為65%～85%",
    "D2_NO_RESCUE": "第二次：不介入",
}

SUMMARY_VALUE_NAMES_ZH = {
    "FIXED_ROW_DATA": "固定逐轉資料",
    "fixed-row-data": "固定逐轉資料",
    "Tier 區間內均勻抽樣 FG": "獎項倍率區間內均勻抽樣 FG",
}

BOOLEAN_REPORT_COLUMNS = {
    "Triggered",
    "Natural_FG",
    "Short_Bad",
    "Mid_Bad",
    "Long_Bad",
    "Rescue_Triggered",
}

NEWBIE_LAST_SPIN = 200

WINDOW_SHORT = 50
WINDOW_MID = 200
WINDOW_LONG = 500
NO_FG_LIMIT = 100
CHECKS_PER_BLOCK = 2
SHORT_RTP_THRESHOLD = 0.40

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

    @property
    def short_bad(self) -> bool:
        return self.short_rtp < SHORT_RTP_THRESHOLD


@dataclass(frozen=True)
class NewbieDDecision:
    spin: int
    rtp: float
    rule: str
    reward_multiplier: float | None

    @property
    def triggered(self) -> bool:
        return self.reward_multiplier is not None


class GameAdapter(ABC):
    """遊戲模擬介面；救援規則只依賴這個介面。"""

    game_key: str

    @abstractmethod
    def natural_spin(self, is_newbie: bool) -> SpinOutcome:
        """產生一個自然付費 Spin（含完整 FG 結果）。"""

    def start_player(self, player_id: int) -> None:
        """切換至指定玩家；固定 Row Data Adapter 會重設該玩家的 Spin 游標。"""

    @abstractmethod
    def rescue_fg(self, tier: str) -> SpinOutcome:
        """產生符合指定 Tier 的 FG 救援結果。"""

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        """回傳報表用遊戲設定。"""

    def multiplier_curve_rows(self) -> list[dict[str, Any]]:
        return []


class FixedRowDataAdapter(GameAdapter):
    game_key = "FIXED_ROW_DATA"

    def __init__(self, seed: int, base_data: str, base_game: str):
        self.seed = int(seed)
        self.base_game = base_game
        self.rng = np.random.default_rng(self.seed)
        self.base_data_path = Path(base_data).resolve()
        if not self.base_data_path.is_file():
            raise FileNotFoundError(f"找不到固定 Row Data：{self.base_data_path}")

        required = ["Player", "Spin", "Bet", "Natural_Multiplier", "Natural_Payout", "Natural_FG"]
        if self.base_data_path.name.lower().endswith((".csv", ".csv.gz")):
            frame = pd.read_csv(
                self.base_data_path,
                usecols=required,
                dtype={
                    "Player": np.int16,
                    "Spin": np.int16,
                    "Bet": np.float32,
                    "Natural_Multiplier": np.float32,
                    "Natural_Payout": np.float32,
                    "Natural_FG": bool,
                },
            )
        else:
            try:
                frame = pd.read_parquet(self.base_data_path, columns=required)
            except ImportError as exc:
                fallback_path = self.base_data_path.with_suffix(".csv.gz")
                if not fallback_path.is_file():
                    raise ImportError("目前 Jupyter 沒有 Parquet 引擎，且找不到 CSV.GZ 備援資料：" f"{fallback_path}") from exc
                self.base_data_path = fallback_path
                frame = pd.read_csv(fallback_path, usecols=required)
        frame = frame.sort_values(["Player", "Spin"], kind="stable").reset_index(drop=True)
        self.data_players = int(frame["Player"].max())
        self.data_spins = int(frame["Spin"].max())
        expected_rows = self.data_players * self.data_spins
        if len(frame) != expected_rows:
            raise ValueError(f"固定 Row Data 不是完整矩形：預期 {expected_rows:,} 筆，實際 {len(frame):,} 筆")
        expected_players = np.repeat(np.arange(1, self.data_players + 1), self.data_spins)
        expected_spins = np.tile(np.arange(1, self.data_spins + 1), self.data_players)
        if not np.array_equal(frame["Player"].to_numpy(), expected_players):
            raise ValueError("固定 Row Data 的 Player 必須從 1 連續編號")
        if not np.array_equal(frame["Spin"].to_numpy(), expected_spins):
            raise ValueError("固定 Row Data 每位玩家的 Spin 必須從 1 連續編號")
        if not np.allclose(frame["Bet"].to_numpy(dtype=np.float64), 1.0):
            raise ValueError("目前模擬器要求固定 Row Data 每轉 Bet 為 1")

        self._natural_multiplier = frame["Natural_Multiplier"].to_numpy(dtype=np.float64).reshape(self.data_players, self.data_spins)
        self._natural_fg = frame["Natural_FG"].to_numpy(dtype=bool).reshape(self.data_players, self.data_spins)
        self._base_rtp = float(frame["Natural_Payout"].sum() / frame["Bet"].sum())
        self._base_fg_count = int(frame["Natural_FG"].sum())
        self._player_index = -1
        self._spin_index = 0

        curve = np.asarray(FIXED_WEIGHT_MULTIPLIER_CURVE, dtype=np.float64)
        curve_weights = curve[:, 2]
        self._curve_multiplier = curve[:, 3]
        self._curve_total_weight = int(curve_weights.sum())
        self._curve_expected_rtp = float(np.sum(self._curve_multiplier * curve_weights) / curve_weights.sum())

    def start_player(self, player_id: int) -> None:
        if not 1 <= player_id <= self.data_players:
            raise ValueError(f"固定 Row Data 只有 {self.data_players:,} 位玩家，無法執行 Player {player_id}")
        self._player_index = player_id - 1
        self._spin_index = 0

    def natural_spin(self, is_newbie: bool) -> SpinOutcome:
        del is_newbie
        if self._player_index < 0:
            raise RuntimeError("讀取自然結果前必須先呼叫 start_player")
        if self._spin_index >= self.data_spins:
            raise ValueError(f"固定 Row Data 每位玩家只有 {self.data_spins:,} 轉")
        multiplier = float(self._natural_multiplier[self._player_index, self._spin_index])
        triggered_fg = bool(self._natural_fg[self._player_index, self._spin_index])
        self._spin_index += 1
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
        metadata = {
            "game": self.game_key,
            "base_game": self.base_game,
            "system_version": SYSTEM_VERSION,
            "base_data": str(self.base_data_path),
            "base_data_players": self.data_players,
            "base_data_spins_per_player": self.data_spins,
            "base_data_rows": self.data_players * self.data_spins,
            "base_data_rtp_%": self._base_rtp * 100.0,
            "base_data_natural_fg_count": self._base_fg_count,
            "natural_multiplier_model": "fixed-row-data",
            "rescue_result": "Tier 區間內均勻抽樣 FG",
        }
        if self.base_game == "超級寶石":
            metadata["fixed_weight_total"] = self._curve_total_weight
            metadata["fixed_weight_expected_rtp_%"] = self._curve_expected_rtp * 100.0
        return metadata

    def multiplier_curve_rows(self) -> list[dict[str, Any]]:
        if self.base_game != "超級寶石":
            return []
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


def _create_fixed_row_data(args: argparse.Namespace) -> GameAdapter:
    base_data = args.base_data or str(BASE_GAME_DATA[args.base_game])
    return FixedRowDataAdapter(
        seed=args.seed,
        base_data=base_data,
        base_game=args.base_game,
    )


GAME_ADAPTERS: dict[str, GameFactory] = {
    "FIXED_ROW_DATA": _create_fixed_row_data,
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


def _oldhand_blocks(total_spins: int) -> list[tuple[str, int, int, str, str]]:
    """回傳（階段、實際起轉、迄轉、區間 ID、企劃顯示區間）。"""

    blocks: list[tuple[str, int, int, str, str]] = [
        ("A", 201, 300, "A_201_300", "200～300"),
        ("B", 301, 400, "B_301_400", "300～400"),
        ("C", 401, 500, "C_401_500", "400～500"),
    ]
    for start in range(501, total_spins + 1, 100):
        end = start + 99
        blocks.append(("D", start, end, f"D_{start}_{end}", f"{start - 1}～{end}"))
    return blocks


def _reporting_blocks(total_spins: int) -> list[tuple[str, int, int, str, str]]:
    blocks: list[tuple[str, int, int, str, str]] = [
        ("新手 D", 1, 100, "NEWBIE_1_100", "0～100"),
        ("新手 D", 101, 200, "NEWBIE_101_200", "100～200"),
    ]
    blocks.extend(_oldhand_blocks(total_spins))
    return [block for block in blocks if block[2] <= total_spins]


def _random_checkpoints(total_spins: int, player_id: int, seed: int) -> dict[int, tuple[str, str]]:
    """每個完整 100 轉區間隨機選 2 個不重複的判定點。"""

    rng = np.random.default_rng(np.random.SeedSequence([seed, player_id, 0xC]))

    checkpoints: dict[int, tuple[str, str]] = {}
    for stage, start, end, block_id, _ in _oldhand_blocks(total_spins):
        selected = rng.choice(
            np.arange(start, end + 1),
            size=CHECKS_PER_BLOCK,
            replace=False,
        )
        for spin_no in sorted(int(value) for value in selected):
            if spin_no <= total_spins:
                checkpoints[spin_no] = (stage, block_id)
    return checkpoints


def _window_rtp(history: list[float], size: int) -> float | None:
    if len(history) < size:
        return None
    # 每轉押注固定為 1 單位，因此前 N 轉 RTP =
    # 前 N 轉總派彩 ÷ 前 N 轉總押注（N），不是另抽一個倍率指標。
    return float(sum(history[-size:]) / size)


def decide_newbie_d(history: list[float], spin_no: int) -> NewbieDDecision | None:
    """新手 D：使用判定回合之前的累積 RTP 覆蓋第 50／150 轉得分。"""

    if spin_no not in (50, 150):
        return None
    if not history:
        raise ValueError("新手 D 判定前沒有歷史資料")

    rtp = float(sum(history) / len(history))
    if spin_no == 50:
        if rtp < 0.50:
            return NewbieDDecision(spin_no, rtp, "D1_RTP_LT_50", 15.0)
        if rtp < 0.70:
            return NewbieDDecision(spin_no, rtp, "D1_RTP_50_70", 10.0)
        if rtp < 1.00:
            return NewbieDDecision(spin_no, rtp, "D1_RTP_70_100", 0.0)
        return NewbieDDecision(spin_no, rtp, "D1_NO_RESCUE", None)

    if rtp < 0.65:
        return NewbieDDecision(spin_no, rtp, "D2_RTP_LT_65", 30.0)
    if rtp < 0.85:
        return NewbieDDecision(spin_no, rtp, "D2_RTP_65_85", 15.0)
    return NewbieDDecision(spin_no, rtp, "D2_NO_RESCUE", None)


def decide_rescue(history: list[float], no_fg_spins: int, stage: str) -> RescueDecision:
    short_rtp = _window_rtp(history, WINDOW_SHORT)
    mid_rtp = _window_rtp(history, WINDOW_MID)
    long_rtp = _window_rtp(history, WINDOW_LONG)
    if short_rtp is None or mid_rtp is None:
        raise ValueError("救援判定前沒有足夠的短期／中期資料")

    no_fg_bad = no_fg_spins > NO_FG_LIMIT
    short_bad = short_rtp < SHORT_RTP_THRESHOLD
    mid_bad = mid_rtp < STAGE_MID_RTP[stage]
    long_bad: bool | None = None if long_rtp is None else long_rtp < 1.0

    if stage in {"A", "B", "C"}:
        if short_bad and mid_bad and no_fg_bad:
            return RescueDecision(stage, "AC_COMBINED", "短期 RTP < 40%、中期 RTP 低於門檻且超過 100 轉未進 FG", "T2", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
        if short_bad and no_fg_bad:
            return RescueDecision(stage, "AC_NO_FG", "短期 RTP < 40% 且超過 100 轉未進 FG", "T5", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
        if short_bad and mid_bad:
            return RescueDecision(stage, "AC_MID_RTP", "短期 RTP < 40% 且中期 RTP 低於階段門檻", "T5", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
        return RescueDecision(stage, "NO_RESCUE", "未符合救援條件", None, short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)

    if long_rtp is None:
        return RescueDecision(stage, "D_NO_LONG_WINDOW", "長期資料尚未滿 500 轉", None, short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    if short_bad and mid_bad and no_fg_bad and bool(long_bad):
        return RescueDecision(stage, "D_COMBINED", "短期 RTP < 40%，且中期 RTP、未進 FG 與長期 RTP 皆符合", "T1", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    if short_bad and mid_bad and bool(long_bad):
        return RescueDecision(stage, "D_MID_LONG", "短期 RTP < 40%，且中期 RTP 與長期 RTP 符合", "T3", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    if short_bad and no_fg_bad and bool(long_bad):
        return RescueDecision(stage, "D_NO_FG_LONG", "短期 RTP < 40%，且未進 FG 與長期 RTP 符合", "T6", short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)
    return RescueDecision(stage, "NO_RESCUE", "未符合救援條件", None, short_rtp, mid_rtp, long_rtp, no_fg_spins, mid_bad, long_bad)


def _pct(value: float | None) -> float | None:
    return None if value is None else value * 100.0


def run_simulation(args: argparse.Namespace, adapter: GameAdapter) -> dict[str, Any]:
    started = time.perf_counter()
    checkpoints: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    newbie_d_rows: list[dict[str, Any]] = []
    stop_after_rescue_rows: list[dict[str, Any]] = []
    fg_exit_rows: list[dict[str, Any]] = []
    completed_stage_rows: list[dict[str, Any]] = []
    players: list[dict[str, Any]] = []
    block_definitions = _oldhand_blocks(args.spins)
    reporting_blocks = _reporting_blocks(args.spins)
    block_by_id = {block_id: (stage, start, end, display_range) for stage, start, end, block_id, display_range in block_definitions}
    block_by_end = {end: (stage, start, block_id, display_range) for stage, start, end, block_id, display_range in reporting_blocks if end <= args.spins}
    reporting_block_by_spin = {spin: (stage, block_id, display_range) for stage, start, end, block_id, display_range in reporting_blocks for spin in range(start, end + 1)}

    stage_scheduled_counts: Counter[str] = Counter()
    stage_check_counts: Counter[str] = Counter()
    stage_cancelled_counts: Counter[str] = Counter()
    stage_trigger_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    newbie_d_rule_counts: Counter[str] = Counter()

    natural_win_total = 0.0
    newbie_d_win_total = 0.0
    actual_win_total = 0.0
    natural_fg_total = 0
    actual_fg_total = 0

    for player_id in range(1, args.players + 1):
        adapter.start_player(player_id)
        history: list[float] = []
        no_fg_spins = 0
        player_natural_total = 0.0
        player_newbie_d_total = 0.0
        player_actual_total = 0.0
        player_trigger_counts: Counter[str] = Counter()
        player_newbie_d_trigger_count = 0
        scheduled_checkpoints = _random_checkpoints(args.spins, player_id, args.seed)
        triggered_blocks: set[str] = set()
        actual_fg_exit_blocks: set[str] = set()
        natural_fg_exit_blocks: set[str] = set()
        player_block_triggers: dict[str, dict[str, Any]] = {}

        for spin_no in range(1, args.spins + 1):
            natural = adapter.natural_spin(is_newbie=spin_no <= NEWBIE_LAST_SPIN)
            player_natural_total += natural.multiplier
            natural_win_total += natural.multiplier
            natural_fg_total += int(natural.triggered_fg)

            after_newbie_d = natural
            newbie_d_decision = decide_newbie_d(history, spin_no)
            if newbie_d_decision is not None:
                newbie_d_rule_counts[newbie_d_decision.rule] += 1
                if newbie_d_decision.triggered:
                    after_newbie_d = SpinOutcome(
                        multiplier=float(newbie_d_decision.reward_multiplier),
                        triggered_fg=natural.triggered_fg,
                    )
                    player_newbie_d_trigger_count += 1
                    newbie_block_id = "NEWBIE_1_100" if spin_no == 50 else "NEWBIE_101_200"
                    newbie_display_range = "0～100" if spin_no == 50 else "100～200"
                    newbie_block_start = 1 if spin_no == 50 else 101
                    newbie_block_payout_through_trigger = sum(history[newbie_block_start - 1 :]) + after_newbie_d.multiplier
                    newbie_block_spins_through_trigger = spin_no - newbie_block_start + 1
                    newbie_block_rtp_after = newbie_block_payout_through_trigger / newbie_block_spins_through_trigger * 100.0
                    cumulative_rtp_after = (sum(history) + after_newbie_d.multiplier) / spin_no * 100.0
                    newbie_trigger_info = {
                        "Spin": spin_no,
                        "Tier": f"{after_newbie_d.multiplier:g}×",
                    }
                    player_block_triggers[newbie_block_id] = newbie_trigger_info
                    stop_after_rescue_rows.append(
                        {
                            "Player": player_id,
                            "Stage": "新手 D",
                            "Display_Range": newbie_display_range,
                            "Actual_Spin_Range": ("1～100" if spin_no == 50 else "101～200"),
                            "Trigger_Spin": spin_no,
                            "Tier": f"{after_newbie_d.multiplier:g}×",
                            "RTP_Before_Rescue_Mid_%": (newbie_d_decision.rtp * 100.0),
                            "Rescue_FG_X": after_newbie_d.multiplier,
                            "RTP_If_Stop_Block_%": newbie_block_rtp_after,
                            "RTP_If_Stop_Cumulative_%": cumulative_rtp_after,
                            "RTP_If_Stop_Natural_Cumulative_%": (player_natural_total / spin_no * 100.0),
                        }
                    )
                newbie_d_rows.append(
                    {
                        "Player": player_id,
                        "Spin": spin_no,
                        "RTP_Before_%": newbie_d_decision.rtp * 100.0,
                        "Rule_ID": newbie_d_decision.rule,
                        "Triggered": newbie_d_decision.triggered,
                        "Natural_X": natural.multiplier,
                        "Newbie_D_X": after_newbie_d.multiplier,
                        "Delta_X": after_newbie_d.multiplier - natural.multiplier,
                        "Natural_FG": natural.triggered_fg,
                    }
                )
            player_newbie_d_total += after_newbie_d.multiplier
            newbie_d_win_total += after_newbie_d.multiplier

            stage = get_stage(spin_no)
            decision: RescueDecision | None = None
            block_id = ""
            checkpoint = scheduled_checkpoints.get(spin_no)
            if checkpoint is not None:
                checkpoint_stage, block_id = checkpoint
                stage_scheduled_counts[checkpoint_stage] += 1
                if block_id in triggered_blocks:
                    stage_cancelled_counts[checkpoint_stage] += 1
                    checkpoints.append(
                        {
                            "Player": player_id,
                            "Spin": spin_no,
                            "Stage": checkpoint_stage,
                            "Block": block_id,
                            "Status": "同區間已觸發，取消判定",
                            "Triggered": False,
                        }
                    )
                else:
                    stage = checkpoint_stage
                    decision = decide_rescue(history, no_fg_spins, stage)
                    stage_check_counts[stage] += 1
                    rule_counts[decision.rule_id] += 1

            actual = after_newbie_d
            if decision is not None and decision.triggered:
                actual = adapter.rescue_fg(decision.tier or "")
                stage_trigger_counts[stage or ""] += 1
                tier_counts[decision.tier or ""] += 1
                player_trigger_counts[decision.tier or ""] += 1
                triggered_blocks.add(block_id)
                _, block_start, block_end, display_range = block_by_id[block_id]
                block_payout_through_trigger = sum(history[block_start - 1 :]) + actual.multiplier
                block_spins_through_trigger = spin_no - block_start + 1
                cumulative_payout_through_trigger = sum(history) + actual.multiplier
                trigger_row = {
                    "Player": player_id,
                    "Spin": spin_no,
                    "Stage": stage,
                    "Block": block_id,
                    "Display_Range": display_range,
                    "Actual_Spin_Range": f"{block_start}～{block_end}",
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
                    "Stop_After_Rescue_Block_RTP_%": (block_payout_through_trigger / block_spins_through_trigger * 100.0),
                    "Stop_After_Rescue_Cumulative_RTP_%": (cumulative_payout_through_trigger / spin_no * 100.0),
                }
                triggers.append(trigger_row)
                player_block_triggers[block_id] = trigger_row
                stop_after_rescue_rows.append(
                    {
                        "Player": player_id,
                        "Stage": stage,
                        "Display_Range": display_range,
                        "Actual_Spin_Range": f"{block_start}～{block_end}",
                        "Trigger_Spin": spin_no,
                        "Tier": decision.tier,
                        "RTP_Before_Rescue_Mid_%": _pct(decision.mid_rtp),
                        "Rescue_FG_X": actual.multiplier,
                        "RTP_If_Stop_Block_%": (block_payout_through_trigger / block_spins_through_trigger * 100.0),
                        "RTP_If_Stop_Cumulative_%": (cumulative_payout_through_trigger / spin_no * 100.0),
                        "RTP_If_Stop_Natural_Cumulative_%": (player_natural_total / spin_no * 100.0),
                    }
                )

            if decision is not None:
                checkpoints.append(
                    {
                        "Player": player_id,
                        "Spin": spin_no,
                        "Stage": stage,
                        "Block": block_id,
                        "Status": "已判定",
                        "Short_Threshold_%": SHORT_RTP_THRESHOLD * 100.0,
                        "Mid_Threshold_%": STAGE_MID_RTP[stage or ""] * 100.0,
                        "Short_RTP_%": _pct(decision.short_rtp),
                        "Mid_RTP_%": _pct(decision.mid_rtp),
                        "Long_RTP_%": _pct(decision.long_rtp),
                        "No_FG_Spins": decision.no_fg_spins,
                        "Short_Bad": decision.short_bad,
                        "Mid_Bad": decision.mid_bad,
                        "Long_Bad": decision.long_bad,
                        "Rule_ID": decision.rule_id,
                        "Tier": decision.tier or "",
                        "Triggered": decision.triggered,
                    }
                )

            reporting_block = reporting_block_by_spin.get(spin_no)
            if reporting_block is not None:
                block_stage, reporting_block_id, display_range = reporting_block
                mechanism_triggered = (
                    newbie_d_decision is not None
                    and newbie_d_decision.triggered
                ) or (decision is not None and decision.triggered)
                if (
                    (actual.triggered_fg or mechanism_triggered)
                    and reporting_block_id not in actual_fg_exit_blocks
                ):
                    actual_fg_exit_blocks.add(reporting_block_id)
                    fg_exit_rows.append(
                        {
                            "Player": player_id,
                            "Stage": block_stage,
                            "Display_Range": display_range,
                            "Scenario": "有機制",
                            "Exit_Spin": spin_no,
                            "Exit_RTP_%": ((player_actual_total + actual.multiplier) / spin_no * 100.0),
                        }
                    )
                if natural.triggered_fg and reporting_block_id not in natural_fg_exit_blocks:
                    natural_fg_exit_blocks.add(reporting_block_id)
                    fg_exit_rows.append(
                        {
                            "Player": player_id,
                            "Stage": block_stage,
                            "Display_Range": display_range,
                            "Scenario": "無機制",
                            "Exit_Spin": spin_no,
                            "Exit_RTP_%": player_natural_total / spin_no * 100.0,
                        }
                    )

            history.append(actual.multiplier)
            player_actual_total += actual.multiplier
            actual_win_total += actual.multiplier
            actual_fg_total += int(actual.triggered_fg)
            no_fg_spins = 0 if actual.triggered_fg else no_fg_spins + 1

            completed_block = block_by_end.get(spin_no)
            if completed_block is not None:
                block_stage, block_start, completed_block_id, display_range = completed_block
                trigger_info = player_block_triggers.get(completed_block_id)
                block_values = history[block_start - 1 : spin_no]
                completed_stage_rows.append(
                    {
                        "Player": player_id,
                        "Stage": block_stage,
                        "Display_Range": display_range,
                        "Actual_Spin_Range": f"{block_start}～{spin_no}",
                        "Completed_Spin": spin_no,
                        "Rescue_Triggered": trigger_info is not None,
                        "Trigger_Spin": (trigger_info["Spin"] if trigger_info is not None else ""),
                        "Tier": (trigger_info["Tier"] if trigger_info is not None else ""),
                        "Completed_Block_RTP_%": (sum(block_values) / len(block_values) * 100.0),
                        "Completed_Cumulative_RTP_%": (sum(history) / spin_no * 100.0),
                    }
                )

        player_row: dict[str, Any] = {
            "Player": player_id,
            "Spins": args.spins,
            "Natural_RTP_%": player_natural_total / args.spins * 100.0,
            "Newbie_D_RTP_%": player_newbie_d_total / args.spins * 100.0,
            "Rescue_RTP_%": player_actual_total / args.spins * 100.0,
            "Newbie_D_Delta_pp": (player_newbie_d_total - player_natural_total) / args.spins * 100.0,
            "Oldhand_C_Delta_pp": (player_actual_total - player_newbie_d_total) / args.spins * 100.0,
            "RTP_Delta_pp": (player_actual_total - player_natural_total) / args.spins * 100.0,
            "Newbie_D_Trigger_Count": player_newbie_d_trigger_count,
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

    newbie_d_players = {int(row["Player"]) for row in newbie_d_rows if bool(row["Triggered"])}
    oldhand_players = {int(row["Player"]) for row in triggers}
    any_mechanism_players = newbie_d_players | oldhand_players

    def usage_row(
        scope: str,
        mechanism: str,
        player_ids: set[int],
        actual_fg_count: int | None = None,
        actual_avg_exit_spin: float | None = None,
        actual_fg_stop_rtp: float | None = None,
        natural_fg_count: int | None = None,
        natural_avg_exit_spin: float | None = None,
        natural_fg_stop_rtp: float | None = None,
        completed_rtp: float | None = None,
    ) -> dict[str, Any]:
        count = len(player_ids)
        return {
            "Scope": scope,
            "Mechanism": mechanism,
            "Players_Used_Rescue": count,
            "Total_Players": args.players,
            "Player_Usage_Rate_%": count / args.players * 100.0,
            "Players_With_FG_有機制": actual_fg_count,
            "Avg_Exit_Spin_有機制": actual_avg_exit_spin,
            "RTP_有機制遇到FG就走_%": actual_fg_stop_rtp,
            "Players_With_FG_無機制": natural_fg_count,
            "Avg_Exit_Spin_無機制": natural_avg_exit_spin,
            "RTP_無機制遇到FG就走_%": natural_fg_stop_rtp,
            "RTP_完整階段_%": completed_rtp,
        }

    rescue_usage_rows = [
        usage_row("任一機制", "新手 D 或老手 C", any_mechanism_players),
        usage_row("新手期", "新手 D", newbie_d_players),
        usage_row("老手全期間", "老手 C", oldhand_players),
    ]
    for block_stage, _, _, _, display_range in reporting_blocks:
        block_stop_rows = [row for row in stop_after_rescue_rows if row["Display_Range"] == display_range]
        block_players = {int(row["Player"]) for row in block_stop_rows}
        actual_fg_rows = [row for row in fg_exit_rows if row["Display_Range"] == display_range and row["Scenario"] == "有機制"]
        natural_fg_rows = [row for row in fg_exit_rows if row["Display_Range"] == display_range and row["Scenario"] == "無機制"]
        block_completed_rows = [row for row in completed_stage_rows if row["Display_Range"] == display_range]
        actual_fg_stop_rtp = float(np.mean([float(row["Exit_RTP_%"]) for row in actual_fg_rows])) if actual_fg_rows else None
        actual_avg_exit_spin = float(np.mean([int(row["Exit_Spin"]) for row in actual_fg_rows])) if actual_fg_rows else None
        natural_fg_stop_rtp = float(np.mean([float(row["Exit_RTP_%"]) for row in natural_fg_rows])) if natural_fg_rows else None
        natural_avg_exit_spin = float(np.mean([int(row["Exit_Spin"]) for row in natural_fg_rows])) if natural_fg_rows else None
        completed_rtp = float(np.mean([float(row["Completed_Block_RTP_%"]) for row in block_completed_rows])) if block_completed_rows else None
        rescue_usage_rows.append(
            usage_row(
                display_range,
                "新手 D" if block_stage == "新手 D" else "老手 C",
                block_players,
                actual_fg_count=len(actual_fg_rows),
                actual_avg_exit_spin=actual_avg_exit_spin,
                actual_fg_stop_rtp=actual_fg_stop_rtp,
                natural_fg_count=len(natural_fg_rows),
                natural_avg_exit_spin=natural_avg_exit_spin,
                natural_fg_stop_rtp=natural_fg_stop_rtp,
                completed_rtp=completed_rtp,
            )
        )

    stage_rows = []
    for stage in ("A", "B", "C", "D"):
        checks = stage_check_counts[stage]
        trigger_count = stage_trigger_counts[stage]
        row: dict[str, Any] = {
            "Stage": stage,
            "Spin_Range": {"A": "201～300", "B": "301～400", "C": "401～500", "D": "501+"}[stage],
            "Short_RTP_Threshold_%": SHORT_RTP_THRESHOLD * 100.0,
            "Mid_RTP_Threshold_%": STAGE_MID_RTP[stage] * 100.0,
            "Scheduled_Checkpoint_Count": stage_scheduled_counts[stage],
            "Evaluated_Checkpoint_Count": checks,
            "Cancelled_Checkpoint_Count": stage_cancelled_counts[stage],
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
        "AC_COMBINED": "A～C：短期 RTP < 40%、中期 RTP 低於門檻且超過 100 轉未進 FG",
        "AC_NO_FG": "A～C：短期 RTP < 40% 且超過 100 轉未進 FG",
        "AC_MID_RTP": "A～C：短期 RTP < 40% 且中期 RTP 低於階段門檻",
        "D_COMBINED": "D：短期 RTP < 40%，且中期 RTP、未進 FG、長期 RTP 皆符合",
        "D_MID_LONG": "D：短期 RTP < 40%，且中期 RTP 與長期 RTP 符合",
        "D_NO_FG_LONG": "D：短期 RTP < 40%，且未進 FG 與長期 RTP 符合",
        "D_NO_LONG_WINDOW": "D：長期資料未滿 500 轉",
        "NO_RESCUE": "未符合救援條件",
    }
    rule_rows = [{"Rule_ID": rule_id, "Description": rule_descriptions.get(rule_id, rule_id), "Count": count} for rule_id, count in sorted(rule_counts.items())]

    summary = {
        **adapter.metadata(),
        "players": args.players,
        "spins_per_player": args.spins,
        "total_paid_spins": total_paid_spins,
        "checks_per_100_spin_block": CHECKS_PER_BLOCK,
        "scheduled_checkpoint_count": sum(stage_scheduled_counts.values()),
        "checkpoint_count": total_checks,
        "cancelled_checkpoint_count": sum(stage_cancelled_counts.values()),
        "rescue_trigger_count": total_triggers,
        "rescue_trigger_rate_per_checkpoint_%": (total_triggers / total_checks * 100.0) if total_checks else 0.0,
        "players_with_rescue": sum(1 for row in players if row["Trigger_Count"] > 0),
        "players_with_any_mechanism": len(any_mechanism_players),
        "player_any_mechanism_rate_%": len(any_mechanism_players) / args.players * 100.0,
        "players_with_newbie_d": len(newbie_d_players),
        "player_newbie_d_rate_%": len(newbie_d_players) / args.players * 100.0,
        "players_with_oldhand_c": len(oldhand_players),
        "player_oldhand_c_rate_%": len(oldhand_players) / args.players * 100.0,
        "natural_rtp_%": natural_win_total / total_paid_spins * 100.0,
        "newbie_d_rtp_%": newbie_d_win_total / total_paid_spins * 100.0,
        "newbie_d_rtp_delta_pp": (newbie_d_win_total - natural_win_total) / total_paid_spins * 100.0,
        "newbie_d_trigger_count": sum(count for rule, count in newbie_d_rule_counts.items() if "NO_RESCUE" not in rule),
        "rescue_rtp_%": actual_win_total / total_paid_spins * 100.0,
        "oldhand_c_rtp_delta_pp": (actual_win_total - newbie_d_win_total) / total_paid_spins * 100.0,
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
        "newbie_d_rows": newbie_d_rows,
        "newbie_d_rule_rows": [{"Rule_ID": rule, "Count": count} for rule, count in sorted(newbie_d_rule_counts.items())],
        "rescue_usage_rows": rescue_usage_rows,
        "stop_after_rescue_rows": stop_after_rescue_rows,
        "completed_stage_rows": completed_stage_rows,
        "player_rows": players,
        "multiplier_curve_rows": adapter.multiplier_curve_rows(),
    }


def _summary_frame(summary: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for key, value in summary.items():
        chinese_name, description = SUMMARY_FIELD_INFO.get(key, (key, "尚未設定中文說明。"))
        rows.append(
            {
                "項目": chinese_name,
                "數值": SUMMARY_VALUE_NAMES_ZH.get(value, value),
                "說明": description,
            }
        )
    return pd.DataFrame(rows)


def _safe_frame(rows: list[dict[str, Any]], columns: list[str] | None = None) -> pd.DataFrame:
    if rows:
        return pd.DataFrame(rows)
    return pd.DataFrame(columns=columns or [])


def _display_block_name(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value.startswith("NEWBIE_"):
        parts = value.split("_")
        if len(parts) == 3:
            return f"{parts[1]}～{parts[2]}"
    parts = value.split("_")
    if len(parts) == 3 and parts[0] in {"A", "B", "C", "D"}:
        return f"{parts[1]}～{parts[2]}"
    return value


def _yes_no(value: Any) -> Any:
    if value is None or value == "":
        return value
    if isinstance(value, (bool, np.bool_)):
        return "是" if bool(value) else "否"
    return value


def _localized_frame(
    rows: list[dict[str, Any]],
    columns: list[str] | None = None,
) -> pd.DataFrame:
    frame = _safe_frame(rows, columns)
    if "Rule_ID" in frame.columns:
        frame["Rule_ID"] = frame["Rule_ID"].map(lambda value: RULE_NAMES_ZH.get(value, value))
    if "Block" in frame.columns:
        frame["Block"] = frame["Block"].map(_display_block_name)
    for column in BOOLEAN_REPORT_COLUMNS.intersection(frame.columns):
        frame[column] = frame[column].map(_yes_no)
    return frame.rename(columns=REPORT_COLUMN_NAMES)


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
        _localized_frame(result["stage_rows"]).to_excel(writer, sheet_name="階段統計", index=False)
        _localized_frame(result["tier_rows"]).to_excel(writer, sheet_name="獎項統計", index=False)
        _localized_frame(result["rule_rows"]).to_excel(writer, sheet_name="規則統計", index=False)
        _localized_frame(result["rescue_usage_rows"]).to_excel(writer, sheet_name="救援玩家比例", index=False)
        _localized_frame(result["newbie_d_rule_rows"]).to_excel(writer, sheet_name="新手D統計", index=False)
        _localized_frame(result["newbie_d_rows"]).to_excel(writer, sheet_name="新手D明細", index=False)
        _localized_frame(result["checkpoint_rows"]).to_excel(writer, sheet_name="判定明細", index=False)
        _localized_frame(result["trigger_rows"]).to_excel(writer, sheet_name="觸發明細", index=False)
        _localized_frame(result["player_rows"]).to_excel(writer, sheet_name="玩家統計", index=False)
        winning_player_rows = sorted(
            (
                row
                for row in result["player_rows"]
                if float(row["Rescue_RTP_%"]) > 100.0
            ),
            key=lambda row: float(row["Rescue_RTP_%"]),
            reverse=True,
        )
        _localized_frame(winning_player_rows).to_excel(
            writer,
            sheet_name="最終RTP超過100%",
            index=False,
        )
        multiplier_rows = result["multiplier_curve_rows"]
        multiplier_frame = _localized_frame(multiplier_rows) if multiplier_rows else pd.DataFrame({"說明": ["此遊戲未使用倍率線型表。"]})
        multiplier_frame.to_excel(writer, sheet_name="倍率線型", index=False)
        _format_excel(writer)
    return report_path


def _default_report_path(args: argparse.Namespace) -> Path:
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    filename = f"simulator_system_{SYSTEM_VERSION}_{args.base_game}_" f"{args.players}p_" f"{args.spins}s_{timestamp}.xlsx"
    return Path(args.report_dir) / filename


def print_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    print("\n=== 老手救援 C 模擬結果 ===")
    print(f"遊戲模型：{summary['game']} / {summary['base_game']}")
    print(f"玩家／每人轉數：{summary['players']:,} / {summary['spins_per_player']:,}")
    print(f"預定判定點：{summary['scheduled_checkpoint_count']:,}")
    print(f"實際判定次數：{summary['checkpoint_count']:,}")
    print(f"同區間觸發後取消：{summary['cancelled_checkpoint_count']:,}")
    print(f"救援觸發次數：{summary['rescue_trigger_count']:,}")
    print(f"任一機制玩家：{summary['players_with_any_mechanism']:,}" f"（{summary['player_any_mechanism_rate_%']:.2f}%）")
    print(f"新手 D 玩家：{summary['players_with_newbie_d']:,}" f"（{summary['player_newbie_d_rate_%']:.2f}%）")
    print(f"老手 C 玩家：{summary['players_with_oldhand_c']:,}" f"（{summary['player_oldhand_c_rate_%']:.2f}%）")
    print(f"自然 RTP：{summary['natural_rtp_%']:.4f}%")
    print(f"新手 D 後 RTP：{summary['newbie_d_rtp_%']:.4f}%" f"（觸發 {summary['newbie_d_trigger_count']:,} 次，" f"{summary['newbie_d_rtp_delta_pp']:+.4f} 個百分點）")
    print(f"老手 C 後 RTP：{summary['rescue_rtp_%']:.4f}%" f"（老手增量 {summary['oldhand_c_rtp_delta_pp']:+.4f} 個百分點）")
    print(f"總 RTP 增量：{summary['rtp_delta_pp']:+.4f} 個百分點")
    print("Tier 觸發：" + ", ".join(f"{row['Tier']}={row['Trigger_Count']:,}" for row in result["tier_rows"]))
    print(f"耗時：{summary['duration_sec']:.2f} 秒")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="老手救援 C 固定 Row Data 模擬器")
    parser.add_argument("--game", default="FIXED_ROW_DATA", choices=sorted(GAME_ADAPTERS), help="遊戲模型")
    parser.add_argument(
        "--base-game",
        default=DEFAULT_BASE_GAME,
        choices=sorted(BASE_GAME_DATA),
        help="固定 Row Data 遊戲；預設超級寶石",
    )
    parser.add_argument(
        "--base-data",
        help="自訂固定自然遊戲 CSV.GZ Row Data；指定時覆蓋 --base-game 路徑",
    )
    parser.add_argument("--players", type=int, default=1000, help="模擬玩家數")
    parser.add_argument("--spins", type=int, default=1000, help="每位玩家付費 Spin 數")
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
    exit_code = main()
    if "ipykernel" not in sys.modules:
        raise SystemExit(exit_code)
