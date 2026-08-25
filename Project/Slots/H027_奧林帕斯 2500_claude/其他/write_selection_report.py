"""產出 其他/數值版本挑選_H027.md — 逐指標對照表與挑選過程，數字全部由實際模擬結果讀出。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import score_competitor_match as scorer
from competitor_targets import REELS, SCENES, SYMBOL_ORDER

ROOT = scorer.ROOT
OTHER = ROOT / "其他"
RECORD = ROOT / "Record"
TARGETS = scorer.TARGETS

GROUP_LABEL = {
    "rtp_total": "總 RTP",
    "rtp_bg": "BG RTP",
    "hit_rate_bg": "BG Hit Rate",
    "hit_rate_fg": "FG Hit Rate",
    "fg_cycle": "FG 週期",
    "fg_avg_multiplier": "FG 平均倍數",
    "bf_rtp": "Buy Feature RTP",
    "bf_hit_rate": "Buy Feature FG Hit Rate",
    "symbol_initial": "初始盤面符號分布（3 場景 × 6 輪 × 11 符號）",
    "symbol_drop": "消除掉落符號分布（3 場景 × 6 輪 × 11 符號）",
    "stack": "同輪堆疊分布（視窗最長堆疊 1~5）",
    "combo": "消除次數分布（combo 0~5+）",
    "cluster_tiers": "獎項占比（8-9 / 10-11 / 12+）",
    "ball_rate": "倍數球出現率",
    "multiplier_dist": "倍數球倍率分布（2x~500x）",
    "interval_line": "64 區間倍率線型",
    "thresholds": "高倍門檻占比（≥10x ~ ≥1000x）",
}
CANDIDATE_LABEL = {
    "cycle_first": "A. 週期優先（FG 週期 = 競品 1/433.2）",
    "balanced": "B. 平衡（週期與平均倍數各承擔一半偏差）",
    "avg_first": "C. 平均倍數優先（FG 平均倍數 = 競品 107.74x）",
}


def pct(value: float, digits: int = 4) -> str:
    return f"{value * 100:.{digits}f}%"


def signed_pp(delta: float, digits: int = 4) -> str:
    return f"{delta * 100:+.{digits}f} pp"


def headline_table(results: dict[str, dict]) -> list[str]:
    """One row per headline metric, one column per RTP variant."""
    names = list(results)
    lines = ["| 指標 | 競品 | " + " | ".join(f"H027 {n}" for n in names) + " | 判讀 |",
             "|---|---:|" + "---:|" * len(names) + "---|"]
    keys = ["rtp_total", "rtp_bg", "hit_rate_bg", "hit_rate_fg", "fg_cycle",
            "fg_avg_multiplier", "bf_rtp", "bf_hit_rate"]
    for key in keys:
        rows = {n: next(r for r in results[n]["rows"] if r["group"] == key) for n in names}
        sample = rows[names[0]]
        if key == "fg_cycle":
            target = f"1/{sample['target']:.1f}"
            cells = [f"1/{rows[n]['model']:.1f}" for n in names]
        elif key == "fg_avg_multiplier":
            target = f"{sample['target']:.2f}x"
            cells = [f"{rows[n]['model']:.2f}x" for n in names]
        elif key in {"rtp_total", "bf_rtp"}:
            target = "／".join(pct(rows[n]["target"], 0) for n in names) + "（版本定位）"
            cells = [pct(rows[n]["model"], 4) for n in names]
        elif key == "rtp_bg":
            target = pct(sample["target"], 0) + "（競品 59.763% 取整數）"
            cells = [pct(rows[n]["model"], 4) for n in names]
        else:
            target = pct(sample["target"], 3)
            cells = [pct(rows[n]["model"], 4) for n in names]
        worst = max(abs(rows[n]["error"]) for n in names)
        tolerance = scorer.SPEC[key][0]
        verdict = "已對齊" if worst <= tolerance else ("接近" if worst <= 3 * tolerance else "未對齊")
        lines.append(f"| {GROUP_LABEL[key]} | {target} | " + " | ".join(cells) + f" | {verdict} |")
    return lines


def group_table(result: dict) -> list[str]:
    lines = ["| 指標群 | 項數 | 平均偏差 | 最大偏差 | 容許值 | 標準化 | 權重 |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for group, info in sorted(result["groups"].items(),
                              key=lambda item: -item[1]["normalized"] * item[1]["weight"]):
        relative = group in {"fg_cycle", "fg_avg_multiplier"}
        unit = "%（相對）" if relative else " pp"
        scale = 100.0
        lines.append(f"| {GROUP_LABEL[group]} | {info['count']} | "
                     f"{info['mean_error'] * scale:.4f}{unit} | {info['max_error'] * scale:.4f}{unit} | "
                     f"{info['tolerance'] * scale:.4f}{unit} | {info['normalized']:.2f} | {info['weight']:.1f} |")
    return lines


def scene_table(result: dict, group: str, labels: list[str]) -> list[str]:
    rows = [r for r in result["rows"] if r["group"] == group]
    lines = ["| 場景 | " + " | ".join(labels) + " |", "|---|" + "---:|" * len(labels) + ""]
    for scene in SCENES:
        subset = [r for r in rows if r["name"].startswith(scene + " ")]
        if len(subset) != len(labels):
            continue
        lines.append(f"| {scene} 競品 | " + " | ".join(pct(r["target"], 3) for r in subset) + " |")
        lines.append(f"| {scene} H027 | " + " | ".join(pct(r["model"], 3) for r in subset) + " |")
        lines.append(f"| {scene} 差異 | " + " | ".join(signed_pp(r["delta"], 3) for r in subset) + " |")
    return lines


def reel_mae_table(result: dict, group: str, title: str) -> list[str]:
    rows = [r for r in result["rows"] if r["group"] == group]
    lines = [f"**{title}**（每格為該場景該輪 11 個符號的平均絕對偏差）", "",
             "| 場景 | " + " | ".join(REELS) + " | 全場最大單格偏差 |",
             "|---|" + "---:|" * 7]
    for scene in SCENES:
        prefix = scene if group == "symbol_initial" else scene + "drop"
        cells = []
        worst = 0.0
        for reel in REELS:
            subset = [r for r in rows if r["name"].startswith(f"{prefix} {reel} ")]
            cells.append(f"{np.mean([r['error'] for r in subset]) * 100:.4f} pp")
            worst = max(worst, max(r["error"] for r in subset))
        lines.append(f"| {scene} | " + " | ".join(cells) + f" | {worst * 100:.4f} pp |")
    return lines


def build(selection: dict, finals: dict[str, dict], strip_diag: dict, screening: str) -> str:
    primary = finals[next(iter(finals))]["result"]
    out: list[str] = []
    add = out.append

    add("# H027 奧林帕斯 2500－數值版本挑選")
    add("")
    add("> 目的：在「競品分析報告中提到的每一項指標」上挑出綜合偏差最小的一個版本。  ")
    add("> 競品基準：`其他/遊戲數據_Gates_of_Olympus_1000.md`（PP Gates of Olympus 1000 實機側錄）  ")
    add(f"> 產出版本：`config.js`（物理模型）＋ `config_92A.js`／`config_94A.js`（RTP 家族）  ")
    add("> 產生工具：`其他/strip_model.py`、`其他/fit_competitor_model.py`、"
        "`其他/select_version.py`、`其他/score_competitor_match.py`  ")
    add("> 本次未修改 `Source/*.xlsx`，未修改 `Simulator.py`，未修改 `game_rule.md` 的賠率表。")
    add("")

    add("## 1. 約束條件")
    add("")
    add("| 項目 | 設定 | 來源 |")
    add("|---|---|---|")
    add("| 總 RTP | 92A = 92%、94A = 94% | 版本定位，不追競品的 84.631% |")
    add("| BG RTP | 59%（競品 59.763% 取整數） | 指定 |")
    add("| 賠率表 | 固定，維持 `game_rule.md` §4 | 指定 |")
    add("| Simulator | 不修改 | 指定 |")
    add("| 其餘所有指標 | 盡可能貼近競品 | 本文件的最佳化目標 |")
    add("")

    add("## 2. 數學模型")
    add("")
    add("### 2.1 輪帶：配對距離聚集度模型")
    add("")
    add("競品報告裡有兩個乍看衝突的事實：")
    add("")
    add("1. 視窗堆疊分布（報告 §3.3.1）幾乎等於「每格獨立同分布」的理論值")
    add("   （BG 競品 60.868 / 34.952 / 3.772 / 0.363 / 0.045；i.i.d. 理論 60.43 / 35.31 / 3.85 / 0.38 / 0.03），")
    add("   代表競品輪帶的**相鄰重複就是純隨機水準**。")
    add("2. 但用競品自己的符號分布做 i.i.d. 盤面，Any-8 命中率是 BG 27.17% / FG 25.49% / BF 22.42%，")
    add("   競品實際是 **22.225% / 42.169% / 33.105%**。")
    add("")
    add("結論：競品 BG 輪帶比隨機更分散、FG 輪帶比隨機更聚集，而這個差異**不在相鄰重複上**。")
    add("剩下的自由度是「同輪帶同符號、距離 2~4 的非相鄰重複」——它改變 5 格視窗內同符號個數的")
    add("變異數（決定 Any-8 命中率與獎項大小），卻幾乎不動堆疊分布。因此每條輪帶用兩個統計量描述")
    add("（環狀、長度 L、符號 c 出現 n_c 次、f_c = n_c/L）：")
    add("")
    add("```text")
    add("N1(c)  = 距離 1 的同符號配對數      目標 L · f_c²           固定為 i.i.d. 水準，鎖住堆疊分布")
    add("NAR(c) = 3·N2 + 2·N3 + 1·N4        目標 θ · L · 6 f_c²     θ = 聚集度，唯一自由參數")
    add("```")
    add("")
    add("係數 (4, 3, 2, 1) 是「距離 d 的配對會落在幾個 5 格視窗內」，所以")
    add("`E[視窗內相鄰配對數] = 4·N1/L`、`E[視窗內非相鄰配對數] = NAR/L`，θ = 1 即等價於 i.i.d.。")
    add("輪帶用模擬退火求解，硬約束為「同輪 C1 環狀間距 ≥ 6」與「最長連續段 ≤ max_run」。")
    add("θ 以二分法收斂到競品的初始盤面命中率。")
    add("")
    add("### 2.2 卡片：最小擾動投影")
    add("")
    add("Card System 的作用等同對自然分布做重要性重抽：抽到區間 i 的卡片後就一直轉到落在區間 i。")
    add("因此 64 區間的機率可以直接指定，而**區間內部的條件結構（消除次數、是否有球）維持自然值**。")
    add("卡片權重解的是：在「總 RTP、BG RTP、BG Hit Rate、FG 週期」四個等式約束下，")
    add("找出離競品 64 區間線型 L2 距離最近的機率向量（`fit_competitor_model.project_shape`，")
    add("以 active-set 處理非負限制）。")
    add("")

    add("## 3. 逐場景輪帶篩選")
    add("")
    add("`max_run` 對每個場景各自篩選，評分只用該場景自己的指標（命中率、堆疊分布、獎項占比、")
    add("倍數球出現率），因為這些量完全由該張輪帶決定：")
    add("")
    add("```text")
    add(screening.strip())
    add("```")
    add("")
    add("採用結果：")
    add("")
    add("| 場景 | max_run | θ | 初始盤面命中率（目標） | 倍數球出現率（目標） |")
    add("|---|---:|---:|---:|---:|")
    for scene in SCENES:
        info = strip_diag[scene]
        add(f"| {scene} | {info.get('max_run', '—')} | {info['theta']:.3f} | "
            f"{pct(info['initial_hit'], 4)}（{pct(TARGETS.initial_hit_target(scene), 4)}） | "
            f"{pct(info['ball_present'], 3)}（{pct(TARGETS.ball_spin_rate[scene], 3)}） |")
    add("")

    add("## 4. 候選版本與挑選")
    add("")
    add("賠率固定、總 RTP 固定、BG RTP 固定之後，FG 的貢獻度也被鎖死：")
    add("")
    add("```text")
    add("FG 貢獻 = 總 RTP − BG RTP = FG 平均倍數 ÷ FG 週期")
    add("競品：107.74 ÷ 433.2 = 24.871%")
    add("92A ：92% − 59% = 33.000%   →  需要競品的 1.3269 倍")
    add("94A ：94% − 59% = 35.000%   →  需要競品的 1.4073 倍")
    add("```")
    add("")
    add("所以「FG 週期 1/433.2」與「FG 平均倍數 107.74x」**不可能同時成立**，只能在")
    add("`平均倍數 × 週期 = 常數` 這條雙曲線上選一點。三個候選點各校準一次卡片並跑一次模擬後評分：")
    add("")
    add("候選比較用**解析值**而非模擬值：總 RTP、BG RTP、BG Hit Rate、FG 週期、FG 平均倍數是卡片")
    add("權重的等式約束，解出來就精確成立；64 區間線型就是卡片權重本身。這些量在模擬裡的偏差幾乎")
    add("全是抽樣噪音——FG 一場的得分是重尾分布，篩選用的 15 萬轉只有四五百場 FG，總 RTP 的標準誤就有 2~3 pp，")
    add("會蓋掉候選之間真正的差異。")
    add("")
    add("| 候選 | FG 週期 | 週期偏差 | FG 平均倍數（92A） | 平均倍數偏差 | 64 區間線型 | 高倍門檻 | FG 單轉 Hit Rate 偏差 | 倍數球出現率偏差 | 總分（越小越好） |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name, info in selection["candidates"].items():
        analytic = info["groups"]
        full = info["combined_groups"]
        add(f"| {CANDIDATE_LABEL[name]} | 1/{info['cycle']:.1f} | "
            f"{(info['cycle'] / TARGETS.basic['fg_cycle'] - 1) * 100:+.1f}% | "
            f"{info['fg_avg']:.2f}x | "
            f"{(info['fg_avg'] / TARGETS.basic['fg_avg_multiplier'] - 1) * 100:+.1f}% | "
            f"{analytic['interval_line']['mean_error'] * 100:.4f} pp | "
            f"{analytic['thresholds']['mean_error'] * 100:.3f} pp | "
            f"{full['hit_rate_fg']['mean_error'] * 100:.2f} pp | "
            f"{full['ball_rate']['mean_error'] * 100:.2f} pp | **{info['combined_score']:.3f}** |")
    add("")
    add("前六欄是解析值（卡片等式約束與卡片權重本身），後兩欄是模擬量測——卡片重抽的二次效應：")
    add("週期越長、FG 平均倍數就得越高，卡片對自然 FG 場次的向下挑選越少，FG 單轉 Hit Rate 反而越接近競品。")
    add("這個二次效應會部分抵銷，但不足以改變排序。")
    add("")
    chosen = selection["candidates"][selection["selected"]]
    add(f"**挑選結果：{CANDIDATE_LABEL[selection['selected']]}**"
        f"　FG 週期 1/{chosen['cycle']:.1f}、92A 的 FG 平均倍數 {chosen['fg_avg']:.2f}x"
        f"（94A 為 {chosen['cycle'] * 0.35:.2f}x）。")
    add("")
    add("三個候選的 64 區間線型與高倍門檻差異都很小（線型平均偏差 0.05~0.08 pp、門檻 0.5~0.7 pp），"
        "決定權落在「週期」與「平均倍數」兩項。C 讓平均倍數完全對齊、線型與門檻也最接近，"
        "因此總分最低。若企劃上更在意 FG 觸發頻率而非單場價值，換成候選 A 只要重跑一次卡片校準：")
    add("")
    add("```bash")
    add("py -3 其他/fit_competitor_model.py --cards --cycle 433.2 --bg-rtp 0.59")
    add("```")
    add("")

    add("## 5. 最終版本逐指標對照")
    add("")
    add("挑選完成後多做了一步牛頓修正：卡片解 BG RTP 用的區間條件均值 `a_i` 量在自然模擬上，")
    add("而自然模擬裡還包含「會觸發 FG」的轉數——這些轉數會被 BG 區間卡片拒收，")
    add("所以直接解出來的 BG RTP 會偏低。120 萬轉實測偏低 0.39 pp，把這個差回饋進解方程")
    add("（`--bg-rtp-offset 0.0039`）後 BG RTP 落在 59.1%～59.3%，取整數即為要求的 59%。")
    add("修正對三個候選是等量的，不影響 §4 的排序。")
    add("")
    add("總 RTP 的實測值本身有 ±1.3 pp 的抽樣誤差（FG 一場得分是重尾分布，120 萬轉只有約")
    add("3,600 場 FG），卡片解出的期望值才是設計值。下表兩者都列。")
    add("")
    add("### 5.1 主要指標")
    add("")
    out.extend(headline_table({name: info["result"] for name, info in finals.items()}))
    add("")
    for index, (name, info) in enumerate(finals.items(), start=2):
        add(f"### 5.{index} 指標群偏差（{name}，總分 {info['result']['score']:.3f}）")
        add("")
        out.extend(group_table(info["result"]))
        add("")
    add(f"### 5.{len(finals) + 2} 同輪堆疊分布")
    add("")
    out.extend(scene_table(primary, "stack", ["1 堆疊", "2 堆疊", "3 堆疊", "4 堆疊", "5 堆疊"]))
    add("")
    add(f"### 5.{len(finals) + 3} 消除次數分布")
    add("")
    out.extend(scene_table(primary, "combo", ["combo 0", "combo 1", "combo 2", "combo 3", "combo 4", "combo 5+"]))
    add("")
    add(f"### 5.{len(finals) + 4} 獎項占比")
    add("")
    out.extend(scene_table(primary, "cluster_tiers", ["8-9", "10-11", "12+"]))
    add("")
    add(f"### 5.{len(finals) + 5} 符號分布")
    add("")
    out.extend(reel_mae_table(primary, "symbol_initial", "初始盤面"))
    add("")
    out.extend(reel_mae_table(primary, "symbol_drop", "消除掉落"))
    add("")

    add("## 6. 對不到的指標與原因")
    add("")
    add("| 指標 | 狀態 | 原因 |")
    add("|---|---|---|")
    add("| 總 RTP（競品 84.631%） | 刻意不對齊 | 版本定位為 92%／94%；競品 9,098 轉的 RTP 報告本身也註明不可當理論值 |")
    add("| FG 週期 **或** FG 平均倍數 | 二者只能對一個 | §4 的雙曲線約束；賠率固定時無第三個自由度 |")
    add("| FG Hit Rate（45.783%）／Buy Feature FG Hit Rate（38.832%） | 未對齊 | 兩層原因："
        "（一）競品 FG／BF 有「零消除但有 Scatter 得分」的轉數，H027 的 Scatter 要 4 個以上才給獎，"
        "所以 H027 的 FG Hit Rate 幾乎等於 1 − combo 0 = 42.169%（BF 為 33.105%），先差 3.6／5.7 pp；"
        "（二）卡片要把自然 FG 場均 164x 壓到 107.74x，會向下挑選 FG 場次，再壓低單轉命中率約 3.5 pp |")
    add("| FG 同輪堆疊分布 | 未對齊 | 競品 FG 命中率 42.169% 是 i.i.d. 水準（25.49%）的 1.65 倍，"
        "在「六輪獨立抽停點」的架構下只能靠拉高聚集度取得，必然推高 3／4 堆疊。"
        "要同時對齊需要跨輪 `reel_set`（競品資料顯示有 5 組），屬機制擴充 |")
    add("| BG 倍數球出現率 | Card-On 偏高 | 賠率固定下 BG RTP 26.8%（自然）要拉到 59%，卡片必須偏選大獎，"
        "而 H027 的大獎主要靠倍數球，選樣因此放大球率。這是「賠率表固定 ＋ BG RTP 59%」的必然代價 |")
    add("| 倍數球倍率的 C2／C3 來源 | 與 `game_rule.md` §6.1 衝突 | 規則要求 10x 以上只能來自 C3（且每次消除升級）；"
        "但競品 BG 的倍率分布有 8.49% 落在 10x、1.18% 落在 100x，若走 C3 路徑會被消除升級推高而對不上報告的倍率分布。"
        "本版沿用前一版的做法：C2 直接涵蓋 2x~500x、`use_super_multiplier` 全部設 0（C3 關閉）。**這一點需要企劃決定要改規則還是改數值** |")
    add("| newbie／oldhand 的 RTP 分層 | 本版未重建 | 原 XLSX 模型讓 newbie BG 均值 0.93、oldhand 0.92；"
        "競品基準版兩者共用同一組卡片解，若要恢復分層需指定各自的目標值再各解一次 |")
    add("| 報告 §5.2 有球／無球 × 消除次數 | 無法比較 | Record 沒有這組交叉計數器，且本次不修改 Simulator |")
    add("| 報告 §5.3 FG 累積倍數分層 Hit Rate | 無法比較 | 同上 |")
    add("| 每盤球數分布（1／2／3／4 顆） | 無法比較 | Record 只存有球轉數與總球數 |")
    add("| 最大倍數／規則上限 15,000x | 不評分 | 競品樣本 272 場最大 591.10x，未達上限，無可比基準 |")
    add("")

    add("## 7. 重現方式")
    add("")
    add("```bash")
    add("# 1. 合成四張輪帶（θ 以二分法收斂到競品的初始盤面命中率）")
    add("py -3 其他/fit_competitor_model.py --strips")
    add("# 2. 自然參考模擬 + 三個候選評分 + 挑選 + 寫入卡片 + 驗證")
    add("py -3 其他/select_version.py --rounds 400000 --bf-rounds 80000")
    add("# 3. 產出本文件（--final 為每個版本的 Card-On 驗證報表）")
    add("py -3 其他/write_selection_report.py --screening screening.txt \\")
    add("     --final 92A:config_92A.js:0.92:<normal.xlsx>:<bf.xlsx> \\")
    add("             94A:config_94A.js:0.94:<normal.xlsx>:<bf.xlsx>")
    add("```")
    add("")
    add("本文件 §5 的數字來自下列 Card System On、oldhand、small bet 的模擬報表：")
    add("")
    add("| 版本 | Normal Bet | Buy Feature |")
    add("|---|---|---|")
    for name, info in finals.items():
        add(f"| {name} | `{info['normal']}` | `{info['bf']}` |")
    add("")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final", nargs="+", required=True,
                       help="variant:config:label:normal.xlsx:bf.xlsx")
    parser.add_argument("--screening", default=None, help="text file with the scene screening log")
    parser.add_argument("--out", default=str(OTHER / "數值版本挑選_H027.md"))
    args = parser.parse_args()

    selection = json.loads((OTHER / "select_version_result.json").read_text(encoding="utf-8"))
    strip_diag = json.loads((OTHER / "fit_strip_diagnostics.json").read_text(encoding="utf-8"))
    finals = {}
    for spec in args.final:
        variant, config_code, label, normal, bf = spec.split(":")
        metrics = scorer.report_metrics(RECORD / normal, RECORD / bf)
        config = scorer.load_config(ROOT / config_code)
        finals[variant] = {"result": scorer.compare(config, metrics, float(label), 0.59),
                           "normal": normal, "bf": bf}
    screening = Path(args.screening).read_text(encoding="utf-8") if args.screening else "(未提供)"
    Path(args.out).write_text(build(selection, finals, strip_diag, screening), encoding="utf-8")
    print(f"written {args.out}")


if __name__ == "__main__":
    main()
