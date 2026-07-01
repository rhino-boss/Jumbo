import asyncio
import html
import io
import os
import re
import shutil
import socket
import subprocess
import tempfile
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font
from telegram import Bot, Update
from telegram.error import Conflict
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import rarfile

r"""

# 從專案根目錄執行：
.\.venv\Scripts\python.exe Tools\TelegramBot\walking_encyclopedia_bot.py

# 功能介紹
  * 整理報表：支援 zip/rar、多檔合併、巢狀壓縮檔，並自動轉成 Excel。
  * 壓測資料重點整理：抓取 RTP、Spin、Coin in、各 pool RTP 等重點欄位。
  * AI 機器人：開發中。

"""

# ==================== 🔑 核心金鑰設定 ====================
TG_TOKEN = "8817922272:AAGAGwyjZQLMHcEE8iRs2Au9XK1EJpgEVVk"
CLAUDE_CMD = os.path.expandvars(r"%APPDATA%\npm\claude.cmd")
CLAUDE_GIT_BASH_CANDIDATES = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
]


# ==================== ⚙️ 機器人參數設定 ====================
MSG_LIMIT = 5  # 每滿 5 條群組訊息，就自動觸發一次「固定格式存檔」
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "generated_reports"
MAX_REPORT_FILES = 20
ARCHIVE_EXTENSIONS = {".zip", ".rar"}
MAX_ARCHIVE_DEPTH = 10
ARCHIVE_BATCH_DELAY_SECONDS = 2
BOT_INSTANCE_LOCK_PORT = 48726
SEVENZIP_CANDIDATES = [
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\7-Zip\7z.exe",
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

# 記憶暫存區
chat_buffers = {}
archive_batches = {}
bot_instance_lock = None

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


def save_to_text_file(chat_title: str, content_text: str):
    """將群組聊天紀錄直接寫入本地的 summary.txt"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("summary.txt", "a", encoding="utf-8") as f:
            f.write(f"========================================\n")
            f.write(f"時間：{current_time}\n")
            f.write(f"來源群組：{chat_title}\n")
            f.write(f"對話備份內容：\n{content_text}\n")
            f.write(f"========================================\n\n")
        print(f"[系統提示] 聊天紀錄已安全寫入 summary.txt 檔案中。")
    except Exception as e:
        print(f"[錯誤] 寫入文字檔失敗: {e}")


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
    tool = shutil.which("7z") or shutil.which("7zz")
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
        raise RuntimeError("找不到可用的 RAR 解壓工具，請安裝 7-Zip 或 UnRAR。")

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


# ==================== 🧠 AI 大腦與防呆邏輯 ====================
def build_claude_env():
    """建立呼叫本機 Claude CLI 所需的環境變數。"""
    env = os.environ.copy()
    git_bash_path = env.get("CLAUDE_CODE_GIT_BASH_PATH", "")

    if not git_bash_path:
        for candidate in CLAUDE_GIT_BASH_CANDIDATES:
            if os.path.exists(candidate):
                git_bash_path = candidate
                break

    if git_bash_path:
        env["CLAUDE_CODE_GIT_BASH_PATH"] = git_bash_path

    return env


async def ask_claude_question(question: str) -> str:
    """透過本機 Claude CLI 回答問題。"""
    prompt = f"請用繁體中文回覆，且回答內容中不要包含任何 emoji 表情符號：{question}"

    try:
        process = await asyncio.create_subprocess_exec(
            CLAUDE_CMD,
            "-p",
            prompt,
            "--output-format",
            "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=build_claude_env(),
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=90)
        output = stdout.decode("utf-8", errors="replace").strip()
        error_output = stderr.decode("utf-8", errors="replace").strip()

        if process.returncode != 0:
            print(f"[系統日誌] Claude CLI 發生錯誤: {error_output}")
            return "Claude 連線失敗"

        return output or "Claude 沒有回覆內容"
    except asyncio.TimeoutError:
        print("[系統日誌] Claude CLI 執行逾時")
        return "Claude 回覆逾時"
    except Exception as e:
        print(f"[系統日誌] Claude CLI 發生錯誤: {e}")
        return "Claude 連線失敗"


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


# ==================== ⚡ Telegram 事件監聽 ====================


async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = update.message.chat.id
    chat_title = update.message.chat.title if update.message.chat.title else "私訊/未知群組"
    user_name = update.message.from_user.full_name
    text = update.message.text.strip()
    chat_type = update.message.chat.type
    bot_username = context.bot.username

    # ---------------- 情況一：主動對話（私訊或群組標記） ----------------
    if chat_type == "private" or f"@{bot_username}" in text:
        # 移除訊息中的 @BotName，拿到純文字
        clean_text = text.replace(f"@{bot_username}", "").strip()

        # 🛠️ 特殊指令判斷：如果開頭是 "ai " 或 ":"
        if clean_text.lower().startswith("ai ") or clean_text.startswith(":"):
            if clean_text.lower().startswith("ai "):
                ai_question = clean_text[3:].strip()
            else:
                ai_question = clean_text[2:].strip()

            if ai_question == "":
                reply = "你想問 AI 什麼問題呢？請在 ai 後面加上你想說的話。"
            else:
                stop_typing_event = asyncio.Event()
                typing_task = asyncio.create_task(send_typing_while_waiting(chat_id, context, stop_typing_event))
                try:
                    reply = await ask_claude_question(ai_question)
                finally:
                    stop_typing_event.set()
                    await typing_task
        elif parsed_report := parse_rtp_report(clean_text):
            reply = format_rtp_report_summary(parsed_report)
            await update.message.reply_text(reply, parse_mode="HTML")
            return
        else:
            # 不是用特殊指令開頭的，一律冷酷秒回「你好」
            reply = "你好"

        await update.message.reply_text(reply)
        return

    # ---------------- 情況二：群組聊天監聽（固定滿 5 條純文字存檔） ----------------
    if chat_id not in chat_buffers:
        chat_buffers[chat_id] = []

    chat_buffers[chat_id].append(f"{user_name}: {text}")
    print(f"[{chat_type}] 暫存訊息 ({len(chat_buffers[chat_id])}/{MSG_LIMIT}): {user_name} -> {text}")

    if len(chat_buffers[chat_id]) >= MSG_LIMIT:
        current_batch = chat_buffers[chat_id].copy()
        chat_buffers[chat_id] = []  # 清空暫存區

        combined_text = "\n".join(current_batch)
        save_to_text_file(chat_title, combined_text)

        report_text = f"【系統自動對話備份存檔成功】\n\n" f"已成功將最近的 {MSG_LIMIT} 條群組訊息安全存檔至本地 summary.txt。\n" f"（此為系統自動發送，不包含 AI 語意摘要）"
        await context.bot.send_message(chat_id=chat_id, text=report_text)


if __name__ == "__main__":
    if not acquire_bot_instance_lock():
        print("[錯誤] 機器人已經在本機執行中，請先關閉另一個 bot 終端後再啟動。")
        raise SystemExit(1)

    if not asyncio.run(check_telegram_polling_available()):
        print("[錯誤] Telegram Bot Token 正在被另一個 getUpdates 程序使用。")
        print("請關閉其他 bot 程序，或到 BotFather 重新產生 token 後再啟動。")
        raise SystemExit(1)

    print("正在啟動混合規則與 AI 捕捉型機器人 中...")
    app = Application.builder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    print("[系統提示] 機器人已成功上線！(請在正下方 Terminal 內按下 Ctrl + C 即可關閉)")
    app.run_polling()
