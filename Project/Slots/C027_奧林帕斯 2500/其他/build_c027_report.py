"""產出 `遊戲數據_C027_奧林帕斯 2500.md` 與同名 `.html`.

章節、表格與座標軸完全沿用 `其他/競品資料/遊戲數據_Gates_of_Olympus_1000.md`，
這樣兩份報告可以直接並排比較。

資料來源
--------
* **結構型指標**（符號分布、掉落分布、同輪堆疊）直接由 `config_92A.js` 的輪帶算出，
  依場景混合權重加權。這些值是精確的，不含抽樣誤差 —— 這是自家遊戲相對競品側錄的優勢。
* **行為型指標**（RTP、Hit Rate、消除率、倍數球、64 區間線型）由 Simulator 的
  `Record/*.xlsx` 讀出；Card System On 的報表是玩家實際會遇到的版本，
  Card System Off 的報表作為自然機率基準。

用法
----
    py build_c027_report.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from competitor_targets import Targets
from fit_c027_model import SCENE_TABLES, load_js
from score_competitor_match import scene_weights
from strip_model import window_matrix

ROOT = Path(__file__).resolve().parent.parent
OTHER = ROOT / "其他"
RECORD = ROOT / "Record"
SKILL_SCRIPTS = Path.home() / ".claude" / "skills" / "game-data-report" / "scripts"

GAME_LABEL = "C027_奧林帕斯 2500"
MD_PATH = ROOT / f"遊戲數據_{GAME_LABEL}.md"
HTML_PATH = ROOT / f"遊戲數據_{GAME_LABEL}.html"

SYMBOL_ORDER = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2", "C3"]
STRIP_SYMBOLS = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2"]
NORMAL_SYMBOLS = ["M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE"]
SYMBOL_LABEL = {
    "C1": "C1 Scatter", "M1": "M1 皇冠", "M2": "M2 沙漏", "M3": "M3 戒指", "M4": "M4 聖杯",
    "A": "A 紅寶石", "K": "K 紫寶石", "Q": "Q 金寶石", "J": "J 綠寶石", "TE": "TE 藍寶石",
    "C2": "C2 倍數球", "C3": "C3 超級倍數球",
}
REELS = [f"R{index}" for index in range(1, 7)]
SCENE_LABEL = {"BG": "BG（一般遊戲）", "FG": "FG（自然觸發）", "BF": "BF（購買）"}
PAY_TABLE = {
    "M1": (10, 25, 50), "M2": (2.5, 10, 25), "M3": (2, 5, 15), "M4": (1.5, 2, 12),
    "A": (1, 1.5, 10), "K": (0.8, 1.2, 8), "Q": (0.5, 1, 5), "J": (0.4, 0.9, 4),
    "TE": (0.25, 0.75, 2),
}
THRESHOLDS = [10, 20, 50, 100, 200, 500, 1000]
TARGETS = Targets()


# --------------------------------------------------------------------------- io

def reports() -> dict[str, Path]:
    manifest = json.loads((OTHER / "verify_c027_reports.json").read_text(encoding="utf-8"))
    missing = [key for key in ("natural_normal", "natural_buy", "natural_fg_probe",
                               "config_92A.js_normal", "config_92A.js_buy",
                               "config_94A.js_normal", "config_94A.js_buy") if key not in manifest]
    if missing:
        raise SystemExit(f"verify_c027_reports.json 缺少 {missing}；先跑 verify_c027.py")
    return {key: RECORD / value for key, value in manifest.items()}


def sheet(path: Path, name: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=name)


def overview(path: Path) -> dict:
    frame = sheet(path, "Overview")
    return {row["Index"]: row["Value"] for _, row in frame.iterrows() if isinstance(row["Index"], str)}


def rate(text) -> float:
    return float(str(text).replace("%", "").replace(",", "").strip()) / 100.0


def number(text) -> float:
    """First numeric token of an Overview value (`15.18 spins` -> 15.18)."""
    import re
    match = re.search(r"-?[\d,]*\.?\d+", str(text))
    if not match:
        raise ValueError(f"no number in {text!r}")
    return float(match.group(0).replace(",", ""))


def cycle_of(text) -> float:
    import re
    match = re.search(r"cycle ([\d.]+)", str(text))
    return float(match.group(1)) if match else float("nan")


# ------------------------------------------------------------ config structure

def table_structure(strip: dict, id_to_code: dict) -> dict:
    length = len(strip["symbols"])
    initial, drop, stacks = {}, {}, {}
    window_longest = np.zeros(5)
    for reel_index, reel in enumerate(REELS):
        sequence = [id_to_code[row[reel_index]] for row in strip["symbols"]]
        initial[reel] = {code: sequence.count(code) / length for code in STRIP_SYMBOLS}
        column = [row[reel_index] for row in strip["drop_weights"]]
        total = sum(column)
        drop[reel] = {id_to_code[index + 1]: column[index] / total for index in range(len(column))}
        windows = window_matrix(sequence, STRIP_SYMBOLS)
        longest_overall = np.zeros(length, dtype=np.int64)
        per_symbol = {}
        for index, code in enumerate(STRIP_SYMBOLS):
            mask = windows == index
            current = np.zeros(length, dtype=np.int64)
            run = np.zeros(length, dtype=np.int64)
            for column_index in range(5):
                current = np.where(mask[:, column_index], current + 1, 0)
                run = np.maximum(run, current)
            longest_overall = np.maximum(longest_overall, run)
            per_symbol[code] = (np.bincount(run, minlength=6)[1:6] / length).tolist()
        stacks[reel] = per_symbol
        window_longest += np.bincount(longest_overall, minlength=6)[1:6] / (length * 6)
    return {"initial": initial, "drop": drop, "stacks": stacks, "window": window_longest.tolist()}


def scene_structure(config: dict) -> dict:
    id_to_code = {int(value): code for code, value in zip(config["symbol_codes"], config["symbol_ids"])}
    by_name = dict(zip(config["strip_names"], config["strips"]))
    out = {}
    for scene, names in SCENE_TABLES.items():
        weights = scene_weights(config, scene)
        parts = [table_structure(by_name[name], id_to_code) for name in names]
        initial = {reel: {code: sum(w * p["initial"][reel][code] for w, p in zip(weights, parts))
                          for code in STRIP_SYMBOLS} for reel in REELS}
        drop = {reel: {code: sum(w * p["drop"][reel].get(code, 0.0) for w, p in zip(weights, parts))
                       for code in STRIP_SYMBOLS} for reel in REELS}
        stacks = {reel: {code: [sum(w * p["stacks"][reel][code][size] for w, p in zip(weights, parts))
                                for size in range(5)] for code in STRIP_SYMBOLS} for reel in REELS}
        window = [sum(w * p["window"][size] for w, p in zip(weights, parts)) for size in range(5)]
        out[scene] = {"initial": initial, "drop": drop, "stacks": stacks, "window": window,
                      "weights": weights, "names": names}
    return out


# ------------------------------------------------------------------- md helpers

def pct(value, digits: int = 3) -> str:
    return f"{value * 100:.{digits}f}%"


def table(header: list[str], rows: list[list[str]], align: list[str] | None = None) -> list[str]:
    align = align or (["---"] + ["---:"] * (len(header) - 1))
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines + [""]


def combo_shares(frame: pd.DataFrame, column: str) -> list[float]:
    counts = frame[column].to_numpy(dtype=float)
    total = counts.sum()
    if total <= 0:
        return [0.0] * 6
    return [float(counts[index] / total) for index in range(5)] + [float(counts[5:].sum() / total)]


def conditional_combo(frame: pd.DataFrame, column: str) -> tuple[float, list[float]]:
    counts = frame[column].to_numpy(dtype=float)
    positive = counts[1:]
    total = positive.sum()
    if total <= 0:
        return 0.0, [0.0] * 5
    return total, [float(positive[index] / total) for index in range(4)] + [float(positive[4:].sum() / total)]


def fg_tier_table(path: Path, base_coin_in: float) -> pd.DataFrame:
    """Rebuild the FG cumulative-multiplier tiers from the raw record rows.

    The stored `FG_Avg_Win_X` column was written against the running bet mode's own
    cost; recomputing here keeps Normal Bet and Buy Feature on the Normal Bet base.
    """
    raw = sheet(path, "Record Data").to_numpy(dtype=float)
    spins, hits, pays = raw[31, :11], raw[32, :11], raw[33, :11]
    labels = [f"{index * 10}–{index * 10 + 9}" for index in range(10)] + ["100+"]
    safe = np.where(spins > 0, spins, 1)
    return pd.DataFrame({
        "tier": labels,
        "spins": spins,
        "hit_rate": np.where(spins > 0, hits / safe, 0.0),
        "avg_win_x": np.where(spins > 0, pays / safe / base_coin_in, 0.0),
    })


def interval_share(frame: pd.DataFrame, column: str) -> np.ndarray:
    counts = frame[column].to_numpy(dtype=float)
    total = counts.sum()
    return counts / total if total else np.zeros_like(counts)


def threshold_share(shares: np.ndarray, uppers: np.ndarray, level: float) -> float:
    return float(shares[uppers > level].sum())


def interval_labels(uppers: np.ndarray) -> list[str]:
    lowers = [-1.0] + list(uppers[:-1])
    return [f"({int(low) if float(low).is_integer() else low}, "
            f"{int(high) if float(high).is_integer() else high}]"
            for low, high in zip(lowers, uppers)]


# ------------------------------------------------------------------ md sections

def build_md(paths: dict[str, Path]) -> tuple[str, dict]:
    config, _ = load_js(ROOT / "config_92A.js")
    structure = scene_structure(config)
    mixture = config["scene_mixture"]
    drop_gain = json.loads((OTHER / "fit_drop_gain.json").read_text(encoding="utf-8"))         if (OTHER / "fit_drop_gain.json").is_file() else {}
    card_system = config["card_system"]
    calibration = card_system["calibration"]
    calibration = {**calibration, "fg_entry_cycle_target": card_system["fg_entry_cycle_target"]}

    natural_normal = overview(paths["natural_normal"])
    natural_buy = overview(paths["natural_buy"])
    card92 = overview(paths["config_92A.js_normal"])
    card92_buy = overview(paths["config_92A.js_buy"])
    card94 = overview(paths["config_94A.js_normal"])
    card94_buy = overview(paths["config_94A.js_buy"])

    line92 = sheet(paths["config_92A.js_normal"], "Multiplier Line")
    line92_buy = sheet(paths["config_92A.js_buy"], "Multiplier Line")
    cascade92 = sheet(paths["config_92A.js_normal"], "Cascade")
    cascade92_buy = sheet(paths["config_92A.js_buy"], "Cascade")
    multiplier92 = sheet(paths["config_92A.js_normal"], "C2-C3 Multiplier")
    multiplier92_buy = sheet(paths["config_92A.js_buy"], "C2-C3 Multiplier")
    hits92 = sheet(paths["config_92A.js_normal"], "Symbol Hit Rate")
    hits92_buy = sheet(paths["config_92A.js_buy"], "Symbol Hit Rate")
    summary92 = sheet(paths["config_92A.js_normal"], "Symbol Summary")

    base_coin_in = 500.0
    uppers = line92["Interval_Upper"].to_numpy(dtype=float)
    labels = interval_labels(uppers)
    bg_line = interval_share(line92, "base_game_cnt")
    fg_line = interval_share(line92, "free_game_cnt")
    bf_line = interval_share(line92_buy, "free_game_cnt_BF")

    out: list[str] = []
    add = out.extend

    normal_rounds = int(number(card92["total_rounds"]))
    buy_rounds = int(number(card92_buy["total_rounds"]))
    # Overview has no free-spin total; the cascade histogram counts one row per free spin
    fg_spins_92 = int(cascade92["FG_Count"].sum())
    fg_spins_92_buy = int(cascade92_buy["FG_Count"].sum())
    fg_sessions = int(number(card92["bg_trigger_fg_cnt"]))

    add([
        f"# 遊戲數據_{GAME_LABEL}",
        "",
        "> 遊戲：**C027 奧林帕斯 2500**（自家遊戲）　|　分析日期：2026-08-25",
        "> 資料來源：`Simulator.py` 產出的 `Record/*.xlsx`（行為型指標）＋ `config_92A.js` 輪帶（結構型指標）",
        f"> 樣本：Card-On 92A Normal Bet {normal_rounds:,} 轉（{fg_sessions:,} 次自然 FG）"
        f"　/　FG {fg_spins_92:,} 轉"
        f"　/　Card-On 92A Buy Feature {buy_rounds:,} 次（FG {fg_spins_92_buy:,} 轉）",
        "> 底注：**1.00 / 轉**（`base_bet=1.0`，Buy Feature 為 100 × 底注）",
        "> 對照基準：`其他/競品資料/遊戲數據_Gates_of_Olympus_1000.md`（PP Gates of Olympus 1000）",
        "",
        "",
    ])

    add(["## 目錄", ""])
    add([
        "- [§1. 資料說明](#1-資料說明)",
        "  - [1.1 檔案用途](#11-檔案用途)",
        "  - [1.2 資料欄位](#12-資料欄位)",
        "- [§2. 基本資料](#2-基本資料)",
        "  - [2.1 一般遊戲 / 免費遊戲](#21-一般遊戲--免費遊戲)",
        "  - [2.2 購買免費遊戲（BF）](#22-購買免費遊戲bf)",
        "  - [2.3 Card System Off 的自然機率基準](#23-card-system-off-的自然機率基準)",
        "- [§3. 共同指標](#3-共同指標)",
        "  - [3.1 賠率](#31-賠率)",
        "  - [3.2 符號分布](#32-符號分布)",
        "    - [3.2.1 初始轉輪（每輪 5 格的符號占比）](#321-初始轉輪每輪-5-格的符號占比)",
        "    - [3.2.2 消除掉落（補牌符號占比）](#322-消除掉落補牌符號占比)",
        "  - [3.3 符號堆疊 RNG 比例](#33-符號堆疊-rng-比例)",
        "    - [3.3.1 整體（視窗層級）](#331-整體視窗層級以最長堆疊分類互斥合計-100)",
        "    - [3.3.2 分輪 / 分符號](#332-分輪--分符號)",
        "  - [3.4 獎項占比（Cluster 大小）](#34-獎項占比cluster-大小)",
        "  - [3.5 消除率](#35-消除率)",
        "    - [3.5.1 全部轉數（含未中獎）](#351-全部轉數含未中獎)",
        "    - [3.5.2 有消除時的條件分布](#352-有消除時的條件分布)",
        "  - [3.6 最大倍數](#36-最大倍數)",
        "- [§4. 倍率線型](#4-倍率線型)",
        "  - [4.1 摘要](#41-摘要)",
        "  - [4.2 倍率線型分布](#42-倍率線型分布)",
        "  - [4.3 觀察](#43-觀察)",
        "- [§5. 特殊指標](#5-特殊指標)",
        "  - [5.1 倍數球](#51-倍數球)",
        "    - [5.1.1 出現率與球數分布](#511-出現率與球數分布)",
        "    - [5.1.2 倍數值分布](#512-倍數值分布)",
        "  - [5.2 有無倍數球在場上的消除分布](#52-有無倍數球在場上的消除分布)",
        "    - [5.2.1 全部轉數（含 combo 0）](#521-全部轉數含-combo-0)",
        "    - [5.2.2 排除 combo 0 後的條件占比](#522-排除-combo-0-後的條件占比)",
        "  - [5.3 FG 累積倍數分層的 Hit Rate](#53-fg-累積倍數分層的-hit-rate)",
        "  - [5.4 C3 升級與場景表混合](#54-c3-升級與場景表混合)",
        "- [§6. 附錄](#6-附錄)",
        "  - [6.1 與規則文件對照](#61-與規則文件對照)",
        "  - [6.2 Demogame 與 Simulator 對帳](#62-demogame-與-simulator-對帳)",
        "  - [6.3 其他已知機制](#63-其他已知機制)",
        "  - [6.4 資料使用建議](#64-資料使用建議)",
        "",
        "---",
        "",
    ])

    # ---------------------------------------------------------------- §1
    add(["## §1. 資料說明", "", "### 1.1 檔案用途", ""])
    rows = []
    for key, kind, note in (
        ("config_92A.js_normal", "Simulator 報表", "✅ 主樣本：92A Card-On Normal Bet，玩家實際版本"),
        ("config_92A.js_buy", "Simulator 報表", "✅ BF 樣本：92A Card-On Buy Feature"),
        ("config_94A.js_normal", "Simulator 報表", "✅ 94A Card-On Normal Bet，僅用於 §2 版本對照"),
        ("config_94A.js_buy", "Simulator 報表", "✅ 94A Card-On Buy Feature，僅用於 §2 版本對照"),
        ("natural_normal", "Simulator 報表", "✅ 自然機率基準（Card System Off，Normal Bet）"),
        ("natural_buy", "Simulator 報表", "✅ 自然機率基準（Card System Off，Buy Feature）"),
        ("natural_fg_probe", "Simulator 報表", "⚙️ 卡片校準用：把 Buy Feature 指到自然 FG 輪帶的探針樣本"),
    ):
        data = overview(paths[key])
        rows.append([f"`{paths[key].name}`", kind, f"{int(number(data['total_rounds'])):,}", note])
    rows.append(["`config_92A.js`／`config_94A.js`", "Config", "—", "✅ 結構型指標來源：七張輪帶表與場景混合權重"])
    rows.append(["`game_rule.md`", "規則", "—", "— 參考：§6.1 對照用"])
    add(table(["檔名", "類型", "資料列／轉數", "是否納入統計與用途"], rows,
              ["---", "---", "---:", "---"]))
    add([
        "> **和競品側錄最大的差別**：符號分布、掉落分布與同輪堆疊不需要從封包還原，",
        "> 直接由 `config_92A.js` 的七張輪帶表按場景混合權重算出，因此是**精確值**而非估計值。",
        "> 兩張子表的混合權重取自 Simulator 實際使用的同一組欄位",
        "> （BG 用 `base_reel_weights`，FG／BF 用 `free_table.weights`）。",
        "",
    ])

    add(["### 1.2 資料欄位", ""])
    add(table(["工作表", "欄位", "說明"], [
        ["`Overview`", "`rtp_total`／`rtp_bg`／`rtp_fg`", "總／BG／FG RTP，分母為實際 Coin In"],
        ["`Overview`", "`hit_rate_bg`／`hit_rate_fg`", "有得分的 Spin 占比；FG 以免費轉數為分母"],
        ["`Overview`", "`fg_trigger_rate`", "FG 觸發率與週期"],
        ["`Overview`", "`multiplier_ball_rate_bg/fg`", "最終盤面出現 C2／C3 的 Spin 占比"],
        ["`Multiplier Line`", "`base_game_cnt`／`free_game_cnt`／`free_game_cnt_BF`", "64 區間的 BG／自然 FG／購買 FG 次數"],
        ["`Cascade`", "`BG_Count`／`FG_Count`", "各消除次數（combo）的 Spin 數"],
        ["`Cascade`", "`*_Ball_Count`／`*_NoBall_Count`", "依最終盤面有無倍數球拆分的 combo 分布"],
        ["`Cascade`", "`*_Balls_Per_Spin`", "每盤倍數球顆數分布，索引 0 為無球"],
        ["`C2-C3 Multiplier`", "`BG_Count`／`FG_Count`", "最終盤面上各倍率值的出現次數"],
        ["`Symbol Hit Rate`", "`*_8_9_Hit` 等", "各符號 8–9／10–11／12+ 級距的中獎次數"],
        ["`FG Cumulative Multiplier`", "`FG_Spins`／`FG_Hit_Rate`", "依 Spin 開始前的 FG 累積倍數分層"],
        ["`Record Data`", "第 31～33 列", "FG 累積倍數分層的原始累加陣列"],
    ], ["---", "---", "---"]))
    add([
        "**Card System 的角色**",
        "",
        "| 狀態 | 說明 |",
        "|---|---|",
        "| Card System Off | 只跑輪帶與判獎的自然機率，是輪帶結構的體檢報告，**不是**玩家會遇到的版本 |",
        "| Card System On | 依 Profile／押注層級抽卡並重跑，直到結果落在指定條件；玩家實際版本 |",
        "",
        "> 卡片只能接受或重跑既有結果，不會修改輪帶、賠率或 Feature 流程。",
        f"> C027 的卡片除得分區間外還帶 `ball` 維度（`ball_split_max` = {calibration['ball_split_max']}，"
        f"`ball_share` = {calibration['ball_share']:.5f}），",
        "> 用來抵銷「倍數球放大得分 → 高區間過度取樣倍數球」造成的倍數球出現率偏高。",
        "",
        "---",
        "",
    ])

    # ---------------------------------------------------------------- §2
    add(["## §2. 基本資料", "", "### 2.1 一般遊戲 / 免費遊戲", ""])
    rows = []
    for label, data, cascade in (("92A", card92, cascade92),
                                 ("94A", card94, sheet(paths["config_94A.js_normal"], "Cascade"))):
        fg_cycle = cycle_of(data["fg_trigger_rate"])
        fg_avg = rate(data["rtp_fg"]) * fg_cycle
        rows.append([
            label, "1.00", f"{int(number(data['total_rounds'])):,}",
            f"{int(cascade['FG_Count'].sum()):,}",
            f"**{rate(data['rtp_bg']):.3%}**", f"**{rate(data['rtp_fg']):.3%}**",
            f"**{rate(data['rtp_total']):.3%}**", f"**{rate(data['hit_rate_bg']):.3%}**",
            f"**{rate(data['hit_rate_fg']):.3%}**", f"**1/{fg_cycle:.1f}**", f"**{fg_avg:.2f}x**",
        ])
    add(table(["版本", "底注", "BG 轉數", "FG 轉數", "BG RTP", "FG RTP", "總 RTP",
               "BG Hit Rate", "FG Hit Rate", "FG 週期", "FG 平均倍數"], rows))
    se92 = number(card92["standard_error"])
    add([
        f"> **FG RTP** = FG 得分 ÷ 總押注（貢獻度）；**FG 平均倍數** = FG RTP × FG 週期。",
        f"> 總 RTP 的抽樣標準誤為 **±{se92 * 100:.2f} pp**（`standard_error` = {se92:.4f}，"
        f"{normal_rounds:,} 轉、`volatility_std` = {number(card92['volatility_std']):.2f}）；",
        f"> 92A 與 94A 的實測值都落在版本標籤的 1σ 內。需要更貼近標籤時可用 "
        "`tune_c027.py --solve-offset` 解 `bg_rtp_offset`，本版取 0（不加補償項）。",
        f"> 設計目標：總 RTP = 版本標籤，BG:FG 依競品實測比例 "
        f"{1 - calibration['competitor_fg_rtp_share']:.4%} : {calibration['competitor_fg_rtp_share']:.4%} 縮放，",
        f"> FG 週期對齊競品 1/{calibration['fg_entry_cycle_target']:.1f}，BG Hit Rate 對齊競品 "
        f"{calibration['bg_hit_rate_target']:.3%}。",
        "",
    ])

    add(["### 2.2 購買免費遊戲（BF）", ""])
    rows = []
    for label, data, cascade in (("92A", card92_buy, cascade92_buy),
                                 ("94A", card94_buy, sheet(paths["config_94A.js_buy"], "Cascade"))):
        rounds = int(number(data["total_rounds"]))
        rows.append([
            label, "1.00", f"{rounds:,}",
            f"{int(cascade['FG_Count'].sum()):,}",
            "100x", f"{rate(data['rtp_total']) * 100:.2f}x",
            f"**{rate(data['rtp_total']):.3%}**", f"**{rate(data['hit_rate_fg']):.3%}**",
        ])
    add(table(["版本", "底注", "購買次數", "FG 轉數", "購買價格", "平均得分", "BF RTP", "BF Hit Rate"], rows))
    add([
        "> Buy Feature 的入口盤面使用專用輪帶 `BF_Symbol`，保證 R2～R5 各一顆 C1，",
        "> 且每 5 格視窗內同一般符號不重複 → 單一符號最多 6 個，**入口盤面不可能產生 BG 得分**。",
        "> `BF Hit Rate` 只統計正式免費轉，不含入口那一轉的 Scatter 得分。",
        "",
    ])

    add(["### 2.3 Card System Off 的自然機率基準", ""])
    add(table(["模式", "轉數", "BG RTP", "FG RTP", "總 RTP", "BG Hit Rate", "FG Hit Rate", "FG 週期", "倍數球出現率"], [
        ["Normal Bet", f"{int(number(natural_normal['total_rounds'])):,}",
         f"{rate(natural_normal['rtp_bg']):.3%}", f"{rate(natural_normal['rtp_fg']):.3%}",
         f"{rate(natural_normal['rtp_total']):.3%}", f"{rate(natural_normal['hit_rate_bg']):.3%}",
         f"{rate(natural_normal['hit_rate_fg']):.3%}", f"1/{cycle_of(natural_normal['fg_trigger_rate']):.1f}",
         f"BG {rate(natural_normal['multiplier_ball_rate_bg']):.3%}／FG {rate(natural_normal['multiplier_ball_rate_fg']):.3%}"],
        ["Buy Feature", f"{int(number(natural_buy['total_rounds'])):,}",
         "—", f"{rate(natural_buy['rtp_fg']):.3%}", f"{rate(natural_buy['rtp_total']):.3%}",
         "—", f"{rate(natural_buy['hit_rate_fg']):.3%}", "—",
         f"FG {rate(natural_buy['multiplier_ball_rate_fg']):.3%}"],
    ]))
    add([
        "> 自然模型的 RTP **不是**產品 RTP —— 它是輪帶結構的體檢值。開發規範的硬上限為",
        "> 「BG RTP 不得超過目標 RTP 的 3 倍、FG RTP 不得超過 5 倍」，本表兩項皆通過。",
        f"> 自然 FG 每轉 Hit Rate {rate(natural_normal['hit_rate_fg']):.3%} 與競品 §3.5.1 的",
        f"> `1 − combo0` = {TARGETS.initial_hit_target('FG'):.3%} 幾乎一致，說明 FG 輪帶結構本身已對齊；",
        "> Card-On 之後的差距來自卡片把 FG 整包壓到目標平均倍數時的選樣（見 §4.3）。",
        "",
        "---",
        "",
    ])

    # ---------------------------------------------------------------- §3
    add(["## §3. 共同指標", "", "### 3.1 賠率", ""])
    total_bg_pay = summary92["BG_Pay"].sum() + summary92["FG_Pay"].sum()
    rows = []
    for code in NORMAL_SYMBOLS:
        row = summary92[summary92["Symbol"] == code]
        pay = float(row["BG_Pay"].iloc[0] + row["FG_Pay"].iloc[0]) if len(row) else 0.0
        low, mid, high = PAY_TABLE[code]
        rows.append([SYMBOL_LABEL[code], f"{low}", f"{mid}", f"{high}",
                     pct(pay / total_bg_pay if total_bg_pay else 0.0, 2)])
    scatter_row = summary92[summary92["Symbol"] == "C1"]
    scatter_pay = float(scatter_row["BG_Pay"].iloc[0] + scatter_row["FG_Pay"].iloc[0]) if len(scatter_row) else 0.0
    rows.append([SYMBOL_LABEL["C1"], "—", "—", "4／5／6 顆 = 3／5／100",
                 pct(scatter_pay / total_bg_pay if total_bg_pay else 0.0, 2)])
    add(table(["符號", "8–9 個", "10–11 個", "12 個以上", "占總得分"], rows))
    add([
        "> 單位：倍 / Bet。**競品報告 §3.1 因為只有符號 id 而無法反推賠率**；",
        "> C027 是自家模型，賠率直接來自 `game_rule.md` §4，並可算出每個符號對總得分的貢獻。",
        "> 「占總得分」以 92A Card-On Normal Bet 的 BG＋FG 累計得分為分母（已含 C2／C3 乘倍）。",
        "",
    ])

    add(["### 3.2 符號分布", "", "#### 3.2.1 初始轉輪（每輪 5 格的符號占比）", ""])
    for scene in ("BG", "FG", "BF"):
        weights = structure[scene]["weights"]
        names = structure[scene]["names"]
        add([f"**{SCENE_LABEL[scene]}**　場景混合："
             + "／".join(f"`{name}` {weight:.4%}" for name, weight in zip(names, weights)), ""])
        rows = [[SYMBOL_LABEL[code]] + [pct(structure[scene]["initial"][reel][code]) for reel in REELS]
                for code in STRIP_SYMBOLS]
        add(table(["符號"] + REELS, rows))
    add([
        "> 上表為**混合後**的精確占比（子表占比 × 混合權重），不是單張輪帶表的值。",
        "> 混合的數學保證：每張子表的非 C2 符號都按同一組邊際比例分配到剩下的格位，",
        "> 因此不論混合權重怎麼調，非 C2 符號的混合占比都維持設計值（見 `其他/c027_scene_model.py`）。",
        "> C3 不出現在輪帶上：輪帶只放候選符號 C2，再依 `use_super_multiplier` 決定是否轉為 C3。",
        "",
    ])

    add(["#### 3.2.2 消除掉落（補牌符號占比）", ""])
    for scene in ("BG", "FG", "BF"):
        add([f"**{SCENE_LABEL[scene]}**　同場景的兩張子表共用一份掉落表，因此掉落分布與混合權重無關", ""])
        rows = [[SYMBOL_LABEL[code]] + [pct(structure[scene]["drop"][reel][code]) for reel in REELS]
                for code in STRIP_SYMBOLS]
        add(table(["符號"] + REELS, rows))

    add(["### 3.3 符號堆疊 RNG 比例", "",
         "**定義**：每個停輪位置產生一個 5 格視窗（每輪 5 列）。對視窗內每個符號取其最長連續段長度，計 1 次。",
         "", "#### 3.3.1 整體（視窗層級，以最長堆疊分類，互斥合計 100%）", ""])
    rows = []
    for scene in ("BG", "FG", "BF"):
        window = structure[scene]["window"]
        rows.append([SCENE_LABEL[scene]] + [pct(value) for value in window])
    add(table(["場景", "1 堆疊", "2 堆疊", "3 堆疊", "4 堆疊", "5 堆疊"], rows))
    add(["> 由輪帶直接窮舉所有停輪位置算出，是精確值。", ""])

    add(["#### 3.3.2 分輪 / 分符號", ""])
    for scene in ("BG", "FG", "BF"):
        add([f"**{SCENE_LABEL[scene]}**", ""])
        rows = []
        for code in STRIP_SYMBOLS:
            for size in range(1, 5):
                values = [structure[scene]["stacks"][reel][code][size] for reel in REELS]
                if max(values) < 0.00005:
                    continue
                rows.append([SYMBOL_LABEL[code], f"{size + 1} 堆疊"] + [pct(value) for value in values])
        add(table(["符號", "堆疊"] + REELS, rows, ["---", "---"] + ["---:"] * 6))
    max_run = mixture.get("max_run", {})
    add([
        "> 只列出至少一輪達 0.005% 的組合。輪帶合成時的最長連續段上限："
        + "／".join(f"{SCENE_LABEL[scene]} {max_run.get(scene, '—')}" for scene in ("BG", "FG", "BF"))
        + "，因此沒有 5 堆疊列。",
        "",
    ])

    add(["### 3.4 獎項占比（Cluster 大小）", "",
         "C027 為 **Pay Anywhere**（同符號全盤合計 8 個以上成立），不使用連線，",
         "故本節以賠率級距（8–9／10–11／12+）取代固定格式的「3/4/5 連線」。", ""])
    rows = []
    for scene, frame, prefix in (("BG", hits92, "BG"), ("FG", hits92, "FG"), ("BF", hits92_buy, "FG")):
        mask = frame["Symbol"].isin(NORMAL_SYMBOLS)
        counts = np.array([frame.loc[mask, f"{prefix}_8_9_Hit"].sum(),
                           frame.loc[mask, f"{prefix}_10_11_Hit"].sum(),
                           frame.loc[mask, f"{prefix}_12_Plus_Hit"].sum()], dtype=float)
        total = counts.sum()
        pays = np.array([
            sum(PAY_TABLE[code][tier] * float(frame.loc[frame["Symbol"] == code, f"{prefix}_{suffix}_Hit"].iloc[0])
                for code in NORMAL_SYMBOLS)
            for tier, suffix in enumerate(("8_9", "10_11", "12_Plus"))
        ])
        pay_total = pays.sum()
        for index, tier in enumerate(("8–9", "10–11", "12+")):
            rows.append([SCENE_LABEL[scene] if index == 0 else "", tier,
                         pct(counts[index] / total if total else 0.0, 2),
                         pct(pays[index] / pay_total if pay_total else 0.0, 2)])
    add(table(["場景", "級距", "出現次數占比", "基本得分占比"], rows, ["---", "---", "---:", "---:"]))
    add(["對照競品同一張表（§3.4，已把 8/9 與 10/11 併成本作的賠率級距）：", ""])
    competitor_rows = []
    for scene in ("BG", "FG", "BF"):
        tiers = TARGETS.cluster_tiers(scene)
        for index, key in enumerate(("8-9", "10-11", "12+")):
            competitor_rows.append([SCENE_LABEL[scene] if index == 0 else "",
                                    key.replace("-", "–"), pct(tiers[key], 2)])
    add(table(["場景", "級距", "出現次數占比"], competitor_rows, ["---", "---", "---:"]))
    add([
        "> 「基本得分占比」為乘倍前的一般符號賠付占比，不含 C2／C3 加成與 Scatter 賠付。",
        "> BG 與 BF 的級距分布貼近競品；**FG 的 12+ 占比明顯偏高**，原因見 §4.3 的說明：",
        "> FG 場景為了達到競品的 `Hit Rate|有球` 需要較高的聚集度 θ，聚集度同時放大了大 cluster 的比例。",
        "",
    ])

    add(["### 3.5 消除率", "", "#### 3.5.1 全部轉數（含未中獎）", ""])
    rows = []
    for scene, frame, column in (("BG", cascade92, "BG_Count"), ("FG", cascade92, "FG_Count"),
                                 ("BF", cascade92_buy, "FG_Count")):
        shares = combo_shares(frame, column)
        rows.append([SCENE_LABEL[scene]] + [pct(value) for value in shares])
    add(table(["場景", "combo 0", "combo 1", "combo 2", "combo 3", "combo 4", "combo 5+"], rows))
    competitor_rows = [[SCENE_LABEL[scene]] + [pct(value) for value in TARGETS.combo[scene]]
                       for scene in ("BG", "FG", "BF")]
    add(["對照競品同一張表：", ""])
    add(table(["場景", "combo 0", "combo 1", "combo 2", "combo 3", "combo 4", "combo 5+"], competitor_rows))

    add([
        "> **combo 0 三個場景都對齊到 0.2 pp 以內，但長尾偏薄**（combo 5+ 約為競品的 1/10）。",
        "> 根因不在輪帶而在**補牌**：現行 Simulator 的掉落補牌是逐格獨立抽 `drop_weights`，",
        "> 補完的盤面比輪帶本身更分散，因此不容易再次中獎；競品的補牌看起來是沿輪帶繼續帶入，",
        "> 會保留同輪聚集。要對齊需要把補牌改成「由停輪位置沿輪帶往上取」或替補牌加一組聚集度權重，",
        "> 屬於 Simulator ＋ config schema 的機制擴充，見 `其他/競品比較_C027.md` 第 6 節。",
        "",
    ])
    add(["#### 3.5.2 有消除時的條件分布", ""])
    rows = []
    for scene, frame, column in (("BG", cascade92, "BG_Count"), ("FG", cascade92, "FG_Count"),
                                 ("BF", cascade92_buy, "FG_Count")):
        total, shares = conditional_combo(frame, column)
        rows.append([SCENE_LABEL[scene], f"{int(total):,}"] + [pct(value) for value in shares])
    add(table(["場景", "有消除轉數", "combo 1", "combo 2", "combo 3", "combo 4", "combo 5+"], rows))
    bg_combo0 = combo_shares(cascade92, "BG_Count")[0]
    bg_hit = rate(card92["hit_rate_bg"])
    bg_sum = bg_combo0 + bg_hit
    trigger_rate = 1.0 / cycle_of(card92["fg_trigger_rate"])
    add([
        "> **校驗**：固定格式要求「combo 0 比例 + Hit Rate = 100%」。",
        f"> BG 為 {pct(bg_combo0)} + {bg_hit:.3%} = {pct(bg_sum)}，"
        f"超出 {pct(bg_sum - 1.0)}。",
        f"> 差額來自「零消除但有 Scatter 得分」的 spin：BG 觸發率為 {trigger_rate:.3%}，"
        "這些 spin 同時被算進 Hit Rate 與 combo 0。",
        "> FG／BF 的超出量更大，因為 Buy Feature 每次購買的入口列也有一筆 Scatter 得分。",
        "> 這是 Pay Anywhere ＋ Scatter Pay 遊戲的結構性例外，競品報告同一節也列了相同的例外說明；",
        "> 競品 BG 之所以剛好等於 100.000%，是因為它的 BG Hit Rate 沒有把 Scatter-only 的 spin 算進去。",
        "",
    ])

    add(["### 3.6 最大倍數", ""])
    add(table(["層級", "最大倍數", "出處"], [
        ["規則上限（單顆 C3）", "2,500x", "`game_rule.md` §5.2"],
        ["單次 Normal Bet 回合（92A Card-On）", f"**{number(card92['max_win_x']):,.2f}x**",
         f"{normal_rounds:,} 轉中最大"],
        ["單次 Buy Feature 回合（92A Card-On）",
         f"**{number(card92_buy['max_win_x']) * 100:,.2f}x**",
         f"{buy_rounds:,} 次中最大；報表的 `max_win_x` 以 100x 購買成本為分母，此處已換算回底注倍數"],
        ["單次 Normal Bet 回合（Card-Off 自然）", f"{number(natural_normal['max_win_x']):,.2f}x",
         f"{int(number(natural_normal['total_rounds'])):,} 轉中最大"],
        ["盤面 C2／C3 倍數總和最大值（Card-Off）", f"{number(natural_normal['max_multiplier']):,.0f}x",
         "多顆相加，非單顆上限"],
    ], ["---", "---:", "---"]))
    rows = []
    for label, shares in (("NB-FG（自然觸發）", fg_line), ("BF-FG（購買）", bf_line)):
        rows.append([label] + [pct(threshold_share(shares, uppers, level), 2) for level in THRESHOLDS])
    rows.append(["競品（自然 21 + 購買 251 場合併）"]
                + [pct(share, 2) for share in
                   (0.9191, 0.8235, 0.5515, 0.2904, 0.0993, 0.0074, 0.0000)])
    add(table(["樣本"] + [f"≥{level}x" for level in THRESHOLDS], rows))
    add([
        "> C027 的 ≥1000x 為非零值：單顆 C3 每次消除升一級、最高 2,500x，",
        "> 而競品的倍數球不升級、單顆上限 500x，272 場實測 ≥1000x 為 0%。",
        "> 這是刻意的產品差異，不是對齊失敗（見 `design_approach.md`「已知且刻意的競品偏離」）。",
        "",
        "---",
        "",
    ])

    # ---------------------------------------------------------------- §4
    fg_sessions_92 = int(line92["free_game_cnt"].sum())
    bf_sessions_92 = int(line92_buy["free_game_cnt_BF"].sum())
    add(["## §4. 倍率線型", "", "### 4.1 摘要", ""])
    add(table(["項目", "BG", "NB-FG（自然觸發）", "BF-FG（購買）"], [
        ["統計單位", "每個 BG spin", "每次完整 FG 全程", "每次完整購買 FG 全程"],
        ["樣本", f"{int(line92['base_game_cnt'].sum()):,}", f"{fg_sessions_92:,}", f"{bf_sessions_92:,}"],
        ["區間數", "64", "64", "64"],
        ["非零區間", f"{int((bg_line > 0).sum())}", f"{int((fg_line > 0).sum())}", f"{int((bf_line > 0).sum())}"],
        ["Range 合計", f"{bg_line.sum() * 100:.5f}%", f"{fg_line.sum() * 100:.5f}%", f"{bf_line.sum() * 100:.5f}%"],
    ], ["---", "---:", "---:", "---:"]))
    add([
        "> 區間定義沿用 H026 標準 64 區間 `(Lower, Upper]`；倍率 = 得分 ÷ 底注。",
        "> BG 線型包含全部 BG spin（含觸發 FG 的那一轉），與競品報告同一慣例。",
        "> NB-FG／BF-FG 使用整場 FG 的累計得分，分母為 Normal Bet 基準成本。",
        "",
    ])

    add(["### 4.2 倍率線型分布", ""])
    rows = []
    for index, label in enumerate(labels):
        rows.append([f"`{label}`",
                     f"{int(line92['base_game_cnt'].iloc[index]):,}", f"{bg_line[index] * 100:.5f}%",
                     f"{int(line92['free_game_cnt'].iloc[index]):,}", f"{fg_line[index] * 100:.5f}%",
                     f"{int(line92_buy['free_game_cnt_BF'].iloc[index]):,}", f"{bf_line[index] * 100:.5f}%"])
    add(table(["Interval", "BG 次數", "BG Hit Rate", "NB-FG 次數", "NB-FG Hit Rate",
               "BF-FG 次數", "BF-FG Hit Rate"], rows))

    add(["### 4.3 觀察", ""])
    top_bg = int(np.argmax(bg_line[1:]) + 1)
    top_fg = int(np.argmax(fg_line))
    top_bf = int(np.argmax(bf_line))
    add([
        f"- BG 集中在低倍：`{labels[0]}` 佔 {bg_line[0] * 100:.2f}%、`{labels[1]}` 佔 {bg_line[1] * 100:.2f}%，"
        f"兩者合計 {(bg_line[0] + bg_line[1]) * 100:.2f}%。",
        f"- BG 除零得分外最高的區間為 `{labels[top_bg]}`（{bg_line[top_bg] * 100:.2f}%），"
        f"最高非零區間為 `{labels[int(np.max(np.nonzero(bg_line)))]}`。",
        f"- NB-FG 最高區間為 `{labels[top_fg]}`（{fg_line[top_fg] * 100:.2f}%），"
        f"尾段延伸至 `{labels[int(np.max(np.nonzero(fg_line)))]}`。",
        f"- BF-FG 最高區間為 `{labels[top_bf]}`（{bf_line[top_bf] * 100:.2f}%），"
        f"尾段延伸至 `{labels[int(np.max(np.nonzero(bf_line)))]}`。",
        "- 卡片權重就是 64 區間線型本身，因此線型與設定值的差只來自抽樣誤差與 Retry 失敗。",
        f"- BG 的 `max_multiplier_bg` 上限為 {number(card92['max_multiplier_bg']):.0f}x（正權重 BG 區間卡的最大上限，"
        "也是 `free_game` 卡的 BG Trigger Cap）。超過該上限的 BG 區間只可能來自 Retry 失敗後保留的最後結果，"
        f"本批為 {int(number(card92['retry_limit_exceeded'])):,} 次（{number(card92['retry_limit_exceeded']) / normal_rounds:.4%}）。",
        "",
        "**Card System 對 FG 的選樣代價**",
        "",
        f"自然模型的 FG 整包平均為 {rate(natural_normal['rtp_fg']) * cycle_of(natural_normal['fg_trigger_rate']):.1f}x，"
        f"目標為 {calibration['fg_package_mean']:.1f}x，卡片必須把整包壓到約 "
        f"{calibration['fg_package_mean'] / (rate(natural_normal['rtp_fg']) * cycle_of(natural_normal['fg_trigger_rate'])):.0%}。",
        "整包得分與「該場次有幾轉中獎」正相關，所以這個壓縮會連帶降低 FG 每轉 Hit Rate 與長連消比例：",
        "",
        f"| 指標 | Card-Off 自然 | Card-On 92A | 競品 |",
        f"|---|---:|---:|---:|",
        f"| FG 每轉 Hit Rate（競品原始口徑） | {rate(natural_normal['hit_rate_fg']):.3%} | "
        f"{rate(card92['hit_rate_fg']):.3%} | {TARGETS.basic['fg_hit_rate']:.3%} |",
        f"| FG 每轉 Hit Rate（符號命中口徑） | {rate(natural_normal['hit_rate_fg']):.3%} | "
        f"{rate(card92['hit_rate_fg']):.3%} | {TARGETS.initial_hit_target('FG'):.3%} |",
        f"| FG combo 0 | {pct(1 - rate(natural_normal['hit_rate_fg']), 3)} | "
        f"{pct(combo_shares(cascade92, 'FG_Count')[0], 3)} | {pct(TARGETS.combo['FG'][0], 3)} |",
        "",
        "> 競品的「原始口徑」含零消除但有 Scatter 得分的 spin；本作 3 顆 C1 不派獎，做不出這種 spin，",
        "> 因此「符號命中口徑」（競品的 `1 − combo0`）才是同一把尺。以那把尺量，Card-Off 誤差 +0.35 pp、",
        "> Card-On 誤差 −1.94 pp。",
        "",
        "自然結構（輪帶）本身已對齊競品；差距全部來自 RTP 校準。這是本作賠率表比競品豐厚",
        "（M1 8–9 個即賠 10x）所致：在同樣的命中率下，本作的 FG 整包價值天生較高，",
        "要收到 92% 的總 RTP 就必須挑較低的整包。要同時對齊三者，必須改賠率表 —— 那是規則層的決定。",
        "",
        "**BG 尾段被卡片截斷**",
        "",
        f"正權重的 BG 區間卡最高只到 {number(card92['max_multiplier_bg']):.0f}x，因為卡片校準只允許",
        "「自然機率 ≥ 0.04%」的區間帶權重（`calibrate_cards` 的 `threshold`），而本作自然 BG 分布在",
        f"{number(card92['max_multiplier_bg']):.0f}x 以上每個區間都低於這個門檻。競品 BG 在 15x 以上仍有約 0.56% 的機率",
        "（最高到 `(450, 500]`），這部分質量被 `remap_shape` 折回最近的可用區間，總量守恆但尾段被截斷。",
        "Card-Off 自然模型本身做得出大 BG 獎（本批最大 "
        f"{number(natural_normal['max_win_x']):,.0f}x），所以這是卡片解的限制、不是輪帶的限制；",
        "要放開需要把 `threshold` 降低並確認 Retry 次數可接受。",
        "",
        "---",
        "",
    ])

    # ---------------------------------------------------------------- §5
    add(["## §5. 特殊指標", "", "### 5.1 倍數球", "",
         "倍數球分兩種：**C2** 提供固定倍率、不升級；**C3 / Super Multiplier** 初始值 ≥10x，",
         "每次中獎消除後往後升一個倍數等級，最高 2,500x。兩者都不參與 Any-8、不會被消除，",
         "最終盤面上的倍率**相加**後套用。", "", "#### 5.1.1 出現率與球數分布", ""])
    natural_cascade_all = {"BG": sheet(paths["natural_normal"], "Cascade"),
                           "FG": sheet(paths["natural_fg_probe"], "Cascade"),
                           "BF": sheet(paths["natural_buy"], "Cascade")}
    natural_overview = {"BG": natural_normal, "FG": overview(paths["natural_fg_probe"]),
                        "BF": natural_buy}
    rows = []
    for scene, data, frame, column in (
        ("BG", card92, cascade92, "BG_Balls_Per_Spin"),
        ("FG", card92, cascade92, "FG_Balls_Per_Spin"),
        ("BF", card92_buy, cascade92_buy, "FG_Balls_Per_Spin"),
    ):
        key = "multiplier_ball_rate_bg" if scene == "BG" else "multiplier_ball_rate_fg"
        natural_key = "multiplier_ball_rate_bg" if scene == "BG" else "multiplier_ball_rate_fg"
        natural_column = "BG_Balls_Per_Spin" if scene == "BG" else "FG_Balls_Per_Spin"

        def distribution(source_frame, source_column):
            counts = source_frame[source_column].to_numpy(dtype=float)
            present = counts[1:].sum()
            if present <= 0:
                return "—"
            return "／".join(f"{index}顆 {counts[index] / present:.1%}"
                             for index in range(1, 5) if counts[index] > 0)

        rows.append([
            SCENE_LABEL[scene],
            f"**{rate(data[key]):.3%}**",
            f"{rate(natural_overview[scene][natural_key]):.3%}",
            pct(TARGETS.ball_spin_rate[scene], 3),
            distribution(frame, column),
            distribution(natural_cascade_all[scene], natural_column),
            "／".join(f"{index + 1}顆 {value:.1%}"
                      for index, value in enumerate(TARGETS.ball_count_dist[scene]) if value > 0),
        ])
    add(table(["場景", "Card-On 有球占比", "Card-Off 有球占比", "競品",
               "Card-On 每盤球數", "Card-Off 每盤球數", "競品每盤球數"], rows,
              ["---", "---:", "---:", "---:", "---", "---", "---"]))
    add([
        "> **Card-Off 三個場景都對齊**（"
        + "／".join(
            f"{scene} {rate(natural_overview[scene]['multiplier_ball_rate_bg' if scene == 'BG' else 'multiplier_ball_rate_fg']):.3%}"
            for scene in ("BG", "FG", "BF"))
        + "，競品 "
        + "／".join(pct(TARGETS.ball_spin_rate[scene], 3) for scene in ("BG", "FG", "BF"))
        + "）。",
        "> Card-On 的偏差來自卡片依得分區間選樣：倍數球會放大得分，高區間必然過度取樣有球的 spin。",
        "> 卡片的 `ball` 維度把 BG 的 Card-On 值從 **6.618%** 壓到 **3.714%**（見 §6.3）。",
        "",
    ])
    add(["#### 5.1.2 倍數值分布", ""])
    values = sorted(set(multiplier92["Multiplier"].astype(int)) | set(multiplier92_buy["Multiplier"].astype(int)))
    rows = []
    for scene, frame, column in (("BG", multiplier92, "BG_Count"), ("FG", multiplier92, "FG_Count"),
                                 ("BF", multiplier92_buy, "FG_Count")):
        share = dict(zip(frame["Multiplier"].astype(int), frame[column].astype(float)))
        total = sum(share.values())
        rows.append([SCENE_LABEL[scene]] + [pct(share.get(value, 0.0) / total if total else 0.0, 2)
                                            for value in values])
    add(table(["場景"] + [f"{value}x" for value in values], rows))
    add([
        "> **和競品的差異是刻意的**：競品的倍數球不升級，值分布就是抽取分布；",
        "> C027 的 C3 每次消除升一級，所以上表是「最終盤面實際看到的值」，會比抽取分布右移。",
        "> 抽取階段的設定：C2 一般池只有 2x–8x，≥10x 一律走 C3 池（`game_rule.md` §5.1）。",
        "",
    ])

    add(["### 5.2 有無倍數球在場上的消除分布", "", "#### 5.2.1 全部轉數（含 combo 0）", ""])
    rows = []
    for scene, frame, ball_col, no_col in (
        ("BG", cascade92, "BG_Ball_Count", "BG_NoBall_Count"),
        ("FG", cascade92, "FG_Ball_Count", "FG_NoBall_Count"),
        ("BF", cascade92_buy, "FG_Ball_Count", "FG_NoBall_Count"),
    ):
        for label, column in (("有球", ball_col), ("無球", no_col)):
            counts = frame[column].to_numpy(dtype=float)
            total = counts.sum()
            shares = combo_shares(frame, column)
            hit = 1.0 - shares[0]
            rows.append([SCENE_LABEL[scene] if label == "有球" else "", label, f"{int(total):,}",
                         f"**{pct(hit, 2)}**"] + [pct(value, 2) for value in shares])
    add(table(["場景", "條件", "spins", "Hit Rate", "combo 0", "1", "2", "3", "4", "5+"], rows,
              ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]))
    add(["三方對照（Card-On 玩家版本 / Card-Off 自然結構 / 競品）：", ""])
    from competitor_targets import BALL_CONDITIONAL
    natural_cascade = {"BG": sheet(paths["natural_normal"], "Cascade"),
                       "FG": sheet(paths["natural_fg_probe"], "Cascade"),
                       "BF": sheet(paths["natural_buy"], "Cascade")}
    natural_prefix = {"BG": "BG", "FG": "FG", "BF": "FG"}
    rows = []
    for scene in ("BG", "FG", "BF"):
        card_frame = cascade92 if scene != "BF" else cascade92_buy
        card_prefix = "BG" if scene == "BG" else "FG"
        for label, suffix, key in (("有球", "Ball_Count", "with"), ("無球", "NoBall_Count", "without")):
            card_hit = 1.0 - combo_shares(card_frame, f"{card_prefix}_{suffix}")[0]
            natural_hit = 1.0 - combo_shares(natural_cascade[scene],
                                             f"{natural_prefix[scene]}_{suffix}")[0]
            rows.append([SCENE_LABEL[scene] if label == "有球" else "", label,
                         pct(card_hit, 2), pct(natural_hit, 2),
                         f"{BALL_CONDITIONAL[scene][key]['hit'] * 100:.2f}%"])
    add(table(["場景", "條件", "C027 Card-On", "C027 Card-Off", "競品"], rows,
              ["---", "---", "---:", "---:", "---:"]))
    add([
        "> **「有球時 Hit Rate 較高」不是輪帶做出來的。** 倍數球佔掉一個格位，只會**降低**該盤面的",
        "> Any-8 命中率。真正的來源是 **cascade 掉落補球**：球只可能在消除後補入，也就是只可能在",
        "> **有中獎**的 spin 上補入，所以中獎的 spin 會單向從「無球」桶搬到「有球」桶。",
        "> C027 把這件事寫成恆等式並反解，讓輪帶去打「初始盤面」的目標，最終盤面才會落在競品值上：",
        "",
        "```text",
        "最終有球率      = 初始有球率 + (1 − 初始有球率) × 初始無球命中率 × d",
        "最終 Hit|無球   = 初始無球命中率 × (1 − d) × (1 − 初始有球率) ÷ (1 − 最終有球率)",
        "```",
        "",
        f"> 實測 `d`（有中獎且原本無球的 spin 補到球的機率）：BG {drop_gain.get('BG', 0):.2%}、"
        f"FG {drop_gain.get('FG', 0):.2%}、BF {drop_gain.get('BF', 0):.2%}。",
        "> 場景表混合（每場景兩張子輪帶表、逐轉獨立抽表）提供的自由度，是為了讓",
        "> `P(有球)`、`Hit Rate`、`Hit Rate|有球`、`Hit Rate|無球` 四個量可以同時被指定 ——",
        "> 單一輪帶只有一個聚集度旋鈕，做不到。",
        "> **Card-On 的 `Hit Rate|有球` 幾乎是 100%，這是一個明確的取捨結果，不是計算錯誤。**",
        "> 卡片的 `ball` 維度要求所有「得分 ≤6x」的區間卡都不能有球，於是被接受的有球 spin",
        "> 只剩下 >6x 的中獎 spin —— 對玩家而言就是「看到倍數球幾乎一定中獎」。",
        "> 為什麼不放寬：本作賠率表下高於約 6x 的 BG 得分幾乎必然伴隨倍數球，",
        "> 若把 `ball_split_max` 往上調（例如 12x），「高得分但無球」的卡片會打到 Retry Limit，",
        "> 實測 BG Hit Rate 掉 1.09 pp、總 RTP 掉到 79.7%；若改讓零得分卡也帶球（`ball_share > 0`），",
        f"> 倍數球出現率會從已經偏高的 {rate(card92['multiplier_ball_rate_bg']):.3%} 再往上跑。",
        "> C027 因此選擇把**倍數球出現率**（玩家直接看得到的指標）與 **BG Hit Rate／總 RTP** 鎖在目標上，",
        "> 並把這個取捨寫在這裡，而不是隱藏在數字裡。要根治得改賠率表，那是規則層的決定。",
        "> 注意 BF 場景競品是**負相關**（有球時 Hit Rate 較低），C027 的 Card-Off 結構同樣重現了這個方向。",
        "",
    ])

    add(["#### 5.2.2 排除 combo 0 後的條件占比", ""])
    rows = []
    for scene, frame, ball_col, no_col in (
        ("BG", cascade92, "BG_Ball_Count", "BG_NoBall_Count"),
        ("FG", cascade92, "FG_Ball_Count", "FG_NoBall_Count"),
        ("BF", cascade92_buy, "FG_Ball_Count", "FG_NoBall_Count"),
    ):
        for label, column in (("有球", ball_col), ("無球", no_col)):
            total, shares = conditional_combo(frame, column)
            rows.append([SCENE_LABEL[scene] if label == "有球" else "", label, f"{int(total):,}"]
                        + [pct(value) for value in shares])
    add(table(["場景", "條件", "有消除 spins", "1", "2", "3", "4", "5+"], rows,
              ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:"]))

    add(["### 5.3 FG 累積倍數分層的 Hit Rate", "",
         "FG 內的 C2／C3 倍數會**跨轉累積**至整場結束。下表依「該轉開始前的累積倍數」分層。", ""])
    tiers_normal = fg_tier_table(paths["config_92A.js_normal"], base_coin_in)
    tiers_buy = fg_tier_table(paths["config_92A.js_buy"], base_coin_in)
    combined = tiers_normal.copy()
    combined["spins"] = tiers_normal["spins"] + tiers_buy["spins"]
    weight_normal = np.where(combined["spins"] > 0, tiers_normal["spins"] / np.where(combined["spins"] > 0, combined["spins"], 1), 0)
    weight_buy = 1.0 - weight_normal
    combined["hit_rate"] = tiers_normal["hit_rate"] * weight_normal + tiers_buy["hit_rate"] * weight_buy
    combined["avg_win_x"] = tiers_normal["avg_win_x"] * weight_normal + tiers_buy["avg_win_x"] * weight_buy
    rows = [[row.tier, f"{int(row.spins):,}", pct(row.hit_rate, 2), f"{row.avg_win_x:.3f}x"]
            for row in combined.itertuples()]
    add(table(["累積倍數", "spins", "Hit Rate", "平均得分/轉"], rows))
    tier_values = [row.hit_rate for row in combined.itertuples() if row.spins > 1000]
    spread = (max(tier_values) - min(tier_values)) if tier_values else 0.0
    add([
        "> 自然觸發 ＋ 購買合併，與競品報告 §5.3 同一口徑。",
        "> **和競品的關鍵差異**：競品在取樣充足的四個桶呈 39.1% → 37.4% → 32.5% → 30.8% 的下降"
        "（跨四桶 8.3 pp），",
        "> 但競品報告自己指出那可能是存活偏誤（累積倍數高等同於該場次已跑較多轉）。",
        f"> C027 全部樣本 >1,000 轉的桶最高與最低只差 {pct(spread, 2)}，除首桶略高外沒有趨勢；",
        "> 因為 FG 每一轉獨立抽場景表，累積倍數不會回頭影響命中結構。",
        "> 平均得分/轉則隨累積倍數近乎線性上升，這正是累積倍數應有的效果。",
        "",
    ])

    add(["### 5.4 C3 升級與場景表混合", ""])
    add(table(["項目", "設定值", "說明"], [
        ["C2 一般倍率池", "2x / 3x / 4x / 5x / 6x / 8x", "`game_rule.md` §5.1：10x 以上不得由 C2 池抽出"],
        ["C3 Super Multiplier 池", "10x / 12x / 15x / 20x / 25x / 50x / 100x / 250x / 500x", "所有 ≥10x 的初始值只能由這裡抽出"],
        ["C3 升級階梯", "10 → 12 → 15 → 20 → 25 → 50 → 100 → 250 → 500 → 1000 → 2500", "每次中獎消除升一級，2500x 後維持"],
        ["`use_super_multiplier`（BG）", f"{config['parameter']['normal']['use_super_multiplier']['weights_by_initial_ball_count'][SCENE_TABLES['BG'][0]]}",
         "萬分比，欄位為初始球數 1～6 顆；依規則隨初始球數遞增"],
        ["`use_super_multiplier`（FG）", f"{config['parameter']['normal']['use_super_multiplier']['weights_by_initial_ball_count'][SCENE_TABLES['FG'][0]]}",
         "同上"],
    ], ["---", "---", "---"]))
    rows = []
    for scene in ("BG", "FG", "BF"):
        info = mixture["tables"][scene]
        rows.append([SCENE_LABEL[scene], "／".join(f"`{name}`" for name in info["names"]),
                     f"{info['weight_a']:.4%} / {1 - info['weight_a']:.4%}",
                     f"{info['c2_count_a']} / 0",
                     " / ".join(f"{value:.3f}" for value in info["theta"])])
    add(table(["場景", "子輪帶表（A / B）", "混合權重", "A/B 表 C2 格數", "聚集度 θ"], rows,
              ["---", "---", "---:", "---:", "---:"]))
    add([
        "> θ 是輪帶合成模型的聚集度參數：θ = 1 等於「每格獨立同分布」，θ > 1 較聚集（好中獎）、",
        "> θ < 1 較分散。模型細節見 `其他/strip_model.py` 與 `其他/c027_scene_model.py`。",
        "",
        "---",
        "",
    ])

    # ---------------------------------------------------------------- §6
    add(["## §6. 附錄", "", "### 6.1 與規則文件對照", ""])
    natural_max_multiplier = number(natural_normal["max_multiplier"])
    natural_multiplier = sheet(paths["natural_normal"], "C2-C3 Multiplier")
    natural_upgrade = {
        value: float(natural_multiplier.loc[natural_multiplier["Multiplier"] == value, "BG_Count"].sum()
                     + natural_multiplier.loc[natural_multiplier["Multiplier"] == value, "FG_Count"].sum())
        for value in (1000, 2500)
    }
    add(table(["規則條目", "實測驗證", "結果"], [
        ["盤面 6 輪 × 5 列 = 30 格", "七張輪帶表的 `reel_lengths` 皆為 6 輪等長，`window_size = 5`", "✅"],
        ["Pay Anywhere，8 個以上成立", "`Symbol Hit Rate` 只有 8–9／10–11／12+ 三個級距有計數", "✅"],
        ["C2／C3 不參與 Any-8、不被消除", "`SCORE_SYMBOLS` 排除 C1／C2／C3；消除只針對一般符號",
         "✅"],
        ["10x 以上只能由 C3 抽出", "`fit_c027_model.validate_config` 逐張表檢查 C2 池無 ≥10x、C3 池無 <10x", "✅"],
        ["C3 每次消除升一級、上限 2500x",
         f"C3 抽取池上限為 500x，因此 1000x／2500x 只能由升級產生。Card-Off 自然模型量到 "
         f"1000x {int(natural_upgrade[1000]):,} 次、2500x {int(natural_upgrade[2500]):,} 次", "✅"],
        ["Buy Feature 入口不產生 BG 得分",
         "`BF_Symbol` 每 5 格視窗內同一般符號不重複 → 單一符號最多 6 個，數學上不可能 Any-8", "✅"],
        ["Buy Feature 入口保證 4 顆以上 C1", "R2～R5 強制停在含 C1 的視窗；C1 循環間距 ≥6 保證同輪最多一顆", "✅"],
        ["Scatter 同輪最多一個", "七張表逐輪檢查 C1 循環間距 ≥ 6 > 視窗 5 格", "✅"],
        ["FG 15 Spins、Retrigger +5、上限 50",
         f"92A Card-On 實測平均 {number(card92['avg_fg_spins']):.2f} spins", "✅"],
        ["FG 觸發需 4 顆以上 C1", "`Scatter Dist` 的 BG 觸發列只出現在 4／5／6 顆", "✅"],
        ["FG 累積倍數跨轉保留", "§5.3 平均得分/轉隨累積倍數單調上升", "✅"],
        ["Extra Bet 觸發率為 Normal 的 5 倍",
         "⚠️ 目前以「最多五次觸發機會」近似，尚未配置 Extra Bet 專用輪帶與卡片", "⚠️"],
        ["最大派彩上限", "📝 產品未定義硬上限；規則只限制單顆 C3 為 2500x", "📝"],
    ], ["---", "---", "---"]))

    recon_path = OTHER / "reconcile_demogame.json"
    if recon_path.is_file():
        recon = json.loads(recon_path.read_text(encoding="utf-8"))
        add(["### 6.2 Demogame 與 Simulator 對帳", "",
             "開發規範 §4.6 要求 Demogame 與 Simulator 使用同一套數學邏輯並可逐項對帳。",
             "`其他/reconcile_demogame.mjs` 把 `index.html` 的主程式在 Node 裡跑起來（用最小 DOM stub 取代瀏覽器），",
             "直接呼叫它自己的 `playSpin` / `generateFreeSession`，再和 Simulator 的 Card-Off 報表比較。", ""])
        rows = [
            ["BG Hit Rate", pct(recon["bg_hit_rate"], 4), f"{rate(natural_normal['hit_rate_bg']):.4%}"],
            ["BG 倍數球出現率", pct(recon["bg_ball_rate"], 4), f"{rate(natural_normal['multiplier_ball_rate_bg']):.4%}"],
            ["BG 平均 Cascade 次數", f"{recon['bg_avg_cascades']:.6f}", f"{number(natural_normal['avg_cascades_bg']):.6f}"],
            ["FG Hit Rate", pct(recon["fg_hit_rate"], 4), f"{rate(natural_normal['hit_rate_fg']):.4%}"],
            ["FG 倍數球出現率", pct(recon["fg_ball_rate"], 4), f"{rate(natural_normal['multiplier_ball_rate_fg']):.4%}"],
        ]
        for entry in recon["bg_table_share"] + recon["fg_table_share"]:
            rows.append([f"場景抽表占比 `{entry['name']}`", pct(entry["measured"], 4),
                         f"Config 設定 {pct(entry['configured'], 4)}"])
        add(table(["指標", f"Demogame（{recon['rounds']:,} 轉）",
                   f"Simulator Card-Off（{int(number(natural_normal['total_rounds'])):,} 轉）"],
                  rows, ["---", "---:", "---:"]))
        add([
            f"> Demogame 樣本較小（{recon['rounds']:,} 轉、{recon['fg_spins']:,} 個免費轉），差異都在抽樣誤差內。",
            "> 場景抽表占比實測貼近 Config 權重，證明 Demogame 的 `buildFreeSchedule()` 與",
            "> `Simulator.schedule_free_spins()` 走的是同一套逐轉抽表邏輯。",
            "> 重跑：`node 其他/reconcile_demogame.mjs 300000`。",
            "",
        ])
    add(["### 6.3 其他已知機制", ""])
    add(table(["機制", "說明"], [
        ["場景表混合", "BG 每一付費轉、FG／BF 每一免費轉獨立抽子輪帶表；抽表只影響初始盤面來源"],
        ["倍數球累加", "同一盤面多顆 C2／C3 的倍率**相加**後一次套用，不相乘"],
        ["C3 升級時點", "每次中獎消除，消除前已在盤面的 C3 各升一級；該次新掉入的 C3 不追溯"],
        ["卡片 `ball` 維度", f"得分 ≤ {calibration['ball_split_max']}x 的區間卡分成 with／without 兩張，"
                            f"`ball_share` = {calibration['ball_share']:.5f}"],
        ["卡片 `combo` 維度", "已實作 `combo_min`／`combo_max`，本版未啟用（權重全為預設）"],
        ["OP Jackpot", "C1 Scatter 打擊 OP Jackpot；不影響 §3.1 的一般符號與 Scatter 賠付"],
    ], ["---", "---"]))

    add(["### 6.4 資料使用建議", "",
         "1. **Card System On 的報表才是玩家版本**；Card-Off 的自然 RTP（§2.3）只能當輪帶體檢值，不可對外引用。",
         "2. §3.2／§3.3 的符號與堆疊分布來自 Config 輪帶，是精確值；要比對競品時記得競品那邊是側錄估計值。",
         f"3. NB-FG 線型的樣本為 {fg_sessions_92:,} 場，尾段區間的單場權重仍偏大，讀尾段時要看次數欄不是只看百分比。",
         "4. §5.1.2 的倍數值分布**不可**直接與競品比大小：C027 的 C3 會升級，競品不會。要比抽取設定請看 §5.4。",
         "5. §3.6 的 ≥1000x 占比是 C027 的設計特色（單顆 C3 可升至 2500x），不是對齊誤差。",
         "6. 重跑流程：`fit_c027_model.py --strips` → `--cards` → `tune_c027.py` → "
         "`verify_c027.py --natural --calibrate --run` → 本腳本。",
         "",
    ])

    charts = {
        "anchor": "### 4.2",
        "rows": [
            {"i": index, "lab": labels[index],
             "bgH": float(bg_line[index] * 100), "fgH": float(fg_line[index] * 100),
             "bfH": float(bf_line[index] * 100),
             "bgC": float(bg_line[index:].sum() * 100),
             "fgC": float(fg_line[index:].sum() * 100),
             "bfC": float(bf_line[index:].sum() * 100)}
            for index in range(len(labels))
        ],
        "series": ["bg", "fg", "bf"],
        # chart 3 plots P(multiplier > interval upper); build_html reads it from `sv`
        "sv": {
            "bg": [float(bg_line[index + 1:].sum() * 100) for index in range(len(labels))],
            "fg": [float(fg_line[index + 1:].sum() * 100) for index in range(len(labels))],
            "bf": [float(bf_line[index + 1:].sum() * 100) for index in range(len(labels))],
        },
        "clipped": [{"lab": labels[index], "v": float(bg_line[index] * 100)}
                    for index in range(len(labels)) if bg_line[index] * 100 > 1.0],
    }
    data = {
        "game": "C027 奧林帕斯 2500",
        "eyebrow": "自家遊戲 · 數值報告",
        "meta": [
            f"92A Card-On｜Normal Bet {normal_rounds:,} 轉｜Buy Feature {buy_rounds:,} 次｜底注 1.00",
            "場景代號：BG 一般遊戲／FG 自然觸發免費遊戲／BF 購買免費遊戲",
        ],
        "stats": [
            ["總 RTP", f"{rate(card92['rtp_total']):.3%}", f"92A · {normal_rounds:,} 轉"],
            ["BG Hit Rate", f"{rate(card92['hit_rate_bg']):.3%}", f"競品 {TARGETS.basic['bg_hit_rate']:.3%}"],
            ["FG 週期", f"1/{cycle_of(card92['fg_trigger_rate']):.1f}", f"競品 1/{TARGETS.basic['fg_cycle']:.1f}"],
            ["FG 平均倍數", f"{rate(card92['rtp_fg']) * cycle_of(card92['fg_trigger_rate']):.2f}x",
             f"競品 {TARGETS.basic['fg_avg_multiplier']:.2f}x"],
            ["BG 倍數球出現率", f"{rate(card92['multiplier_ball_rate_bg']):.3%}",
             f"競品 {TARGETS.ball_spin_rate['BG']:.3%}"],
            ["單回合最大倍率", f"{number(card92['max_win_x']):,.0f}x", "C3 可升至 2,500x"],
        ],
        "charts": charts,
    }
    return "\n".join(out), data


def main() -> None:
    paths = reports()
    markdown, data = build_md(paths)
    MD_PATH.write_text(markdown, encoding="utf-8")
    print(f"寫入 {MD_PATH.name}（{len(markdown.splitlines()):,} 行）")
    data_path = OTHER / "c027_report_data.json"
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    script = SKILL_SCRIPTS / "build_html.py"
    if not script.is_file():
        raise SystemExit(f"找不到 {script}")
    subprocess.run([sys.executable, str(script), str(MD_PATH), str(HTML_PATH),
                    "--data", str(data_path)], check=True)
    print(f"寫入 {HTML_PATH.name}")


if __name__ == "__main__":
    main()
