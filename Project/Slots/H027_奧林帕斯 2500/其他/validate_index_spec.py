"""Interactive smoke test for H027 index.html specification controls."""

from __future__ import annotations

import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    url = f"{(ROOT / 'index.html').as_uri()}?version=0.0.0.0&config=92A"
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--allow-file-access-from-files")
    options.set_capability("ms:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Edge(options=options)
    try:
        wait = WebDriverWait(driver, 20)
        driver.get(url)
        wait.until(lambda page: page.find_element(By.ID, "messageBar").text.startswith("Ready"))

        cell_metrics = driver.execute_script(
            """
            const cells = [...document.querySelectorAll('#board .cell')].slice(0, 2);
            const rects = cells.map((cell) => cell.getBoundingClientRect());
            return {
              width: rects[0].width,
              height: rects[0].height,
              gap: rects[1].left - rects[0].right,
              boxSizing: getComputedStyle(cells[0]).boxSizing,
            };
            """
        )
        assert cell_metrics["boxSizing"] == "border-box"
        assert cell_metrics["width"] <= 62.01
        assert abs(cell_metrics["width"] - cell_metrics["height"]) < 0.01
        assert abs(cell_metrics["gap"] / cell_metrics["width"] - 4 / 62) < 0.001

        driver.set_window_size(420, 900)
        responsive_metrics = driver.execute_script(
            """
            const board = document.querySelector('#board').getBoundingClientRect();
            const cells = [...document.querySelectorAll('#board .cell')];
            const first = cells[0].getBoundingClientRect();
            const second = cells[1].getBoundingClientRect();
            const nextRow = cells[6].getBoundingClientRect();
            return {
              squareError: Math.abs(first.width - first.height),
              columnStep: (second.left - first.left) / board.width,
              rowStep: (nextRow.top - first.top) / board.width,
              boardRatio: board.height / board.width,
            };
            """
        )
        assert responsive_metrics["squareError"] < 0.01
        assert abs(responsive_metrics["columnStep"] - 66 / 392) < 0.001
        assert abs(responsive_metrics["rowStep"] - 66 / 392) < 0.001
        assert abs(responsive_metrics["boardRatio"] - 326 / 392) < 0.001

        combined = Select(driver.find_element(By.ID, "demogameConfigSelect"))
        assert combined.first_selected_option.text == "92A-Oldhand"
        assert [option.text for option in combined.options] == [
            "92A-Newbie",
            "92A-Oldhand",
            "94A-Newbie",
            "94A-Oldhand",
        ]
        assert driver.execute_script("return window.DEMOGAME_CARD_SYSTEM_ENABLED") is False

        driver.find_element(By.ID, "cardSystemInput").click()
        driver.find_element(By.ID, "debugModeInput").click()
        card = Select(driver.find_element(By.ID, "cardRangeSelect"))
        assert len(card.options) > 1

        rng = driver.find_element(By.ID, "rngInput")
        rng.send_keys("0 0 0 0 0 0")
        wait.until(lambda page: page.find_element(By.ID, "cardRangeSelect").get_attribute("disabled") is not None)

        rng.clear()
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}))", rng)
        card = Select(driver.find_element(By.ID, "cardRangeSelect"))
        card.select_by_index(1)
        wait.until(lambda page: page.find_element(By.ID, "rngInput").get_attribute("disabled") is not None)

        card.select_by_index(0)
        driver.find_element(By.ID, "cardSystemInput").click()
        driver.find_element(By.ID, "spinBtn").click()
        wait.until(lambda page: page.find_element(By.ID, "roundCountValue").text == "1")
        wait.until(lambda page: page.find_element(By.ID, "spinBtn").get_attribute("disabled") is None)

        severe = [entry for entry in driver.get_log("browser") if entry.get("level") == "SEVERE"]
        result = {
            "model": combined.first_selected_option.text,
            "card_options": len(card.options),
            "rounds": driver.find_element(By.ID, "roundCountValue").text,
            "message": driver.find_element(By.ID, "messageBar").text,
            "cell_metrics": cell_metrics,
            "responsive_metrics": responsive_metrics,
            "severe_console_entries": severe,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if severe:
            raise AssertionError("Browser console contains severe errors")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
