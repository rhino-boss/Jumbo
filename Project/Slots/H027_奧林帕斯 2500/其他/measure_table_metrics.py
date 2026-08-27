from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from numba import njit


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_MD = ROOT / "其他" / "各輪帶表_HitRate_消除率.md"
OUTPUT_JSON = ROOT / "其他" / "各輪帶表_HitRate_消除率.json"
os.environ["H027_RUN_ALL_COMBINATIONS"] = "false"
os.environ["H027_OUTPUT_REPORT"] = "false"
os.environ["H027_CARD_SYSTEM_ENABLED"] = "false"
sys.path.insert(0, str(ROOT))
import Simulator as sim  # noqa: E402


@njit(nogil=True)
def measure_table(table_id: int, profile_index: int, rounds: int, seed: int):
    np.random.seed(seed)
    counts = np.zeros(10, dtype=np.int64)
    payout_hits = 0
    for _ in range(rounds):
        result = sim.play_cluster_spin(table_id, profile_index, 0, sim.BET_MULTI)
        cascades = int(result[5])
        counts[min(cascades, 9)] += 1
        raw_pay = result[0]
        scatter_pay = result[1]
        multiplier = result[3]
        final_pay = raw_pay * (multiplier if multiplier > 0 else 1) + scatter_pay
        payout_hits += 1 if final_pay > 0 else 0
    return counts, payout_hits


def percent(value: float) -> str:
    return f"{value:.4%}"


def main() -> None:
    rounds = int(os.environ.get("H027_MEASURE_ROUNDS", "1000000"))
    base_seed = int(os.environ.get("H027_MEASURE_SEED", "20260827"))
    rows: list[dict[str, object]] = []

    for index, table_name in enumerate(sim.STRIP_NAMES):
        table_id = sim.TABLE_BY_NAME[table_name]
        profile = sim.FEATUREBUY_PROFILE_INDEX if table_name == "BF_Symbol" else 0
        counts, payout_hits = measure_table(table_id, profile, rounds, base_seed + index * 1009)
        rates = counts.astype(np.float64) / rounds
        elimination_hit_rate = 1.0 - rates[0]
        payout_hit_rate = payout_hits / rounds
        if int(counts.sum()) != rounds:
            raise AssertionError(f"{table_name}: combo count does not equal rounds")
        if not np.isclose(elimination_hit_rate, rates[1:].sum(), rtol=0.0, atol=1e-12):
            raise AssertionError(f"{table_name}: elimination Hit Rate does not equal Combo 1+")
        if payout_hit_rate + 1e-12 < elimination_hit_rate:
            raise AssertionError(f"{table_name}: payout Hit Rate is lower than elimination Hit Rate")
        rows.append(
            {
                "table": table_name,
                "rounds": rounds,
                "hit_rate": payout_hit_rate,
                "elimination_hit_rate": elimination_hit_rate,
                "counts": counts.tolist(),
                "rates": rates.tolist(),
                "profile": "featurebuy" if profile == sim.FEATUREBUY_PROFILE_INDEX else "normal",
                "bf_entry_override": bool(
                    table_id == sim.FEATUREBUY_TABLE_ID
                    and profile == sim.FEATUREBUY_PROFILE_INDEX
                ),
            }
        )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "config_file": sim.CONFIG_FILE,
        "base_excel_version": sim.BASE_CONFIG_VERSION,
        "runtime_version": sim.CONFIG_VERSION,
        "rounds_per_table": rounds,
        "seed": base_seed,
        "definitions": {
            "hit_rate": "Spin 至少有一筆得分的機率；包含一般符號得獎與 Scatter 得分。",
            "elimination_hit_rate": "Spin 至少發生 1 次得獎消除的機率；等於 Combo 1+。",
            "combo_n": "該 Spin 恰好發生 n 次得獎消除。",
            "combo_9_plus": "該 Spin 發生至少 9 次得獎消除。",
        },
        "tables": rows,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    headers = ["指標"] + [str(row["table"]) for row in rows]
    lines = [
        "# 各輪帶表 Hit Rate 與消除率",
        "",
        f"- 來源：目前 v1 `config.js`（Base Version `{sim.BASE_CONFIG_VERSION}` / Runtime Version `{sim.CONFIG_VERSION}`）",
        f"- 樣本：每張表 `{rounds:,}` Spin，固定種子 `{base_seed}`（各表使用不同子種子）",
        "- Hit Rate：與 Simulator 正式統計口徑相同，Spin 至少有一筆一般符號或 Scatter 得分。",
        "- 消除 Hit Rate：至少發生 1 次得獎消除；因此 `消除 Hit Rate = Combo 1+ = 1 - Combo 0`。",
        "- Combo n：每個 Spin 恰好發生 n 次得獎消除；`9+` 合併所有 9 次以上。",
        "- 數值保留四位小數，單張表的 Combo 0～9+ 合計為 100%。",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] + ["---:"] * (len(headers) - 1)) + " |",
    ]
    metric_rows = [
        ("Hit Rate", lambda row: float(row["hit_rate"])),
        ("消除 Hit Rate", lambda row: float(row["elimination_hit_rate"])),
    ]
    metric_rows.extend(
        (
            f"Combo {combo if combo < 9 else '9+'}",
            lambda row, combo=combo: float(row["rates"][combo]),
        )
        for combo in range(10)
    )
    for label, getter in metric_rows:
        cells = [label] + [percent(getter(row)) for row in rows]
        lines.append("| " + " | ".join(cells) + " |")

    lines.extend(
        [
            "",
            "## 僅 Combo 1+ 的消除分布",
            "",
            "排除 Combo 0 後重新正規化；每張輪帶表的 Combo 1～9+ 合計為 100%。",
            "",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] + ["---:"] * (len(headers) - 1)) + " |",
        ]
    )
    for combo in range(1, 10):
        values = []
        for row in rows:
            rates = row["rates"]
            assert isinstance(rates, list)
            positive_total = sum(float(value) for value in rates[1:])
            values.append(float(rates[combo]) / positive_total if positive_total else 0.0)
        label = f"Combo {combo if combo < 9 else '9+'}"
        lines.append("| " + " | ".join([label] + [percent(value) for value in values]) + " |")

    lines.extend(
        [
            "",
            "## BF_Symbol 口徑",
            "",
            "`BF_Symbol` 列使用遊戲實際 Buy Feature 入場邏輯：初始盤面固定在 R2～R5 各放 1 顆 C1，其餘格子由 9 個一般得獎符號等機率生成；後續掉落才使用 `BF_Symbol` 輪帶。因此這列是 Index/Simulator 真正玩到的 BF 結果，不是將 BF 輪帶當作普通初始盤面抽取。",
            "",
            "## 校驗",
            "",
            "- 每張表的 Combo 計數合計都等於樣本數。",
            "- 每張表的消除 Hit Rate 都與 Combo 1～9+ 之和一致。",
            "- 正式 Hit Rate 不得低於消除 Hit Rate；兩者差值來自「沒有一般符號消除，但 Scatter 有得分」的 Spin。",
            "- 可重現指令：`set H027_MEASURE_ROUNDS=1000000 && .venv\\Scripts\\python.exe Project\\Slots\\H027_奧林帕斯 2500\\其他\\measure_table_metrics.py`。",
        ]
    )
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Markdown: {OUTPUT_MD}")
    print(f"JSON: {OUTPUT_JSON}")
    for row in rows:
        rates = row["rates"]
        assert isinstance(rates, list)
        print(
            f"{row['table']}: hit={percent(float(row['hit_rate']))}, elimination_hit={percent(float(row['elimination_hit_rate']))}, "
            + ", ".join(
                f"combo{index if index < 9 else '9+'}={percent(float(value))}"
                for index, value in enumerate(rates)
            )
        )


if __name__ == "__main__":
    main()
