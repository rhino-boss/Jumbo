"""老手救援 C 模擬器。

目前使用固定自然遊戲 Row Data：

* 可切換超級寶石與彩罐熱舞的 1000 人 × 1000 轉固定 CSV.GZ 資料。
* 超級寶石沒有自然 FG；彩罐熱舞由 BG Free Game 卡觸發後另抽 FG 卡。
* 前 200 轉套用新手體驗 D，第 50／150 轉依累積 RTP 改寫得分。
* 老手救援依當日 50× 體驗發放 50× 或 20× FG；救援成功時只採救援結果。
* 每次 Spin 使用共用權重池抽取至多一個 JP4／JP3／JP2／JP1 彩金，彩金倍率加在該轉得分上。
* 遊戲層透過 GameAdapter 隔離。

第 200 轉後，每滿 50 轉固定在該週期第 50 轉判定。

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
from wcwidth import wcswidth

# 切換 RTP 組合，只需修改這一行：
#   "92+2+2" = 92% 基礎遊戲 + 2% JP1/JP2 + 2% JP3/JP4
#   "94+0+2" = 94% 基礎遊戲 + 0% JP1/JP2 + 2% JP3/JP4
# RTP_PROFILE_MODE = "92+2+2"
RTP_PROFILE_MODE = "94+0+2"

# 自訂模擬 Seed，只需修改這一行；相同 Seed 會得到相同的隨機結果：
SIMULATION_SEED = 20260721

# 是否啟用共同池硬上限：
#   True  = 共同池餘額不足時取消救援
#   False = 不執行共同池限制，也不記錄／顯示共同池收支
ENABLE_COMMON_POOL = True

# 老手 C 判定資料窗口（判定回合本身不納入）：
WINDOW_SHORT = 50
WINDOW_MID = 200
WINDOW_LONG = 500

# 老手 C 一般救援資格門檻：
SHORT_RTP_THRESHOLD = 0.50
STAGE_MID_RTP = {
    "A": 0.50,
    "B": 0.50,
    "C": 0.55,
    "D": 0.55,
}
LONG_RTP_THRESHOLD = 1.00

# 個人池不足時使用的固定嚴格門檻（不隨一般門檻調整）：
STRICT_SHORT_RTP_THRESHOLD = 0.40
STRICT_STAGE_MID_RTP = {
    "A": 0.50,
    "B": 0.50,
    "C": 0.55,
    "D": 0.55,
}
STRICT_LONG_RTP_THRESHOLD = 1.00


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
DEFAULT_REPORT_DIR = SCRIPT_DIR / "record"
RTP_PROFILE_CONFIGS: dict[str, dict[str, Any]] = {
    "92+2+2": {
        "label": "92% 基礎遊戲 + 2% JP1/JP2 + 2% JP3/JP4",
        "base_files": {
            "超級寶石": "超級寶石_基礎遊戲_1000人_1000轉.csv.gz",
            "彩罐熱舞": "彩罐熱舞_基礎遊戲_1000人_1000轉.csv.gz",
        },
        "base_source": ("原始 92% 固定 Row Data；超級寶石來自 Fixed Weight 倍率線型，" "彩罐熱舞來自 BG Hit Rate、FG觸發率與FG權重"),
        "jackpot_source": ("使用者提供的彩金機率／獎金表；" "JP1 1%＋JP2 1%＋JP3 0.8%＋JP4 1.2%"),
        "jackpot_weights": {
            "JP1": 130,
            "JP2": 500,
            "JP3": 1_600_000,
            "JP4": 12_000_000,
        },
    },
    "94+0+2": {
        "label": "94% 基礎遊戲 + 0% JP1/JP2 + 2% JP3/JP4",
        "base_files": {
            "超級寶石": "超級寶石_基礎遊戲94RTP_1000人_1000轉.csv.gz",
            "彩罐熱舞": "彩罐熱舞_基礎遊戲94RTP_1000人_1000轉.csv.gz",
        },
        "base_source": "既有 92% 固定 Row Data 等比例校正至 94%（機制模擬用）",
        "jackpot_source": ("使用者提供的彩金機率／獎金表；" "停用 JP1／JP2，啟用 JP3 0.8%＋JP4 1.2%"),
        "jackpot_weights": {
            "JP1": 0,
            "JP2": 0,
            "JP3": 1_600_000,
            "JP4": 12_000_000,
        },
    },
}
if RTP_PROFILE_MODE not in RTP_PROFILE_CONFIGS:
    raise ValueError(f"不支援的 RTP_PROFILE_MODE：{RTP_PROFILE_MODE!r}；" f"可用值：{', '.join(RTP_PROFILE_CONFIGS)}")
ACTIVE_RTP_PROFILE = RTP_PROFILE_CONFIGS[RTP_PROFILE_MODE]
BASE_GAME_DATA = {game: SCRIPT_DIR / "rowdata" / filename for game, filename in ACTIVE_RTP_PROFILE["base_files"].items()}
DEFAULT_BASE_GAME = "超級寶石"
SYSTEM_VERSION = "b08c.4"
RTP_PROFILE = str(ACTIVE_RTP_PROFILE["label"])
BASE_RTP_PARAMETER_SOURCE = str(ACTIVE_RTP_PROFILE["base_source"])
JACKPOT_PARAMETER_SOURCE = str(ACTIVE_RTP_PROFILE["jackpot_source"])

SUMMARY_FIELD_INFO = {
    "game": ("遊戲模型", "模擬器使用的遊戲資料模型。"),
    "base_game": ("基礎遊戲", "本次使用的固定逐轉資料遊戲。"),
    "system_version": ("系統版本", "老手救援系統版本。"),
    "rtp_profile": ("RTP Profile", "本次模擬使用的基礎遊戲與彩金 RTP 組合。"),
    "base_rtp_parameter_source": ("基礎RTP參數來源", "基礎遊戲 RTP 的資料來源與建立方式。"),
    "jackpot_parameter_source": ("彩金RTP參數來源", "彩金 RTP 的啟用獎項與資料來源。"),
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
    "checkpoint_interval_spins": ("判定週期轉數", "老手 C 每 50 轉為一個判定週期。"),
    "checkpoint_active_spins": ("判定週期涵蓋轉數", "每滿 50 轉固定在第 50 轉判定。"),
    "checkpoint_cooldown_spins": ("冷卻轉數", "C 版固定判定沒有額外冷卻區。"),
    "common_pool_contribution_rate_%": ("共同池提撥率", "每筆押注提撥至共同池的比例。"),
    "common_pool_enabled": ("是否啟用共同池", "是否使用共同池餘額作為救援硬上限；關閉時不記錄共同池收支。"),
    "oldhand_base_rtp_target_%": ("老手期基礎 RTP 目標", "說明書 C 版設定的老手期基礎配置 RTP 目標。"),
    "oldhand_total_rtp_target_%": ("老手期總 RTP 目標", "老手期基礎 RTP 加上救援提撥預算後的總目標。"),
    "personal_pool_initial_balance_x": ("個人池初始額度", "說明書尚待確認；本次模擬採用的個人池初始額度。"),
    "daily_50x_simulation_scope": ("當日 50× 模擬範圍", "說明書尚待確認；本次模擬採用的當日判定範圍。"),
    "pool_start_spin": ("共同／個人 Pool 起始轉數", "共同池與個人池從此付費轉開始累積；新手期不納入。"),
    "common_pool_eligible_bets": ("共同池有效押注數", "第 201 轉後納入共同池提撥的 Total Bet 筆數。"),
    "common_pool_income_x": ("共同池累積收入", "累積 Total Bet 乘以共同池提撥率。"),
    "common_pool_spent_x": ("共同池累積支出", "老手救援實際送出的完整派彩倍率合計。"),
    "common_pool_balance_x": ("共同池剩餘餘額", "共同池累積收入減去累積支出。"),
    "common_pool_insufficient_cancel_count": ("共同池餘額不足取消次數", "共同池餘額不足以支付預定救援成本而取消的次數。"),
    "general_standard_check_count": ("一般門檻判定次數", "共同池足夠且個人池足夠，進入一般短／中／長期門檻判定的次數。"),
    "general_standard_pass_count": ("一般門檻通過次數", "個人池足夠且通過一般短／中／長期門檻的次數。"),
    "general_standard_fail_count": ("一般門檻未通過次數", "個人池足夠但未通過一般短／中／長期門檻的次數。"),
    "strict_standard_check_count": ("嚴格門檻判定次數", "共同池足夠但個人池不足，進入嚴格門檻判定的次數。"),
    "personal_pool_insufficient_count": ("個人池餘額不足次數", "共同池已通過，但個人池不足以支應預定獎項的次數。"),
    "strict_standard_pass_count": ("嚴格標準通過次數", "個人池不足但通過嚴格標準並成功透支救援的次數。"),
    "strict_standard_cancel_count": ("嚴格標準未通過取消次數", "個人池不足且未通過嚴格標準而取消的次數。"),
    "personal_pool_funded_trigger_count": ("個人池支應救援次數", "個人池餘額足夠並由個人池支應的救援次數。"),
    "overdraft_trigger_count": ("共同池透支救援次數", "個人池不足、嚴格標準通過，由共同池支應並記為個人透支的次數。"),
    "overdraft_trigger_rate_%": ("透支救援比例", "共同池透支救援次數占全部老手救援次數的比例。"),
    "personal_pool_negative_player_count": ("個人池負餘額玩家數", "模擬結束時個人池仍處於透支狀態的玩家數。"),
    "personal_pool_total_balance_x": ("全部個人池餘額合計", "所有玩家個人池餘額的合計；應與共同池餘額一致。"),
    "scheduled_checkpoint_count": ("預定判定點總數", "所有玩家原先安排的判定點總數。"),
    "checkpoint_count": ("實際判定次數", "實際執行救援資格判斷的固定判定點次數，包含後續被 Pool 取消者。"),
    "experience_condition_matched_count": ("觸發體驗條件次數", "符合該老手階段短期、中期及必要長期 RTP 門檻的判定次數。"),
    "experience_condition_matched_rate_%": ("觸發體驗條件比例", "觸發體驗條件次數占實際判定次數的比例。"),
    "experience_condition_not_matched_count": ("體驗條件未符合次數", "實際判定中，短期或中期 RTP 未符合體驗條件的次數。"),
    "experience_short_only_not_matched_count": ("僅短期體驗未符合次數", "中期符合，但短期 RTP 未低於 40% 的次數。"),
    "experience_mid_only_not_matched_count": ("僅中期體驗未符合次數", "短期符合，但中期 RTP 未低於該階段門檻的次數。"),
    "experience_both_not_matched_count": ("短中期體驗皆未符合次數", "短期與中期 RTP 均未符合該階段門檻的次數。"),
    "experience_long_not_matched_count": ("長期體驗未符合次數", "第 4 階段短期與中期符合，但長期 RTP 未低於 100% 的次數。"),
    "cancelled_checkpoint_count": ("觸發體驗但取消救援次數", "體驗條件符合，但後續因個人條件或 Pool 上限而取消救援的次數。"),
    "rescue_trigger_count": ("老手 C 觸發次數", "老手 C 救援的觸發總次數。"),
    "rescue_50x_trigger_count": ("老手 C 50× 觸發次數", "老手 C 成功發出 50× 救援的次數。"),
    "rescue_20x_trigger_count": ("老手 C 20× 觸發次數", "老手 C 成功發出 20× 救援的次數。"),
    "rescue_trigger_rate_per_checkpoint_%": ("判定點救援觸發率", "老手 C 觸發次數占實際判定次數的比例。"),
    "players_with_rescue": ("使用老手救援玩家數", "至少觸發一次老手 C 的玩家數。"),
    "players_with_any_mechanism": ("使用任一機制玩家數", "至少觸發一次新手 D 或老手 C 的玩家數。"),
    "player_any_mechanism_rate_%": ("任一機制玩家比例", "使用過新手 D 或老手 C 的玩家比例。"),
    "players_with_newbie_d": ("使用新手 D 玩家數", "至少觸發一次新手 D 的玩家數。"),
    "player_newbie_d_rate_%": ("新手 D 玩家比例", "觸發新手 D 的玩家比例。"),
    "players_with_oldhand_c": ("使用老手 C 玩家數", "至少觸發一次老手 C 的玩家數。"),
    "player_oldhand_c_rate_%": ("老手 C 玩家比例", "觸發老手 C 的玩家比例。"),
    "oldhand_avg_triggers_all_players": ("全玩家平均老手觸發次數", "老手 C 總觸發次數除以全部玩家數。"),
    "oldhand_avg_triggers_triggered_players": ("觸發玩家平均老手觸發次數", "老手 C 總觸發次數除以至少觸發一次的玩家數。"),
    "natural_rtp_%": ("自然 RTP（不含機制）", "含自然遊戲與彩金，但完全沒有新手 D 與老手 C 時的 RTP。"),
    "newbie_period_paid_spins": ("新手期 RTP 分母轉數", "所有玩家第 1～200 轉的付費轉數合計。"),
    "newbie_period_natural_rtp_%": ("新手期自然 RTP", "新手期自然派彩除以新手期全部轉數。"),
    "newbie_d_rtp_%": ("新手期套用 D 後 RTP", "新手 D 後派彩除以新手期全部轉數。"),
    "newbie_d_rtp_delta_pp": ("新手期 D RTP 增量", "新手期套用 D 後 RTP 相對新手期自然 RTP 增加的百分點。"),
    "newbie_d_trigger_count": ("新手 D 觸發次數", "新手 D 的觸發總次數。"),
    "newbie_d_checkpoint_count": ("新手 D 總判定次數", "第 50 與第 150 轉實際執行新手 D 判定的合計次數。"),
    "newbie_d_trigger_rate_%": ("新手 D 觸發比例", "新手 D 觸發次數占新手 D 總判定次數的比例。"),
    "newbie_d_spin_50_trigger_count": ("第 50 轉觸發體驗次數", "第 50 轉符合新手 D 介入條件的次數。"),
    "newbie_d_spin_50_trigger_rate_%": ("第 50 轉觸發體驗比例", "第 50 轉觸發次數占第 50 轉實際判定次數的比例。"),
    "newbie_d_spin_150_trigger_count": ("第 150 轉觸發體驗次數", "第 150 轉符合新手 D 介入條件的次數。"),
    "newbie_d_spin_150_trigger_rate_%": ("第 150 轉觸發體驗比例", "第 150 轉觸發次數占第 150 轉實際判定次數的比例。"),
    "newbie_d_not_trigger_count": ("新手 D 體驗條件未符合次數", "第 50 或第 150 轉未符合新手 D 介入條件的次數。"),
    "newbie_d_spin_50_not_trigger_count": ("第 50 轉 RTP ≥ 100% 次數", "第 50 轉因判定前累積 RTP 不低於 100% 而不介入的次數。"),
    "newbie_d_spin_150_not_trigger_count": ("第 150 轉 RTP ≥ 85% 次數", "第 150 轉因判定前累積 RTP 不低於 85% 而不介入的次數。"),
    "oldhand_period_paid_spins": ("老手期 RTP 分母轉數", "所有玩家第 201 轉後的付費轉數合計。"),
    "oldhand_period_natural_rtp_%": ("老手期自然 RTP", "老手期自然派彩除以老手期全部轉數。"),
    "rescue_rtp_%": ("老手期套用 C 後 RTP", "老手 C 後派彩除以老手期全部轉數。"),
    "oldhand_c_rtp_delta_pp": ("老手期 C RTP 增量", "老手期套用 C 後 RTP 相對老手期自然 RTP 增加的百分點。"),
    "overall_rescue_rtp_%": ("全程套用機制後 RTP", "新手 D 與老手 C 全部套用後，以全部付費轉數為分母的 RTP。"),
    "rtp_delta_pp": ("總 RTP 增量", "最終 RTP 相對自然 RTP 增加的總百分點。"),
    "natural_fg_count": ("本次自然 FG 次數", "本次模擬範圍內固定逐轉資料的自然 FG 次數。"),
    "actual_fg_count": ("本次實際 FG 總數", "自然 FG 加上老手救援 FG 後的實際 FG 次數。"),
    "jackpot_weight_denominator": ("彩金權重分母", "每轉使用彩金權重除以此數值作為觸發機率。"),
    "jackpot_theoretical_hit_rate_%": ("彩金理論觸發率", "每轉觸發任一彩金的理論機率。"),
    "jackpot_theoretical_rtp_%": ("彩金理論 RTP", "各彩金觸發機率乘以獎項倍率後的理論 RTP 貢獻。"),
    "jackpot_trigger_count": ("彩金實際觸發次數", "本次模擬觸發任一彩金的總次數。"),
    "jackpot_actual_hit_rate_%": ("彩金實際觸發率", "彩金實際觸發次數除以付費轉數。"),
    "jackpot_actual_rtp_%": ("彩金實際 RTP", "彩金實際派彩金額除以 Total Bet。"),
    "base_game_rtp_%": ("基礎遊戲 RTP", "固定 Row Data 原始遊戲結果、不含彩金與機制的 RTP。"),
    "game_rtp_with_jackpot_%": ("含彩金 Game RTP", "固定 Row Data 自然得分加上彩金後、尚未套用新手 D 與老手 C 的 RTP。"),
    "duration_sec": ("執行時間（秒）", "本次模擬所需時間。"),
    "seed": ("亂數種子", "判定點與救援倍率使用的固定亂數種子。"),
}

REPORT_COLUMN_NAMES = {
    "Stage": "階段",
    "Spin_Range": "轉數區間",
    "Short_RTP_Threshold_%": "短期RTP門檻(%)",
    "Mid_RTP_Threshold_%": "中期RTP門檻(%)",
    "Long_RTP_Threshold_%": "長期RTP門檻(%)",
    "Strict_Mid_RTP_Threshold_%": "嚴格中期RTP門檻(%)",
    "Strict_Long_RTP_Threshold_%": "嚴格長期RTP門檻(%)",
    "Scheduled_Checkpoint_Count": "預定判定點數",
    "Evaluated_Checkpoint_Count": "實際判定次數",
    "Experience_Condition_Matched_Count": "體驗條件命中次數",
    "Experience_Condition_Matched_Rate_%": "體驗條件命中率(%)",
    "Cancelled_Checkpoint_Count": "Pool取消救援次數",
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
    "Strict_Short_Threshold_%": "嚴格短期門檻(%)",
    "Strict_Mid_Threshold_%": "嚴格中期門檻(%)",
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
    "Natural_RTP_%": "自然RTP(不含機制)(%)",
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
    "Personal_RTP_%": "個人Pool RTP(第201轉起)(%)",
    "Personal_Pool_Spins": "個人Pool累積轉數",
    "Personal_Pool_Total_Win_X": "個人Pool累積得分",
    "Personal_Pool_Final_RTP_%": "個人Pool最終RTP(第201轉起)(%)",
    "Personal_Pool_Contribution_X": "個人Pool累積提撥",
    "Personal_Pool_Spent_X": "個人Pool累積救援成本",
    "Personal_Pool_Balance_X": "個人Pool最終餘額",
    "Experienced_50X": "當日是否已體驗50×",
    "Reward_X": "預定救援倍率",
    "Condition_Matched": "階段條件是否符合",
    "Platform_RTP_Before_%": "判定前平台RTP(%)",
    "Projected_Platform_RTP_%": "救援後預估平台RTP(%)",
    "Projected_Oldhand_Delta_pp": "救援後預估老手增量(百分點)",
    "Common_Pool_Balance_Before_X": "判定前共同池餘額",
    "Rescue_Cost_X": "救援成本",
    "Common_Pool_Balance_After_X": "預估救援後共同池餘額",
    "Personal_Pool_Balance_Before_X": "判定前個人池餘額",
    "Personal_Pool_Balance_After_X": "預估救援後個人池餘額",
    "Strict_Standard_Passed": "嚴格標準是否通過",
    "Applied_Standard": "本次套用門檻",
    "Selected_Standard_Passed": "套用門檻是否通過",
    "Funding_Source": "救援支應來源",
    "Experienced_50X_Before": "判定前當日是否體驗50×",
    "Pool_Result": "Pool判定結果",
    "Period": "時期",
    "Paid_Spins": "付費轉數",
    "Oldhand_C_Trigger_Count": "老手C觸發次數",
    "Oldhand_C_Eligible_Without_Common_Pool_Count": "無共同池應觸發次數",
    "Oldhand_C_Actual_vs_Eligible_Rate_%": "老手C實際觸發率(%)",
    "Cumulative_Natural_RTP_%": "累積自然RTP(不含機制)(%)",
    "Cumulative_Newbie_D_RTP_%": "累積新手D後RTP(%)",
    "Cumulative_Rescue_RTP_%": "累積最終機制RTP(%)",
    "Cumulative_Newbie_D_Delta_pp": "累積新手D增量(百分點)",
    "Cumulative_Oldhand_C_Delta_pp": "累積老手C增量(百分點)",
    "Cumulative_RTP_Delta_pp": "累積總增量(百分點)",
    "Jackpot": "彩金",
    "Jackpot_Weight": "彩金權重",
    "Jackpot_Probability_%": "彩金理論觸發率(%)",
    "Jackpot_Award_Cents": "彩金金額(分)",
    "Jackpot_X": "彩金倍率",
    "Jackpot_Theoretical_RTP_%": "彩金理論RTP(%)",
    "Jackpot_Trigger_Count": "彩金觸發次數",
    "Jackpot_Actual_RTP_%": "彩金實際RTP(%)",
    "Base_Game_X": "基礎遊戲倍率",
    "Game_X_With_Jackpot": "含彩金遊戲倍率",
    "Base_Game_RTP_%": "基礎遊戲RTP(%)",
    "Limit_Level": "統計層級",
    "Limit_Type": "上限類型",
    "Cancel_Reason": "取消原因",
    "Share_Within_Limit_%": "占同類上限取消比例(%)",
    "Avg_Personal_RTP_%": "平均個人Pool RTP(%)",
    "Avg_Platform_RTP_Before_%": "平均判定前平台RTP(%)",
    "Avg_Projected_Platform_RTP_%": "平均救援後預估平台RTP(%)",
    "Avg_Common_Pool_Balance_Before_X": "平均判定前共同池餘額",
    "Avg_Rescue_Cost_X": "平均預定救援成本",
    "Avg_Common_Pool_Balance_After_X": "平均救援後共同池餘額",
    "Avg_Personal_Pool_Balance_Before_X": "平均判定前個人池餘額",
    "Avg_Personal_Pool_Balance_After_X": "平均救援後個人池餘額",
    "Avg_Short_RTP_%": "平均短期RTP(%)",
    "Avg_Mid_RTP_%": "平均中期RTP(%)",
    "Avg_Long_RTP_%": "平均長期RTP(%)",
    "Scenario_Summary": "情境概述",
}

RULE_NAMES_ZH = {
    "AC_COMBINED": "A～C：短期＋中期＋未進FG",
    "AC_NO_FG": "A～C：短期＋未進FG",
    "STAGE_RTP_QUALIFIED": "符合該老手階段 RTP 資格",
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
    "Condition_Matched",
    "Strict_Standard_Passed",
    "Selected_Standard_Passed",
    "Experienced_50X_Before",
    "Experienced_50X",
}

NEWBIE_LAST_SPIN = 200

CHECKPOINT_INTERVAL_SPINS = 50
CHECKPOINT_ACTIVE_SPINS = 50
CHECKPOINT_COOLDOWN_SPINS = 0
COMMON_POOL_CONTRIBUTION_RATE = 0.01
OLDHAND_BASE_RTP_TARGET = 0.96
OLDHAND_TOTAL_RTP_TARGET = OLDHAND_BASE_RTP_TARGET + COMMON_POOL_CONTRIBUTION_RATE
PERSONAL_POOL_INITIAL_BALANCE = 0.0
DAILY_50X_SIMULATION_SCOPE = "每位玩家本次完整模擬視為同一個遊戲日"
REWARD_HIGH_X = 50.0
REWARD_LOW_X = 20.0
REWARD_LABELS = ("20×", "50×")

JACKPOT_WEIGHT_DENOMINATOR = 10_000_000_000
JACKPOT_CONFIG = (
    ("JP1", ACTIVE_RTP_PROFILE["jackpot_weights"]["JP1"], 76_923_076.92),
    ("JP2", ACTIVE_RTP_PROFILE["jackpot_weights"]["JP2"], 20_000_000),
    ("JP3", ACTIVE_RTP_PROFILE["jackpot_weights"]["JP3"], 5_000),
    ("JP4", ACTIVE_RTP_PROFILE["jackpot_weights"]["JP4"], 1_000),
)


def _jackpot_from_draw(draw: int) -> tuple[str, float]:
    """以單一共用權重池抽出至多一個彩金，回傳（彩金名稱, 倍率）。"""

    cumulative_weight = 0
    for jackpot, weight, award_cents in JACKPOT_CONFIG:
        cumulative_weight += weight
        if draw < cumulative_weight:
            return jackpot, award_cents / 100.0
    return "", 0.0


TIER_RANGES = {
    "20×": (20.0, 20.0),
    "50×": (50.0, 50.0),
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

    def natural_spin_at(self, player_id: int, spin_no: int) -> SpinOutcome:
        """依玩家與轉數讀取自然結果；共用平台 Pool 模擬使用。"""

        raise NotImplementedError("此遊戲 Adapter 不支援依玩家／轉數讀取結果")

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

    def natural_spin_at(self, player_id: int, spin_no: int) -> SpinOutcome:
        if not 1 <= player_id <= self.data_players:
            raise ValueError(f"固定 Row Data 只有 {self.data_players:,} 位玩家，無法執行 Player {player_id}")
        if not 1 <= spin_no <= self.data_spins:
            raise ValueError(f"固定 Row Data 每位玩家只有 {self.data_spins:,} 轉")
        return SpinOutcome(
            multiplier=float(self._natural_multiplier[player_id - 1, spin_no - 1]),
            triggered_fg=bool(self._natural_fg[player_id - 1, spin_no - 1]),
        )

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
            "rescue_result": "救援通過只採救援FG結果；未通過才採自然結果；共同池按完整救援成本控管",
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


def _checkpoint_windows(total_spins: int) -> list[tuple[str, int, int, str, str]]:
    """第 200 轉後每 50 轉一段，只保留完整週期。"""

    windows: list[tuple[str, int, int, str, str]] = []
    for start in range(201, total_spins + 1, CHECKPOINT_INTERVAL_SPINS):
        active_end = start + CHECKPOINT_INTERVAL_SPINS - 1
        if active_end > total_spins:
            continue
        stage = get_stage(start)
        if stage is None:
            continue
        window_id = f"CHECK_{start}_{active_end}"
        windows.append((stage, start, active_end, window_id, f"{start}～{active_end}"))
    return windows


def _fixed_checkpoints(total_spins: int) -> dict[int, tuple[str, str]]:
    """每個老手 50 轉週期固定在第 50 轉判定。"""

    checkpoints: dict[int, tuple[str, str]] = {}
    for stage, start, end, window_id, _ in _checkpoint_windows(total_spins):
        checkpoints[end] = (stage, window_id)
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

    short_bad = short_rtp < SHORT_RTP_THRESHOLD
    mid_bad = mid_rtp < STAGE_MID_RTP[stage]
    long_bad: bool | None = None if long_rtp is None else long_rtp < LONG_RTP_THRESHOLD
    long_qualified = stage != "D" or long_bad is True

    if stage == "D" and long_rtp is None:
        return RescueDecision(
            stage,
            "D_NO_LONG_WINDOW",
            "老手第4階段判定前尚無完整500轉資料，不救援",
            None,
            short_rtp,
            mid_rtp,
            long_rtp,
            no_fg_spins,
            mid_bad,
            long_bad,
        )

    if short_bad and mid_bad and long_qualified:
        long_text = f"，且長期 RTP < {LONG_RTP_THRESHOLD * 100:g}%" if stage == "D" else ""
        return RescueDecision(
            stage,
            "STAGE_RTP_QUALIFIED",
            f"{stage} 階段：短期 RTP < {SHORT_RTP_THRESHOLD * 100:g}%、" f"中期 RTP < {STAGE_MID_RTP[stage] * 100:g}%{long_text}",
            "QUALIFIED",
            short_rtp,
            mid_rtp,
            long_rtp,
            no_fg_spins,
            mid_bad,
            long_bad,
        )
    return RescueDecision(
        stage,
        "NO_RESCUE",
        "未符合該階段短期／中期／長期資格門檻",
        None,
        short_rtp,
        mid_rtp,
        long_rtp,
        no_fg_spins,
        mid_bad,
        long_bad,
    )


def meets_strict_rescue_standard(decision: RescueDecision) -> bool:
    """個人池不足時，使用一般門檻各減 10 個百分點的嚴格標準複判。"""

    if decision.short_rtp >= STRICT_SHORT_RTP_THRESHOLD:
        return False
    if decision.mid_rtp >= STRICT_STAGE_MID_RTP[decision.stage]:
        return False
    if decision.stage == "D":
        return decision.long_rtp is not None and decision.long_rtp < STRICT_LONG_RTP_THRESHOLD
    return True


def _pct(value: float | None) -> float | None:
    return None if value is None else value * 100.0


def _run_simulation_legacy(args: argparse.Namespace, adapter: GameAdapter) -> dict[str, Any]:
    started = time.perf_counter()
    checkpoints: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    newbie_d_rows: list[dict[str, Any]] = []
    stop_after_rescue_rows: list[dict[str, Any]] = []
    fg_exit_rows: list[dict[str, Any]] = []
    completed_stage_rows: list[dict[str, Any]] = []
    jackpot_rows: list[dict[str, Any]] = []
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
        scheduled_checkpoints = _fixed_checkpoints(args.spins)
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
                mechanism_triggered = (newbie_d_decision is not None and newbie_d_decision.triggered) or (decision is not None and decision.triggered)
                if (actual.triggered_fg or mechanism_triggered) and reporting_block_id not in actual_fg_exit_blocks:
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
            "Long_RTP_Threshold_%": LONG_RTP_THRESHOLD * 100.0 if stage == "D" else None,
            "Strict_Mid_RTP_Threshold_%": STRICT_STAGE_MID_RTP[stage] * 100.0,
            "Strict_Long_RTP_Threshold_%": STRICT_LONG_RTP_THRESHOLD * 100.0 if stage == "D" else None,
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
        "rtp_profile": RTP_PROFILE,
        "base_rtp_parameter_source": BASE_RTP_PARAMETER_SOURCE,
        "jackpot_parameter_source": JACKPOT_PARAMETER_SOURCE,
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


def run_simulation(args: argparse.Namespace, adapter: GameAdapter) -> dict[str, Any]:
    """以轉數為時間軸模擬共用平台 Pool 與個人 Pool。"""

    started = time.perf_counter()
    checkpoints: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    newbie_d_rows: list[dict[str, Any]] = []
    stop_after_rescue_rows: list[dict[str, Any]] = []
    fg_exit_rows: list[dict[str, Any]] = []
    completed_stage_rows: list[dict[str, Any]] = []
    jackpot_rows: list[dict[str, Any]] = []

    reporting_blocks = _reporting_blocks(args.spins)
    period_stats: dict[str, dict[str, Any]] = {}
    for index, (stage, start, end, block_id, display_range) in enumerate(reporting_blocks):
        if index < 2:
            period_name = f"新手{index + 1}階段"
            mechanism = "新手 D"
        else:
            period_name = f"老手{index - 1}階段"
            mechanism = "老手 C"
        period_stats[block_id] = {
            "Period": period_name,
            "Mechanism": mechanism,
            "Stage": stage,
            "Spin_Range": f"{start}～{end}",
            "Display_Range": display_range,
            "Paid_Spins": 0,
            "Base_Game_Win": 0.0,
            "Jackpot_Win": 0.0,
            "Natural_Win": 0.0,
            "Newbie_D_Win": 0.0,
            "Final_Win": 0.0,
            "Newbie_D_Trigger_Count": 0,
            "Oldhand_C_Trigger_Count": 0,
            "Oldhand_C_Eligible_Without_Common_Pool_Count": 0,
        }
    checkpoint_windows = _checkpoint_windows(args.spins)
    checkpoint_by_id = {window_id: (stage, start, end, display_range) for stage, start, end, window_id, display_range in checkpoint_windows}
    block_by_end = {end: (stage, start, block_id, display_range) for stage, start, end, block_id, display_range in reporting_blocks}
    reporting_block_by_spin = {spin: (stage, start, end, block_id, display_range) for stage, start, end, block_id, display_range in reporting_blocks for spin in range(start, end + 1)}

    states: dict[int, dict[str, Any]] = {}
    for player_id in range(1, args.players + 1):
        states[player_id] = {
            "history": [],
            "no_fg_spins": 0,
            "base_total": 0.0,
            "jackpot_total": 0.0,
            "jackpot_counts": Counter(),
            "natural_total": 0.0,
            "newbie_total": 0.0,
            "actual_total": 0.0,
            "personal_pool_total": 0.0,
            "personal_pool_spins": 0,
            "personal_pool_spent": 0.0,
            "experienced_50x_today": False,
            "trigger_counts": Counter(),
            "newbie_trigger_count": 0,
            "scheduled_checkpoints": _fixed_checkpoints(args.spins),
            "actual_exit_blocks": set(),
            "natural_exit_blocks": set(),
            "block_triggers": {},
        }

    stage_scheduled_counts: Counter[str] = Counter()
    stage_check_counts: Counter[str] = Counter()
    stage_cancelled_counts: Counter[str] = Counter()
    stage_trigger_counts: Counter[str] = Counter()
    stage_experience_match_counts: Counter[str] = Counter()
    reward_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    newbie_d_rule_counts: Counter[str] = Counter()

    base_win_total = 0.0
    jackpot_win_total = 0.0
    jackpot_trigger_total = 0
    jackpot_counts: Counter[str] = Counter()
    natural_win_total = 0.0
    newbie_d_win_total = 0.0
    actual_win_total = 0.0
    platform_bet_total = 0
    common_pool_bet_total = 0
    common_pool_spent_total = 0.0
    natural_fg_total = 0
    actual_fg_total = 0
    common_pool_insufficient_cancel_count = 0
    personal_pool_insufficient_count = 0
    strict_standard_pass_count = 0
    strict_standard_cancel_count = 0
    personal_pool_funded_trigger_count = 0
    overdraft_trigger_count = 0

    order_rng = np.random.default_rng(np.random.SeedSequence([args.seed, 0xC07]))
    jackpot_rng = np.random.default_rng(np.random.SeedSequence([args.seed, 0x4A50]))

    for spin_no in range(1, args.spins + 1):
        player_order = np.arange(1, args.players + 1)
        order_rng.shuffle(player_order)
        jackpot_draws = jackpot_rng.integers(
            0,
            JACKPOT_WEIGHT_DENOMINATOR,
            size=args.players,
            dtype=np.int64,
        )

        for player_value in player_order:
            player_id = int(player_value)
            state = states[player_id]
            history: list[float] = state["history"]

            base_natural = adapter.natural_spin_at(player_id, spin_no)
            jackpot, jackpot_x = _jackpot_from_draw(int(jackpot_draws[player_id - 1]))
            natural = SpinOutcome(
                multiplier=base_natural.multiplier + jackpot_x,
                triggered_fg=base_natural.triggered_fg,
            )
            state["base_total"] += base_natural.multiplier
            state["jackpot_total"] += jackpot_x
            state["natural_total"] += natural.multiplier
            base_win_total += base_natural.multiplier
            jackpot_win_total += jackpot_x
            natural_win_total += natural.multiplier
            natural_fg_total += int(natural.triggered_fg)
            if jackpot:
                jackpot_trigger_total += 1
                jackpot_counts[jackpot] += 1
                state["jackpot_counts"][jackpot] += 1
                jackpot_rows.append(
                    {
                        "Player": player_id,
                        "Spin": spin_no,
                        "Jackpot": jackpot,
                        "Jackpot_X": jackpot_x,
                        "Base_Game_X": base_natural.multiplier,
                        "Game_X_With_Jackpot": natural.multiplier,
                    }
                )

            after_newbie_d = natural
            newbie_d_decision = decide_newbie_d(history, spin_no)
            if newbie_d_decision is not None:
                newbie_d_rule_counts[newbie_d_decision.rule] += 1
                if newbie_d_decision.triggered:
                    after_newbie_d = SpinOutcome(
                        multiplier=float(newbie_d_decision.reward_multiplier) + jackpot_x,
                        triggered_fg=natural.triggered_fg,
                    )
                    state["newbie_trigger_count"] += 1
                    newbie_block_id = "NEWBIE_1_100" if spin_no == 50 else "NEWBIE_101_200"
                    newbie_display_range = "0～100" if spin_no == 50 else "100～200"
                    newbie_block_start = 1 if spin_no == 50 else 101
                    block_payout = sum(history[newbie_block_start - 1 :]) + after_newbie_d.multiplier
                    block_spins = spin_no - newbie_block_start + 1
                    trigger_info = {"Spin": spin_no, "Tier": f"{after_newbie_d.multiplier:g}×"}
                    state["block_triggers"][newbie_block_id] = trigger_info
                    stop_after_rescue_rows.append(
                        {
                            "Player": player_id,
                            "Stage": "新手 D",
                            "Display_Range": newbie_display_range,
                            "Actual_Spin_Range": "1～100" if spin_no == 50 else "101～200",
                            "Trigger_Spin": spin_no,
                            "Tier": trigger_info["Tier"],
                            "RTP_Before_Rescue_Mid_%": newbie_d_decision.rtp * 100.0,
                            "Rescue_FG_X": after_newbie_d.multiplier,
                            "RTP_If_Stop_Block_%": block_payout / block_spins * 100.0,
                            "RTP_If_Stop_Cumulative_%": (state["actual_total"] + after_newbie_d.multiplier) / spin_no * 100.0,
                            "RTP_If_Stop_Natural_Cumulative_%": state["natural_total"] / spin_no * 100.0,
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
                        "Base_Game_X": base_natural.multiplier,
                        "Jackpot": jackpot,
                        "Jackpot_X": jackpot_x,
                        "Newbie_D_X": after_newbie_d.multiplier,
                        "Delta_X": after_newbie_d.multiplier - natural.multiplier,
                        "Natural_FG": natural.triggered_fg,
                    }
                )

            state["newbie_total"] += after_newbie_d.multiplier
            newbie_d_win_total += after_newbie_d.multiplier

            decision: RescueDecision | None = None
            actual = after_newbie_d
            actual_rescue_triggered = False
            reward_x: float | None = None
            reward_label = ""
            pool_result = "未安排判定"
            personal_rtp: float | None = None
            platform_rtp_before = actual_win_total / platform_bet_total if platform_bet_total else 0.0
            projected_platform_rtp: float | None = None
            projected_oldhand_delta: float | None = None
            common_pool_balance_before: float | None = None
            rescue_cost: float | None = None
            rescue_delta_vs_natural: float | None = None
            common_pool_balance_after: float | None = None
            personal_pool_balance_before: float | None = None
            personal_pool_balance_after: float | None = None
            strict_standard_passed: bool | None = None
            applied_standard = ""
            selected_standard_passed = False
            funding_source = ""
            experienced_50x_before = bool(state["experienced_50x_today"])
            checkpoint = state["scheduled_checkpoints"].get(spin_no)

            if checkpoint is not None:
                stage, checkpoint_id = checkpoint
                stage_scheduled_counts[stage] += 1
                stage_check_counts[stage] += 1
                decision = decide_rescue(history, state["no_fg_spins"], stage)
                rule_counts[decision.rule_id] += 1
                personal_rtp = state["personal_pool_total"] / state["personal_pool_spins"] if state["personal_pool_spins"] else 0.0
                personal_pool_income = state["personal_pool_spins"] * COMMON_POOL_CONTRIBUTION_RATE
                personal_pool_balance_before = PERSONAL_POOL_INITIAL_BALANCE + personal_pool_income - state["personal_pool_spent"]
                reward_x = REWARD_LOW_X if experienced_50x_before else REWARD_HIGH_X
                reward_label = f"{reward_x:g}×"
                rescue_outcome = adapter.rescue_fg(reward_label)
                # 判定轉採二選一路徑：救援成功只使用救援結果；未救援才使用自然結果。
                # 自然結果仍保留作為「無機制」對照，但不與救援結果比大小。
                rescue_multiplier = rescue_outcome.multiplier
                rescue_cost = rescue_multiplier
                rescue_delta_vs_natural = rescue_multiplier - natural.multiplier
                projected_bet = platform_bet_total + 1
                projected_platform_rtp = (actual_win_total + rescue_multiplier) / projected_bet
                projected_common_pool_bets = common_pool_bet_total + 1
                projected_oldhand_delta = (actual_win_total + rescue_multiplier - newbie_d_win_total) / projected_common_pool_bets
                if ENABLE_COMMON_POOL:
                    common_pool_income = common_pool_bet_total * COMMON_POOL_CONTRIBUTION_RATE
                    common_pool_balance_before = common_pool_income - common_pool_spent_total
                    common_pool_balance_after = common_pool_balance_before - rescue_cost
                else:
                    common_pool_balance_before = None
                    common_pool_balance_after = None
                personal_pool_balance_after = personal_pool_balance_before - rescue_cost
                strict_standard_passed = meets_strict_rescue_standard(decision)
                personal_can_fund = rescue_cost <= max(personal_pool_balance_before, 0.0) + 1e-12

                # 「不考慮共同池時應觸發」依個人池路由後所適用的門檻計算。
                would_trigger_without_common_pool = decision.triggered if personal_can_fund else strict_standard_passed
                if would_trigger_without_common_pool:
                    _, _, _, candidate_block_id, _ = reporting_block_by_spin[spin_no]
                    period_stats[candidate_block_id]["Oldhand_C_Eligible_Without_Common_Pool_Count"] += 1

                # 正式順序：共同池 → 個人池 → 一般／嚴格門檻；通過即救援。
                if ENABLE_COMMON_POOL and rescue_cost > common_pool_balance_before + 1e-12:
                    common_pool_insufficient_cancel_count += 1
                    stage_cancelled_counts[stage] += 1
                    pool_result = "共同池餘額不足，取消救援"
                elif personal_can_fund:
                    applied_standard = "一般標準"
                    selected_standard_passed = decision.triggered
                    if selected_standard_passed:
                        funding_source = "個人池"
                    else:
                        stage_cancelled_counts[stage] += 1
                        pool_result = "個人池足夠，但未通過一般短／中／長期門檻"
                else:
                    personal_pool_insufficient_count += 1
                    applied_standard = "嚴格標準"
                    selected_standard_passed = strict_standard_passed
                    if selected_standard_passed:
                        funding_source = "共同池（透支）" if ENABLE_COMMON_POOL else "系統支應（共同池關閉）"
                    else:
                        strict_standard_cancel_count += 1
                        stage_cancelled_counts[stage] += 1
                        pool_result = "個人池不足且未通過嚴格標準，取消救援"

                if selected_standard_passed:
                    stage_experience_match_counts[stage] += 1

                    if funding_source:
                        actual = SpinOutcome(multiplier=rescue_multiplier, triggered_fg=True)
                        actual_rescue_triggered = True
                        pool_result = f"通過，發出救援；{funding_source}支應"
                        common_pool_spent_total += rescue_cost
                        state["personal_pool_spent"] += rescue_cost
                        if funding_source != "個人池":
                            strict_standard_pass_count += 1
                            overdraft_trigger_count += 1
                        else:
                            personal_pool_funded_trigger_count += 1
                        stage_trigger_counts[stage] += 1
                        reward_counts[reward_label] += 1
                        state["trigger_counts"][reward_label] += 1

                        check_stage, check_start, check_end, check_display = checkpoint_by_id[checkpoint_id]
                        reporting_info = reporting_block_by_spin[spin_no]
                        _, report_start, report_end, report_block_id, report_display = reporting_info
                        block_payout = sum(history[report_start - 1 :]) + actual.multiplier
                        block_spins = spin_no - report_start + 1
                        cumulative_payout = state["actual_total"] + actual.multiplier
                        trigger_row = {
                            "Player": player_id,
                            "Spin": spin_no,
                            "Stage": stage,
                            "Block": checkpoint_id,
                            "Display_Range": report_display,
                            "Actual_Spin_Range": check_display,
                            "Rule_ID": decision.rule_id,
                            "Rule": decision.rule_description,
                            "Tier": reward_label,
                            "Personal_RTP_%": personal_rtp * 100.0,
                            "Short_RTP_%": _pct(decision.short_rtp),
                            "Mid_RTP_%": _pct(decision.mid_rtp),
                            "Long_RTP_%": _pct(decision.long_rtp),
                            "Natural_X": natural.multiplier,
                            "Base_Game_X": base_natural.multiplier,
                            "Jackpot": jackpot,
                            "Jackpot_X": jackpot_x,
                            "Reward_X": reward_x,
                            "Rescue_FG_X": actual.multiplier,
                            "Delta_X": rescue_delta_vs_natural,
                            "Platform_RTP_Before_%": platform_rtp_before * 100.0,
                            "Projected_Platform_RTP_%": projected_platform_rtp * 100.0,
                            "Projected_Oldhand_Delta_pp": projected_oldhand_delta * 100.0,
                            "Common_Pool_Balance_Before_X": common_pool_balance_before,
                            "Rescue_Cost_X": rescue_cost,
                            "Common_Pool_Balance_After_X": common_pool_balance_after,
                            "Personal_Pool_Balance_Before_X": personal_pool_balance_before,
                            "Personal_Pool_Balance_After_X": personal_pool_balance_after,
                            "Strict_Standard_Passed": strict_standard_passed,
                            "Applied_Standard": applied_standard,
                            "Selected_Standard_Passed": selected_standard_passed,
                            "Funding_Source": funding_source,
                            "Experienced_50X_Before": experienced_50x_before,
                            "Stop_After_Rescue_Block_RTP_%": block_payout / block_spins * 100.0,
                            "Stop_After_Rescue_Cumulative_RTP_%": cumulative_payout / spin_no * 100.0,
                        }
                        triggers.append(trigger_row)
                        state["block_triggers"][report_block_id] = trigger_row
                        stop_after_rescue_rows.append(
                            {
                                "Player": player_id,
                                "Stage": stage,
                                "Display_Range": report_display,
                                "Actual_Spin_Range": f"{report_start}～{report_end}",
                                "Trigger_Spin": spin_no,
                                "Tier": reward_label,
                                "RTP_Before_Rescue_Mid_%": _pct(decision.mid_rtp),
                                "Rescue_FG_X": actual.multiplier,
                                "RTP_If_Stop_Block_%": block_payout / block_spins * 100.0,
                                "RTP_If_Stop_Cumulative_%": cumulative_payout / spin_no * 100.0,
                                "RTP_If_Stop_Natural_Cumulative_%": state["natural_total"] / spin_no * 100.0,
                            }
                        )

                checkpoints.append(
                    {
                        "Player": player_id,
                        "Spin": spin_no,
                        "Stage": stage,
                        "Block": checkpoint_id,
                        "Status": "已判定",
                        "Short_Threshold_%": SHORT_RTP_THRESHOLD * 100.0,
                        "Mid_Threshold_%": STAGE_MID_RTP[stage] * 100.0,
                        "Strict_Short_Threshold_%": STRICT_SHORT_RTP_THRESHOLD * 100.0,
                        "Strict_Mid_Threshold_%": STRICT_STAGE_MID_RTP[stage] * 100.0,
                        "Short_RTP_%": _pct(decision.short_rtp),
                        "Mid_RTP_%": _pct(decision.mid_rtp),
                        "Long_RTP_%": _pct(decision.long_rtp),
                        "Short_Bad": decision.short_bad,
                        "Mid_Bad": decision.mid_bad,
                        "Long_Bad": decision.long_bad,
                        "Rule_ID": decision.rule_id,
                        "Condition_Matched": selected_standard_passed,
                        "Personal_RTP_%": personal_rtp * 100.0 if personal_rtp is not None else None,
                        "Reward_X": reward_x,
                        "Platform_RTP_Before_%": platform_rtp_before * 100.0,
                        "Projected_Platform_RTP_%": _pct(projected_platform_rtp),
                        "Projected_Oldhand_Delta_pp": _pct(projected_oldhand_delta),
                        "Common_Pool_Balance_Before_X": common_pool_balance_before,
                        "Rescue_Cost_X": rescue_cost,
                        "Common_Pool_Balance_After_X": common_pool_balance_after,
                        "Personal_Pool_Balance_Before_X": personal_pool_balance_before,
                        "Personal_Pool_Balance_After_X": personal_pool_balance_after,
                        "Strict_Standard_Passed": strict_standard_passed,
                        "Applied_Standard": applied_standard,
                        "Selected_Standard_Passed": selected_standard_passed,
                        "Funding_Source": funding_source,
                        "Experienced_50X_Before": experienced_50x_before,
                        "Pool_Result": pool_result,
                        "Tier": reward_label,
                        "Triggered": actual_rescue_triggered,
                    }
                )

            reporting_block = reporting_block_by_spin.get(spin_no)
            if reporting_block is not None:
                block_stage, _, _, reporting_block_id, display_range = reporting_block
                mechanism_triggered = (newbie_d_decision is not None and newbie_d_decision.triggered) or actual_rescue_triggered
                if (actual.triggered_fg or mechanism_triggered) and reporting_block_id not in state["actual_exit_blocks"]:
                    state["actual_exit_blocks"].add(reporting_block_id)
                    fg_exit_rows.append(
                        {
                            "Player": player_id,
                            "Stage": block_stage,
                            "Display_Range": display_range,
                            "Scenario": "有機制",
                            "Exit_Spin": spin_no,
                            "Exit_RTP_%": (state["actual_total"] + actual.multiplier) / spin_no * 100.0,
                        }
                    )
                if natural.triggered_fg and reporting_block_id not in state["natural_exit_blocks"]:
                    state["natural_exit_blocks"].add(reporting_block_id)
                    fg_exit_rows.append(
                        {
                            "Player": player_id,
                            "Stage": block_stage,
                            "Display_Range": display_range,
                            "Scenario": "無機制",
                            "Exit_Spin": spin_no,
                            "Exit_RTP_%": state["natural_total"] / spin_no * 100.0,
                        }
                    )

                period = period_stats[reporting_block_id]
                period["Paid_Spins"] += 1
                period["Base_Game_Win"] += base_natural.multiplier
                period["Jackpot_Win"] += jackpot_x
                period["Natural_Win"] += natural.multiplier
                period["Newbie_D_Win"] += after_newbie_d.multiplier
                period["Final_Win"] += actual.multiplier
                period["Newbie_D_Trigger_Count"] += int(newbie_d_decision is not None and newbie_d_decision.triggered)
                period["Oldhand_C_Trigger_Count"] += int(actual_rescue_triggered)

            history.append(actual.multiplier)
            state["actual_total"] += actual.multiplier
            if spin_no > NEWBIE_LAST_SPIN:
                state["personal_pool_total"] += actual.multiplier
                state["personal_pool_spins"] += 1
                common_pool_bet_total += 1
            if actual.multiplier >= 50.0:
                state["experienced_50x_today"] = True
            actual_win_total += actual.multiplier
            platform_bet_total += 1
            actual_fg_total += int(actual.triggered_fg)
            state["no_fg_spins"] = 0 if actual.triggered_fg else state["no_fg_spins"] + 1

            completed_block = block_by_end.get(spin_no)
            if completed_block is not None:
                block_stage, block_start, completed_block_id, display_range = completed_block
                trigger_info = state["block_triggers"].get(completed_block_id)
                block_values = history[block_start - 1 : spin_no]
                completed_stage_rows.append(
                    {
                        "Player": player_id,
                        "Stage": block_stage,
                        "Display_Range": display_range,
                        "Actual_Spin_Range": f"{block_start}～{spin_no}",
                        "Completed_Spin": spin_no,
                        "Rescue_Triggered": trigger_info is not None,
                        "Trigger_Spin": trigger_info["Spin"] if trigger_info is not None else "",
                        "Tier": trigger_info["Tier"] if trigger_info is not None else "",
                        "Completed_Block_RTP_%": sum(block_values) / len(block_values) * 100.0,
                        "Completed_Cumulative_RTP_%": state["actual_total"] / spin_no * 100.0,
                    }
                )

        if args.progress_every > 0 and (spin_no % args.progress_every == 0 or spin_no == args.spins):
            print(f"進度：第 {spin_no:,}/{args.spins:,} 轉", flush=True)

    players: list[dict[str, Any]] = []
    for player_id, state in states.items():
        player_row: dict[str, Any] = {
            "Player": player_id,
            "Spins": args.spins,
            "Base_Game_RTP_%": state["base_total"] / args.spins * 100.0,
            "Jackpot_Actual_RTP_%": state["jackpot_total"] / args.spins * 100.0,
            "Natural_RTP_%": state["natural_total"] / args.spins * 100.0,
            "Newbie_D_RTP_%": state["newbie_total"] / args.spins * 100.0,
            "Rescue_RTP_%": state["actual_total"] / args.spins * 100.0,
            "Newbie_D_Delta_pp": (state["newbie_total"] - state["natural_total"]) / args.spins * 100.0,
            "Oldhand_C_Delta_pp": (state["actual_total"] - state["newbie_total"]) / args.spins * 100.0,
            "RTP_Delta_pp": (state["actual_total"] - state["natural_total"]) / args.spins * 100.0,
            "Personal_Pool_Spins": state["personal_pool_spins"],
            "Personal_Pool_Total_Win_X": state["personal_pool_total"],
            "Personal_Pool_Final_RTP_%": (state["personal_pool_total"] / state["personal_pool_spins"] * 100.0 if state["personal_pool_spins"] else None),
            "Personal_Pool_Contribution_X": state["personal_pool_spins"] * COMMON_POOL_CONTRIBUTION_RATE,
            "Personal_Pool_Spent_X": state["personal_pool_spent"],
            "Personal_Pool_Balance_X": (PERSONAL_POOL_INITIAL_BALANCE + state["personal_pool_spins"] * COMMON_POOL_CONTRIBUTION_RATE - state["personal_pool_spent"]),
            "Experienced_50X": state["experienced_50x_today"],
            "Newbie_D_Trigger_Count": state["newbie_trigger_count"],
            "Jackpot_Trigger_Count": sum(state["jackpot_counts"].values()),
            "Trigger_Count": sum(state["trigger_counts"].values()),
        }
        for jackpot, _, _ in JACKPOT_CONFIG:
            player_row[jackpot] = state["jackpot_counts"][jackpot]
        for reward_label in REWARD_LABELS:
            player_row[reward_label] = state["trigger_counts"][reward_label]
        players.append(player_row)

    total_paid_spins = args.players * args.spins
    period_rows: list[dict[str, Any]] = []
    cumulative_paid_spins = 0
    cumulative_natural_win = 0.0
    cumulative_newbie_win = 0.0
    cumulative_final_win = 0.0
    for _, _, _, block_id, _ in reporting_blocks:
        period = period_stats[block_id]
        paid_spins = int(period["Paid_Spins"])
        natural_win = float(period["Natural_Win"])
        newbie_win = float(period["Newbie_D_Win"])
        final_win = float(period["Final_Win"])

        cumulative_paid_spins += paid_spins
        cumulative_natural_win += natural_win
        cumulative_newbie_win += newbie_win
        cumulative_final_win += final_win

        period_rows.append(
            {
                "Period": period["Period"],
                "Mechanism": period["Mechanism"],
                "Spin_Range": period["Spin_Range"],
                "Paid_Spins": paid_spins,
                "Base_Game_RTP_%": float(period["Base_Game_Win"]) / paid_spins * 100.0,
                "Jackpot_Actual_RTP_%": float(period["Jackpot_Win"]) / paid_spins * 100.0,
                "Natural_RTP_%": natural_win / paid_spins * 100.0,
                "Newbie_D_RTP_%": newbie_win / paid_spins * 100.0,
                "Rescue_RTP_%": final_win / paid_spins * 100.0,
                "Newbie_D_Delta_pp": (newbie_win - natural_win) / paid_spins * 100.0,
                "Oldhand_C_Delta_pp": (final_win - newbie_win) / paid_spins * 100.0,
                "RTP_Delta_pp": (final_win - natural_win) / paid_spins * 100.0,
                "Newbie_D_Trigger_Count": period["Newbie_D_Trigger_Count"],
                "Oldhand_C_Trigger_Count": period["Oldhand_C_Trigger_Count"],
                "Oldhand_C_Eligible_Without_Common_Pool_Count": period["Oldhand_C_Eligible_Without_Common_Pool_Count"],
                "Oldhand_C_Actual_vs_Eligible_Rate_%": (period["Oldhand_C_Trigger_Count"] / period["Oldhand_C_Eligible_Without_Common_Pool_Count"] * 100.0 if period["Oldhand_C_Eligible_Without_Common_Pool_Count"] else 0.0),
                "Cumulative_Natural_RTP_%": cumulative_natural_win / cumulative_paid_spins * 100.0,
                "Cumulative_Newbie_D_RTP_%": cumulative_newbie_win / cumulative_paid_spins * 100.0,
                "Cumulative_Rescue_RTP_%": cumulative_final_win / cumulative_paid_spins * 100.0,
                "Cumulative_Newbie_D_Delta_pp": (cumulative_newbie_win - cumulative_natural_win) / cumulative_paid_spins * 100.0,
                "Cumulative_Oldhand_C_Delta_pp": (cumulative_final_win - cumulative_newbie_win) / cumulative_paid_spins * 100.0,
                "Cumulative_RTP_Delta_pp": (cumulative_final_win - cumulative_natural_win) / cumulative_paid_spins * 100.0,
            }
        )
    jackpot_weight_total = sum(weight for _, weight, _ in JACKPOT_CONFIG)
    jackpot_theoretical_rtp = sum(weight / JACKPOT_WEIGHT_DENOMINATOR * (award_cents / 100.0) for _, weight, award_cents in JACKPOT_CONFIG)
    jackpot_stat_rows = []
    for jackpot, weight, award_cents in JACKPOT_CONFIG:
        award_x = award_cents / 100.0
        jackpot_stat_rows.append(
            {
                "Jackpot": jackpot,
                "Jackpot_Weight": weight,
                "Jackpot_Probability_%": weight / JACKPOT_WEIGHT_DENOMINATOR * 100.0,
                "Jackpot_Award_Cents": award_cents,
                "Jackpot_X": award_x,
                "Jackpot_Theoretical_RTP_%": weight / JACKPOT_WEIGHT_DENOMINATOR * award_x * 100.0,
                "Jackpot_Trigger_Count": jackpot_counts[jackpot],
                "Jackpot_Actual_RTP_%": jackpot_counts[jackpot] * award_x / total_paid_spins * 100.0,
            }
        )
    total_checks = sum(stage_check_counts.values())
    experience_condition_matched_count = sum(stage_experience_match_counts.values())
    experience_condition_not_matched_count = total_checks - experience_condition_matched_count
    experience_not_matched_rows = [row for row in checkpoints if not bool(row["Condition_Matched"])]
    experience_short_only_not_matched_count = sum(not bool(row["Short_Bad"]) and bool(row["Mid_Bad"]) for row in experience_not_matched_rows)
    experience_mid_only_not_matched_count = sum(bool(row["Short_Bad"]) and not bool(row["Mid_Bad"]) for row in experience_not_matched_rows)
    experience_both_not_matched_count = sum(not bool(row["Short_Bad"]) and not bool(row["Mid_Bad"]) for row in experience_not_matched_rows)
    experience_long_not_matched_count = sum(bool(row["Short_Bad"]) and bool(row["Mid_Bad"]) and row.get("Long_Bad") is False for row in experience_not_matched_rows)
    total_triggers = sum(reward_counts.values())
    general_standard_check_count = total_checks - common_pool_insufficient_cancel_count - personal_pool_insufficient_count
    general_standard_pass_count = personal_pool_funded_trigger_count
    general_standard_fail_count = general_standard_check_count - general_standard_pass_count
    strict_standard_check_count = personal_pool_insufficient_count
    common_pool_limit_specs = (
        (
            (
                "共同池餘額",
                "共同池餘額不足，取消救援",
                "共同池目前餘額不足以支付本次完整救援成本。",
            ),
        )
        if ENABLE_COMMON_POOL
        else ()
    )
    pool_limit_specs = common_pool_limit_specs + (
        (
            "嚴格標準",
            "個人池不足且未通過嚴格標準，取消救援",
            "共同池足夠但個人池不足，且短期／中期／長期未通過嚴格標準。",
        ),
    )

    def pool_limit_row(
        level: str,
        limit_type: str,
        cancel_reason: str,
        source_rows: list[dict[str, Any]],
        type_total: int,
        stage: str,
        reward_x: float | str | None,
        scenario_summary: str,
    ) -> dict[str, Any]:
        def average(field: str) -> float | None:
            values = [float(row[field]) for row in source_rows if row.get(field) is not None]
            return float(np.mean(values)) if values else None

        return {
            "Limit_Level": level,
            "Limit_Type": limit_type,
            "Cancel_Reason": cancel_reason,
            "Stage": stage,
            "Reward_X": reward_x,
            "Count": len(source_rows),
            "Share_Within_Limit_%": len(source_rows) / type_total * 100.0 if type_total else 0.0,
            "Avg_Personal_RTP_%": average("Personal_RTP_%"),
            "Avg_Platform_RTP_Before_%": average("Platform_RTP_Before_%"),
            "Avg_Projected_Platform_RTP_%": average("Projected_Platform_RTP_%"),
            "Avg_Common_Pool_Balance_Before_X": average("Common_Pool_Balance_Before_X"),
            "Avg_Rescue_Cost_X": average("Rescue_Cost_X"),
            "Avg_Common_Pool_Balance_After_X": average("Common_Pool_Balance_After_X"),
            "Avg_Personal_Pool_Balance_Before_X": average("Personal_Pool_Balance_Before_X"),
            "Avg_Personal_Pool_Balance_After_X": average("Personal_Pool_Balance_After_X"),
            "Avg_Short_RTP_%": average("Short_RTP_%"),
            "Avg_Mid_RTP_%": average("Mid_RTP_%"),
            "Avg_Long_RTP_%": average("Long_RTP_%"),
            "Scenario_Summary": scenario_summary,
        }

    pool_limit_rows: list[dict[str, Any]] = []
    for limit_type, cancel_reason, summary_text in pool_limit_specs:
        limit_rows = [row for row in checkpoints if row["Pool_Result"] == cancel_reason]
        pool_limit_rows.append(
            pool_limit_row(
                "總計",
                limit_type,
                cancel_reason,
                limit_rows,
                len(limit_rows),
                "全部",
                "全部",
                summary_text if limit_rows else f"本次模擬未發生{limit_type}取消。",
            )
        )
        grouped_keys = sorted(
            {(str(row["Stage"]), row.get("Reward_X")) for row in limit_rows},
            key=lambda item: (item[0], float(item[1]) if item[1] is not None else -1.0),
        )
        for stage, reward_x in grouped_keys:
            grouped_rows = [row for row in limit_rows if str(row["Stage"]) == stage and row.get("Reward_X") == reward_x]
            reward_text = f"{float(reward_x):g}×" if reward_x is not None else "不適用"
            if limit_type == "共同池餘額":
                scenario = f"{stage} 階段原預定給 {reward_text}，但共同池餘額不足以支付完整救援成本。"
            else:
                scenario = f"{stage} 階段原預定給 {reward_text}，個人池不足且未通過嚴格標準。"
            pool_limit_rows.append(
                pool_limit_row(
                    "情境",
                    limit_type,
                    cancel_reason,
                    grouped_rows,
                    len(limit_rows),
                    stage,
                    reward_text,
                    scenario,
                )
            )
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
        actual_exit_rows = [row for row in fg_exit_rows if row["Display_Range"] == display_range and row["Scenario"] == "有機制"]
        natural_exit_rows = [row for row in fg_exit_rows if row["Display_Range"] == display_range and row["Scenario"] == "無機制"]
        block_completed_rows = [row for row in completed_stage_rows if row["Display_Range"] == display_range]
        rescue_usage_rows.append(
            usage_row(
                display_range,
                "新手 D" if block_stage == "新手 D" else "老手 C",
                block_players,
                actual_fg_count=len(actual_exit_rows),
                actual_avg_exit_spin=float(np.mean([int(row["Exit_Spin"]) for row in actual_exit_rows])) if actual_exit_rows else None,
                actual_fg_stop_rtp=float(np.mean([float(row["Exit_RTP_%"]) for row in actual_exit_rows])) if actual_exit_rows else None,
                natural_fg_count=len(natural_exit_rows),
                natural_avg_exit_spin=float(np.mean([int(row["Exit_Spin"]) for row in natural_exit_rows])) if natural_exit_rows else None,
                natural_fg_stop_rtp=float(np.mean([float(row["Exit_RTP_%"]) for row in natural_exit_rows])) if natural_exit_rows else None,
                completed_rtp=float(np.mean([float(row["Completed_Block_RTP_%"]) for row in block_completed_rows])) if block_completed_rows else None,
            )
        )

    stage_rows = []
    for stage in ("A", "B", "C", "D"):
        checks = stage_check_counts[stage]
        experience_match_count = stage_experience_match_counts[stage]
        trigger_count = stage_trigger_counts[stage]
        row: dict[str, Any] = {
            "Stage": stage,
            "Spin_Range": {"A": "201～300", "B": "301～400", "C": "401～500", "D": "501+"}[stage],
            "Short_RTP_Threshold_%": SHORT_RTP_THRESHOLD * 100.0,
            "Mid_RTP_Threshold_%": STAGE_MID_RTP[stage] * 100.0,
            "Long_RTP_Threshold_%": LONG_RTP_THRESHOLD * 100.0 if stage == "D" else None,
            "Strict_Mid_RTP_Threshold_%": STRICT_STAGE_MID_RTP[stage] * 100.0,
            "Strict_Long_RTP_Threshold_%": STRICT_LONG_RTP_THRESHOLD * 100.0 if stage == "D" else None,
            "Scheduled_Checkpoint_Count": stage_scheduled_counts[stage],
            "Evaluated_Checkpoint_Count": checks,
            "Experience_Condition_Matched_Count": experience_match_count,
            "Experience_Condition_Matched_Rate_%": experience_match_count / checks * 100.0 if checks else 0.0,
            "Cancelled_Checkpoint_Count": stage_cancelled_counts[stage],
            "Trigger_Count": trigger_count,
            "Trigger_Rate_%": trigger_count / checks * 100.0 if checks else 0.0,
        }
        for reward_label in REWARD_LABELS:
            row[reward_label] = sum(1 for item in triggers if item["Stage"] == stage and item["Tier"] == reward_label)
        stage_rows.append(row)

    tier_rows = []
    for reward_x in (REWARD_LOW_X, REWARD_HIGH_X):
        reward_label = f"{reward_x:g}×"
        tier_rows.append(
            {
                "Tier": reward_label,
                "Low_X": reward_x,
                "High_X": reward_x,
                "Trigger_Count": reward_counts[reward_label],
                "Share_of_Triggers_%": reward_counts[reward_label] / total_triggers * 100.0 if total_triggers else 0.0,
            }
        )

    rule_descriptions = {
        "STAGE_RTP_QUALIFIED": "符合該階段短期、中期及必要長期 RTP 門檻",
        "D_NO_LONG_WINDOW": "第4階段判定前沒有完整500轉資料",
        "NO_RESCUE": "未符合救援條件",
    }
    rule_rows = [{"Rule_ID": rule_id, "Description": rule_descriptions.get(rule_id, rule_id), "Count": count} for rule_id, count in sorted(rule_counts.items())]

    newbie_period_stats = [period for period in period_stats.values() if period["Mechanism"] == "新手 D"]
    oldhand_period_stats = [period for period in period_stats.values() if period["Mechanism"] == "老手 C"]

    newbie_period_paid_spins = sum(int(period["Paid_Spins"]) for period in newbie_period_stats)
    newbie_period_natural_win = sum(float(period["Natural_Win"]) for period in newbie_period_stats)
    newbie_period_mechanism_win = sum(float(period["Newbie_D_Win"]) for period in newbie_period_stats)
    oldhand_period_paid_spins = sum(int(period["Paid_Spins"]) for period in oldhand_period_stats)
    oldhand_period_natural_win = sum(float(period["Natural_Win"]) for period in oldhand_period_stats)
    oldhand_period_mechanism_win = sum(float(period["Final_Win"]) for period in oldhand_period_stats)

    def period_rtp(win: float, spins: int) -> float:
        return win / spins * 100.0 if spins else 0.0

    personal_pool_balances = [PERSONAL_POOL_INITIAL_BALANCE + state["personal_pool_spins"] * COMMON_POOL_CONTRIBUTION_RATE - state["personal_pool_spent"] for state in states.values()]
    personal_pool_negative_player_count = sum(balance < -1e-12 for balance in personal_pool_balances)
    personal_pool_total_balance = float(sum(personal_pool_balances))

    newbie_d_spin_50_checkpoint_count = sum(count for rule, count in newbie_d_rule_counts.items() if rule.startswith("D1_"))
    newbie_d_spin_150_checkpoint_count = sum(count for rule, count in newbie_d_rule_counts.items() if rule.startswith("D2_"))
    newbie_d_spin_50_not_trigger_count = newbie_d_rule_counts["D1_NO_RESCUE"]
    newbie_d_spin_150_not_trigger_count = newbie_d_rule_counts["D2_NO_RESCUE"]
    newbie_d_spin_50_trigger_count = newbie_d_spin_50_checkpoint_count - newbie_d_spin_50_not_trigger_count
    newbie_d_spin_150_trigger_count = newbie_d_spin_150_checkpoint_count - newbie_d_spin_150_not_trigger_count
    newbie_d_checkpoint_count = newbie_d_spin_50_checkpoint_count + newbie_d_spin_150_checkpoint_count
    newbie_d_trigger_count = newbie_d_spin_50_trigger_count + newbie_d_spin_150_trigger_count
    newbie_d_not_trigger_count = newbie_d_spin_50_not_trigger_count + newbie_d_spin_150_not_trigger_count

    summary = {
        **adapter.metadata(),
        "rtp_profile": RTP_PROFILE,
        "base_rtp_parameter_source": BASE_RTP_PARAMETER_SOURCE,
        "jackpot_parameter_source": JACKPOT_PARAMETER_SOURCE,
        "players": args.players,
        "spins_per_player": args.spins,
        "total_paid_spins": total_paid_spins,
        "checkpoint_interval_spins": CHECKPOINT_INTERVAL_SPINS,
        "checkpoint_active_spins": CHECKPOINT_ACTIVE_SPINS,
        "checkpoint_cooldown_spins": CHECKPOINT_COOLDOWN_SPINS,
        "common_pool_enabled": "開啟" if ENABLE_COMMON_POOL else "關閉",
        "common_pool_contribution_rate_%": COMMON_POOL_CONTRIBUTION_RATE * 100.0,
        "oldhand_base_rtp_target_%": OLDHAND_BASE_RTP_TARGET * 100.0,
        "oldhand_total_rtp_target_%": OLDHAND_TOTAL_RTP_TARGET * 100.0,
        "personal_pool_initial_balance_x": PERSONAL_POOL_INITIAL_BALANCE,
        "daily_50x_simulation_scope": DAILY_50X_SIMULATION_SCOPE,
        "pool_start_spin": NEWBIE_LAST_SPIN + 1,
        "common_pool_eligible_bets": common_pool_bet_total if ENABLE_COMMON_POOL else None,
        "common_pool_income_x": common_pool_bet_total * COMMON_POOL_CONTRIBUTION_RATE if ENABLE_COMMON_POOL else None,
        "common_pool_spent_x": common_pool_spent_total if ENABLE_COMMON_POOL else None,
        "common_pool_balance_x": (common_pool_bet_total * COMMON_POOL_CONTRIBUTION_RATE - common_pool_spent_total if ENABLE_COMMON_POOL else None),
        "scheduled_checkpoint_count": sum(stage_scheduled_counts.values()),
        "checkpoint_count": total_checks,
        "experience_condition_matched_count": experience_condition_matched_count,
        "experience_condition_matched_rate_%": (experience_condition_matched_count / total_checks * 100.0 if total_checks else 0.0),
        "experience_condition_not_matched_count": experience_condition_not_matched_count,
        "experience_short_only_not_matched_count": experience_short_only_not_matched_count,
        "experience_mid_only_not_matched_count": experience_mid_only_not_matched_count,
        "experience_both_not_matched_count": experience_both_not_matched_count,
        "experience_long_not_matched_count": experience_long_not_matched_count,
        "cancelled_checkpoint_count": sum(stage_cancelled_counts.values()),
        "common_pool_insufficient_cancel_count": (common_pool_insufficient_cancel_count if ENABLE_COMMON_POOL else None),
        "general_standard_check_count": general_standard_check_count,
        "general_standard_pass_count": general_standard_pass_count,
        "general_standard_fail_count": general_standard_fail_count,
        "strict_standard_check_count": strict_standard_check_count,
        "personal_pool_insufficient_count": personal_pool_insufficient_count,
        "strict_standard_pass_count": strict_standard_pass_count,
        "strict_standard_cancel_count": strict_standard_cancel_count,
        "personal_pool_funded_trigger_count": personal_pool_funded_trigger_count,
        "overdraft_trigger_count": overdraft_trigger_count,
        "overdraft_trigger_rate_%": overdraft_trigger_count / total_triggers * 100.0 if total_triggers else 0.0,
        "personal_pool_negative_player_count": personal_pool_negative_player_count,
        "personal_pool_total_balance_x": personal_pool_total_balance,
        "rescue_trigger_count": total_triggers,
        "rescue_50x_trigger_count": reward_counts["50×"],
        "rescue_20x_trigger_count": reward_counts["20×"],
        "rescue_trigger_rate_per_checkpoint_%": total_triggers / total_checks * 100.0 if total_checks else 0.0,
        "players_with_rescue": len(oldhand_players),
        "players_with_any_mechanism": len(any_mechanism_players),
        "player_any_mechanism_rate_%": len(any_mechanism_players) / args.players * 100.0,
        "players_with_newbie_d": len(newbie_d_players),
        "player_newbie_d_rate_%": len(newbie_d_players) / args.players * 100.0,
        "players_with_oldhand_c": len(oldhand_players),
        "player_oldhand_c_rate_%": len(oldhand_players) / args.players * 100.0,
        "oldhand_avg_triggers_all_players": total_triggers / args.players,
        "oldhand_avg_triggers_triggered_players": total_triggers / len(oldhand_players) if oldhand_players else 0.0,
        "jackpot_weight_denominator": JACKPOT_WEIGHT_DENOMINATOR,
        "jackpot_theoretical_hit_rate_%": jackpot_weight_total / JACKPOT_WEIGHT_DENOMINATOR * 100.0,
        "jackpot_theoretical_rtp_%": jackpot_theoretical_rtp * 100.0,
        "jackpot_trigger_count": jackpot_trigger_total,
        "jackpot_actual_hit_rate_%": jackpot_trigger_total / total_paid_spins * 100.0,
        "jackpot_actual_rtp_%": jackpot_win_total / total_paid_spins * 100.0,
        "base_game_rtp_%": base_win_total / total_paid_spins * 100.0,
        "game_rtp_with_jackpot_%": natural_win_total / total_paid_spins * 100.0,
        "natural_rtp_%": natural_win_total / total_paid_spins * 100.0,
        "newbie_period_paid_spins": newbie_period_paid_spins,
        "newbie_period_natural_rtp_%": period_rtp(newbie_period_natural_win, newbie_period_paid_spins),
        "newbie_d_rtp_%": period_rtp(newbie_period_mechanism_win, newbie_period_paid_spins),
        "newbie_d_rtp_delta_pp": period_rtp(
            newbie_period_mechanism_win - newbie_period_natural_win,
            newbie_period_paid_spins,
        ),
        "newbie_d_trigger_count": newbie_d_trigger_count,
        "newbie_d_checkpoint_count": newbie_d_checkpoint_count,
        "newbie_d_trigger_rate_%": (newbie_d_trigger_count / newbie_d_checkpoint_count * 100.0 if newbie_d_checkpoint_count else 0.0),
        "newbie_d_spin_50_trigger_count": newbie_d_spin_50_trigger_count,
        "newbie_d_spin_50_trigger_rate_%": (newbie_d_spin_50_trigger_count / newbie_d_spin_50_checkpoint_count * 100.0 if newbie_d_spin_50_checkpoint_count else 0.0),
        "newbie_d_spin_150_trigger_count": newbie_d_spin_150_trigger_count,
        "newbie_d_spin_150_trigger_rate_%": (newbie_d_spin_150_trigger_count / newbie_d_spin_150_checkpoint_count * 100.0 if newbie_d_spin_150_checkpoint_count else 0.0),
        "newbie_d_not_trigger_count": newbie_d_not_trigger_count,
        "newbie_d_spin_50_not_trigger_count": newbie_d_spin_50_not_trigger_count,
        "newbie_d_spin_150_not_trigger_count": newbie_d_spin_150_not_trigger_count,
        "oldhand_period_paid_spins": oldhand_period_paid_spins,
        "oldhand_period_natural_rtp_%": period_rtp(oldhand_period_natural_win, oldhand_period_paid_spins),
        "rescue_rtp_%": period_rtp(oldhand_period_mechanism_win, oldhand_period_paid_spins),
        "oldhand_c_rtp_delta_pp": period_rtp(
            oldhand_period_mechanism_win - oldhand_period_natural_win,
            oldhand_period_paid_spins,
        ),
        "overall_rescue_rtp_%": actual_win_total / total_paid_spins * 100.0,
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
        "period_rows": period_rows,
        "pool_limit_rows": pool_limit_rows,
        "jackpot_stat_rows": jackpot_stat_rows,
        "jackpot_rows": jackpot_rows,
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
    if len(parts) == 3 and parts[0] in {"A", "B", "C", "D", "CHECK"}:
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
            header = str(column_cells[0].value or "")
            is_percent_column = "(%)" in header
            values = [str(cell.value) if cell.value is not None else "" for cell in column_cells]
            width = min(60, max(10, max((len(value) for value in values), default=0) + 2))
            worksheet.column_dimensions[column_cells[0].column_letter].width = width
            for cell in column_cells[1:]:
                if not isinstance(cell.value, (int, float)) or isinstance(cell.value, bool):
                    continue
                if is_percent_column:
                    # 報表中的百分比已經用 92.00 表示 92%，因此只加上百分號字面值。
                    cell.number_format = '0.00"%"'
                elif isinstance(cell.value, float):
                    cell.number_format = "0.00"

        if worksheet.title == "總覽":
            for row_cells in worksheet.iter_rows(min_row=2):
                item = str(row_cells[0].value or "")
                value_cell = row_cells[1]
                if not isinstance(value_cell.value, (int, float)) or isinstance(value_cell.value, bool):
                    continue
                is_percentage = ("RTP" in item and "增量" not in item) or "比例" in item or "觸發率" in item or "門檻" in item
                if is_percentage:
                    value_cell.number_format = '0.00"%"'
                elif isinstance(value_cell.value, float):
                    value_cell.number_format = "0.00"


def write_report(result: dict[str, Any], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        _summary_frame(result["summary"]).to_excel(writer, sheet_name="總覽", index=False)
        _localized_frame(result["stage_rows"]).to_excel(writer, sheet_name="階段統計", index=False)
        _localized_frame(result["period_rows"]).to_excel(writer, sheet_name="各時期RTP增量", index=False)
        _localized_frame(result["tier_rows"]).to_excel(writer, sheet_name="獎項統計", index=False)
        _localized_frame(result["rule_rows"]).to_excel(writer, sheet_name="規則統計", index=False)
        _localized_frame(result["rescue_usage_rows"]).to_excel(writer, sheet_name="救援玩家比例", index=False)
        _localized_frame(result["newbie_d_rule_rows"]).to_excel(writer, sheet_name="新手D統計", index=False)
        _localized_frame(result["newbie_d_rows"]).to_excel(writer, sheet_name="新手D明細", index=False)
        _localized_frame(result["checkpoint_rows"]).to_excel(writer, sheet_name="判定明細", index=False)
        _localized_frame(result["pool_limit_rows"]).to_excel(writer, sheet_name="Pool上限統計", index=False)
        _localized_frame(result["trigger_rows"]).to_excel(writer, sheet_name="觸發明細", index=False)
        _localized_frame(result["player_rows"]).to_excel(writer, sheet_name="玩家統計", index=False)
        _localized_frame(result["jackpot_stat_rows"]).to_excel(writer, sheet_name="彩金統計", index=False)
        _localized_frame(result["jackpot_rows"]).to_excel(writer, sheet_name="彩金明細", index=False)
        winning_player_rows = sorted(
            (row for row in result["player_rows"] if float(row["Rescue_RTP_%"]) > 100.0),
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
    filename = f"simulator_system_{SYSTEM_VERSION}_{RTP_PROFILE_MODE}_" f"{args.base_game}_{args.players}p_{args.spins}s_{timestamp}.xlsx"
    return Path(args.report_dir) / filename


def print_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    value_column = 48

    def section(title: str) -> None:
        print(f"\n[{title}]")

    def row(label: str, value: str) -> None:
        label_width = wcswidth(label)
        if label_width < 0:
            label_width = len(label)
        padding = " " * max(1, value_column - label_width)
        print(f"  {label}{padding}{value}")

    print("\n" + "=" * 62)
    print(f"  老手救援 C 模擬結果｜系統版本 {summary['system_version']}")
    print("=" * 62)

    section("模擬資料")
    row("RTP 配置", "Game 94% + 0% Lnik + 2% Bonus")
    row("遊戲模型", str(summary["game"]))
    row("基礎遊戲", str(summary["base_game"]))
    row(
        "資料數量（玩家數*轉數=Total Spin）",
        f"{summary['players']:,}*{summary['spins_per_player']:,}= {summary['total_paid_spins']:,}",
    )
    row("RTP（不含機制）", f"{summary['oldhand_base_rtp_target_%']:.2f}%")
    row("RTP", f"{summary['oldhand_total_rtp_target_%']:.2f}%")

    section("Pool 判定結果")

    print("\n  判定門檻")
    row(
        "  ├─ 判定資料窗口",
        f"短期 {WINDOW_SHORT} 轉／中期 {WINDOW_MID} 轉／長期 {WINDOW_LONG} 轉（不含判定轉）",
    )
    row("  ├─ 一般短期", f"RTP < {SHORT_RTP_THRESHOLD * 100:.2f}%")
    row(
        "  ├─ 一般中期（A／B／C／D）",
        "／".join(f"{STAGE_MID_RTP[stage] * 100:.2f}%" for stage in "ABCD"),
    )
    row("  ├─ 一般長期（D）", f"RTP < {LONG_RTP_THRESHOLD * 100:.2f}%")
    row("  ├─ 嚴格短期", f"RTP < {STRICT_SHORT_RTP_THRESHOLD * 100:.2f}%")
    row(
        "  ├─ 嚴格中期（A／B／C／D）",
        "／".join(f"{STRICT_STAGE_MID_RTP[stage] * 100:.2f}%" for stage in "ABCD"),
    )
    row("  └─ 嚴格長期（D）", f"RTP < {STRICT_LONG_RTP_THRESHOLD * 100:.2f}%")

    print("\n  體驗")
    row(
        "  ├─ 觸發體驗次數",
        f"{summary['newbie_d_trigger_count']:,} 次（{summary['newbie_d_trigger_rate_%']:.2f}%）",
    )
    row(
        "  ├─ 觸發體驗次數（50轉）",
        f"{summary['newbie_d_spin_50_trigger_count']:,} 次（{summary['newbie_d_spin_50_trigger_rate_%']:.2f}%）",
    )
    row(
        "  ├─ 觸發體驗次數（150轉）",
        f"{summary['newbie_d_spin_150_trigger_count']:,} 次（{summary['newbie_d_spin_150_trigger_rate_%']:.2f}%）",
    )
    row("  └─ 體驗條件未符合", f"{summary['newbie_d_not_trigger_count']:,} 次")
    print("      未觸發原因：")
    row("      ├─ 第50轉：判定前累積 RTP ≥ 100%", f"{summary['newbie_d_spin_50_not_trigger_count']:,} 次")
    row("      └─ 第150轉：判定前累積 RTP ≥ 85%", f"{summary['newbie_d_spin_150_not_trigger_count']:,} 次")

    print("\n  救援")
    row("  ├─ 共同池設定", "開啟" if summary["common_pool_enabled"] == "開啟" else "關閉（不限制救援）")
    row("  ├─ 總判定次數（每50轉判定一次）", f"{summary['checkpoint_count']:,} 次")
    total_check_count = summary["checkpoint_count"]
    rescue_success_rate = summary["rescue_trigger_count"] / total_check_count * 100.0 if total_check_count else 0.0
    overdraft_all_player_rate = summary["overdraft_trigger_count"] / summary["players"] * 100.0
    negative_pool_player_rate = summary["personal_pool_negative_player_count"] / summary["players"] * 100.0
    if summary["common_pool_enabled"] == "開啟":
        common_cancel_rate = summary["common_pool_insufficient_cancel_count"] / total_check_count * 100.0 if total_check_count else 0.0
        row(
            "  ├─ 共同池餘額不足，直接取消",
            f"{summary['common_pool_insufficient_cancel_count']:,} 次（占總判定 {common_cancel_rate:.2f}%）",
        )
        row("  ├─ 共同池累積收入", f"{summary['common_pool_income_x']:,.2f} 倍")
        row("  ├─ 共同池剩餘餘額", f"{summary['common_pool_balance_x']:,.2f} 倍")
    else:
        row("  ├─ 共同池累積收入", "未啟用")
        row("  ├─ 共同池剩餘餘額", "未啟用")
    row("  ├─ 個人池足夠，進入一般門檻", f"{summary['general_standard_check_count']:,} 次")
    row("  │   ├─ 一般門檻通過", f"{summary['general_standard_pass_count']:,} 次")
    row("  │   └─ 一般門檻未通過", f"{summary['general_standard_fail_count']:,} 次")
    row("  ├─ 個人池不足，進入嚴格門檻", f"{summary['strict_standard_check_count']:,} 次")
    row("  │   ├─ 嚴格門檻通過", f"{summary['strict_standard_pass_count']:,} 次")
    row("  │   └─ 嚴格門檻未通過", f"{summary['strict_standard_cancel_count']:,} 次")
    row(
        "  ├─ 成功發出救援次數",
        f"{summary['rescue_trigger_count']:,} 次（占總判定 {rescue_success_rate:.2f}%）",
    )
    row("  │   ├─ 50× 救援觸發", f"{summary['rescue_50x_trigger_count']:,} 次")
    row("  │   └─ 20× 救援觸發", f"{summary['rescue_20x_trigger_count']:,} 次")
    row(
        "  ├─ 個人池不夠還是有觸發",
        f"{summary['overdraft_trigger_count']:,} 次（占所有玩家 {overdraft_all_player_rate:.2f}%）",
    )
    row(
        "  ├─ 個人池負餘額玩家",
        f"{summary['personal_pool_negative_player_count']:,} 人（占所有玩家 {negative_pool_player_rate:.2f}%）",
    )
    row("  └─ 全部個人池餘額合計", f"{summary['personal_pool_total_balance_x']:,.2f} 倍")

    section("玩家使用情況")
    row("使用任一機制", f"{summary['players_with_any_mechanism']:,} 人（{summary['player_any_mechanism_rate_%']:.2f}%）")
    row("使用新手 D", f"{summary['players_with_newbie_d']:,} 人（{summary['player_newbie_d_rate_%']:.2f}%）")
    row("使用老手 C", f"{summary['players_with_oldhand_c']:,} 人（{summary['player_oldhand_c_rate_%']:.2f}%）")

    section("RTP 結果")
    row("基礎遊戲 RTP", f"{summary['base_game_rtp_%']:.2f}%")
    row("彩金 RTP", f"{summary['jackpot_actual_rtp_%']:.2f}%（理論 {summary['jackpot_theoretical_rtp_%']:.2f}%）")
    row("自然 RTP（不含機制）", f"{summary['natural_rtp_%']:.2f}%")
    row(
        "新手期套用 D 後",
        f"{summary['newbie_d_rtp_%']:.2f}%  [{summary['newbie_d_rtp_delta_pp']:+.2f} 個百分點]" f"（分母 {summary['newbie_period_paid_spins']:,} 轉）",
    )
    row(
        "老手期套用 C 後",
        f"{summary['rescue_rtp_%']:.2f}%  [{summary['oldhand_c_rtp_delta_pp']:+.2f} 個百分點]" f"（分母 {summary['oldhand_period_paid_spins']:,} 轉）",
    )
    row("全程套用機制後", f"{summary['overall_rescue_rtp_%']:.2f}%")
    row("相對自然 RTP 總增量", f"{summary['rtp_delta_pp']:+.2f} 個百分點")

    section("各時期 RTP 增量")
    for period in result["period_rows"]:
        trigger_count = period["Newbie_D_Trigger_Count"] if period["Mechanism"] == "新手 D" else period["Oldhand_C_Trigger_Count"]
        trigger_text = f"本階段觸發 {trigger_count:,} 次"
        if period["Mechanism"] == "老手 C":
            eligible_count = period["Oldhand_C_Eligible_Without_Common_Pool_Count"]
            trigger_rate = period["Oldhand_C_Actual_vs_Eligible_Rate_%"]
            trigger_text += f"，實際應該 {eligible_count:,} 次，觸發率 {trigger_rate:.2f}%"
        row(
            f"{period['Period']}（{period['Spin_Range']}）",
            (f"自然 {period['Natural_RTP_%']:.2f}% → " f"機制 {period['Rescue_RTP_%']:.2f}% " f"[{period['RTP_Delta_pp']:+.2f}%]；" f"累積 {period['Cumulative_Rescue_RTP_%']:.2f}% " f"[{period['Cumulative_RTP_Delta_pp']:+.2f}]；" f"{trigger_text}"),
        )

    section("觸發明細")
    row("彩金", f"{summary['jackpot_trigger_count']:,} 次（觸發率 {summary['jackpot_actual_hit_rate_%']:.2f}%）")
    row("新手 D", f"{summary['newbie_d_trigger_count']:,} 次")
    row("老手 C 獎項", "、".join(f"{item['Tier']}：{item['Trigger_Count']:,} 次" for item in result["tier_rows"]))

    section("執行資訊")
    row("耗時", f"{summary['duration_sec']:.2f} 秒")
    print("=" * 62)


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
    parser.add_argument(
        "--seed",
        type=int,
        default=SIMULATION_SEED,
        help=f"亂數種子；未指定時使用程式頂部 SIMULATION_SEED={SIMULATION_SEED}",
    )
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
            print("\n[輸出檔案]")
            print("  Excel 報表：")
            print(f"  {output}")
        return 0
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit_code = main()
    if "ipykernel" not in sys.modules:
        raise SystemExit(exit_code)
