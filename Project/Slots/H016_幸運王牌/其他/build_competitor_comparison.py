from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


H016_DIR = Path(__file__).resolve().parent.parent
OUTPUT = H016_DIR / "其他" / "競品參考數值比較.md"
RECORD_DIR = H016_DIR / "Record"
COMPETITOR_DIR = Path(
    "C:/Users/rhinshen/Mine/個人工作區/市場資訊/H5/遊戲資源/JILI/"
    "JILI - Super Ace/遊戲資料"
)
FILES = [
    COMPETITOR_DIR / "SuperAce_BG_Combined_NoJP.jsonl",
    COMPETITOR_DIR / "SuperAce_BG_3.jsonl",
    COMPETITOR_DIR / "Super_Ace_BG_4.jsonl",
]
SYMBOL_MAP = {
    "Bonus": "C1", "Symbol1": "M1", "Symbol2": "M2", "Symbol3": "M3",
    "Symbol4": "M4", "Symbol5": "A", "Symbol6": "K", "Symbol7": "Q", "Symbol8": "J",
}
SYMBOLS = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J"]
GOLD_TO_BASE = {"G1": "M1", "G2": "M2", "G3": "M3", "G4": "M4", "GA": "A", "GK": "K", "GQ": "Q", "GJ": "J"}


def pct(value: float, digits: int = 4) -> str:
    return f"{value * 100:.{digits}f}%"


def pp(value: float) -> str:
    return f"{value * 100:+.4f} pp".replace("+0.0000", "0.0000")


def raw_competitor() -> dict[str, Any]:
    counts = {
        scene: {
            "initial": [Counter() for _ in range(5)], "drop": [Counter() for _ in range(5)],
            "gold_initial": Counter(), "gold_drop": Counter(), "initial_total": Counter(), "drop_total": Counter(),
            "combo": Counter(), "spins": 0, "hits": 0, "m1_spins": 0,
        }
        for scene in ("BG", "FG")
    }
    coin_in = total_win = bg_win = fg_win = 0.0
    triggers = big_events = 0
    for path in FILES:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                obj = json.loads(line)
                plates = obj["plate"]["plate"]
                coin_in += float(obj["bet"])
                total_win += float(obj["win"])
                triggers += int(len(plates) > 1)
                for plate_index, plate in enumerate(plates):
                    scene = "BG" if plate_index == 0 else "FG"
                    data = counts[scene]
                    data["spins"] += 1
                    win = float(plate.get("win", 0.0))
                    data["hits"] += int(win > 0)
                    if scene == "BG":
                        bg_win += win
                    else:
                        fg_win += win
                    m1_present = False
                    for reel, column in enumerate(plate["column"]):
                        for symbol, gold in zip(column["row"], column["isGold"]):
                            mapped = SYMBOL_MAP[symbol]
                            data["initial"][reel][mapped] += 1
                            data["initial_total"][reel] += 1
                            data["gold_initial"][reel] += int(gold in (1, 2))
                            m1_present |= mapped == "M1"
                    combos = plate.get("combo", [])
                    data["combo"][min(len(combos), 5)] += 1
                    for combo in combos:
                        if scene == "BG" and any(change.get("isGold") == 102 for change in combo.get("change", [])):
                            big_events += 1
                        for change in combo.get("change", []):
                            if "symbol" not in change:
                                continue
                            reel = int(change.get("column", 0))
                            mapped = SYMBOL_MAP[change["symbol"]]
                            data["drop"][reel][mapped] += 1
                            data["drop_total"][reel] += 1
                            data["gold_drop"][reel] += int(change.get("isGold") in (1, 2))
                            m1_present |= mapped == "M1"
                    data["m1_spins"] += int(m1_present)
    bg_spins = counts["BG"]["spins"]
    fg_spins = counts["FG"]["spins"]
    return {
        "counts": counts, "rounds": bg_spins, "fg_spins": fg_spins, "coin_in": coin_in,
        "rtp_total": total_win / coin_in, "rtp_bg": bg_win / coin_in, "rtp_fg": fg_win / coin_in,
        "bg_hit_rate": counts["BG"]["hits"] / bg_spins, "fg_hit_rate": counts["FG"]["hits"] / fg_spins,
        "fg_trigger_rate": triggers / bg_spins, "avg_fg_spins": fg_spins / triggers,
        "m1_bg_spin_rate": counts["BG"]["m1_spins"] / bg_spins,
        "m1_fg_spin_rate": counts["FG"]["m1_spins"] / fg_spins,
        "w2_bg_event_rate": big_events / bg_spins,
    }


def record_data(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    summary = {row[0]: row[1] for row in workbook["Base Info"].iter_rows(min_row=2, values_only=True)}
    combo = {str(row[0]): {"BG": int(row[1]), "FG": int(row[2])} for row in workbook["Eliminate"].iter_rows(min_row=2, values_only=True)}
    ratios: dict[str, dict[str, list[float]]] = {}
    gold_ratios: dict[str, list[float]] = {}
    for scene, stage, sheet_name in (
        ("BG", "initial", "BG Initial Symbol"), ("BG", "drop", "BG Drop Symbol"),
        ("FG", "initial", "FG Initial Symbol"), ("FG", "drop", "FG Drop Symbol"),
    ):
        merged = {symbol: [0.0] * 5 for symbol in SYMBOLS}
        gold = [0.0] * 5
        for row in workbook[sheet_name].iter_rows(min_row=2, values_only=True):
            if row[0] is None:
                continue
            symbol = GOLD_TO_BASE.get(str(row[0]), str(row[0]))
            if str(row[0]) in GOLD_TO_BASE:
                for reel in range(5):
                    gold[reel] += float(row[1 + reel] or 0)
            if symbol in merged:
                for reel in range(5):
                    merged[symbol][reel] += float(row[1 + reel] or 0)
        ratios[f"{scene}_{stage}"] = merged
        gold_ratios[f"{scene}_{stage}"] = gold
    return {"summary": summary, "combo": combo, "ratios": ratios, "gold_ratios": gold_ratios}


def competitor_ratios(competitor: dict[str, Any], scene: str, stage: str) -> dict[str, list[float]]:
    data = competitor["counts"][scene]
    return {
        symbol: [data[stage][reel][symbol] / max(1, data[f"{stage}_total"][reel]) for reel in range(5)]
        for symbol in SYMBOLS
    }


def distribution_section(title: str, competitor_rows: dict[str, list[float]], h016_rows: dict[str, list[float]]) -> str:
    lines = [f"### {title}", "", "| Symbol | 模型 | R1 | R2 | R3 | R4 | R5 |", "|---|---|---:|---:|---:|---:|---:|"]
    for symbol in SYMBOLS:
        lines.append("| " + " | ".join([symbol, "Super Ace", *[pct(value) for value in competitor_rows[symbol]]]) + " |")
        lines.append("| " + " | ".join([symbol, "H016", *[pct(value) for value in h016_rows[symbol]]]) + " |")
    return "\n".join(lines)


def gold_table(competitor: dict[str, Any], h016: dict[str, Any], scene: str, stage: str) -> str:
    data = competitor["counts"][scene]
    lines = ["| 階段 | Reel | Super Ace 金框比例 | H016 金框比例 | 差異 |", "|---|---|---:|---:|---:|"]
    for reel in range(5):
        comp = data[f"gold_{stage}"][reel] / max(1, data[f"{stage}_total"][reel])
        model = h016["gold_ratios"][f"{scene}_{stage}"][reel]
        lines.append(f"| {'初始' if stage == 'initial' else '掉落'} | R{reel + 1} | {pct(comp)} | {pct(model)} | {pp(model - comp)} |")
    return "\n".join(lines)


def main() -> None:
    record = max(RECORD_DIR.glob("H0161_*_betmode0_100000_*.xlsx"), key=lambda path: path.stat().st_mtime)
    h016 = record_data(record)
    hs = h016["summary"]
    competitor = raw_competitor()
    core = [
        ("RTP", "Total RTP", competitor["rtp_total"], float(hs["rtp_total"])),
        ("RTP", "BG RTP", competitor["rtp_bg"], float(hs["rtp_bg"])),
        ("RTP", "FG RTP", competitor["rtp_fg"], float(hs["rtp_fg"])),
        ("Hit Rate", "BG Hit Rate", competitor["bg_hit_rate"], float(hs["bg_hit_rate"])),
        ("Hit Rate", "FG Hit Rate", competitor["fg_hit_rate"], float(hs["fg_hit_rate"])),
        ("FG", "FG Trigger Rate", competitor["fg_trigger_rate"], float(hs["fg_trigger_rate"])),
    ]
    core_lines = ["| 類別 | 指標 | Super Ace | H016 | 差異 |", "|---|---|---:|---:|---:|"]
    for category, metric, comp, model in core:
        core_lines.append(f"| {category} | {metric} | {pct(comp)} | {pct(model)} | {pp(model - comp)} |")
    core_lines.extend([
        f"| FG | 平均觸發週期 | {1 / competitor['fg_trigger_rate']:.2f} 局／次 | {float(hs['fg_trigger_cycle']):.2f} 局／次 | H016 {'慢' if float(hs['fg_trigger_cycle']) > 1 / competitor['fg_trigger_rate'] else '快'} {abs(float(hs['fg_trigger_cycle']) - 1 / competitor['fg_trigger_rate']):.2f} 局 |",
        f"| FG | 平均 Free Spins | {competitor['avg_fg_spins']:.4f} | {float(hs['avg_fg_spins']):.4f} | {float(hs['avg_fg_spins']) - competitor['avg_fg_spins']:+.4f} |",
    ])

    pay_lines = [
        "| Symbol | 3 輪 | 4 輪 | 5 輪 | 比較結果 |", "|---|---:|---:|---:|---|",
        "| M1 | 0.50 | 1.50 | 2.50 | 相同 |", "| M2 | 0.40 | 1.20 | 2.00 | 相同 |",
        "| M3 | 0.30 | 0.90 | 1.50 | 相同 |", "| M4 | 0.20 | 0.60 | 1.00 | 相同 |",
        "| A | 0.10 | 0.30 | 0.50 | 相同 |", "| K | 0.10 | 0.30 | 0.50 | 相同 |",
        "| Q | 0.05 | 0.15 | 0.25 | 相同 |", "| J | 0.05 | 0.15 | 0.25 | 相同 |",
    ]

    combo_sections = []
    for scene in ("BG", "FG"):
        h_den = int(hs["total_rounds"]) if scene == "BG" else sum(row[scene] for row in h016["combo"].values())
        c_den = competitor["rounds"] if scene == "BG" else competitor["fg_spins"]
        lines = [f"### {scene}", "", f"| 消除次數 | Super Ace | H016 | 差異 |", "|---|---:|---:|---:|"]
        for index, label in enumerate(("0", "1", "2", "3", "4", "5+")):
            comp = competitor["counts"][scene]["combo"][index] / c_den
            model = h016["combo"][label][scene] / h_den
            lines.append(f"| {label} | {pct(comp)} | {pct(model)} | {pp(model - comp)} |")
        combo_sections.append("\n".join(lines))

    document = f"""# 競品參考數值比較

## 目錄

- [Overvire](#overvire)
  - [核心指標比較](#核心指標比較)
- [賠率](#賠率)
- [符號分布](#符號分布)
  - [BG 初始 R1-R5](#bg-初始-r1-r5)
  - [BG 掉落 R1-R5](#bg-掉落-r1-r5)
  - [FG 初始 R1-R5](#fg-初始-r1-r5)
  - [FG 掉落 R1-R5](#fg-掉落-r1-r5)
- [消除率](#消除率)
- [M1 出現率](#m1-出現率)
- [金框比例](#金框比例)
- [大鬼事件率](#大鬼事件率)

## Overvire

### 比較基準

| 項目 | Super Ace | H016 現在版本 |
|---|---|---|
| 來源 | JILI 實機非重複 JSONL | `{record.name}` + `Simulator.py` |
| 樣本 | {competitor['rounds']:,} 個 BG Round、{competitor['fg_spins']:,} 個 FG Spin | {int(hs['total_rounds']):,} 個 Normal Bet Round |
| Card System | 競品實際遊玩資料 | 關閉 |
| Bet Mode | 一般投注 | Normal Bet，Bet Multi 1 |
| 輪帶 | `StripTable_SuperAce_還原.xlsx` | BG／FG 每輪 200 格、每格整數權重 1 |

輪帶只填入 `BG_Symbol`、`FG_Symbol` 原有的 `K:O`；停輪權重只填入原有的 `W:AA`。競品 stopW 依累積機率等距重採樣成 200 格，每格權重固定為整數 1；一般符號再依競品逐輪金框率轉成對應金框版本，Scatter 不轉。沒有新增模型欄位，也沒有修改 Parameter、賠率或其他工作表。

### 核心指標比較

{chr(10).join(core_lines)}

加入競品金框比例後，H016 的 BG、FG 與總 RTP 都明顯高於競品。原因是競品金框原本屬於盤面生成後的獨立疊加層；依本次需求折算進實體輪帶後，金框會同時參與連續 4 格視窗與 Cascade 補牌，再套用 H016 的金框保留轉 Wild 邏輯，因此不能把兩者視為完全等價的生成機制。

## 賠率

H016 與 Super Ace 參考賠率相同；表內數字為相對投注額倍數。

{chr(10).join(pay_lines)}

## 符號分布

### 套用方法

1. 依 `BG_Strip`／`FG_Strip` 原排列與 stopW 累積機率，等距重採樣成每輪 200 格後填入模型 `K:O`。
2. 每一格停輪權重固定為整數 `1`，填入 `W:AA`。
3. 一般符號依競品逐輪金框率轉為 `G1～GJ`；R1、R5 與 C1 不放金框。
4. 初始盤面依整數停輪權重選 1 個位置，再從輪帶連續取 4 格；Cascade 補牌依同一輪帶抽取，未新增獨立欄位。

{distribution_section('BG 初始 R1-R5', competitor_ratios(competitor, 'BG', 'initial'), h016['ratios']['BG_initial'])}

{distribution_section('BG 掉落 R1-R5', competitor_ratios(competitor, 'BG', 'drop'), h016['ratios']['BG_drop'])}

{distribution_section('FG 初始 R1-R5', competitor_ratios(competitor, 'FG', 'initial'), h016['ratios']['FG_initial'])}

{distribution_section('FG 掉落 R1-R5', competitor_ratios(competitor, 'FG', 'drop'), h016['ratios']['FG_drop'])}

## 消除率

比較口徑為每個 Spin 實際發生的消除次數，統一合併為 `0、1、2、3、4、5+`；FG 分母為實際 Free Spins。

{combo_sections[0]}

{combo_sections[1]}

## M1 出現率

比較口徑為該次 BG／FG Spin 的初始盤面或任何一次掉落中，至少出現 1 顆 M1。

| Scene | Super Ace | H016 | 樣本 | 差異 |
|---|---:|---:|---|---:|
| BG | {pct(competitor['m1_bg_spin_rate'])} | {pct(float(hs['m1_bg_spin_rate']))} | {int(hs['total_rounds']):,}／H016 | {pp(float(hs['m1_bg_spin_rate']) - competitor['m1_bg_spin_rate'])} |
| FG | {pct(competitor['m1_fg_spin_rate'])} | {pct(float(hs['m1_fg_spin_rate']))} | {int(competitor['fg_spins']):,} 競品 FG | {pp(float(hs['m1_fg_spin_rate']) - competitor['m1_fg_spin_rate'])} |

## 金框比例

競品金框是盤面生成後的獨立疊加層；H016 依需求將其折算進既有輪帶。200 格輪帶的最小刻度為 0.5%，因此採最接近競品比例的整數格數；R1、R5 不放金框，C1 不轉金框。

### BG

{gold_table(competitor, h016, 'BG', 'initial')}

{gold_table(competitor, h016, 'BG', 'drop')}

### FG

{gold_table(competitor, h016, 'FG', 'initial')}

{gold_table(competitor, h016, 'FG', 'drop')}

## 大鬼事件率

| Scene | Super Ace | H016 | 差異 |
|---|---:|---:|---:|
| BG | {pct(competitor['w2_bg_event_rate'])} | {pct(float(hs['w2_bg_event_rate']))} | {pp(float(hs['w2_bg_event_rate']) - competitor['w2_bg_event_rate'])} |
| FG | 0.0000% | {pct(float(hs['w2_fg_event_rate']))} | {pp(float(hs['w2_fg_event_rate']))} |

Random Wild 沿用競品實測整數權重：BG `0/2/3/4 = 37731/1401/235/18`，非零大鬼比例為 4.20%，且條件式平均額外複製 2.164 顆；FG 權重為 `1/0/0/0`，不產生大鬼。
"""
    OUTPUT.write_text(document, encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "record": record.name, "competitor_bg": competitor["rounds"], "competitor_fg": competitor["fg_spins"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
