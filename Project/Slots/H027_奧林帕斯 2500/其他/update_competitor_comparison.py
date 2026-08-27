from __future__ import annotations

import json
import re
from collections import Counter
from io import StringIO
from pathlib import Path

import pandas as pd


_cwd = Path.cwd()
_file_root = Path(__file__).resolve().parent.parent
_workspace_root = Path("C:/Users/rhinshen/Mine/個人工作區/工作區/Project/Slots/H027_奧林帕斯 2500")
ROOT = _cwd if (_cwd / "config.js").exists() else (_file_root if (_file_root / "config.js").exists() else _workspace_root)
RECORD = ROOT / "Record"
OUTPUT = ROOT / "其他" / "競品比較_H027.md"
COMPETITOR_ROOT = ROOT.parents[3] / "市場資訊" / "H5" / "遊戲資源" / "PP - Gates of Olympus 1000"
COMPETITOR_HTML = COMPETITOR_ROOT / "遊戲數據_Gates_of_Olympus_1000.html"
COMPETITOR_MD = COMPETITOR_ROOT / "遊戲數據_Gates_of_Olympus_1000.md"
REELS = [f"R{i}" for i in range(1, 7)]
SYMBOLS = ["C1", "M1", "M2", "M3", "M4", "A", "K", "Q", "J", "TE", "C2"]
SOURCE_TO_CODE = dict(zip(["1", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"], SYMBOLS))
COMP_COMBO = {
    "BG": [71.197, 17.838, 5.643, 2.780, 1.443, 1.099],
}
COMP_STACK = {
    "BG": [60.779, 35.114, 3.715, 0.364, 0.028],
    "FG": [61.313, 34.823, 3.598, 0.253, 0.014],
    "BF": [61.704, 34.560, 3.417, 0.299, 0.020],
}
COMP_BALL_RATE = {"BG": 3.711, "BF": 100.000}
COMP_BALL_HIT = {"BG": (48.89, 28.03), "BF": (100.00, None)}
MULTIPLIERS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 50, 100, 250, 500, 1000]
COMP_MULT = {
    "BG": [11.50, 9.67, 10.37, 14.39, 18.33, 15.53, 9.41, 4.81, 1.53, 2.06, .92, .92, .52, .04, 0, 0],
    "FG": [43.61, 23.87, 14.00, 11.57, 2.91, 1.86, 1.29, .32, .24, .16, .08, .08, 0, 0, 0, 0],
    "BF": [46.29, 24.84, 11.80, 10.09, 3.20, 1.41, .63, .63, .40, .23, .15, .25, .08, 0, 0, 0],
}


def load_js(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def latest(pattern: str) -> Path:
    return max(RECORD.glob(pattern), key=lambda path: path.stat().st_mtime)


def overview(path: Path) -> dict[str, str]:
    frame = pd.read_excel(path, sheet_name="Overview")
    return {str(row["Index"]): str(row["Value"]) for _, row in frame.dropna(subset=["Index"]).iterrows()}


def percent_value(value: str) -> float:
    return float(str(value).split("%", 1)[0])


def cycle_value(value: str) -> float:
    match = re.search(r"cycle ([0-9.]+)", str(value))
    return float(match.group(1))


def distribution_targets():
    tables = pd.read_html(StringIO(COMPETITOR_HTML.read_text(encoding="utf-8")))
    output = {}
    for scene, initial_index, drop_index in (("BG", 11, 14), ("FG", 12, 15), ("BF", 13, 16)):
        output[scene] = {}
        for stage, table_index in (("Initial", initial_index), ("Drop", drop_index)):
            frame = tables[table_index]
            first = frame.columns[0]
            values = {code: {} for code in SYMBOLS}
            for row_index, (_, row) in enumerate(frame.iterrows()):
                raw = str(row[first]).strip().removesuffix(".0")
                code = SOURCE_TO_CODE.get(raw)
                if code:
                    for reel in REELS:
                        values[code][reel] = float(str(row[reel]).replace("%", ""))
            output[scene][stage] = values
    return output


def config_distributions(config):
    result = {}
    id_to_code = dict(zip(config["symbol_ids"], config["symbol_codes"]))
    strips = dict(zip(config["strip_names"], config["strips"]))
    profiles = {
        "BG": (config["parameter"]["normal"]["base_reel_names"], config["parameter"]["normal"]["base_reel_weights"]),
        "FG": (config["parameter"]["normal"]["free_table"]["names"], config["parameter"]["normal"]["free_table"]["initial"]),
        "BF": (config["parameter"]["featurebuy"]["free_table"]["names"], config["parameter"]["featurebuy"]["free_table"]["initial"]),
    }
    for scene, (names, table_weights) in profiles.items():
        initial = {code: {} for code in SYMBOLS}
        for reel_index, reel in enumerate(REELS):
            rates = Counter()
            scene_total = sum(table_weights)
            for name, table_weight in zip(names, table_weights):
                strip = strips[name]
                total = sum(row[reel_index] for row in strip["weights"])
                counts = Counter()
                for symbols, weights in zip(strip["symbols"], strip["weights"]):
                    counts[id_to_code[symbols[reel_index]]] += weights[reel_index]
                for code in SYMBOLS:
                    rates[code] += table_weight * counts[code] / total
            for code in SYMBOLS:
                initial[code][reel] = rates[code] / scene_total * 100
        # Cascade replacements come from the same selected circular strip.
        result[scene] = {"Initial": initial, "Drop": {code: dict(values) for code, values in initial.items()}}
    return result


def window_stack(config, strip_name):
    strip = dict(zip(config["strip_names"], config["strips"]))[strip_name]
    id_to_code = dict(zip(config["symbol_ids"], config["symbol_codes"]))
    result = {}
    for reel_index, reel in enumerate(REELS):
        reel_length = strip["reel_lengths"][reel_index]
        sequence = [id_to_code[row[reel_index]] for row in strip["symbols"][:reel_length]]
        counts = Counter()
        for start in range(len(sequence)):
            window = [sequence[(start + offset) % len(sequence)] for offset in range(5)]
            maximum = 1
            run = 1
            for index in range(1, 5):
                if window[index] == window[index - 1] and window[index] not in {"C1", "C2", "C3"}:
                    run += 1
                    maximum = max(maximum, run)
                else:
                    run = 1
            counts[maximum] += 1
        result[reel] = [counts[size] / len(sequence) * 100 for size in range(1, 6)]
    return result


def mixed_window_stack(config, names, weights):
    tables = [window_stack(config, name) for name in names]
    total = sum(weights)
    return {
        reel: [sum(weight * table[reel][size] for weight, table in zip(weights, tables)) / total for size in range(5)]
        for reel in REELS
    }


def cascade_rates(path, scene):
    frame = pd.read_excel(path, sheet_name="Cascade")
    column = "BG_Count" if scene == "BG" else "FG_Count"
    values = dict(zip(frame["Cascade_Count"].astype(int), frame[column].astype(int)))
    total = sum(values.values())
    all_rates = [values.get(i, 0) / total * 100 for i in range(5)]
    all_rates.append(sum(value for key, value in values.items() if key >= 5) / total * 100)
    positive = total - values.get(0, 0)
    conditional = [values.get(i, 0) / positive * 100 for i in range(1, 5)]
    conditional.append(sum(value for key, value in values.items() if key >= 5) / positive * 100)
    return all_rates, conditional


def ball_cascade(path, scene):
    frame = pd.read_excel(path, sheet_name="Ball Cascade")
    prefix = "BG" if scene == "BG" else "FG"
    output = []
    for suffix in ("With_Ball", "Without_Ball"):
        column = f"{prefix}_{suffix}"
        total = frame[column].sum()
        hit = (total - int(frame.loc[frame["Cascade_Count"] == 0, column].iloc[0])) / total * 100
        output.append(hit)
    return tuple(output)


def prize_shares(path, scene):
    frame = pd.read_excel(path, sheet_name="Symbol Hit Rate")
    hit_cols = [f"{scene}_8_9_Hit", f"{scene}_10_11_Hit", f"{scene}_12_Plus_Hit"]
    pay_cols = [f"{scene}_8_9_Pay", f"{scene}_10_11_Pay", f"{scene}_12_Plus_Pay"]
    hits = [frame[col].sum() for col in hit_cols]
    pays = [frame[col].sum() for col in pay_cols]
    return [value / sum(hits) * 100 for value in hits], [value / sum(pays) * 100 for value in pays]


def multiplier_distribution(path, scene):
    frame = pd.read_excel(path, sheet_name="C2-C3 Multiplier")
    column = f"{scene}_Count"
    counts = dict(zip(frame["Multiplier"].astype(int), frame[column].astype(int)))
    total = sum(counts.values())
    return {value: counts.get(value, 0) / total * 100 for value in counts}, total


def fmt(values):
    return " | ".join(f"{value:.3f}%" for value in values)


def card_summary_row(label: str, path: Path) -> str:
    values = overview(path)
    is_bf = label.endswith("BF")
    sample = values["total_rounds"]
    bg_rtp = "—" if is_bf else values["rtp_bg"]
    bg_hit = "—" if is_bf else values["hit_rate_bg"]
    cycle = "—" if is_bf else values["fg_trigger_rate"]
    return (
        f"| {label} | {sample} | {values['rtp_total']} | {bg_rtp} | {values['rtp_fg']} | "
        f"{bg_hit} | {values['hit_rate_fg']} | {cycle} |"
    )


def main():
    competitor_intervals = []
    for line in COMPETITOR_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("| `("):
            parts = [part.strip() for part in line.split("|")[1:-1]]
            competitor_intervals.append([
                float(parts[2].replace("%", "")),
                float(parts[4].replace("%", "")),
                float(parts[6].replace("%", "")),
            ])
    if len(competitor_intervals) != 64:
        raise ValueError(f"Expected 64 competitor multiplier intervals, got {len(competitor_intervals)}")

    config = load_js(ROOT / "config.js")
    normal = latest("H0271_01_*_betmode0_106.xlsx")
    bf = latest("H0271_01_*_betmode2_200000.xlsx")
    card_reports = {
        "92A Normal": latest("H027192_01000000_*_betmode0_*_oldhand_small_bet_card.xlsx"),
        "92A BF": latest("H027192_01000000_*_betmode2_*_oldhand_small_bet_card.xlsx"),
        "94A Normal": latest("H027194_01000000_*_betmode0_*_oldhand_small_bet_card.xlsx"),
        "94A BF": latest("H027194_01000000_*_betmode2_*_oldhand_small_bet_card.xlsx"),
    }
    normal_overview, bf_overview = overview(normal), overview(bf)
    comp_dist, h_dist = distribution_targets(), config_distributions(config)
    lines = [
        "# H027 奧林帕斯 2500－競品數值比較",
        "",
        "> 比較日期：2026-08-26  ",
        "> 競品：Gates of Olympus 1000 實機資料；H027：v1 目前參數的最新模擬。  ",
        "> 初版設計原則：自然機率先對標，卡片後收斂 RTP／倍率線型。",
        "",
        "## 目錄",
        "",
        "- [Executive Summary](#executive-summary)",
        "- [基本指標](#基本指標)",
        "- [符號分布](#符號分布)",
        "- [符號堆疊](#符號堆疊)",
        "- [獎項占比](#獎項占比)",
        "- [消除分布](#消除分布)",
        "- [倍數球](#倍數球)",
        "- [倍率線型與最大倍數](#倍率線型與最大倍數)",
        "- [資料與限制](#資料與限制)",
        "",
        "## Executive Summary",
        "",
        "| 指標 | 結果 | 說明 |",
        "|---|---|---|",
        "| 自然 RTP | 仍偏高 | H027 98.485%，競品樣本 90.748%；主要差在 FG 貢獻 +18.535 pp。 |",
        "| Hit Rate | 接近 | BG +0.220 pp；FG +0.489 pp，兩者都略高於競品。 |",
        "| FG 週期／平均倍數 | 仍有差距 | 週期慢 27.39 spins；自然 FG 平均約 184.46x，高於競品 94.47x。 |",
        "| 符號與堆疊 | 輪帶層已對標 | 符號序列來自競品還原輪帶，每輪 63～64 stops，掉落沿同輪帶補入。 |",
        "| 卡片調整 | 已生效 | 92A／94A 最新 10 萬場抽驗均已分開 Normal 與 BF，見下表。 |",
        "| 倍數分布 | 架構達成、比例待收斂 | C2 只出 2x～8x；10x 以上只由 C3／Super，球數越多機率越高。 |",
        "| 倍數球 | 分布待調整 | BG 有球率 3.440%，略低於競品 3.711%；FG 球上倍率仍比競品偏尾。 |",
        "| FG 平均倍數 | 偏高 | 自然值約 221.20x，高於競品 107.74x；待自然盤確認後由 92A／94A 卡片收斂。 |",
        "",
        "## 基本指標",
        "",
        "| 指標 | 競品 | H027 Card-Off | 差異 |",
        "|---|---:|---:|---:|",
        f"| BG RTP | 68.536% | {normal_overview['rtp_bg']} | {percent_value(normal_overview['rtp_bg']) - 68.536:+.3f} pp |",
        f"| FG RTP 貢獻 | 22.212% | {normal_overview['rtp_fg']} | {percent_value(normal_overview['rtp_fg']) - 22.212:+.3f} pp |",
        f"| 總 RTP | 90.748%（樣本） | {normal_overview['rtp_total']} | {percent_value(normal_overview['rtp_total']) - 90.748:+.3f} pp |",
        f"| BG Hit Rate | 28.807% | {normal_overview['hit_rate_bg']} | {percent_value(normal_overview['hit_rate_bg']) - 28.807:+.3f} pp |",
        f"| FG Hit Rate | 43.564% | {normal_overview['hit_rate_fg']} | {percent_value(normal_overview['hit_rate_fg']) - 43.564:+.3f} pp |",
        f"| FG 週期 | 1/425.3 | {normal_overview['fg_trigger_rate']} | {cycle_value(normal_overview['fg_trigger_rate']) - 425.3:+.2f} spins |",
        f"| FG 平均倍數 | 94.47x | {percent_value(normal_overview['rtp_fg']) / 100 * cycle_value(normal_overview['fg_trigger_rate']):.2f}x | {percent_value(normal_overview['rtp_fg']) / 100 * cycle_value(normal_overview['fg_trigger_rate']) - 94.47:+.2f}x |",
        f"| 最大得分 | 競品自然 FG 422.45x／BF 591.10x | {normal_overview['max_win_x']}x | 樣本最大值比較 |",
        f"| BF RTP／平均得分 | 85.413% | {bf_overview['rtp_total']} | {percent_value(bf_overview['rtp_total']) - 85.413:+.3f} pp |",
        "",
        "### Card-On 最新抽驗",
        "",
        "| 版本／模式 | 樣本 | 總 RTP | BG RTP | FG RTP | BG Hit | FG Hit | FG 週期 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        *[card_summary_row(label, path) for label, path in card_reports.items()],
        "",
        "Card-On 僅 10 萬場，用來確認卡片有生效；最終 RTP 驗收仍應放大樣本。",
        "",
        "## 符號分布",
        "",
        "每格格式為 `競品/H027`；R1～R6 分開列。",
    ]
    for stage in ("Initial", "Drop"):
        lines += ["", f"### {'初始轉輪' if stage == 'Initial' else '消除後掉落'}"]
        for scene in ("BG", "FG", "BF"):
            lines += ["", f"#### {scene}", "", "| Symbol | R1 | R2 | R3 | R4 | R5 | R6 |", "|---|---:|---:|---:|---:|---:|---:|"]
            for symbol in SYMBOLS:
                cells = [f"{comp_dist[scene][stage][symbol][reel]:.3f}/{h_dist[scene][stage][symbol][reel]:.3f}%" for reel in REELS]
                lines.append(f"| {symbol} | " + " | ".join(cells) + " |")
    lines += ["", "**差異摘要：** H027 使用還原輪帶的實際符號序列，但目前各 Set 的使用比例不等於競品 Response 樣本中的混合比例，因此逐輪邊際分布仍有明顯差距；掉落也因沿同輪帶補入，不會自動變成競品實測掉落分布。"]

    lines += ["", "## 符號堆疊", "", "競品為實機整體五格視窗；H027 為還原輪帶依實際 Set 使用比例加權後的 R1～R6。"]
    stack_profiles = {
        "BG": (config["parameter"]["normal"]["base_reel_names"], config["parameter"]["normal"]["base_reel_weights"]),
        "FG": (config["parameter"]["normal"]["free_table"]["names"], config["parameter"]["normal"]["free_table"]["initial"]),
        "BF": (config["parameter"]["featurebuy"]["free_table"]["names"], config["parameter"]["featurebuy"]["free_table"]["initial"]),
    }
    for scene, (strip_names, strip_weights) in stack_profiles.items():
        stacks = mixed_window_stack(config, strip_names, strip_weights)
        lines += ["", f"### {scene}", "", "| 版本／輪 | Stack 1 | Stack 2 | Stack 3 | Stack 4 | Stack 5 |", "|---|---:|---:|---:|---:|---:|", f"| 競品整體 | {fmt(COMP_STACK[scene])} |"]
        for reel in REELS:
            lines.append(f"| H027 {reel} | {fmt(stacks[reel])} |")
    lines += ["", "**差異摘要：** H027 目前明顯偏向 2～3 堆疊；競品整體則約 61% 為 Stack 1、35% 為 Stack 2。這是現在最大的輪帶結構差異之一。"]

    lines += ["", "## 獎項占比", "", "| 場景 | 版本 | 8–9 | 10–11 | 12+ |", "|---|---|---:|---:|---:|"]
    comp_prize = {"BG": ([86.52, 12.57, .91], [74.40, 19.95, 5.65]), "FG": ([82.41, 15.99, 1.61], [71.27, 20.75, 7.98]), "BF": ([83.37, 15.31, 1.33], [69.67, 23.30, 7.03])}
    for scene, path in (("BG", normal), ("FG", normal), ("BF", bf)):
        hit_share, pay_share = prize_shares(path, "BG" if scene == "BG" else "FG")
        lines += [
            f"| {scene} | 競品出現 | {fmt(comp_prize[scene][0])} |",
            f"| {scene} | H027 出現 | {fmt(hit_share)} |",
            f"| {scene} | 競品得分 | {fmt(comp_prize[scene][1])} |",
            f"| {scene} | H027 得分 | {fmt(pay_share)} |",
        ]
    lines += ["", "**差異摘要：** 獎項出現占比已相當接近；得分占比仍有偏移，尤其 H027 BG 12+ 較高，FG／BF 12+ 反而較低。"]

    lines += ["", "## 消除分布", "", "最新競品報告只有可直接對比的 BG 付費 Spin 數據；Combo 5+ 合併所有 5 次以上消除。"]
    all_rates, conditional = cascade_rates(normal, "BG")
    comp_positive = COMP_COMBO["BG"][1:]
    comp_positive = [value / sum(comp_positive) * 100 for value in comp_positive]
    lines += ["", "### BG", "", "| 版本 | Combo 0 | Combo 1 | Combo 2 | Combo 3 | Combo 4 | Combo 5+ |", "|---|---:|---:|---:|---:|---:|---:|", f"| 競品 | {fmt(COMP_COMBO['BG'])} |", f"| H027 | {fmt(all_rates)} |", "", "| 版本 | Combo 1 | Combo 2 | Combo 3 | Combo 4 | Combo 5+ |", "|---|---:|---:|---:|---:|---:|", f"| 競品 | {fmt(comp_positive)} |", f"| H027 | {fmt(conditional)} |"]
    lines += ["", "**差異摘要：** BG 整體消除分布已很接近；排除 Combo 0 後，H027 Combo 1 低約 1.46 pp，Combo 2～4 略高。"]

    lines += ["", "## 倍數球", "", "### 出現率與有／無球 Hit", "", "| 場景 | 競品有球率 | H027 有球率 | 競品有球／無球 Hit | H027 有球／無球 Hit |", "|---|---:|---:|---:|---:|"]
    for scene, path, report_scene in (("BG", normal, "BG"),):
        ov = overview(path)
        rate = ov["multiplier_ball_rate_bg" if report_scene == "BG" else "multiplier_ball_rate_fg"]
        hits = ball_cascade(path, report_scene)
        lines.append(f"| {scene} | {COMP_BALL_RATE[scene]:.3f}% | {rate} | {COMP_BALL_HIT[scene][0]:.2f}%／{COMP_BALL_HIT[scene][1]:.2f}% | {hits[0]:.2f}%／{hits[1]:.2f}% |")
    fg_hits = ball_cascade(normal, "FG")
    bf_hits = ball_cascade(bf, "FG")
    lines += ["", f"H027 FG 有球率 {normal_overview['multiplier_ball_rate_fg']}，有球／無球 Hit {fg_hits[0]:.2f}%／{fg_hits[1]:.2f}%；H027 BF 有球率 {bf_overview['multiplier_ball_rate_fg']}，有球／無球 Hit {bf_hits[0]:.2f}%／{bf_hits[1]:.2f}%。競品最新報告沒有可直接對比的 FG 有球率。", "", "### 球上倍率分布", "", "| 倍率 | 競品 BG | H027 BG | 競品 FG | H027 FG | 競品 BF | H027 BF |", "|---:|---:|---:|---:|---:|---:|---:|"]
    bg_mult, _ = multiplier_distribution(normal, "BG")
    fg_mult, _ = multiplier_distribution(normal, "FG")
    bf_mult, _ = multiplier_distribution(bf, "FG")
    for index, value in enumerate(MULTIPLIERS + [2500]):
        comp_values = [COMP_MULT[scene][index] if index < len(MULTIPLIERS) else 0 for scene in ("BG", "FG", "BF")]
        lines.append(f"| {value}x | {comp_values[0]:.3f}% | {bg_mult.get(value, 0):.3f}% | {comp_values[1]:.3f}% | {fg_mult.get(value, 0):.3f}% | {comp_values[2]:.3f}% | {bf_mult.get(value, 0):.3f}% |")
    lines += ["", "**差異摘要：** FG／BF 的 2x～8x 已接近競品；BG 仍過度集中在 2x／3x，競品則有更多 5x～20x。H027 還有競品樣本未出現的 500x～2500x 尾部。"]
    normal_profile = config["parameter"]["normal"]
    lines += ["", "每顆 C2 轉成 C3 的機率（依初始 C2 數量 1～6）：", "", f"- BG：{normal_profile['c2_to_c3']['weights_by_initial_ball_count']['BG_Symbol (2)']} / 10000", f"- FG：{normal_profile['c2_to_c3']['weights_by_initial_ball_count']['FG_Symbol']} / 10000", "", "C2、C3 共用同一套競品球上倍率分布；C3 僅在後續得分消除時依倍率階層升級。", "", "## 倍率線型與最大倍數", ""]
    line_frame = pd.read_excel(normal, sheet_name="Multiplier Line")
    eligible = {}
    for scene, column, denominator in (("BG", "base_game_cnt", int(normal_overview["total_rounds"].replace(",", ""))), ("FG", "free_game_cnt", int(line_frame["free_game_cnt"].sum()))):
        valid = line_frame.loc[line_frame[column] / denominator >= .001, "Interval_Upper"]
        eligible[scene] = int(valid.max()) if len(valid) else 0
    lines += [f"- Card-Off 最大實測：{normal_overview['max_win_x']}x；最大累積球倍數：{normal_overview['max_multiplier']}x。", f"- 0.1% 自然命中門檻可用最高區間：BG 上限 {eligible['BG']}x；FG 上限 {eligible['FG']}x。", "- 92A／94A 卡片已依目前 v1 自然盤重新校準；區間仍只使用自然命中率至少 0.1% 的範圍。", "", "### 64 區間（競品 → H027 Card-Off）", "", "| Interval Upper | BG | FG | BF |", "|---:|---:|---:|---:|"]
    bf_line = pd.read_excel(bf, sheet_name="Multiplier Line")
    bg_rates = line_frame["base_game_cnt"] / int(normal_overview["total_rounds"].replace(",", "")) * 100
    fg_rates = line_frame["free_game_cnt"] / line_frame["free_game_cnt"].sum() * 100
    bf_column = "free_game_cnt_BF" if bf_line["free_game_cnt_BF"].sum() else "free_game_cnt"
    bf_rates = bf_line[bf_column] / bf_line[bf_column].sum() * 100
    for index, upper in enumerate(line_frame["Interval_Upper"]):
        comp = competitor_intervals[index] if index < len(competitor_intervals) else [0, 0, 0]
        lines.append(f"| {int(upper)} | {comp[0]:.5f}% → {bg_rates.iloc[index]:.5f}% | {comp[1]:.5f}% → {fg_rates.iloc[index]:.5f}% | {comp[2]:.5f}% → {bf_rates.iloc[index]:.5f}% |")

    lines += ["", "## 資料與限制", "", f"- Card-Off Normal：`Record/{normal.name}`。", f"- Card-Off Buy Feature：`Record/{bf.name}`。", *[f"- Card-On {label}：`Record/{path.name}`。" for label, path in card_reports.items()], "- 輪帶來源：`還原輪帶_Gates_of_Olympus_1000.xlsx`；Set 0～4 的每輪長度為 63 或 64。", "- 競品 RTP／最大值來自有限實機樣本，不視為理論值。", "- 競品最新報告沒有可直接對比的 FG Combo 分布與 FG 有球率，因此未使用舊版數值補齊。", "- 掉落符號不使用 Symbol Drop Weight；每輪沿同一條環狀輪帶依序補入。", ""]
    lines = [line for line in lines if not line.startswith("| FG 平均倍數 | 偏高 | 自然值約 221.20x")]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Updated: {OUTPUT}")


if __name__ == "__main__":
    main()
