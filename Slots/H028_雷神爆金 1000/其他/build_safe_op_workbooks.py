from __future__ import annotations

import re
import zipfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
backup_dir = root / "Versions" / "3.2.0.0" / "Source_Backup"
output_dir = root / "Source"

newbie_scr = 3_864_674_550
bf_scr = 51_240_310_600
oldhand = {
    "H028188B.xlsx": 3_800_982_750,
    "H028190B.xlsx": 3_805_450_200,
    "H028192A.xlsx": 3_834_937_400,
    "H028194A.xlsx": 3_836_181_680,
}


def row(xml: str, number: int) -> str:
    match = re.search(rf'<row r="{number}"\b.*?</row>', xml, flags=re.DOTALL)
    if match is None:
        raise RuntimeError(f"Row {number} not found")
    return match.group(0)


def move_row(fragment: str, old: int, new: int) -> str:
    fragment = fragment.replace(f'<row r="{old}"', f'<row r="{new}"', 1)
    for column in ("A", "B", "C"):
        fragment = fragment.replace(f'r="{column}{old}"', f'r="{column}{new}"')
    return fragment


def put_value(fragment: str, coordinate: str, value: int) -> str:
    pattern = rf'(<c r="{coordinate}"[^>]*)/>'
    replacement = rf'\1><v>{value}</v></c>'
    updated, count = re.subn(pattern, replacement, fragment, count=1)
    if count != 1:
        raise RuntimeError(f"Cell {coordinate} not found")
    return updated


def patch_sheet(payload: bytes, nb_scr: int) -> bytes:
    xml = payload.decode("utf-8")
    rows = [row(xml, n) for n in (2, 4, 5, 7, 9, 10)]
    rows[2] = put_value(rows[2], "C5", newbie_scr)
    rows[3] = put_value(move_row(rows[3], 7, 6), "C6", nb_scr)
    rows[4] = put_value(move_row(rows[4], 9, 7), "C7", bf_scr)
    rows[5] = move_row(rows[5], 10, 8)
    new_sheet_data = "<sheetData>" + "".join(rows) + "</sheetData>"
    xml, count = re.subn(r"<sheetData>.*?</sheetData>", new_sheet_data, xml, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError("sheetData replacement failed")
    xml = xml.replace('<dimension ref="A2:C10"/>', '<dimension ref="A2:C8"/>', 1)
    return xml.encode("utf-8")


for name, nb_scr in oldhand.items():
    backup = backup_dir / f"{Path(name).stem}_before_op_jackpot_scr_260903.xlsx"
    output = output_dir / f"{Path(name).stem}_safe.xlsx"
    with zipfile.ZipFile(backup, "r") as source_zip, zipfile.ZipFile(output, "w") as target_zip:
        for info in source_zip.infolist():
            data = source_zip.read(info.filename)
            if info.filename == "xl/worksheets/sheet5.xml":
                data = patch_sheet(data, nb_scr)
            target_zip.writestr(info, data)
    print(f"BUILT {output.name}")
