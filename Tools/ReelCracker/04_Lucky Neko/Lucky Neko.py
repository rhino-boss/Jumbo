# %%


from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
import re
import threading
import time
import urllib.parse
import zlib
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import pyautogui
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver

try:
    import win32api
    import win32con
    import win32gui
except Exception:
    win32api = None
    win32con = None
    win32gui = None

try:
    from pywinauto import Application  # type: ignore[import-not-found]
except Exception:
    Application = None


# %%
# ------------------------
# Runtime configuration
# ------------------------
BASE_URL = "https://www.pko99.ph/"
GAME_URL = "https://www.panalo888ko.com/common/opengame?payload=0xvl%2Fw9pt3bz0kTOkycqo7W9HxcKeYQvr2fcwC18jQWnJNGqt7udi3H4JrUHhyKjpXgVcPtYhFI7ExLRfkFK%2FeUHPL6wmD7jA3Uany7HqzxZKWPjESKPA6FIWbvd3yX%2FuvzjrL6d3jueKqYrxa%2FfnXIsZUduJ8Duk1l8SWNlFMz3qqJ%2FqftMxkh4%2FTJBdaMYhbPKZOlaAar%2B%2BSWl3fHc2ueGV6zO8EIrcYBWvAcnGqfDyAK3iUaEc18qsERpE4VzeSHcFwNMI0%2B9EKM%2BbX7nWQTFYQ1v0%2BFw0XwLn%2FeJ0cS3XtUGIYEHxCoZxJroITQZ6eA03iz8yWrJss9Z0rPp3z0UTpHxy5ySzxrR7B%2B5yplYjVu8q5yzrST8joN%2BMZllhre6zZd8fnX0K2ZetgON14zGGduqhDkcnBvtvbDZZA%2Bt09Z%2BqJcncWWRm8z%2BuDZuxpu46exNUJBwR6jjyYiHMo51h6zbCp1HF3t7FmxhniBldb5wU%2Bdou%2Fwi5fzXPGBmOu4JOqMWphtQ3Ykyqffbbm3%2BhbztHw5DjMtjZWb6oBqHpNglZpVNNEPYL9%2FqywVF%2Fdqp%2BB6br18r3pabQb8Sh3jS2mjYqeJGOWMECyRJjuq3eZrLfzuOVgx%2FS8Wr9wCaX048j2GDJuPw%2B%2FimHb4KO%2BasdnHK8tPe2ZSVwPfE1S9PUKpsIGKj4JH%2FOrrUQD3tqYXPbkiGrVmLPR4XrIl0SUOsohzVrS1ZSagX0EVWwrF5Yy0NqErj2nd0LkD35UiCQNWP0t1%2BRqTHwl7%2F5tBrVH6WU2WHd6gUe27P8eU5R06ginTkBM2vuf%2BHoaJCz6cHYjH4085Y80vZ7sSxKLBeRNQ26aoMfDpx0WUcA2LhV%2FU%2BiRSjnENv1G%2BnQZU7LVomBoYh8nTdHLlgKdFqJLHjaMXGaDaArfS9jmiTlFwvBpVDTywZsI4zn1dnVyxwdAc0xfcQonyTmbn9hqPKzJwhZw%3D%3D&skipCustomerService=true"

CHROMEDRIVER_PATH = r"D:\jumbo_JI\12_Pinata\chromedriver-win64\chromedriver.exe"
PKO_USERNAME = "jlmath3"
PKO_PASSWORD = "abc8888"

CLICK_X1 = 1000
CLICK_Y1 = 700
CLICK_X2 = 950
CLICK_Y2 = 900
CLICK_TIMES = 10000
CLICK_INTERVAL_SECONDS = 0.5
SAVE_EVERY = 1000
RESPONSE_SETTLE_SECONDS = 1.5
REQUEST_EXACT_FRAGMENT = "Spin?"
CLICK_MODE = "postmessage"  # options: "pyautogui" or "postmessage"
CHROME_TITLE_RE = ".*Panaloko - Philippine Legal Online Vegas Site.*"

OUTPUT_SUMMARY_CSV = "lucky_neko_summary.csv"
stop_requested = False
click_loop_thread: threading.Thread | None = None
last_run_data: list[dict[str, Any]] | None = None

# Keep XML-valid chars only (Excel/OpenXML safe)
INVALID_XML_RE = re.compile(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]")

# %%


def create_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--force-device-scale-factor=1.0")

    if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
        return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    return webdriver.Chrome(options=options)


def get_chrome_window_handle() -> int | None:
    # Prefer direct Win32 title scan (more stable for Chrome windows).
    if win32gui is not None:
        gui = win32gui
        matched: list[int] = []
        pattern = re.compile(CHROME_TITLE_RE)

        def _enum_handler(hwnd: int, _: Any) -> None:
            if not gui.IsWindowVisible(hwnd):
                return
            title = gui.GetWindowText(hwnd) or ""
            if pattern.search(title):
                matched.append(hwnd)

        gui.EnumWindows(_enum_handler, None)
        if matched:
            return matched[0]

    # Fallback to pywinauto if available.
    if Application is None:
        return None
    try:
        app = Application(backend="uia").connect(title_re=CHROME_TITLE_RE)
        window = app.top_window()
        return int(window.handle)
    except Exception:
        return None


def list_visible_window_titles(limit: int = 15) -> list[str]:
    if win32gui is None:
        return []
    gui = win32gui
    titles: list[str] = []

    def _enum_handler(hwnd: int, _: Any) -> None:
        if not gui.IsWindowVisible(hwnd):
            return
        title = (gui.GetWindowText(hwnd) or "").strip()
        if title:
            titles.append(title)

    gui.EnumWindows(_enum_handler, None)
    return titles[:limit]


def postmessage_click_absolute(hwnd: int, abs_x: int, abs_y: int) -> None:
    if win32gui is None or win32api is None or win32con is None:
        raise RuntimeError("pywin32 modules are unavailable.")
    left, top, _, _ = win32gui.GetWindowRect(hwnd)
    rel_x = int(abs_x - left)
    rel_y = int(abs_y - top)
    lparam = win32api.MAKELONG(rel_x, rel_y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.02)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)


def click_point(abs_x: int, abs_y: int, click_mode: str, hwnd: int | None) -> None:
    if click_mode == "postmessage" and hwnd:
        postmessage_click_absolute(hwnd, abs_x, abs_y)
        return

    pyautogui.moveTo(abs_x, abs_y)
    pyautogui.click()


def dismiss_popup(driver: webdriver.Chrome) -> None:
    try:
        close_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME, "dark-close")))
        close_btn.click()
    except TimeoutException:
        pass


def login(driver: webdriver.Chrome, username: str, password: str) -> None:
    if not username or not password:
        raise ValueError("Username/password is empty. Fill PKO_USERNAME/PKO_PASSWORD in script.")

    username_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-input")))
    username_input.clear()
    username_input.send_keys(username)

    password_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-input.form-password")))
    password_input.clear()
    password_input.send_keys(password)

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                '//*[@id="__layout"]/div/div[2]/div[2]/header/div[1]/div/div/div[2]/div/div/div[2]/ul/li[1]/div',
            )
        )
    )
    login_button.click()


def clean_excel_value(value: Any) -> str:
    return INVALID_XML_RE.sub("", str(value))


def decode_body(raw_body: bytes, response_headers: dict[str, str]) -> tuple[str, str]:
    content_encoding = (response_headers.get("content-encoding") or "").lower()

    payload = raw_body
    decode_method = "utf8"

    try:
        if "gzip" in content_encoding:
            payload = gzip.decompress(raw_body)
            decode_method = "gzip+utf8"
        elif "deflate" in content_encoding:
            payload = zlib.decompress(raw_body)
            decode_method = "deflate+utf8"
        elif len(raw_body) >= 2 and raw_body[:2] == b"\x1f\x8b":
            payload = gzip.decompress(raw_body)
            decode_method = "magic-gzip+utf8"
    except Exception:
        payload = raw_body
        decode_method = "fallback-utf8"

    return payload.decode("utf-8", errors="replace"), decode_method


def parse_payload(decoded_text: str) -> tuple[str, Any]:
    try:
        parsed_json = json.loads(decoded_text)
        return "json", parsed_json
    except Exception:
        pass

    parsed_qs = {k: v[0] if v else "" for k, v in urllib.parse.parse_qs(decoded_text).items()}
    if parsed_qs:
        return "querystring", parsed_qs

    return "text", decoded_text


def build_request_record(request) -> dict[str, Any]:
    response = request.response
    response_headers = dict(response.headers) if response else {}
    request_headers = dict(request.headers) if request else {}
    raw_body = response.body if response and response.body else b""
    decoded_text, decode_method = decode_body(raw_body, response_headers)
    payload_type, payload_parsed = parse_payload(decoded_text)

    body_sha256 = hashlib.sha256(raw_body).hexdigest()
    body_b64 = base64.b64encode(raw_body).decode("ascii")

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": request.url or "",
        "method": request.method or "",
        "status_code": response.status_code if response else None,
        "request_headers": request_headers,
        "response_headers": response_headers,
        "response_content_type": response_headers.get("content-type", ""),
        "response_content_encoding": response_headers.get("content-encoding", ""),
        "body_length": len(raw_body),
        "body_sha256": body_sha256,
        "decode_method": decode_method,
        "payload_type": payload_type,
        "payload_parsed": payload_parsed,
        "body_text": decoded_text,
        "body_base64": body_b64,
    }


def build_summary_row(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("payload_parsed")
    dt_si = None
    dt_obj = None
    err_value = None
    if isinstance(payload, dict):
        dt_obj = payload.get("dt") if isinstance(payload.get("dt"), dict) else None
        dt_si = dt_obj.get("si") if isinstance(dt_obj, dict) else None
        err_value = payload.get("err")

    payload_for_csv = payload
    if isinstance(payload_for_csv, (dict, list)):
        payload_for_csv = json.dumps(payload_for_csv, ensure_ascii=False)
    elif payload_for_csv is None:
        payload_for_csv = ""
    else:
        payload_for_csv = str(payload_for_csv)

    summary = {
        "captured_at": record.get("captured_at"),
        "url": record.get("url"),
        "method": record.get("method"),
        "status_code": record.get("status_code"),
        "payload_type": record.get("payload_type"),
        "decode_method": record.get("decode_method"),
        "body_length": record.get("body_length"),
        "body_sha256": record.get("body_sha256"),
        "sid": None,
        "psid": None,
        "aw": None,
        "tw": None,
        "bl": None,
        "blb": None,
        "blab": None,
        "err": None,
        "raw_full": payload_for_csv,
    }

    if isinstance(dt_si, dict):
        summary["sid"] = dt_si.get("sid")
        summary["psid"] = dt_si.get("psid")
        summary["aw"] = dt_si.get("aw")
        summary["tw"] = dt_si.get("tw")
        summary["bl"] = dt_si.get("bl")
        summary["blb"] = dt_si.get("blb")
        summary["blab"] = dt_si.get("blab")
        # Flatten every dt.si key to its own CSV column.
        for key, value in dt_si.items():
            col_name = f"si_{key}"
            if isinstance(value, (dict, list)):
                summary[col_name] = json.dumps(value, ensure_ascii=False)
            else:
                summary[col_name] = value
    if isinstance(dt_obj, dict):
        for key, value in dt_obj.items():
            if key == "si":
                continue
            col_name = f"dt_{key}"
            if isinstance(value, (dict, list)):
                summary[col_name] = json.dumps(value, ensure_ascii=False)
            else:
                summary[col_name] = value

    if isinstance(payload, dict):
        if isinstance(err_value, (dict, list)):
            summary["err"] = json.dumps(err_value, ensure_ascii=False)
        else:
            summary["err"] = err_value

    return summary


def collect_spin_records(driver: webdriver.Chrome, seen_keys: set[str]) -> list[dict[str, Any]]:
    matched = 0
    new_records: list[dict[str, Any]] = []

    for request in driver.requests:
        if not request.response:
            continue
        request_url = request.url or ""
        if REQUEST_EXACT_FRAGMENT not in request_url:
            continue

        matched += 1
        record = build_request_record(request)
        unique_key = f"{record['url']}|{record['status_code']}|{record['body_sha256']}"
        if unique_key in seen_keys:
            continue

        seen_keys.add(unique_key)
        new_records.append(record)

    print(f"Matched requests by fragment '{REQUEST_EXACT_FRAGMENT}': {matched}, " f"new unique records: {len(new_records)}")
    return new_records


def save_data(new_records: list[dict[str, Any]], all_records: list[dict[str, Any]]) -> None:
    if not new_records:
        print("No new records in this batch.")
        return

    output_summary_csv = globals().get("OUTPUT_SUMMARY_CSV", "spin_summary.csv")
    summary_rows = [build_summary_row(r) for r in all_records]
    summary_df = pd.DataFrame(summary_rows).astype(str)

    try:
        summary_df.to_csv(output_summary_csv, index=False, encoding="utf-8-sig")
        print(f"Saved summary CSV: {output_summary_csv} (rows={len(summary_df)})")
    except PermissionError:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fallback_csv = output_summary_csv.replace(".csv", f"_{ts}.csv")
        summary_df.to_csv(fallback_csv, index=False, encoding="utf-8-sig")
        print(f"CSV is locked: {output_summary_csv}. " f"Saved fallback file: {fallback_csv} (rows={len(summary_df)})")


def run_click_loop(driver: webdriver.Chrome) -> list[dict[str, Any]]:
    global stop_requested
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    settle_seconds = max(CLICK_INTERVAL_SECONDS, RESPONSE_SETTLE_SECONDS)
    click_mode = CLICK_MODE

    all_records: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    hwnd = None
    if click_mode == "postmessage":
        if win32api is None or win32con is None or win32gui is None:
            print("Click mode postmessage requested, but pywin32 is unavailable. Fallback to pyautogui.")
            click_mode = "pyautogui"
        hwnd = get_chrome_window_handle()
        if click_mode == "postmessage" and hwnd:
            print(f"Click mode: postmessage (hwnd={hwnd})")
        elif click_mode == "postmessage":
            print("Click mode postmessage requested, but Chrome window handle not found. " "Fallback to pyautogui.")
            print(f"CHROME_TITLE_RE={CHROME_TITLE_RE}")
            visible_titles = list_visible_window_titles()
            if visible_titles:
                print("Visible window titles sample:")
                for t in visible_titles:
                    print(f"  - {t}")
            click_mode = "pyautogui"

    driver.requests.clear()
    click_point(CLICK_X1, CLICK_Y1, click_mode, hwnd)
    executed_clicks = 0
    next_progress_milestone = 10

    for i in range(1, CLICK_TIMES + 1):
        if stop_requested:
            print(f"Stop requested at loop {i}. Exiting click loop safely.")
            break

        click_point(CLICK_X2, CLICK_Y2, click_mode, hwnd)
        click_point(CLICK_X1, CLICK_Y1, click_mode, hwnd)
        time.sleep(settle_seconds)
        executed_clicks += 1
        progress_percent = int((executed_clicks * 100) / CLICK_TIMES)
        if progress_percent >= next_progress_milestone:
            print(f"..........Progress: {next_progress_milestone}% ({executed_clicks}/{CLICK_TIMES})")
            next_progress_milestone += 10

        if i % SAVE_EVERY == 0:
            batch = collect_spin_records(driver, seen_keys)
            all_records.extend(batch)
            save_data(batch, all_records)

    if executed_clicks % SAVE_EVERY != 0:
        final_batch = collect_spin_records(driver, seen_keys)
        all_records.extend(final_batch)
        save_data(final_batch, all_records)

    return all_records


def run_click_loop_async(driver: webdriver.Chrome) -> threading.Thread:
    global click_loop_thread, stop_requested, last_run_data
    stop_requested = False

    def _runner() -> None:
        global last_run_data
        last_run_data = run_click_loop(driver)

    click_loop_thread = threading.Thread(target=_runner, daemon=True)
    click_loop_thread.start()
    return click_loop_thread


def request_stop() -> None:
    global stop_requested
    stop_requested = True
    print("Stop requested=True")


# single-run block (kept for your line-by-line execution style)
driver = create_driver()
driver.get(BASE_URL)
# dismiss_popup(driver)
login(driver, PKO_USERNAME, PKO_PASSWORD)
driver.get(GAME_URL)
print(f"Start clicking at ({CLICK_X1},{CLICK_Y1}) and ({CLICK_X2},{CLICK_Y2}), " f"times={CLICK_TIMES}, save_every={SAVE_EVERY}")
all_data = run_click_loop(driver)
print(f"Done. Total records: {len(all_data)}")

# manual close when finished in console:
# driver.quit()
