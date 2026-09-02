"""由既有 92% 固定 Row Data 建立可追溯的 94% 模擬資料。

此工具只做倍率等比例校正，不代表正式遊戲的 94% 權重版本。
原始每轉順序、FG 位置、玩家與 Spin 編號均保持不變。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = SCRIPT_DIR / "rowdata"
TARGET_RTP = 0.94
GAMES = ("超級寶石", "彩罐熱舞")
PAYOUT_COLUMNS = (
    "Natural_Multiplier",
    "Natural_Payout",
    "Natural_BG_Multiplier",
    "Natural_FG_Multiplier",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_game(game: str) -> None:
    source_path = DATA_DIR / f"{game}_基礎遊戲_1000人_1000轉.csv.gz"
    output_path = DATA_DIR / f"{game}_基礎遊戲94RTP_1000人_1000轉.csv.gz"
    metadata_path = DATA_DIR / f"{game}_基礎遊戲94RTP_1000人_1000轉.metadata.json"

    frame = pd.read_csv(source_path)
    source_rtp = float(frame["Natural_Payout"].sum() / frame["Bet"].sum())
    scale_factor = TARGET_RTP / source_rtp

    for column in PAYOUT_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].astype("float64") * scale_factor

    frame.to_csv(output_path, index=False, compression="gzip")
    actual_rtp = float(frame["Natural_Payout"].sum() / frame["Bet"].sum())
    metadata = {
        "description": f"{game}：由既有固定 Row Data 等比例校正的 94% 模擬資料",
        "game": game,
        "profile": "94% 基礎遊戲 + 2% 彩金",
        "method": "所有自然得分倍率等比例乘上 target_rtp / source_actual_rtp",
        "scope_note": "供機制模擬使用，不代表正式遊戲 94% 權重設定",
        "players": int(frame["Player"].nunique()),
        "spins_per_player": int(frame["Spin"].max()),
        "rows": int(len(frame)),
        "source_file": source_path.name,
        "source_sha256": sha256(source_path),
        "source_actual_rtp_percent": source_rtp * 100.0,
        "target_rtp_percent": TARGET_RTP * 100.0,
        "scale_factor": scale_factor,
        "actual_rtp_percent": actual_rtp * 100.0,
        "csv_gz_file": output_path.name,
        "csv_gz_sha256": sha256(output_path),
    }
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"{game}：{source_rtp * 100:.9f}% × {scale_factor:.12f} = {actual_rtp * 100:.9f}%")
    print(f"  Row Data：{output_path}")
    print(f"  Metadata：{metadata_path}")


def main() -> None:
    for game in GAMES:
        build_game(game)


if __name__ == "__main__":
    main()
