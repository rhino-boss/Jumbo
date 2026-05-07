import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parents[3]
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import Project.Slots.Source.H026_Box as Box


DEFAULT_OUTPUT = THIS_DIR / "H026_Demogame_data.js"
FRAME_BG = "./Image/P026_Symbol/pinata-wins_symbol_s_frame_bg.png"
FRAME_TOP = "./Image/P026_Symbol/pinata-wins_symbol_s_frame.png"
ASSET_MAP = {
    "WW": "./Image/P026_Symbol/pinata-wins_symbol_s_wild.png",
    "C1": "./Image/P026_Symbol/pinata-wins_symbol_s_scatter.png",
    "M1": "./Image/P026_Symbol/pinata-wins_symbol_m1_skull.png",
    "M2": "./Image/P026_Symbol/pinata-wins_symbol_m2_sombrero.png",
    "M3": "./Image/P026_Symbol/pinata-wins_symbol_m3_maracas.png",
    "M4": "./Image/P026_Symbol/pinata-wins_symbol_m4_taco.png",
    "M5": "./Image/P026_Symbol/pinata-wins_symbol_m5_chilli.png",
    "A": "./Image/P026_Symbol/pinata-wins_symbol_l4_a.png",
    "K": "./Image/P026_Symbol/pinata-wins_symbol_l3_k.png",
    "Q": "./Image/P026_Symbol/pinata-wins_symbol_l2_q.png",
    "J": "./Image/P026_Symbol/pinata-wins_symbol_l1_j.png",
}


def to_plain(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): to_plain(sub_value) for key, sub_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def build_payload():
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_box": "Project.Slots.Source.H026_Box",
        "game_id": str(Box.game_ID),
        "game_name": "H026 Demogame",
        "bet_options": [1, 2, 3, 5, 10],
        "mode_normalbet": int(Box.mode_normalbet),
        "mode_featurebuy": int(Box.mode_featurebuy),
        "scene_bg": int(Box.scence_BG),
        "scene_fg": int(Box.scence_FG),
        "scene_bf": 2,
        "reel_num": int(Box.reel_num),
        "window_size": int(Box.window_size),
        "default_coin_in": int(Box.default_coin_in),
        "normalbet": int(Box.normalbet),
        "featurebuy": int(Box.featurebuy),
        "special_pool_weight_base": int(Box.special_pool_weight_base),
        "paylines": to_plain(Box.paylines),
        "pay_table": to_plain(Box.pay_table),
        "symbol_id": to_plain(Box.symbol_id),
        "symbol_str": {str(key): str(value) for key, value in Box.symbol_str.items()},
        "base_symbol_of": to_plain(Box.base_symbol_of),
        "is_gold_symbol": to_plain(Box.is_gold_symbol),
        "is_score_symbol": to_plain(Box.is_score_symbol),
        "symbols_score": to_plain(Box.symbols_score),
        "value_multiplier_range": to_plain(Box.value_multiplier_range),
        "weight_table_bg": to_plain(Box.weight_table_BG),
        "weight_table_fg": to_plain(Box.weight_table_FG),
        "weight_table_bf": to_plain(Box.weight_table_BF),
        "weight_cum_table_bg": to_plain(Box.weight_cum_table_BG),
        "weight_cum_table_fg": to_plain(Box.weight_cum_table_FG),
        "weight_cum_table_bf": to_plain(Box.weight_cum_table_BF),
        "fg_table_rule": {
            "type": "multiplier_threshold",
            "thresholds": [10, 20],
            "table_ids": [3, 4, 5],
            "table_names": [str(Box.strip_name_map[idx]) for idx in (3, 4, 5)],
            "rules": [
                {"min_multiplier": 0, "max_exclusive": 10, "table_id": 3, "table_name": str(Box.strip_name_map[3])},
                {"min_multiplier": 10, "max_exclusive": 20, "table_id": 4, "table_name": str(Box.strip_name_map[4])},
                {"min_multiplier": 20, "max_exclusive": None, "table_id": 5, "table_name": str(Box.strip_name_map[5])},
            ],
        },
        "weight_multiple_special": to_plain(Box.weight_multiple_special),
        "weight_multiple_r3_before": to_plain(Box.weight_multiple_r3_before),
        "weight_multiple_r3_after": to_plain(Box.weight_multiple_r3_after),
        "weight_multiple_before": to_plain(Box.weight_multiple_before),
        "weight_multiple_after": to_plain(Box.weight_multiple_after),
        "weight_cum_multiple_special": to_plain(Box.weight_cum_multiple_special),
        "weight_cum_multiple_r3_before": to_plain(Box.weight_cum_multiple_r3_before),
        "weight_cum_multiple_r3_after": to_plain(Box.weight_cum_multiple_r3_after),
        "weight_cum_multiple_before": to_plain(Box.weight_cum_multiple_before),
        "weight_cum_multiple_after": to_plain(Box.weight_cum_multiple_after),
        "weight_special_pool": to_plain(Box.weight_special_pool),
        "arr_reels": to_plain(Box.arr_reels),
        "arr_reels_weight": to_plain(Box.arr_reels_weight),
        "arr_reels_weight_cum": to_plain(Box.arr_reels_weight_cum),
        "drop_weight_a": to_plain(Box.drop_weight_a),
        "drop_weight_b": to_plain(Box.drop_weight_b),
        "drop_weight_a_cum": to_plain(Box.drop_weight_a_cum),
        "drop_weight_b_cum": to_plain(Box.drop_weight_b_cum),
        "reels_len": to_plain(Box.reels_len),
        "strip_name_map": to_plain(Box.strip_name_map),
        "frame_bg": FRAME_BG,
        "frame_top": FRAME_TOP,
        "asset_map": ASSET_MAP,
    }


def write_js(output_path: Path):
    payload = build_payload()
    js_text = "window.H026_BOX_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    output_path.write_text(js_text, encoding="utf-8")
    return output_path, len(js_text)


def main():
    parser = argparse.ArgumentParser(description="Update H026 demogame parameter data from H026_Box.py")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help="Output js path")
    args, _unknown = parser.parse_known_args()

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written_path, size = write_js(output_path)
    print(f"Wrote {written_path} ({size} chars)")


if __name__ == "__main__":
    main()
