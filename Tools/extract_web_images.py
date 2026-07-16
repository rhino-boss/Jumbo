"""Load a dynamic web page in Chrome and save image network responses."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options


IMAGE_MIME_EXTENSIONS = {
    "image/avif": ".avif",
    "image/bmp": ".bmp",
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
    "image/x-icon": ".ico",
}


def safe_name(url: str, mime_type: str, body: bytes) -> str:
    parsed = urlparse(url)
    raw_name = unquote(Path(parsed.path).name) or "image"
    raw_name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_name).strip("._") or "image"
    ext = Path(raw_name).suffix.lower()
    expected_ext = IMAGE_MIME_EXTENSIONS.get(mime_type.split(";", 1)[0].lower(), "")
    if not ext or len(ext) > 6:
        raw_name += expected_ext
    digest = hashlib.sha256(body).hexdigest()[:10]
    stem = Path(raw_name).stem[:100] or "image"
    suffix = Path(raw_name).suffix or expected_ext or ".bin"
    return f"{stem}_{digest}{suffix}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--seconds", type=int, default=45)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=options)
    responses: dict[str, dict[str, str]] = {}
    saved: dict[str, dict[str, object]] = {}
    errors: list[dict[str, str]] = []
    network_responses: list[dict[str, object]] = []
    try:
        driver.execute_cdp_cmd("Network.enable", {"maxTotalBufferSize": 200_000_000})
        driver.get(args.url)
        deadline = time.monotonic() + args.seconds
        idle_since = time.monotonic()
        while time.monotonic() < deadline:
            logs = driver.get_log("performance")
            if logs:
                idle_since = time.monotonic()
            for entry in logs:
                message = json.loads(entry["message"])["message"]
                method = message["method"]
                params = message.get("params", {})
                if method == "Network.responseReceived":
                    response = params["response"]
                    mime_type = response.get("mimeType", "").split(";", 1)[0].lower()
                    resource_type = params.get("type", "")
                    network_responses.append(
                        {
                            "url": response.get("url", ""),
                            "status": response.get("status"),
                            "mime_type": mime_type,
                            "resource_type": resource_type,
                        }
                    )
                    if mime_type.startswith("image/") or resource_type == "Image":
                        responses[params["requestId"]] = {
                            "url": response.get("url", ""),
                            "mime_type": mime_type,
                        }
                elif method == "Network.loadingFinished":
                    request_id = params["requestId"]
                    meta = responses.pop(request_id, None)
                    if not meta:
                        continue
                    try:
                        result = driver.execute_cdp_cmd(
                            "Network.getResponseBody", {"requestId": request_id}
                        )
                        body = result["body"]
                        data = base64.b64decode(body) if result.get("base64Encoded") else body.encode()
                        if not data:
                            continue
                        digest = hashlib.sha256(data).hexdigest()
                        if digest in saved:
                            continue
                        filename = safe_name(meta["url"], meta["mime_type"], data)
                        (args.output_dir / filename).write_bytes(data)
                        saved[digest] = {
                            "file": filename,
                            "url": meta["url"],
                            "mime_type": meta["mime_type"],
                            "bytes": len(data),
                        }
                    except WebDriverException as exc:
                        errors.append({"url": meta["url"], "error": str(exc)[:500]})
            if saved and time.monotonic() - idle_since > 8:
                break
            time.sleep(0.5)

        driver.save_screenshot(str(args.output_dir / "page_screenshot.png"))
    finally:
        driver.quit()

    manifest = {
        "source_url": args.url,
        "image_count": len(saved),
        "images": list(saved.values()),
        "errors": errors,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output_dir / "network_responses.json").write_text(
        json.dumps(network_responses, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Saved {len(saved)} unique images to {args.output_dir}")
    for item in saved.values():
        print(f"{item['file']}\t{item['bytes']} bytes\t{item['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
