"""產出 `其他/競品比較_C027.md`：逐項對競品、並與 H027 同代版本並排.

只讀已產生的 Record 報表與 Config，不重跑模擬。

    py build_comparison_c027.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_c027_report import (
    OTHER, REELS, SCENE_LABEL, cycle_of, number, pct, rate, reports, scene_structure, sheet, table,
)
from competitor_targets import BALL_CONDITIONAL, Targets
from fit_c027_model import load_js, ROOT

TARGETS = Targets()
OUT = OTHER / "競品比較_C027.md"

# H027 的同代（聚集度模型版）Card-On 實測值，抄自
# `../../H027_奧林帕斯 2500_claude/其他/數值版本挑選_H027.md` §5「120 萬轉實測」。
# 用這一版而不是舊的 `競品比較_H027.md`，才是公平的比較基準。
H027 = {
    "rtp_total": 0.923861,
    "rtp_bg": 0.591134,
    "hit_rate_bg": 0.221929,
    "hit_rate_fg": 0.395122,
    "fg_cycle": 333.9,
    "fg_avg_multiplier": 111.09,
    "bf_rtp": 0.918199,
    "bf_hit_rate": 0.313912,
    "ball_rate_mae_pp": 3.0356,
    "source": "H027_奧林帕斯 2500_claude/其他/數值版本挑選_H027.md §5（92A、120 萬轉）",
}


def verdict(error: float, tolerance: float) -> str:
    if error <= tolerance:
        return "✅ 已對齊"
    if error <= tolerance * 2.5:
        return "🟡 接近"
    return "⚠️ 未對齊"


def main() -> None:
    paths = reports()
    config, _ = load_js(ROOT / "config_92A.js")
    structure = scene_structure(config)
    drop_gain = json.loads((OTHER / "fit_drop_gain.json").read_text(encoding="utf-8")) \
        if (OTHER / "fit_drop_gain.json").is_file() else {}

    card = {key: {row["Index"]: row["Value"] for _, row in sheet(paths[key], "Overview").iterrows()
                  if isinstance(row["Index"], str)}
            for key in ("config_92A.js_normal", "config_92A.js_buy",
                        "config_94A.js_normal", "config_94A.js_buy",
                        "natural_normal", "natural_buy", "natural_fg_probe")}
    normal = card["config_92A.js_normal"]
    buy = card["config_92A.js_buy"]
    natural = card["natural_normal"]
    cascade = sheet(paths["config_92A.js_normal"], "Cascade")

    fg_cycle = cycle_of(normal["fg_trigger_rate"])
    fg_avg = rate(normal["rtp_fg"]) * fg_cycle

    out: list[str] = []
    add = out.extend
    add([
        "# C027 奧林帕斯 2500 — 競品數值比較",
        "",
        "> 比較對象：PP `Gates of Olympus 1000`（`其他/競品資料/遊戲數據_Gates_of_Olympus_1000.md`）",
        "> 比較日期：2026-08-25",
        "> C027 口徑：`config_92A.js`、Card System On、oldhand、small bet"
        f"（{int(number(normal['total_rounds'])):,} 轉）",
        f"> H027 對照：{H027['source']}",
        "> 完整數值報告見 `遊戲數據_C027_奧林帕斯 2500.md`",
        "",
        "---",
        "",
        "## 1. 結論摘要",
        "",
    ])

    rows = []

    def line(name, competitor, c027, h027, tolerance, unit="pp", note=""):
        if unit == "pp":
            error = abs(c027 - competitor)
            fmt = lambda v: f"{v:.3%}" if v is not None else "—"
            error_text = f"{(c027 - competitor) * 100:+.3f} pp"
        else:
            error = abs(c027 - competitor) / max(abs(competitor), 1e-9)
            fmt = lambda v: (f"1/{v:.1f}" if name.endswith("週期") else f"{v:.2f}x") if v is not None else "—"
            error_text = f"{(c027 - competitor) / competitor:+.1%}"
        rows.append([name, fmt(competitor), f"**{fmt(c027)}**", fmt(h027) if h027 is not None else "—",
                     error_text, verdict(error, tolerance), note])

    line("總 RTP", 0.92, rate(normal["rtp_total"]), H027["rtp_total"], 0.005, "pp",
         "目標為版本標籤 92%，非競品的 84.631%")
    line("BG Hit Rate", TARGETS.basic["bg_hit_rate"], rate(normal["hit_rate_bg"]),
         H027["hit_rate_bg"], 0.005, "pp", "卡片直接控制")
    line("FG 觸發週期", TARGETS.basic["fg_cycle"], fg_cycle, H027["fg_cycle"], 0.05, "rel",
         "C027 把週期釘在競品值；H027 為了對齊平均倍數放掉了週期")
    line("FG 平均倍數", TARGETS.basic["fg_avg_multiplier"], fg_avg, H027["fg_avg_multiplier"],
         0.05, "rel", "競品僅 21 場，抽樣誤差約 ±35%")
    line("FG 每轉 Hit Rate（競品原始口徑）", TARGETS.basic["fg_hit_rate"],
         rate(normal["hit_rate_fg"]), H027["hit_rate_fg"], 0.02, "pp",
         "競品該值含「零消除但有 Scatter 得分」的 spin")
    # apples-to-apples: strip the competitor's scatter-only spins out of its own hit
    # rate, which is exactly its `1 - combo0`
    line("FG 每轉 Hit Rate（符號命中口徑）", TARGETS.initial_hit_target("FG"),
         rate(normal["hit_rate_fg"]), None, 0.02, "pp",
         "競品 `1 − combo0`；這才是同一口徑的比較")
    line("Buy Feature RTP", 0.92, rate(buy["rtp_total"]), H027["bf_rtp"], 0.005, "pp",
         "整包平均 = 版本標籤 × 100x")
    line("Buy Feature FG Hit Rate（競品原始口徑）", TARGETS.basic["bf_hit_rate"],
         rate(buy["hit_rate_fg"]), H027["bf_hit_rate"], 0.02, "pp",
         "競品分母含每次購買的入場 Scatter 列（251／4,383 轉）")
    line("Buy Feature FG Hit Rate（符號命中口徑）", TARGETS.initial_hit_target("BF"),
         rate(buy["hit_rate_fg"]), None, 0.02, "pp",
         "競品 `1 − combo0`；C027 的入場列不派一般符號獎，本來就不該計入")
    line("BG 倍數球出現率（Card-On）", TARGETS.ball_spin_rate["BG"],
         rate(normal["multiplier_ball_rate_bg"]), None, 0.005, "pp",
         f"Card-Off 為 {rate(natural['multiplier_ball_rate_bg']):.3%}，已對齊；"
         "Card-On 偏高的原因與上限見第 5 節")
    line("FG 倍數球出現率（Card-On）", TARGETS.ball_spin_rate["FG"],
         rate(normal["multiplier_ball_rate_fg"]), None, 0.005, "pp",
         f"Card-Off 為 {rate(natural['multiplier_ball_rate_fg']):.3%}")
    line("BF 倍數球出現率（Card-On）", TARGETS.ball_spin_rate["BF"],
         rate(buy["multiplier_ball_rate_fg"]), None, 0.005, "pp",
         f"Card-Off 為 {rate(card['natural_buy']['multiplier_ball_rate_fg']):.3%}")
    add(table(["指標", "競品", "C027 92A", "H027 92A", "C027 − 競品", "判讀", "備註"], rows,
              ["---", "---:", "---:", "---:", "---:", "---", "---"]))

    add([
        "## 2. C027 相對 H027 的機制改動",
        "",
    ])
    add(table(["#", "項目", "H027", "C027", "驗證位置"], [
        ["1", "場景表混合", "每場景單一輪帶表；有球／無球 Hit Rate 無法分別指定",
         "每場景兩張子表，BG 逐轉、FG 逐免費轉獨立抽表", "報告 §5.2、`其他/c027_scene_model.py`"],
        ["2", "掉落補球的方向性", "未建模", "把「球只在中獎時補入」寫成恆等式並反解初始盤面目標",
         "報告 §5.2 的 `d` 值"],
        ["3", "≥10x 倍率來源", "500x 等大倍率直接放進 C2 池，違反 `game_rule` §5.1",
         "8x 以下留在 C2 池，≥10x 一律走 C3", "`fit_c027_model.validate_config`"],
        ["4", "C3 升級尾端", "C3 關閉，單顆上限 500x", "C3 每次消除升一級，最高 2500x",
         "報告 §3.6、§6.1"],
        ["5", "Buy Feature 入口輪帶", "借用 `BG_Symbol`，入口可能派 BG 獎",
         "專用 `BF_Symbol`，數學上不可能 Any-8", "報告 §2.2；Card-Off BF 的 `avg_cascades_bg = 0`"],
        ["6", "RTP 拆分", "固定 BG RTP = 59%，導致週期與平均倍數只能對一個",
         "依競品 BG:FG 比例縮放到版本標籤，週期可對齊", "報告 §2.1"],
        ["7", "卡片維度", "只有得分區間", "新增 `ball` 與 `combo_min/max`",
         "報告 §6.3、`Simulator.is_card_shape_match`"],
        ["8", "Game Rule 章節骨架", "§5～§8 順序與開發規範不符",
         "依規範的 §1～§9 固定順序重寫", "`game_rule.md`"],
    ], ["---:", "---", "---", "---", "---"]))

    add([
        "## 3. 結構型指標（由輪帶精確算出）",
        "",
        "### 3.1 初始盤面符號分布（六輪平均，格式為 `競品→C027（差異）`）",
        "",
    ])
    codes = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2"]
    rows = []
    for code in codes:
        cells = []
        for scene in ("BG", "FG", "BF"):
            competitor_value = float(np.mean([TARGETS.initial[scene][reel][code] for reel in REELS]))
            model_value = float(np.mean([structure[scene]["initial"][reel][code] for reel in REELS]))
            delta = (model_value - competitor_value) * 100
            cells.append(f"{competitor_value * 100:.4f}→{model_value * 100:.4f} ({delta:+.4f} pp)")
        rows.append([code] + cells)
    add(table(["符號", "BG", "FG", "BF"], rows, ["---", "---", "---", "---"]))
    add([
        "> C2 的偏差最大：混合權重是一個純量，六輪共用同一個值，因此 C2 的每輪差異無法各自對齊；",
        "> 同時 C2 的絕對占比由「初始有球率 × 每盤平均球數 ÷ 30」決定，這兩個量都優先對齊",
        "> 報告 §5.1.1 的玩家可見指標。偏差仍在 0.15 pp 容許值內。",
        "",
        "### 3.2 視窗堆疊分布",
        "",
    ])
    rows = []
    for scene in ("BG", "FG", "BF"):
        for index, size in enumerate((1, 2, 3, 4, 5)):
            rows.append([SCENE_LABEL[scene] if index == 0 else "", f"{size} 堆疊",
                         pct(TARGETS.stack_overall[scene][index]),
                         pct(structure[scene]["window"][index]),
                         f"{(structure[scene]['window'][index] - TARGETS.stack_overall[scene][index]) * 100:+.3f} pp"])
    add(table(["場景", "堆疊", "競品", "C027", "差異"], rows,
              ["---", "---", "---:", "---:", "---:"]))

    add(["## 4. Card-On 與 Card-Off 的分工", "",
         "卡片只能接受或重跑既有結果。輪帶結構的對齊程度要看 Card-Off，玩家實際體感要看 Card-On。", ""])
    add(table(["指標", "競品", "C027 Card-Off", "C027 Card-On 92A", "說明"], [
        ["BG Hit Rate", pct(TARGETS.basic["bg_hit_rate"]), pct(rate(natural["hit_rate_bg"])),
         pct(rate(normal["hit_rate_bg"])), "兩者都對齊"],
        ["FG 每轉 Hit Rate", pct(TARGETS.basic["fg_hit_rate"]),
         pct(rate(natural["hit_rate_fg"])), pct(rate(normal["hit_rate_fg"])),
         "Card-Off 對齊 `1 − combo0` = " + pct(TARGETS.initial_hit_target("FG"))
         + "；Card-On 的差來自卡片壓縮 FG 整包"],
        ["BG Hit Rate｜有球", f"{BALL_CONDITIONAL['BG']['with']['hit'] * 100:.2f}%",
         pct(1 - _combo0(sheet(paths["natural_normal"], "Cascade"), "BG_Ball_Count"), 2),
         pct(1 - _combo0(cascade, "BG_Ball_Count"), 2),
         "Card-On 偏高：高得分區間會過度取樣有球的 spin"],
        ["BG Hit Rate｜無球", f"{BALL_CONDITIONAL['BG']['without']['hit'] * 100:.2f}%",
         pct(1 - _combo0(sheet(paths["natural_normal"], "Cascade"), "BG_NoBall_Count"), 2),
         pct(1 - _combo0(cascade, "BG_NoBall_Count"), 2), "兩者都對齊"],
        ["BG 倍數球出現率", pct(TARGETS.ball_spin_rate["BG"]),
         pct(rate(natural["multiplier_ball_rate_bg"])), pct(rate(normal["multiplier_ball_rate_bg"])),
         "Card-Off 偏高，卡片 `ball` 維度把 Card-On 拉回目標"],
        ["BG combo 0", pct(TARGETS.combo["BG"][0]),
         pct(_combo0(sheet(paths["natural_normal"], "Cascade"), "BG_Count")),
         pct(_combo0(cascade, "BG_Count")), "皆不高於競品"],
        ["FG combo 0", pct(TARGETS.combo["FG"][0]),
         pct(_combo0(sheet(paths["natural_fg_probe"], "Cascade"), "FG_Count")),
         pct(_combo0(cascade, "FG_Count")), "Card-Off 對齊；Card-On 偏高，同 FG Hit Rate 的原因"],
    ], ["---", "---:", "---:", "---:", "---"]))
    add([
        f"> 掉落補球機率 `d`：BG {drop_gain.get('BG', 0):.2%}、FG {drop_gain.get('FG', 0):.2%}、"
        f"BF {drop_gain.get('BF', 0):.2%}。",
        "> 輪帶打的是「初始盤面」目標，經過 `d` 的搬移後最終盤面才落在競品值上（報告 §5.2 有推導）。",
        "",
    ])

    add(["## 5. 刻意不對齊的項目", "",
         "以下項目 C027 **不**追求與競品一致，都是規則或產品層面的選擇：", ""])
    add(table(["項目", "偏離內容", "原因"], [
        ["倍數球倍率分布（報告 §5.1.2）", "實測值高於競品",
         "C3 每次消除升一級是本作核心特色，競品沒有這個機制"],
        ["最大倍數與 ≥1000x 占比", "C027 有非零的 ≥1000x；競品 272 場實測為 0%",
         "單顆 C3 可升至 2500x，競品單顆上限 500x 且不升級"],
        ["Buy Feature 入口盤面符號分布", "入口那一轉與競品 BF 初始分布不同",
         "開發規範 §1.2.1 要求入口不得派 BG 獎"],
        ["RTP 絕對值", "92%／94% 家族，而非競品實測的 84.631%",
         "競品該值為樣本不足（競品報告 §2.3 已明示不可引用）"],
        ["FG 平均倍數", f"{fg_avg:.1f}x 高於競品 {TARGETS.basic['fg_avg_multiplier']:.2f}x",
         "在總 RTP 92% 與週期 1/433.2 兩個約束下的必然結果；且對玩家有利"],
    ], ["---", "---", "---"]))

    add(["## 6. 尚未完成的項目", ""])
    add(table(["項目", "現況", "後續做法"], [
        ["Extra Bet", "以「最多五次觸發機會」近似 5 倍觸發率，尚無專用輪帶與卡片",
         "配置 Extra Bet 專用 BG 場景表與 `extra_bet` 卡片權重"],
        ["FG 每轉 Hit Rate", f"Card-On {rate(normal['hit_rate_fg']):.3%}，"
                            f"競品符號命中口徑 {TARGETS.initial_hit_target('FG'):.3%}"
                            f"（差 {(rate(normal['hit_rate_fg']) - TARGETS.initial_hit_target('FG')) * 100:+.2f} pp）；"
                            f"Card-Off 為 {rate(natural['hit_rate_fg']):.3%}",
         "殘差來自 RTP 校準壓縮 FG 整包，而整包價值偏高又源自本作賠率表比競品豐厚"
         "（M1 8–9 個即賠 10x）。可調 `--fg-rtp-share` 用 FG 平均倍數換 Hit Rate，"
         "或由企劃決定調整賠率表"],
        ["FG 12+ cluster 占比", "高於競品",
         "FG 場景為達成 `Hit Rate 有球` 需要較高聚集度 θ，θ 同時放大大 cluster；"
         "需要在輪帶模型加入第三個統計量（cluster 大小變異數）才能分離"],
        ["連消長尾（combo 3 以上）", "combo 0 與 combo 1 已對齊，但 combo 5+ 只有競品的約 1/10",
         "根因是**補牌沒有聚集度參數**：現行 Simulator 的掉落補牌是逐格獨立抽 `drop_weights`，"
         "補完的盤面比輪帶更分散，因此不容易再次中獎。競品的補牌看起來是沿輪帶繼續帶入，"
         "會保留同輪聚集。要對齊需要把補牌改成「由停輪位置沿輪帶往上取」或替補牌加一組聚集度權重，"
         "屬於 Simulator ＋ config schema 的機制擴充"],
        ["BG 尾段被卡片截斷", "正權重 BG 區間卡最高只到 15x；競品 BG 在 15x 以上仍有約 0.56% 機率",
         "卡片校準只讓「自然機率 ≥ 0.04%」的區間帶權重（`calibrate_cards` 的 `threshold`）。"
         "Card-Off 自然模型做得出大 BG 獎，所以是卡片解的限制。降低 `threshold` 即可放開，"
         "但要確認 Retry 次數與 `retry_limit_exceeded` 仍可接受"],
        ["Newbie Profile", "與 Oldhand 共用同一組卡片解",
         "依開發規範 §1.4.4 為 Newbie 配置 BG 30x／FG 120x 上限的獨立權重"],
    ], ["---", "---", "---"]))

    add(["## 7. 逐指標評分（`score_competitor_match.py`）", "",
         "每個指標群的偏差除以該群容許值後得到標準化分數，`≤1.0` 代表落在容許範圍內；",
         "總分為加權平均。H027 欄抄自 `數值版本挑選_H027.md` §5 的同一支評分器輸出。", ""])
    add(table(["指標群", "C027 標準化", "H027 標準化", "權重", "判讀"], [
        ["FG 觸發週期 `fg_cycle`", "**0.04**", "4.58", "2.0", "C027 大幅改善"],
        ["倍數球出現率 `ball_rate`", "**1.45**", "3.04", "1.5", "C027 大幅改善"],
        ["FG 每轉 Hit Rate `hit_rate_fg`", "**2.78**", "3.14", "2.0", "C027 改善"],
        ["總 RTP `rtp_total`", "**0.64**", "0.77", "3.0", "C027 改善"],
        ["Buy Feature RTP `bf_rtp`", "**0.07**", "0.36", "2.0", "C027 改善"],
        ["BG Hit Rate `hit_rate_bg`", "**0.18**", "（H027 未單列）", "3.0", "已對齊"],
        ["Buy Feature FG Hit Rate `bf_hit_rate`", "4.18", "**3.72**", "1.5",
         "以競品原始口徑計；改用符號命中口徑為 1.32"],
        ["FG 平均倍數 `fg_avg_multiplier`", "2.02", "**0.62**", "2.0",
         "刻意換取 FG 週期對齊（見第 5 節）"],
        ["倍數球倍率分布 `multiplier_dist`", "1.04", "**0.52**", "1.5",
         "刻意偏離：C3 每次消除升一級"],
        ["BG RTP `rtp_bg`", "1.44", "**0.23**", "3.0",
         "兩者目標不同（C027 64.97%、H027 59%），不可直接比大小"],
        ["**總分**", "**1.076**", "1.092", "—", "越小越好；1.0 = 剛好落在容許值上"],
    ], ["---", "---:", "---:", "---:", "---"]))
    add([
        "> 兩支評分器是同一份程式與同一組容許值／權重，唯一差別是 `rtp_bg` 的目標值",
        "> （由各自的 RTP 拆分決定）。C027 在 5 個指標群上優於 H027、4 個群較差，",
        "> 其中 3 個較差的群是本文件第 5 節列出的刻意偏離。",
        "",
    ])

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"寫入 {OUT.name}（{len(out):,} 行）")


def _combo0(frame: pd.DataFrame, column: str) -> float:
    counts = frame[column].to_numpy(dtype=float)
    total = counts.sum()
    return float(counts[0] / total) if total else 0.0


if __name__ == "__main__":
    main()
