from __future__ import annotations

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
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from seleniumwire.utils import decode as decode_body


# %% 基本設定

LOGIN_URL = "https://www.pko99.ph/"
CHROME_DRIVER_VERSION = "151.0.7922.174"
SETTINGS_VERSION = 3

# 舊版程式使用的三個座標只作為初始參考；點擊步數與用途皆可重新設定。
DEFAULT_CLICK_POINTS = [
    {"name": "點擊 1", "x": 373, "y": 415},
    {"name": "點擊 2", "x": 1123, "y": 684},
    {"name": "點擊 3", "x": 1123, "y": 684},
]


def resolve_script_dir() -> Path:
    """同時支援直接執行 .py 與 VS Code Interactive Window。"""
    if "__file__" in globals():
        return Path(__file__).resolve().parent

    candidate = Path.cwd() / "Tools" / "ReelCracker" / "02_Gates of Olympus 1000"
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

# 保留瀏覽器物件，讓 VS Code Interactive Window 再次執行時仍可沿用 Session。
if "ACTIVE_BROWSER" not in globals():
    ACTIVE_BROWSER: webdriver.Chrome | None = None


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


def create_driver() -> webdriver.Chrome:
    if not DRIVER_PATH.is_file():
        raise FileNotFoundError(f"找不到 ChromeDriver：{DRIVER_PATH}")

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--force-device-scale-factor=1.0")
    options.add_argument("--ignore-certificate-errors")

    seleniumwire_options = {
        "request_storage": "memory",
        "request_storage_max_size": 20000,
    }
    browser = webdriver.Chrome(
        service=Service(str(DRIVER_PATH)),
        options=options,
        seleniumwire_options=seleniumwire_options,
    )
    browser.scopes = [r".*[Gg]ame[Ss]ervice.*"]
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


def parse_response_body(request: object) -> dict[str, object] | None:
    response = getattr(request, "response", None)
    if response is None:
        return None

    raw_body = response.body or b""
    encoding = response.headers.get("Content-Encoding", "identity")
    try:
        raw_body = decode_body(raw_body, encoding)
    except Exception:
        pass

    text = raw_body.decode("utf-8", errors="ignore").strip()
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


def collect_game_responses(
    browser: webdriver.Chrome,
    records: dict[str, dict[str, object]],
    processed_requests: set[int],
) -> int:
    added = 0
    for request in list(browser.requests):
        request_id = id(request)
        if request_id in processed_requests or request.response is None:
            continue
        if "gameservice" not in request.url.lower():
            continue

        parsed = parse_response_body(request)
        if parsed is None:
            continue

        processed_requests.add(request_id)
        fallback_key = f"response_{len(records) + 1}"
        record_key = str(parsed.get("index") or fallback_key)
        records[record_key] = parsed
        added += 1
    return added


def make_excel_safe(record: dict[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in record.items():
        if isinstance(value, (dict, list)):
            safe[key] = json.dumps(value, ensure_ascii=False)
        else:
            safe[key] = value
    return safe


def save_records(
    records: dict[str, dict[str, object]],
    excel_path: Path,
    json_path: Path,
) -> None:
    if not records:
        print("目前尚未擷取到 gameService 回應。")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    record_list = list(records.values())
    excel_records = [make_excel_safe(record) for record in record_list]

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
    workbook.save(excel_path)
    json_path.write_text(
        json.dumps(record_list, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已保存 {len(record_list)} 筆：{excel_path.name}")


# %% 自動執行


def run_click_loop(
    browser: webdriver.Chrome,
    hwnd: int,
    points: list[dict[str, int | str]],
    rounds: int,
    click_delay: float,
    save_every: int,
    excel_path: Path,
    json_path: Path,
) -> None:
    stop_event = threading.Event()
    pause_event = threading.Event()
    records: dict[str, dict[str, object]] = {}
    processed_requests: set[int] = set()

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
                added = collect_game_responses(browser, records, processed_requests)
                print(f"本次新增 {added} 筆回應。")
                save_records(records, excel_path, json_path)
    finally:
        keyboard.remove_hotkey(stop_hotkey)
        keyboard.remove_hotkey(pause_hotkey)
        time.sleep(0.5)
        collect_game_responses(browser, records, processed_requests)
        save_records(records, excel_path, json_path)


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


def main() -> None:
    global ACTIVE_BROWSER

    print("=== Gates of Olympus 1000 Reel Cracker v2 ===")
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

        if browser is None:
            print("\n正在啟動 Chrome...")
            browser = create_driver()
            ACTIVE_BROWSER = browser
            browser.get(LOGIN_URL)

            print("\n請在剛開啟的 Chrome 中：")
            print("1. 手動登入")
            print("2. 開啟要操作的遊戲或頁面")
            print("3. 等遊戲畫面完全載入")
            input("完成後回到這裡按 Enter 繼續...")

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
                excel_path = DATA_DIR / f"game_responses_{run_started}.xlsx"
                json_path = DATA_DIR / f"game_responses_{run_started}.json"

                run_click_loop(
                    browser=browser,
                    hwnd=hwnd,
                    points=click_points,
                    rounds=rounds,
                    click_delay=click_delay,
                    save_every=save_every,
                    excel_path=excel_path,
                    json_path=json_path,
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
            else:
                print("無效選項，請輸入 1 到 5。")
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
    elif IS_FROZEN:
        try:
            main()
        except Exception:
            traceback.print_exc()
            input("\n發生錯誤，按 Enter 關閉程式...")
    else:
        main()
