import asyncio
import html
import io
import logging
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import Conflict
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes
import rarfile

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("tgbot")

r"""

# 在 VM 上執行：
python3 walking_encyclopedia_bot_vm.py

# 功能介紹（VM 版，移植自 walking_encyclopedia_bot.py）
  * 整理報表：支援 zip/rar、多檔合併、巢狀壓縮檔，並自動轉成 Excel。
  * 壓測資料重點整理：抓取 RTP、Spin、Coin in、各 pool RTP 等重點欄位。
  * H026 模擬器指令（/run_start、/run_status、/run_cancel，僅限管理者）。
  * /help 說明本檔案完整功能。
  * 本版不包含 AI 問答功能（原版透過本機 Claude CLI 回答，VM 上未設置）。

"""

# ==================== 🔑 核心金鑰設定 ====================
TG_TOKEN = "8817922272:AAEzFERpAAlhLTf3bs1bFsdoevtUdzNU4cA"
ALLOWED_USER_ID = 5539551776  # 只有這個 Telegram 使用者 ID 可以下模擬器指令


# ==================== ⚙️ 機器人參數設定 ====================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "generated_reports"
MAX_REPORT_FILES = 20
ARCHIVE_EXTENSIONS = {".zip", ".rar"}
MAX_ARCHIVE_DEPTH = 10
ARCHIVE_BATCH_DELAY_SECONDS = 2
BOT_INSTANCE_LOCK_PORT = 48726
SEVENZIP_CANDIDATES = [
    "/usr/bin/7z",
    "/usr/bin/7za",
    "/usr/local/bin/7z",
]

VALIDATOR_HEADER_PATTERNS = {
    "GameID": r"GameID\s*=\s*(\d+)",
    "optionID": r"optionID\s*=\s*(\d+)",
    "Coin in": r"Coin in\s*=\s*([0-9.]+)",
    "TotalSpin": r"TotalSpin\s*=\s*([0-9.]+)",
    "TotalRtp (including JP/bonus)": r"TotalRtp \(including JP/bonus\)\s*=\s*([0-9.]+)",
    "avgPeriod": r"avgPeriod\s*=\s*([0-9.]+)",
    "BaseGameRtp": r"BaseGameRtp\s*=\s*([0-9.]+)",
    "ScatterRtp": r"ScatterRtp\s*=\s*([0-9.]+)",
    "FreeGameRtp": r"FreeGameRtp\s*=\s*([0-9.]+)",
    "BonusJP Rtp": r"BonusJP\s+Rtp\s*=\s*([0-9.]+)|BonusJP\s+RTP\s*=\s*([0-9.]+)",
    "LinkJP Rtp": r"LinkJP\s+Rtp\s*=\s*([0-9.]+)|LinkJP\s+RTP\s*=\s*([0-9.]+)",
}

# ==================== 🎰 H026 模擬器設定 ====================
GAME_DIR = BASE_DIR / "games" / "H026"
GAME_SCRIPT = GAME_DIR / "Simulator.py"
CONFIGS = {"92A", "92B", "94A", "94B"}
BET_MODES = {"0": "Normal Bet", "1": "Extra Bet", "2": "Feature Buy"}
MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "20000000"))
SUMMARY_LINE_RE = re.compile(r"^\* .+$", re.MULTILINE)
REPORT_LINE_RE = re.compile(r"^Report: (.+)$", re.MULTILINE)

current_job = None  # dict: {"proc", "chat_id", "started_at", "label"}
job_lock = asyncio.Lock()
ROUNDS_PRESETS = [
    ("10 萬", 100_000),
    ("100 萬", 1_000_000),
    ("1000 萬", 10_000_000),
    ("2000 萬（上限）", 20_000_000),
]

# 記憶暫存區
archive_batches = {}
bot_instance_lock = None
simulator_wizard_state = {}  # chat_id -> {"config", "bet_mode", "card", "rounds", "awaiting_rounds"}


def authorized(func):
    """限制只有 ALLOWED_USER_ID 能使用模擬器指令。"""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user is None or update.effective_user.id != ALLOWED_USER_ID:
            await update.message.reply_text("🚫 你沒有權限使用這個指令。")
            return
        await func(update, context)

    return wrapper

# ==================== 💾 本地文字檔儲存邏輯 ====================


def acquire_bot_instance_lock() -> bool:
    """避免同一支 bot 在本機重複啟動，造成 Telegram getUpdates Conflict。"""
    global bot_instance_lock

    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        lock_socket.bind(("127.0.0.1", BOT_INSTANCE_LOCK_PORT))
        lock_socket.listen(1)
    except OSError:
        lock_socket.close()
        return False

    bot_instance_lock = lock_socket
    return True


async def check_telegram_polling_available() -> bool:
    try:
        async with Bot(TG_TOKEN) as bot:
            await bot.get_updates(timeout=0, limit=1)
        return True
    except Conflict:
        return False
    except Exception as e:
        print(f"[警告] Telegram polling 預檢失敗，將繼續嘗試啟動: {e}")
        return True


def ensure_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)


def prune_old_reports():
    """只保留最新的 20 份產出文件。"""
    ensure_output_dir()
    files = [path for path in OUTPUT_DIR.iterdir() if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    for old_file in files[MAX_REPORT_FILES:]:
        try:
            old_file.unlink()
            print(f"[系統提示] 已刪除舊檔案: {old_file.name}")
        except Exception as e:
            print(f"[錯誤] 刪除舊檔案失敗 {old_file.name}: {e}")


def extract_validator_field(pattern: str, text: str) -> str:
    match = re.search(pattern, text)
    if not match:
        return ""
    groups = [group for group in match.groups() if group is not None]
    return groups[0] if groups else match.group(1)


def get_source_txt_filename(source_name: str) -> str:
    return Path(source_name.replace("\\", "/").split("!")[-1]).name


def get_source_txt_folder_name(source_name: str) -> str:
    txt_path = Path(source_name.replace("\\", "/").split("!")[-1])
    return txt_path.parent.name if str(txt_path.parent) != "." else ""


def parse_validator_txt(text: str, source_name: str) -> dict[str, str]:
    row = {
        "source_txt": get_source_txt_filename(source_name),
        "txt在的資料夾名稱": get_source_txt_folder_name(source_name),
    }

    for field, pattern in VALIDATOR_HEADER_PATTERNS.items():
        row[field] = extract_validator_field(pattern, text)

    for pool_index, rtp in re.findall(r"pool\[(\d+)\].*?rtp\s*=\s*([0-9.]+)", text):
        row[f"pool[{pool_index}] rtp"] = rtp

    return row


def is_supported_archive_name(name: str) -> bool:
    return Path(name).suffix.lower() in ARCHIVE_EXTENSIONS


def is_supported_archive_bytes(data: bytes) -> bool:
    return data.startswith(b"PK\x03\x04") or data.startswith(b"Rar!\x1a\x07")


def collect_validator_rows_from_zip(zf: zipfile.ZipFile, archive_label: str, depth: int) -> list[dict[str, str]]:
    rows = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename
        data = zf.read(info)
        rows.extend(collect_validator_rows_from_member(data, f"{archive_label}!{name}", depth + 1))

    return rows


def collect_validator_rows_from_rar(rf: rarfile.RarFile, archive_label: str, depth: int) -> list[dict[str, str]]:
    rows = []
    for info in rf.infolist():
        if info.isdir():
            continue
        name = info.filename
        data = rf.read(info)
        rows.extend(collect_validator_rows_from_member(data, f"{archive_label}!{name}", depth + 1))

    return rows


def collect_validator_rows_from_extracted_dir(extract_dir: Path, archive_label: str, depth: int) -> list[dict[str, str]]:
    rows = []
    for path in extract_dir.rglob("*"):
        if not path.is_file():
            continue
        relative_name = path.relative_to(extract_dir).as_posix()
        rows.extend(collect_validator_rows_from_member(path.read_bytes(), f"{archive_label}!{relative_name}", depth + 1))
    return rows


def find_sevenzip_tool() -> str | None:
    tool = shutil.which("7z") or shutil.which("7zz") or shutil.which("7za")
    if tool:
        return tool

    for candidate in SEVENZIP_CANDIDATES:
        if Path(candidate).exists():
            return candidate

    return None


def configure_rarfile_tools():
    sevenzip = find_sevenzip_tool()
    if sevenzip:
        rarfile.SEVENZIP_TOOL = sevenzip
    elif shutil.which("tar") and not shutil.which("bsdtar"):
        rarfile.BSDTAR_TOOL = "tar"

    try:
        rarfile.tool_setup(force=True)
    except rarfile.RarCannotExec:
        pass


def extract_archive_with_external_tool(archive_path: Path, extract_dir: Path):
    sevenzip = find_sevenzip_tool()
    unrar = shutil.which("unrar")
    tar = shutil.which("tar") or shutil.which("bsdtar")

    if sevenzip:
        command = [sevenzip, "x", "-y", f"-o{extract_dir}", str(archive_path)]
    elif unrar:
        command = [unrar, "x", "-y", str(archive_path), str(extract_dir)]
    elif tar:
        command = [tar, "-xf", str(archive_path), "-C", str(extract_dir)]
    else:
        raise RuntimeError("找不到可用的 RAR 解壓工具，請安裝 p7zip 或 unrar。")

    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        error_output = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"RAR 解壓失敗: {error_output}")


def collect_validator_rows_from_rar_path(rar_path: Path, archive_label: str, depth: int) -> list[dict[str, str]]:
    configure_rarfile_tools()
    try:
        with rarfile.RarFile(rar_path) as rf:
            return collect_validator_rows_from_rar(rf, archive_label, depth)
    except Exception as rar_error:
        extract_dir = Path(tempfile.mkdtemp(prefix="telegram_bot_rar_"))
        try:
            try:
                extract_archive_with_external_tool(rar_path, extract_dir)
            except Exception as extract_error:
                raise RuntimeError(f"RAR 讀取失敗: {rar_error}; 外部解壓也失敗: {extract_error}") from extract_error
            return collect_validator_rows_from_extracted_dir(extract_dir, archive_label, depth)
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)


def collect_validator_rows_from_member(data: bytes, source_name: str, depth: int = 0) -> list[dict[str, str]]:
    if depth > MAX_ARCHIVE_DEPTH:
        raise ValueError(f"壓縮檔巢狀層數超過 {MAX_ARCHIVE_DEPTH} 層: {source_name}")

    lower_name = source_name.lower()
    if lower_name.endswith(".txt"):
        text = data.decode("utf-8", errors="replace")
        return [parse_validator_txt(text, source_name)]

    if not is_supported_archive_name(source_name) and not is_supported_archive_bytes(data):
        return []

    archive_bytes = io.BytesIO(data)
    if lower_name.endswith(".zip") or data.startswith(b"PK\x03\x04"):
        with zipfile.ZipFile(archive_bytes) as zf:
            return collect_validator_rows_from_zip(zf, source_name, depth)

    if lower_name.endswith(".rar") or data.startswith(b"Rar!\x1a\x07"):
        ensure_output_dir()
        temp_rar_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".rar", dir=OUTPUT_DIR) as temp_rar:
                temp_rar.write(data)
                temp_rar_path = Path(temp_rar.name)

            return collect_validator_rows_from_rar_path(temp_rar_path, source_name, depth)
        finally:
            if temp_rar_path and temp_rar_path.exists():
                temp_rar_path.unlink()

    return []


def collect_validator_rows(archive_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    lower_name = archive_path.name.lower()
    if lower_name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            rows = collect_validator_rows_from_zip(zf, archive_path.name, 0)
    elif lower_name.endswith(".rar"):
        rows = collect_validator_rows_from_rar_path(archive_path, archive_path.name, 0)
    else:
        rows = collect_validator_rows_from_member(archive_path.read_bytes(), archive_path.name)

    pool_fields = {field for row in rows for field in row if field.startswith("pool[")}

    pool_headers = sorted(pool_fields, key=lambda value: int(re.search(r"\[(\d+)\]", value).group(1)))
    return rows, pool_headers


def collect_validator_rows_from_archives(archive_paths: list[Path]) -> tuple[list[dict[str, str]], list[str]]:
    rows = []
    pool_fields = set()

    for archive_path in archive_paths:
        archive_rows, _ = collect_validator_rows(archive_path)
        rows.extend(archive_rows)
        pool_fields.update(field for row in archive_rows for field in row if field.startswith("pool["))

    pool_headers = sorted(pool_fields, key=lambda value: int(re.search(r"\[(\d+)\]", value).group(1)))
    return rows, pool_headers


def write_validator_xlsx(rows: list[dict[str, str]], pool_headers: list[str], output_path: Path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Summary"

    headers = [
        "source_txt",
        "txt在的資料夾名稱",
        "GameID",
        "optionID",
        "Coin in",
        "TotalSpin",
        "TotalRtp (including JP/bonus)",
        "avgPeriod",
        "BaseGameRtp",
        "ScatterRtp",
        "FreeGameRtp",
        "BonusJP Rtp",
        "LinkJP Rtp",
        *pool_headers,
    ]

    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        sheet.append([row.get(header, "") for header in headers])

    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 32)

    workbook.save(output_path)


def generate_xlsx_from_archive(archive_path: Path, output_path: Path):
    rows, pool_headers = collect_validator_rows(archive_path)
    write_validator_xlsx(rows, pool_headers, output_path)
    return output_path


def generate_xlsx_from_archives(archive_paths: list[Path], output_path: Path):
    rows, pool_headers = collect_validator_rows_from_archives(archive_paths)
    write_validator_xlsx(rows, pool_headers, output_path)
    return output_path


async def download_validator_archive(document, context: ContextTypes.DEFAULT_TYPE, timestamp: str, index: int) -> Path:
    """下載 Telegram 壓縮檔並轉成 xlsx。"""
    source_name = document.file_name or f"validator_{timestamp}.zip"
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(source_name).stem).strip("._") or f"validator_{timestamp}"
    source_suffix = Path(source_name).suffix.lower()
    archive_suffix = source_suffix if source_suffix in ARCHIVE_EXTENSIONS else ".zip"
    archive_path = OUTPUT_DIR / f"{timestamp}_{index:02d}_{safe_stem}{archive_suffix}"

    telegram_file = await context.bot.get_file(document.file_id)
    await telegram_file.download_to_drive(custom_path=str(archive_path))
    return archive_path


async def build_validator_report_from_documents(documents, context: ContextTypes.DEFAULT_TYPE, batch_name: str | None = None) -> Path:
    """下載 Telegram 壓縮檔並合併轉成 xlsx。"""
    ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if batch_name:
        safe_output_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", batch_name).strip("._") or f"validator_{timestamp}"
    elif len(documents) == 1:
        source_name = documents[0].file_name or f"validator_{timestamp}.zip"
        safe_output_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(source_name).stem).strip("._") or f"validator_{timestamp}"
    else:
        safe_output_stem = f"validator_batch_{timestamp}"

    archive_paths = []
    xlsx_path = OUTPUT_DIR / f"{timestamp}_{safe_output_stem}.xlsx"
    try:
        for index, document in enumerate(documents, start=1):
            archive_paths.append(await download_validator_archive(document, context, timestamp, index))

        generate_xlsx_from_archives(archive_paths, xlsx_path)
    finally:
        for archive_path in archive_paths:
            if archive_path.exists():
                archive_path.unlink()

    prune_old_reports()
    return xlsx_path


async def build_validator_report_from_document(document, context: ContextTypes.DEFAULT_TYPE) -> Path:
    return await build_validator_report_from_documents([document], context)


async def send_typing_while_waiting(chat_id: int, context: ContextTypes.DEFAULT_TYPE, stop_event: asyncio.Event):
    """在長時間處理完成前，持續顯示 Telegram typing 狀態。"""
    while not stop_event.is_set():
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        except Exception as e:
            print(f"[系統日誌] 發送 typing 狀態失敗: {e}")
            return

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=4)
        except asyncio.TimeoutError:
            continue


def is_supported_archive_document(document) -> bool:
    file_name = (document.file_name or "").lower()
    mime_type = (document.mime_type or "").lower()
    is_supported_archive = Path(file_name).suffix.lower() in ARCHIVE_EXTENSIONS
    is_supported_mime = "zip" in mime_type or "rar" in mime_type
    return is_supported_archive or is_supported_mime


async def process_archive_batch_after_delay(batch_key, context: ContextTypes.DEFAULT_TYPE):
    try:
        await asyncio.sleep(ARCHIVE_BATCH_DELAY_SECONDS)
    except asyncio.CancelledError:
        return

    batch = archive_batches.pop(batch_key, None)
    if not batch:
        return

    message = batch["message"]
    documents = batch["documents"]
    chat_id = message.chat.id
    batch_name = f"validator_batch_{len(documents)}files"

    stop_typing_event = asyncio.Event()
    typing_task = asyncio.create_task(send_typing_while_waiting(chat_id, context, stop_typing_event))

    try:
        xlsx_path = await build_validator_report_from_documents(documents, context, batch_name=batch_name)
    except Exception as e:
        print(f"[系統日誌] 批次轉換壓縮檔為 xlsx 失敗: {e}")
        await message.reply_text("批次轉換壓縮檔失敗，請確認 zip/rar 檔案格式是否正確。")
    else:
        with xlsx_path.open("rb") as report_file:
            await message.reply_document(document=report_file, filename=xlsx_path.name)
    finally:
        stop_typing_event.set()
        await typing_task


def parse_rtp_report(report_text: str):
    """解析 Formal RTP Report 文字，整理出摘要資料。"""
    if "Formal RTP Report" not in report_text or "Scenario RTP" not in report_text:
        return None

    machine_type = ""
    extra_bet = ""
    bet = ""
    section = None
    summary_rows = []
    current_row = None

    for raw_line in report_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("- machineType ="):
            machine_type = line.split("=", 1)[1].strip()
            continue
        if line.startswith("- extraBet ="):
            extra_bet = line.split("=", 1)[1].strip()
            continue
        if line.startswith("- Bet ="):
            bet = line.split("=", 1)[1].strip()
            continue

        if line == "Scenario RTP":
            section = "scenario"
            current_row = None
            continue
        if line == "SettingID RTP":
            if current_row:
                summary_rows.append(current_row)
            section = "setting"
            current_row = None
            continue
        if line == "SettingID Trigger Count":
            if current_row:
                summary_rows.append(current_row)
                current_row = None
            break

        if section not in {"scenario", "setting"}:
            continue

        is_new_row = False
        if section == "scenario" and not line.startswith("-"):
            is_new_row = True
        elif section == "setting" and re.match(r"^SettingID \d+", line):
            is_new_row = True

        if is_new_row:
            if section == "scenario" and line != "整體 RTP":
                if current_row:
                    summary_rows.append(current_row)
                current_row = None
                continue
            if current_row:
                summary_rows.append(current_row)
            current_row = {
                "label": line,
                "game": "",
                "jackpot": "",
                "bonus": "",
            }
            continue

        if current_row and line.startswith("-"):
            match = re.match(r"-\s*(Game|Jackpot|Bonus Game) RTP\s*=\s*([0-9.]+%)", line)
            if not match:
                continue
            rtp_type, value = match.groups()
            if rtp_type == "Game":
                current_row["game"] = value
            elif rtp_type == "Jackpot":
                current_row["jackpot"] = value
            elif rtp_type == "Bonus Game":
                current_row["bonus"] = value

    if current_row:
        summary_rows.append(current_row)

    if not summary_rows:
        return None

    return {
        "machine_type": machine_type,
        "extra_bet": extra_bet,
        "bet": bet,
        "rows": summary_rows,
    }


def normalize_row_label(label: str) -> str:
    """將報表項目名稱整理成較精簡的顯示格式。"""
    if label == "整體 RTP":
        return "Total RTP"

    match = re.match(r"^(SettingID\s+\d+)\s+[^（(]+[（(]([^）)]+)[）)]$", label)
    if match:
        _, display_name = match.groups()
        short_name_map = {
            "一般": "沒有機制",
            "新手救援": "新手救援",
            "老手救援": "老手救援",
            "新手體驗 D": "新手體驗 FG",
            "新手 mini game 體驗 D": "新手體驗 JP",
        }
        return short_name_map.get(display_name, display_name)
    return label


def get_display_width(text: str) -> int:
    """估算字串在 monospace 環境中的顯示寬度。"""
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    return width


def pad_display_text(text: str, target_width: int) -> str:
    """依顯示寬度補空白，避免中英混排時表格錯位。"""
    padding = max(0, target_width - get_display_width(text))
    return text + (" " * padding)


def pad_item_label(text: str, target_width: int) -> str:
    """微調項目欄位顯示。"""
    padded = pad_display_text(text, target_width)
    if text == "Total RTP" and padded.endswith(" "):
        return padded[:-1]
    return padded


def format_item_label(text: str) -> str:
    """調整項目欄位顯示文字。"""
    if text not in {"項目", "Total RTP", "Total RTP加總"}:
        return f"{text} "
    return text


def extract_bet_type(extra_bet: str) -> str:
    """從 extraBet 欄位取出數值型 BetType。"""
    match = re.match(r"^(\d+)", extra_bet.strip())
    return match.group(1) if match else extra_bet


def percent_to_float(value: str) -> float:
    """將百分比字串轉成數值。"""
    return float(value.rstrip("%"))


def float_to_percent(value: float) -> str:
    """將數值轉成百分比字串。"""
    return f"{value:.2f}%"


def format_rtp_report_summary(parsed_report: dict) -> str:
    """輸出適合 Telegram 顯示的 RTP 摘要。"""
    parsed_rows = [
        {
            **row,
            "display_label": normalize_row_label(row["label"]),
        }
        for row in parsed_report["rows"]
    ]

    display_rows = [row for row in parsed_rows if row["display_label"] != "Total RTP"]
    total_game = sum(percent_to_float(row["game"]) for row in display_rows)
    total_jackpot = sum(percent_to_float(row["jackpot"]) for row in display_rows)
    total_bonus = sum(percent_to_float(row["bonus"]) for row in display_rows)
    total_rtp = float_to_percent(total_game + total_jackpot + total_bonus)

    item_width = max(get_display_width(format_item_label("項目")), *(get_display_width(format_item_label(row["display_label"])) for row in display_rows), get_display_width("Total RTP"))
    game_width = max(get_display_width("GameRTP"), *(get_display_width(row["game"]) for row in display_rows))
    jackpot_width = max(get_display_width("Jackpot"), *(get_display_width(row["jackpot"]) for row in display_rows))
    bonus_width = max(get_display_width("BonusRTP"), *(get_display_width(row["bonus"]) for row in display_rows))

    def build_row(item: str, game: str, jackpot: str, bonus: str) -> str:
        display_item = format_item_label(item)
        return f"{pad_item_label(display_item, item_width)} | " f"{pad_display_text(game.rjust(game_width), game_width)} | " f"{pad_display_text(jackpot.rjust(jackpot_width), jackpot_width)} | " f"{pad_display_text(bonus.rjust(bonus_width), bonus_width)}"

    separator = "---------------------------------------"
    table_lines = [
        f'ID: {parsed_report["machine_type"]} | BetType: {extract_bet_type(parsed_report["extra_bet"])} | Bet: {parsed_report["bet"]}',
        separator,
        build_row("項目", "GameRTP", "Jackpot", "BonusRTP"),
        separator,
    ]

    for row in display_rows:
        table_lines.append(build_row(row["display_label"], row["game"], row["jackpot"], row["bonus"]))

    table_lines.append(separator)
    table_lines.append(f"Total RTP | {total_rtp}")
    escaped_table = html.escape("\n".join(table_lines))
    return f"<pre>{escaped_table}</pre>"


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return

    document = update.message.document
    if not is_supported_archive_document(document):
        await update.message.reply_text("目前只支援上傳 RTP Validator 的 zip/rar 壓縮檔。")
        return

    media_group_id = update.message.media_group_id
    if media_group_id:
        batch_key = (update.message.chat.id, media_group_id)
        batch = archive_batches.setdefault(
            batch_key,
            {
                "documents": [],
                "message": update.message,
                "task": None,
            },
        )
        batch["documents"].append(document)
        batch["message"] = update.message

        if batch["task"] and not batch["task"].done():
            batch["task"].cancel()
        batch["task"] = asyncio.create_task(process_archive_batch_after_delay(batch_key, context))
        return

    stop_typing_event = asyncio.Event()
    typing_task = asyncio.create_task(send_typing_while_waiting(update.message.chat.id, context, stop_typing_event))

    try:
        xlsx_path = await build_validator_report_from_document(document, context)
    except Exception as e:
        print(f"[系統日誌] 轉換壓縮檔為 xlsx 失敗: {e}")
        await update.message.reply_text("轉換壓縮檔失敗，請確認 zip/rar 檔案格式是否正確。")
    else:
        with xlsx_path.open("rb") as report_file:
            await update.message.reply_document(document=report_file, filename=xlsx_path.name)
    finally:
        stop_typing_event.set()
        await typing_task


# ==================== 🎰 H026 模擬器指令 ====================


def build_help_text() -> str:
    return (
        "🤖 *Jumbo 工具機器人 — 功能說明*\n\n"
        "📄 *RTP Validator 壓縮檔轉表格*\n"
        "直接丟 zip/rar 壓縮檔給我（支援巢狀壓縮、多檔一起丟），我會抓出 GameID、Coin in、TotalSpin、各項 RTP、pool RTP 等欄位，自動轉成 xlsx 傳回來。\n\n"
        "📊 *RTP Report 文字摘要*\n"
        "私訊我或在群組 @我，貼上 Formal RTP Report 文字，我會幫你整理成表格摘要（GameRTP / Jackpot / BonusRTP / Total RTP）。\n\n"
        "🎰 *H026 模擬器指令*（僅限管理者）:\n"
        "`/simulator` 開啟選單，按按鈕操作\n"
        "`/run_start <config> <bet_mode> <rounds> [card]` 一行直接執行\n\n"
        f"config: {', '.join(sorted(CONFIGS))}\n"
        "bet_mode: 0=一般 / 1=加碼 / 2=買免費 (Feature Buy)\n"
        f"rounds: 模擬局數（最大 {MAX_ROUNDS:,}）\n"
        "card: new=新手卡池 / old=一般卡池（預設 old）\n\n"
        "範例:\n"
        "`/run_start 92A 0 1000000 old`\n\n"
        "`/run_status` 查看目前是否有模擬在跑\n"
        "`/run_cancel` 中止目前模擬"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(build_help_text(), parse_mode=ParseMode.MARKDOWN)


def build_status_text() -> str:
    if current_job is None:
        return "目前沒有模擬在跑。"
    elapsed = int(time.time() - current_job["started_at"])
    return f"⏳ 執行中: {current_job['label']}\n已耗時 {elapsed}s"


async def cancel_current_job() -> str:
    global current_job
    async with job_lock:
        if current_job is None:
            return "目前沒有模擬在跑。"
        current_job["proc"].terminate()
        label = current_job["label"]
    return f"🛑 已送出中止指令: {label}"


async def start_simulation_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int, config: str, bet_mode: str, rounds: int, card: str) -> str:
    """驗證參數並啟動模擬工作，回傳要回覆給使用者的訊息文字。"""
    global current_job

    config = config.upper()
    if config not in CONFIGS:
        return f"❌ config 必須是: {', '.join(sorted(CONFIGS))}"
    if bet_mode not in BET_MODES:
        return "❌ bet_mode 必須是 0, 1 或 2"
    if rounds < 1000 or rounds > MAX_ROUNDS:
        return f"❌ rounds 必須介於 1,000 ~ {MAX_ROUNDS:,} 之間"
    if card not in {"new", "old"}:
        return "❌ card 必須是 new 或 old"
    if not GAME_SCRIPT.exists():
        return f"❌ 找不到模擬器腳本: {GAME_SCRIPT}"

    async with job_lock:
        if current_job is not None:
            elapsed = int(time.time() - current_job["started_at"])
            return f"⏳ 已經有模擬在跑了（{current_job['label']}，已耗時 {elapsed}s），請先 /run_cancel 或等它跑完。"

        label = f"config={config} bet_mode={BET_MODES[bet_mode]} rounds={rounds:,} card={card}"
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["H026_RUN_ALL_COMBINATIONS"] = "false"
        env["H026_CONFIG_FILE"] = f"config_{config}.js"
        env["H026_BET_MODE"] = bet_mode
        env["H026_TOTAL_ROUNDS"] = str(rounds)
        env["H026_CARD_SYSTEM_IS_NEWBIE"] = "true" if card == "new" else "false"

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(GAME_SCRIPT),
            cwd=str(GAME_DIR),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        current_job = {"proc": proc, "chat_id": chat_id, "started_at": time.time(), "label": label}

    asyncio.create_task(watch_simulator_job(context, proc, chat_id, label))
    return f"🚀 開始模擬: {label}\n跑完會傳結果回來。"


@authorized
async def run_start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "用法: /run_start <config> <bet_mode> <rounds> [card]\n"
            "範例: /run_start 92A 0 1000000 old"
        )
        return

    config, bet_mode, rounds_raw = args[0], args[1], args[2]
    card = args[3].lower() if len(args) > 3 else "old"

    if not rounds_raw.isdigit():
        await update.message.reply_text("❌ rounds 必須是正整數")
        return

    reply = await start_simulation_job(context, update.effective_chat.id, config, bet_mode, int(rounds_raw), card)
    await update.message.reply_text(reply)


async def watch_simulator_job(context: ContextTypes.DEFAULT_TYPE, proc, chat_id, label):
    global current_job
    stdout, stderr = await proc.communicate()
    async with job_lock:
        current_job = None

    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")

    if proc.returncode != 0:
        tail = stderr_text[-1500:] if stderr_text else "(無錯誤輸出)"
        await context.bot.send_message(chat_id, f"❌ 模擬失敗（{label}）\nexit code={proc.returncode}\n```\n{tail}\n```", parse_mode=ParseMode.MARKDOWN)
        return

    summary_lines = SUMMARY_LINE_RE.findall(stdout_text)
    report_match = REPORT_LINE_RE.search(stdout_text)

    if not summary_lines:
        await context.bot.send_message(chat_id, f"⚠️ 模擬跑完但沒有解析到摘要（{label}）\n輸出最後 1000 字:\n```\n{stdout_text[-1000:]}\n```", parse_mode=ParseMode.MARKDOWN)
        return

    text = f"✅ 模擬完成: {label}\n\n" + "\n".join(summary_lines)
    if report_match:
        report_name = os.path.basename(report_match.group(1).strip())
        text += f"\n\n報表檔案（存在 VM 上）: {report_name}"

    await context.bot.send_message(chat_id, text)


@authorized
async def run_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(build_status_text())


@authorized
async def run_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(await cancel_current_job())


async def on_error(update, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled error", exc_info=context.error)


# ==================== 🕹️ /simulator 按鈕選單 ====================


def build_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Help", callback_data="sim:menu:help"), InlineKeyboardButton("🚀 Run", callback_data="sim:menu:run")],
            [InlineKeyboardButton("📊 Status", callback_data="sim:menu:status"), InlineKeyboardButton("🛑 Cancel", callback_data="sim:menu:cancel")],
        ]
    )


def build_config_keyboard() -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(config, callback_data=f"sim:config:{config}") for config in sorted(CONFIGS)]
    return InlineKeyboardMarkup([row])


def build_bet_keyboard() -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(label, callback_data=f"sim:bet:{key}") for key, label in BET_MODES.items()]
    return InlineKeyboardMarkup([row])


def build_card_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("新手卡池 (new)", callback_data="sim:card:new"), InlineKeyboardButton("一般卡池 (old)", callback_data="sim:card:old")]]
    )


def build_rounds_keyboard() -> InlineKeyboardMarkup:
    preset_buttons = [InlineKeyboardButton(label, callback_data=f"sim:rounds:{value}") for label, value in ROUNDS_PRESETS]
    rows = [preset_buttons[i : i + 2] for i in range(0, len(preset_buttons), 2)]
    rows.append([InlineKeyboardButton("✏️ 其他（輸入數字）", callback_data="sim:rounds:custom")])
    return InlineKeyboardMarkup(rows)


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ 確認執行", callback_data="sim:confirm:yes"), InlineKeyboardButton("❌ 取消", callback_data="sim:confirm:no")]])


def build_wizard_summary_text(state: dict) -> str:
    return (
        "請確認模擬參數:\n"
        f"config: {state['config']}\n"
        f"bet_mode: {BET_MODES[state['bet_mode']]}\n"
        f"rounds: {state['rounds']:,}\n"
        f"card: {state['card']}"
    )


async def simulator_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None or update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("🚫 你沒有權限使用這個指令。")
        return
    await update.message.reply_text("請選擇要做什麼:", reply_markup=build_menu_keyboard())


async def simulator_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user is None or query.from_user.id != ALLOWED_USER_ID:
        await query.answer("🚫 你沒有權限", show_alert=True)
        return
    await query.answer()

    parts = (query.data or "").split(":")
    if len(parts) != 3 or parts[0] != "sim":
        return
    _, stage, value = parts
    chat_id = query.message.chat.id

    if stage == "menu":
        if value == "help":
            await query.edit_message_text(build_help_text(), parse_mode=ParseMode.MARKDOWN)
        elif value == "status":
            await query.edit_message_text(build_status_text())
        elif value == "cancel":
            await query.edit_message_text(await cancel_current_job())
        elif value == "run":
            simulator_wizard_state[chat_id] = {}
            await query.edit_message_text("步驟 1/4：請選擇 config", reply_markup=build_config_keyboard())
        return

    state = simulator_wizard_state.setdefault(chat_id, {})

    if stage == "config":
        state["config"] = value
        await query.edit_message_text("步驟 2/4：請選擇 bet_mode", reply_markup=build_bet_keyboard())
        return

    if stage == "bet":
        state["bet_mode"] = value
        await query.edit_message_text("步驟 3/4：請選擇卡池", reply_markup=build_card_keyboard())
        return

    if stage == "card":
        state["card"] = value
        await query.edit_message_text("步驟 4/4：請選擇模擬局數", reply_markup=build_rounds_keyboard())
        return

    if stage == "rounds":
        if value == "custom":
            state["awaiting_rounds"] = True
            await query.edit_message_text(f"請直接輸入模擬局數（純數字，1,000 ~ {MAX_ROUNDS:,}）")
            return
        state["rounds"] = int(value)
        state.pop("awaiting_rounds", None)
        await query.edit_message_text(build_wizard_summary_text(state), reply_markup=build_confirm_keyboard())
        return

    if stage == "confirm":
        if value == "no":
            simulator_wizard_state.pop(chat_id, None)
            await query.edit_message_text("已取消。")
            return
        final_state = simulator_wizard_state.pop(chat_id, None)
        if not final_state or not all(key in final_state for key in ("config", "bet_mode", "rounds", "card")):
            await query.edit_message_text("❌ 選單狀態不完整，請重新 /simulator。")
            return
        reply = await start_simulation_job(context, chat_id, final_state["config"], final_state["bet_mode"], final_state["rounds"], final_state["card"])
        await query.edit_message_text(reply)
        return


# ==================== ⚡ Telegram 事件監聽 ====================


async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat.id
    text = update.message.text.strip()
    chat_type = update.message.chat.type
    bot_username = context.bot.username

    # /simulator 選單正在等待使用者輸入自訂局數
    wizard_state = simulator_wizard_state.get(chat_id)
    if wizard_state and wizard_state.get("awaiting_rounds") and update.effective_user and update.effective_user.id == ALLOWED_USER_ID:
        if not text.isdigit() or not (1000 <= int(text) <= MAX_ROUNDS):
            await update.message.reply_text(f"❌ 請輸入 1,000 ~ {MAX_ROUNDS:,} 之間的正整數。")
            return
        wizard_state["rounds"] = int(text)
        wizard_state.pop("awaiting_rounds", None)
        await update.message.reply_text(build_wizard_summary_text(wizard_state), reply_markup=build_confirm_keyboard())
        return

    # 只處理主動對話（私訊或群組標記），其他群組閒聊一律忽略
    if chat_type == "private" or f"@{bot_username}" in text:
        # 移除訊息中的 @BotName，拿到純文字
        clean_text = text.replace(f"@{bot_username}", "").strip()

        if parsed_report := parse_rtp_report(clean_text):
            reply = format_rtp_report_summary(parsed_report)
            await update.message.reply_text(reply, parse_mode="HTML")
            return

        # 不是可解析的 RTP 報表，一律冷酷秒回「你好」
        reply = "你好"

        await update.message.reply_text(reply)


if __name__ == "__main__":
    if not acquire_bot_instance_lock():
        print("[錯誤] 機器人已經在本機執行中，請先關閉另一個 bot 程序後再啟動。")
        raise SystemExit(1)

    if not asyncio.run(check_telegram_polling_available()):
        print("[錯誤] Telegram Bot Token 正在被另一個 getUpdates 程序使用。")
        print("請關閉其他 bot 程序，或到 BotFather 重新產生 token 後再啟動。")
        raise SystemExit(1)

    print("正在啟動混合規則型機器人 中...")
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("simulator", simulator_menu_cmd))
    app.add_handler(CommandHandler("run_start", run_start_cmd))
    app.add_handler(CommandHandler("run_status", run_status_cmd))
    app.add_handler(CommandHandler("run_cancel", run_cancel_cmd))
    app.add_handler(CallbackQueryHandler(simulator_callback, pattern=r"^sim:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_error_handler(on_error)
    print("[系統提示] 機器人已成功上線！(請按 Ctrl + C 即可關閉)")
    app.run_polling()
