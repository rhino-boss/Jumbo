from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
from datetime import datetime
from pathlib import Path

import keyboard
import win32api
import win32con
import win32gui
from openpyxl import Workbook
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver
from seleniumwire.utils import decode as decode_body


# %% 基本設定

CHROME_DRIVER_VERSION = "151.0.7922.174"
SETTINGS_VERSION = 3

# PP 官方免費試玩（bigwinboard 評測頁的 Demo 連結），不需登入。
DEMO_URL = (
    "https://demogamesfree.pragmaticplay.net/gs2c/openGame.do"
    "?lang=en&cur=USD&gameSymbol={symbol}&jurisdiction=99"
)
GAMES = [
    {"name": "Sugar Rush 1000", "symbol": "vs20sugarrushx", "intro": (0.844, 0.585)},
    {"name": "Sugar Rush Super Scatter", "symbol": "vs20sugrushss", "intro": (0.80, 0.713)},
]

# 自動模式固定畫面大小，點擊位置用畫面比例表示（在此尺寸下實測）。
AUTO_VIEWPORT = (984, 649)
AUTO_SPIN_POINT = (0.819, 0.901)
AUTO_CENTER_POINT = (0.5, 0.5)
AUTO_STALL_SECONDS = 8.0
AUTO_RELOAD_SECONDS = 120.0
AUTO_MIN_BALANCE = 1000.0

# 只需點 Spin；座標依螢幕不同，第一次執行請重新校正。
DEFAULT_CLICK_POINTS = [
    {"name": "Spin", "x": 1123, "y": 684},
]

# 請求參數只留判讀用欄位，不存 mgckey 等 Session 資訊。
REQUEST_FIELDS = ["action", "c", "l", "bl", "pur", "ind", "index", "counter"]


def resolve_script_dir() -> Path:
    """同時支援直接執行 .py 與 VS Code Interactive Window。"""
    if "__file__" in globals():
        return Path(__file__).resolve().parent

    candidate = Path.cwd() / "Tools" / "ReelCracker" / "05_Sugar Rush"
    return candidate if candidate.is_dir() else Path.cwd()


IS_FROZEN = bool(getattr(sys, "frozen", False))
if IS_FROZEN:
    SCRIPT_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", SCRIPT_DIR))
    DRIVER_PATH = (
        RESOURCE_DIR
        / "drivers"
        / CHROME_DRIVER_VERSION
        / "chromedriver-win64"
        / "chromedriver.exe"
    )
else:
    SCRIPT_DIR = resolve_script_dir()
    RESOURCE_DIR = SCRIPT_DIR
    DRIVER_PATH = (
        SCRIPT_DIR.parent
        / "drivers"
        / CHROME_DRIVER_VERSION
        / "chromedriver-win64"
        / "chromedriver.exe"
    )

DATA_DIR = SCRIPT_DIR / "data"
SETTINGS_FILE = SCRIPT_DIR / "reel_cracker_settings.json"
# 自動模式執行中建立這個檔就會保存並結束（SSH 遠端停止用）；下次啟動前要刪掉。
STOP_FILE = SCRIPT_DIR / "STOP"

# 保留瀏覽器物件，讓 VS Code Interactive Window 再次執行時仍可沿用 Session。
if "ACTIVE_BROWSER" not in globals():
    ACTIVE_BROWSER: webdriver.Chrome | None = None
    ACTIVE_GAME: dict[str, str] | None = None

# interceptor 在 seleniumwire 的背景執行緒寫入，主執行緒定期取走。
if "CAPTURED" not in globals():
    CAPTURED: list[dict[str, object]] = []
    CAPTURED_LOCK = threading.Lock()


# %% 輸入與設定工具


class InputCancelled(Exception):
    """使用者在輸入提示中輸入 q／exit 取消目前操作。"""


def is_cancel_command(value: str) -> bool:
    return value.strip().lower() in {"q", "quit", "exit", "cancel", "取消", "退出"}


def ask_int(prompt: str, default: int, minimum: int = 1) -> int:
    while True:
        value = input(f"{prompt} [{default}]（輸入 q 取消）: ").strip()
        if is_cancel_command(value):
            raise InputCancelled
        if not value:
            return default
        try:
            number = int(value)
            if number >= minimum:
                return number
        except ValueError:
            pass
        print(f"請輸入大於或等於 {minimum} 的整數。")


def ask_float(prompt: str, default: float, minimum: float = 0.0) -> float:
    while True:
        value = input(f"{prompt} [{default}]（輸入 q 取消）: ").strip()
        if is_cancel_command(value):
            raise InputCancelled
        if not value:
            return default
        try:
            number = float(value)
            if number >= minimum:
                return number
        except ValueError:
            pass
        print(f"請輸入大於或等於 {minimum} 的數字。")


def ask_yes_no(prompt: str, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} [{hint}]（q 取消）: ").strip().lower()
        if is_cancel_command(value):
            raise InputCancelled
        if not value:
            return default
        if value in {"y", "yes", "是"}:
            return True
        if value in {"n", "no", "否"}:
            return False
        print("請輸入 y 或 n。")


def load_click_points() -> tuple[list[dict[str, int | str]], bool]:
    if not SETTINGS_FILE.exists():
        return [dict(point) for point in DEFAULT_CLICK_POINTS], False

    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if settings.get("version") != SETTINGS_VERSION:
            print("舊座標使用不同座標系，請重新校正一次。")
            return [dict(point) for point in DEFAULT_CLICK_POINTS], False
        points = settings.get("click_points")
        if (
            isinstance(points, list)
            and len(points) >= 1
            and all(
                isinstance(point, dict)
                and {"name", "x", "y"}.issubset(point)
                for point in points
            )
        ):
            return points, True
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    print("座標設定檔無法讀取，改用內建預設座標。")
    return [dict(point) for point in DEFAULT_CLICK_POINTS], False


def save_click_points(points: list[dict[str, int | str]]) -> None:
    SETTINGS_FILE.write_text(
        json.dumps(
            {
                "version": SETTINGS_VERSION,
                "coordinate_system": "chrome_client_area",
                "click_points": points,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"座標已保存：{SETTINGS_FILE}")


# %% 瀏覽器與視窗工具


def create_driver(headless: bool = False) -> webdriver.Chrome:
    # Chrome 會自動更新，內附 ChromeDriver 版本對不上時改由 Selenium Manager 下載相符版本。
    if DRIVER_PATH.is_file():
        try:
            return build_driver(Service(str(DRIVER_PATH)), headless)
        except SessionNotCreatedException:
            print(f"內附 ChromeDriver {CHROME_DRIVER_VERSION} 與目前 Chrome 版本不符，改用 Selenium Manager。")
    return build_driver(Service(), headless)


def build_driver(service: Service, headless: bool) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    if headless:
        # 無介面模式（SSH 遠端執行）：WebGL 改用軟體繪圖，背景分頁不降速。
        options.add_argument("--headless=new")
        options.add_argument(f"--window-size={AUTO_VIEWPORT[0]},{AUTO_VIEWPORT[1]}")
        options.add_argument("--use-angle=swiftshader")
        options.add_argument("--enable-unsafe-swiftshader")
        options.add_argument("--mute-audio")
    else:
        options.add_argument("--start-maximized")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--force-device-scale-factor=1.0")
    options.add_argument("--ignore-certificate-errors")

    # 封包改由 response_interceptor 即時收進 CAPTURED，不靠 browser.requests 輪詢，
    # 長時間跑不會累積記憶體，也不會在清除時漏掉剛到的回應。
    seleniumwire_options = {
        "request_storage": "memory",
        "request_storage_max_size": 100,
    }
    browser = webdriver.Chrome(
        service=service,
        options=options,
        seleniumwire_options=seleniumwire_options,
    )
    browser.scopes = [r".*[Gg]ame[Ss]ervice.*"]
    browser.response_interceptor = capture_response
    return browser


def get_chrome_windows() -> list[int]:
    windows: list[int] = []

    def collect(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        if win32gui.GetClassName(hwnd) != "Chrome_WidgetWin_1":
            return
        if win32gui.GetWindowText(hwnd).strip():
            windows.append(hwnd)

    win32gui.EnumWindows(collect, None)
    return windows


def find_controlled_chrome_window(browser: webdriver.Chrome) -> int:
    windows = get_chrome_windows()
    if not windows:
        raise RuntimeError("找不到可見的 Chrome 視窗。")

    page_title = browser.title.strip().lower()
    if page_title:
        matching = [
            hwnd
            for hwnd in windows
            if page_title in win32gui.GetWindowText(hwnd).strip().lower()
        ]
        if matching:
            return matching[0]

    foreground = win32gui.GetForegroundWindow()
    if foreground in windows:
        return foreground

    def area(hwnd: int) -> int:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return max(0, right - left) * max(0, bottom - top)

    return max(windows, key=area)


def select_target_chrome_window() -> int:
    """由滑鼠所在位置鎖定目標 Chrome，避免多個 Chrome 視窗時選錯。"""
    print("\n=== 選擇目標 Chrome ===")
    input("只移動滑鼠到遊戲 Chrome 視窗內，游標停住後直接按鍵盤 Enter...")
    mouse_x, mouse_y = win32api.GetCursorPos()
    pointed_hwnd = win32gui.WindowFromPoint((mouse_x, mouse_y))
    root_hwnd = win32gui.GetAncestor(pointed_hwnd, win32con.GA_ROOT)

    if not root_hwnd or win32gui.GetClassName(root_hwnd) != "Chrome_WidgetWin_1":
        raise ValueError("滑鼠所在位置不是 Chrome 視窗，請重新選擇。")

    print(f"已鎖定 Chrome 視窗：{win32gui.GetWindowText(root_hwnd)}")
    return root_hwnd


def calibrate_click_points(
    hwnd: int,
    default_count: int,
) -> list[dict[str, int | str]]:
    point_count = ask_int("每一局需要點擊幾個位置", default_count)
    points: list[dict[str, int | str]] = []

    print("\n=== 自訂點擊流程與座標校正 ===")
    print("只移動滑鼠、不點擊；游標停在指定位置時直接按鍵盤 Enter。")
    print("不要把游標移回 VS Code，校正程式會直接讀取當下滑鼠位置。")
    for index in range(1, point_count + 1):
        default_name = f"點擊 {index}"
        label = input(f"第 {index} 步名稱 [{default_name}]: ").strip() or default_name
        while True:
            input(f"{index}/{point_count} 將滑鼠移到「{label}」後按 Enter...")
            mouse_x, mouse_y = win32api.GetCursorPos()
            client_x, client_y = win32gui.ScreenToClient(hwnd, (mouse_x, mouse_y))
            _, _, client_right, client_bottom = win32gui.GetClientRect(hwnd)
            if 0 <= client_x < client_right and 0 <= client_y < client_bottom:
                point = {"name": label, "x": client_x, "y": client_y}
                points.append(point)
                print(f"已記錄 {label}: ({point['x']}, {point['y']})")
                break
            print(
                f"座標 ({client_x}, {client_y}) 不在目標 Chrome 的 "
                f"{client_right}x{client_bottom} 客戶區內，請保持游標在遊戲畫面重新記錄。"
            )

    save_click_points(points)
    return points


def click_window(hwnd: int, x: int, y: int) -> None:
    if not win32gui.IsWindow(hwnd):
        raise RuntimeError("Chrome 視窗已關閉。")

    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    width = right - left
    height = bottom - top
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(
            f"點擊座標 ({x}, {y}) 超出 Chrome 客戶區 {width}x{height}，請重新校正。"
        )

    # 保持舊版的背景點擊方式，不移動或占用實體滑鼠。
    # 僅沿著指定 Chrome 的子視窗尋找渲染區，不會誤送到遮住 Chrome 的其他程式。
    target_hwnd = hwnd
    target_point = (x, y)
    child_flags = (
        win32con.CWP_SKIPINVISIBLE
        | win32con.CWP_SKIPDISABLED
        | win32con.CWP_SKIPTRANSPARENT
    )
    while True:
        child_hwnd = win32gui.ChildWindowFromPointEx(
            target_hwnd,
            target_point,
            child_flags,
        )
        if not child_hwnd or child_hwnd == target_hwnd:
            break
        screen_point = win32gui.ClientToScreen(target_hwnd, target_point)
        target_point = win32gui.ScreenToClient(child_hwnd, screen_point)
        target_hwnd = child_hwnd

    target_x, target_y = target_point
    packed_position = win32api.MAKELONG(target_x, target_y)

    win32gui.PostMessage(
        target_hwnd,
        win32con.WM_LBUTTONDOWN,
        win32con.MK_LBUTTON,
        packed_position,
    )
    time.sleep(0.02)
    win32gui.PostMessage(target_hwnd, win32con.WM_LBUTTONUP, 0, packed_position)


# %% 封包整理與輸出


def parse_query_text(text: str) -> dict[str, object] | None:
    text = text.strip()
    if not text:
        return None

    try:
        parsed_json = json.loads(text)
        if isinstance(parsed_json, dict):
            return parsed_json
    except json.JSONDecodeError:
        pass

    parsed_query = urllib.parse.parse_qs(text, keep_blank_values=True)
    if not parsed_query:
        return None
    return {key: values[0] if len(values) == 1 else values for key, values in parsed_query.items()}


def capture_response(request: object, response: object) -> None:
    """seleniumwire response_interceptor：每個 gameService 回應到達時立即收下。"""
    if "gameservice" not in request.url.lower():
        return

    raw_body = response.body or b""
    encoding = response.headers.get("Content-Encoding", "identity")
    try:
        raw_body = decode_body(raw_body, encoding)
    except Exception:
        pass

    parsed = parse_query_text(raw_body.decode("utf-8", errors="ignore"))
    if parsed is None:
        return

    # 附上請求端的動作與押注參數（doSpin／doCollect、c、l、pur…），方便區分轉數與購買。
    request_params = parse_query_text((request.body or b"").decode("utf-8", errors="ignore")) or {}
    for field in REQUEST_FIELDS:
        if field in request_params:
            parsed[f"req_{field}"] = request_params[field]
    parsed["captured_at"] = datetime.now().isoformat(timespec="milliseconds")

    with CAPTURED_LOCK:
        CAPTURED.append(parsed)


def collect_game_responses(records: list[dict[str, object]], jsonl_path: Path) -> int:
    with CAPTURED_LOCK:
        new_records = CAPTURED[:]
        CAPTURED.clear()
    if not new_records:
        return 0

    records.extend(new_records)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as handle:
        for record in new_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(new_records)


def make_excel_safe(record: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            safe[key] = json.dumps(value, ensure_ascii=False)
        else:
            safe[key] = value
    return safe


def save_records(records: list[dict[str, object]], excel_path: Path) -> None:
    if not records:
        print("目前尚未擷取到 gameService 回應。")
        return

    excel_path.parent.mkdir(parents=True, exist_ok=True)
    excel_records = [make_excel_safe(record) for record in records]

    columns: list[str] = []
    for record in excel_records:
        for column in record:
            if column not in columns:
                columns.append(column)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "game_data"
    worksheet.append(columns)
    for record in excel_records:
        worksheet.append([record.get(column, "") for column in columns])
    try:
        workbook.save(excel_path)
    except PermissionError:
        print(f"{excel_path.name} 被 Excel 開著無法寫入；資料仍在 .jsonl，關掉 Excel 後下次保存會補上。")
        return
    spins = sum(1 for record in records if record.get("req_action") == "doSpin")
    print(f"已保存 {len(records)} 筆（doSpin {spins}）：{excel_path.name}")


# %% 自動執行


def run_click_loop(
    browser: webdriver.Chrome,
    hwnd: int,
    points: list[dict[str, int | str]],
    rounds: int,
    click_delay: float,
    save_every: int,
    excel_path: Path,
    jsonl_path: Path,
) -> None:
    stop_event = threading.Event()
    pause_event = threading.Event()
    records: list[dict[str, object]] = []
    # 丟掉開始前（載入、手動試轉）收到的回應，只留本批次。
    with CAPTURED_LOCK:
        CAPTURED.clear()

    def stop() -> None:
        stop_event.set()
        print("\n收到停止指令，正在保存本批次；Chrome 不會關閉。")

    def toggle_pause() -> None:
        if pause_event.is_set():
            pause_event.clear()
            print("\n已繼續。")
        else:
            pause_event.set()
            print("\n已暫停；按 F3 繼續。")

    stop_hotkey = keyboard.add_hotkey("f1", stop)
    pause_hotkey = keyboard.add_hotkey("f3", toggle_pause)

    print("\n3 秒後開始；F3 暫停／繼續，F1 結束本批次並回到選單。")
    print("使用背景點擊，不會移動或占用你的滑鼠。")
    for remaining in range(3, 0, -1):
        print(f"{remaining}...")
        if stop_event.wait(1):
            break

    try:
        for round_number in range(1, rounds + 1):
            if stop_event.is_set():
                break

            while pause_event.is_set() and not stop_event.is_set():
                time.sleep(0.1)

            for point in points:
                if stop_event.is_set():
                    break
                click_window(hwnd, int(point["x"]), int(point["y"]))
                if stop_event.wait(click_delay):
                    break

            if round_number == 1 or round_number % 10 == 0:
                print(f"已完成 {round_number}/{rounds} 局")

            if round_number % save_every == 0:
                added = collect_game_responses(records, jsonl_path)
                print(f"本次新增 {added} 筆回應。")
                save_records(records, excel_path)
    finally:
        keyboard.remove_hotkey(stop_hotkey)
        keyboard.remove_hotkey(pause_hotkey)
        time.sleep(0.5)
        collect_game_responses(records, jsonl_path)
        save_records(records, excel_path)


# %% 無介面自動模式（--auto）


def parse_balance(value: object) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def click_viewport(browser: webdriver.Chrome, point: tuple[float, float]) -> None:
    """經 WebDriver 送出點擊，不需要桌面、滑鼠或座標校正。"""
    width, height = AUTO_VIEWPORT
    action = ActionBuilder(browser)
    action.pointer_action.move_to_location(int(width * point[0]), int(height * point[1])).click()
    action.perform()


def fit_viewport(browser: webdriver.Chrome) -> None:
    width, height = AUTO_VIEWPORT
    browser.set_window_size(width, height)
    inner_width, inner_height = browser.execute_script("return [innerWidth, innerHeight]")
    if (inner_width, inner_height) != (width, height):
        browser.set_window_size(2 * width - inner_width, 2 * height - inner_height)


def load_game_auto(browser: webdriver.Chrome, game: dict[str, object]) -> None:
    """開啟試玩、等 doInit 回應、點掉開場畫面。"""
    with CAPTURED_LOCK:
        CAPTURED.clear()
    browser.get(DEMO_URL.format(symbol=game["symbol"]))
    fit_viewport(browser)

    deadline = time.time() + 90
    while time.time() < deadline:
        with CAPTURED_LOCK:
            if any(record.get("req_action") == "doInit" for record in CAPTURED):
                break
        time.sleep(0.5)
    else:
        raise TimeoutError("90 秒內沒收到 doInit，遊戲沒有載入。")

    time.sleep(8)  # 等開場動畫
    click_viewport(browser, AUTO_CENTER_POINT)
    time.sleep(2)
    click_viewport(browser, game["intro"])
    time.sleep(4)
    with CAPTURED_LOCK:
        CAPTURED.clear()
    print("遊戲已載入。", flush=True)


def hold_turbo(browser: webdriver.Chrome) -> None:
    """按住空白鍵＝遊戲內建 Turbo Spin，會一直轉下去，比點 Spin 快約 2 倍。"""
    ActionChains(browser).key_up(Keys.SPACE).key_down(Keys.SPACE).perform()


def run_auto(
    game: dict[str, object],
    target_spins: int,
    click_delay: float,
    save_every: int,
    headless: bool,
    turbo: bool,
    tag: str,
) -> None:
    run_started = datetime.now().strftime("%Y%m%d_%H%M%S")
    game_dir = DATA_DIR / str(game["name"])
    file_stem = f"game_responses_{game['name']}_{run_started}{'_' + tag if tag else ''}"
    excel_path = game_dir / f"{file_stem}.xlsx"
    jsonl_path = game_dir / f"{file_stem}.jsonl"

    print(f"=== 自動模式：{game['name']}，目標 {target_spins} 局（付費轉數）===", flush=True)
    print(f"輸出：{jsonl_path}", flush=True)

    browser = create_driver(headless=headless)
    records: list[dict[str, object]] = []
    paid_spins = 0
    next_save = save_every
    last_balance: float | None = None
    started = time.time()
    try:
        load_game_auto(browser, game)
        if turbo:
            hold_turbo(browser)
        last_response = time.time()
        last_nudge = 0.0
        while paid_spins < target_spins:
            if STOP_FILE.exists():
                print("偵測到 STOP 檔，保存後結束。", flush=True)
                break
            if not turbo:
                click_viewport(browser, AUTO_SPIN_POINT)
            time.sleep(click_delay)

            start_index = len(records)
            if collect_game_responses(records, jsonl_path):
                last_response = time.time()
            for record in records[start_index:]:
                balance = parse_balance(record.get("balance"))
                if balance is None:
                    continue
                # 只有付費 spin 會扣款；連消與免費遊戲的 doSpin 餘額不變。
                if (
                    record.get("req_action") == "doSpin"
                    and last_balance is not None
                    and balance < last_balance - 1e-9
                ):
                    paid_spins += 1
                last_balance = balance

            idle = time.time() - last_response
            if idle > AUTO_RELOAD_SECONDS:
                print(f"{int(idle)} 秒沒有回應，重新載入遊戲。", flush=True)
                load_game_auto(browser, game)
                if turbo:
                    hold_turbo(browser)
                last_response = time.time()
                continue
            if idle > AUTO_STALL_SECONDS and time.time() - last_nudge > AUTO_STALL_SECONDS:
                # 可能停在 FG 開始／結算彈窗，點畫面中央與開場按鈕位置把它關掉，再重新按住空白鍵。
                click_viewport(browser, AUTO_CENTER_POINT)
                time.sleep(0.5)
                click_viewport(browser, game["intro"])
                if turbo:
                    hold_turbo(browser)
                last_nudge = time.time()

            if last_balance is not None and last_balance < AUTO_MIN_BALANCE:
                print(f"試玩餘額剩 {last_balance:,.2f}，重新載入以重置餘額。", flush=True)
                load_game_auto(browser, game)
                if turbo:
                    hold_turbo(browser)
                last_balance = None
                last_response = time.time()

            if paid_spins >= next_save:
                save_records(records, excel_path)
                elapsed = time.time() - started
                rate = paid_spins / elapsed * 3600 if elapsed else 0
                print(
                    f"[{datetime.now():%H:%M:%S}] {paid_spins}/{target_spins} 局，"
                    f"約 {rate:,.0f} 局／小時",
                    flush=True,
                )
                next_save += save_every
    except KeyboardInterrupt:
        print("\n收到中斷，保存後結束。", flush=True)
    finally:
        collect_game_responses(records, jsonl_path)
        save_records(records, excel_path)
        print(f"共 {paid_spins} 局付費轉數，{len(records)} 筆回應。", flush=True)
        browser.quit()


def parse_auto_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sugar Rush 試玩封包自動擷取（無介面）")
    parser.add_argument("--auto", action="store_true", help="無介面自動模式")
    parser.add_argument(
        "--game",
        type=int,
        default=1,
        choices=range(1, len(GAMES) + 1),
        help="1=Sugar Rush 1000，2=Sugar Rush Super Scatter",
    )
    parser.add_argument("--spins", type=int, default=5000, help="付費轉數")
    parser.add_argument("--delay", type=float, default=0.5, help="檢查回應／點擊 Spin 的間隔秒數")
    parser.add_argument("--save-every", type=int, default=200, help="每幾局保存 xlsx")
    parser.add_argument("--show", action="store_true", help="顯示 Chrome 視窗（本機觀察用）")
    parser.add_argument("--no-turbo", action="store_true", help="改用點 Spin，不按住空白鍵")
    parser.add_argument("--tag", default="", help="檔名後綴；同時開多個程式時用來區分輸出")
    return parser.parse_args(argv)


def run_self_test() -> None:
    """供打包後驗證必要資源，不啟動瀏覽器或操作滑鼠。"""
    if not DRIVER_PATH.is_file():
        raise FileNotFoundError(f"自我測試找不到 ChromeDriver：{DRIVER_PATH}")

    driver_version = subprocess.run(
        [str(DRIVER_PATH), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    print(f"ChromeDriver：{driver_version}")
    print(f"設定與輸出目錄：{SCRIPT_DIR}")
    print("SELF_TEST_OK")


def choose_game(default_index: int = 1) -> dict[str, str]:
    print("\n=== 選擇遊戲 ===")
    for number, game in enumerate(GAMES, start=1):
        print(f"{number}. {game['name']}（{game['symbol']}）")
    while True:
        number = ask_int("遊戲編號", default_index)
        if number <= len(GAMES):
            return GAMES[number - 1]
        print(f"請輸入 1 到 {len(GAMES)}。")


def open_game(browser: webdriver.Chrome, game: dict[str, str]) -> None:
    browser.get(DEMO_URL.format(symbol=game["symbol"]))
    print(f"\n已開啟 {game['name']} 試玩。請在 Chrome 中：")
    print("1. 等遊戲載入完成，點掉開場畫面")
    print("2. 手動設定押注額／押注模式（Ante、購買等）")
    print("3. 確認點 Spin 會轉")
    input("完成後回到這裡按 Enter 繼續...")


def main() -> None:
    global ACTIVE_BROWSER, ACTIVE_GAME

    print("=== Sugar Rush Reel Cracker（PP 免費試玩）===")
    click_points, has_saved_points = load_click_points()
    print("目前座標：")
    for point in click_points:
        print(f"- {point['name']}: ({point['x']}, {point['y']})")

    browser: webdriver.Chrome | None = None
    close_browser = False
    batch_has_run = False

    try:
        if ACTIVE_BROWSER is not None:
            try:
                ACTIVE_BROWSER.current_url
                browser = ACTIVE_BROWSER
                print("\n已沿用目前開啟的 Chrome Session。")
            except Exception:
                ACTIVE_BROWSER = None

        if browser is None or ACTIVE_GAME is None:
            ACTIVE_GAME = choose_game()
            if browser is None:
                print("\n正在啟動 Chrome...")
                browser = create_driver()
                ACTIVE_BROWSER = browser
            open_game(browser, ACTIVE_GAME)
        game = ACTIVE_GAME
        print(f"目前遊戲：{game['name']}")

        hwnd = select_target_chrome_window()

        recalibrate_default = not has_saved_points
        if ask_yes_no("要重新設定點擊流程與座標嗎？", recalibrate_default):
            click_points = calibrate_click_points(hwnd, len(click_points))

        while True:
            print("\n=== 操作選單 ===")
            print("1. 開始新批次")
            print("2. 重新設定點擊流程與座標")
            print("3. 顯示目前座標")
            if IS_FROZEN:
                print("4. 待命並保留 Chrome")
            else:
                print("4. 結束 main() 但保留 Chrome")
            print("5. 關閉 Chrome 並結束程式")
            print(f"6. 換遊戲（目前：{game['name']}）")
            default_choice = "4" if batch_has_run else "1"
            choice = input(f"請選擇 [{default_choice}]（q 關閉並退出）: ").strip()
            if not choice:
                choice = default_choice
            if is_cancel_command(choice):
                choice = "5"

            if choice == "1":
                if not win32gui.IsWindow(hwnd):
                    hwnd = select_target_chrome_window()
                try:
                    rounds = ask_int("本批次執行局數", 5000)
                    click_delay = ask_float("每個點擊之間等待秒數", 0.3)
                    save_every = ask_int("每幾局自動保存一次", 50)
                except InputCancelled:
                    print("已取消本批次，回到操作選單。")
                    continue
                run_started = datetime.now().strftime("%Y%m%d_%H%M%S")
                game_dir = DATA_DIR / game["name"]
                file_stem = f"game_responses_{game['name']}_{run_started}"
                excel_path = game_dir / f"{file_stem}.xlsx"
                jsonl_path = game_dir / f"{file_stem}.jsonl"

                run_click_loop(
                    browser=browser,
                    hwnd=hwnd,
                    points=click_points,
                    rounds=rounds,
                    click_delay=click_delay,
                    save_every=save_every,
                    excel_path=excel_path,
                    jsonl_path=jsonl_path,
                )
                batch_has_run = True
                print("本批次已結束，Chrome 與登入狀態仍保留。")
            elif choice == "2":
                try:
                    hwnd = select_target_chrome_window()
                    click_points = calibrate_click_points(hwnd, len(click_points))
                except InputCancelled:
                    print("已取消重新校正，回到操作選單。")
            elif choice == "3":
                print("目前點擊流程：")
                for index, point in enumerate(click_points, start=1):
                    print(f"{index}. {point['name']}: ({point['x']}, {point['y']})")
            elif choice == "4":
                if IS_FROZEN:
                    print("目前為待命狀態，Chrome 保持開啟；可繼續選擇其他操作。")
                    continue
                print("main() 已結束，Chrome Session 保留在目前 Kernel 中。")
                return
            elif choice == "5":
                close_browser = True
                return
            elif choice == "6":
                try:
                    next_index = (GAMES.index(game) + 1) % len(GAMES) + 1
                    game = choose_game(default_index=next_index)
                    ACTIVE_GAME = game
                    open_game(browser, game)
                except InputCancelled:
                    print("已取消換遊戲。")
            else:
                print("無效選項，請輸入 1 到 6。")
    except InputCancelled:
        print("\n已取消目前操作；Chrome 將保持開啟。")
    except KeyboardInterrupt:
        print("\n已中斷目前操作；Chrome 將保持開啟。")
    except Exception as error:
        print(f"\n執行失敗：{type(error).__name__}: {error}")
        raise
    finally:
        if close_browser and browser is not None:
            browser.quit()
            ACTIVE_BROWSER = None
            print("Chrome 已關閉。")
        elif browser is not None:
            ACTIVE_BROWSER = browser
            print("Chrome 保持開啟，可再次執行 main() 沿用目前 Session。")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    elif "--auto" in sys.argv:
        args = parse_auto_args(sys.argv[1:])
        run_auto(
            game=GAMES[args.game - 1],
            target_spins=args.spins,
            click_delay=args.delay,
            save_every=args.save_every,
            headless=not args.show,
            turbo=not args.no_turbo,
            tag=args.tag,
        )
    elif IS_FROZEN:
        try:
            main()
        except Exception:
            traceback.print_exc()
            input("\n發生錯誤，按 Enter 關閉程式...")
    else:
        main()
