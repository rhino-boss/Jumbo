# Repository Guidelines

Contributor guide for the Fortune Gems math simulation suite. Keep updates concise, reproducible, and in sync with shared Excel assets.

## Project Structure & Module Organization
- Root scripts: `FortuneGems.py` (main Monte Carlo batches) and `FortuneGems_yv.py` (variant flow); adjust both when logic overlaps.
- Shared helpers: `common/` (`DataExport.py`, `InputSettings.py`, `Lines.xlsx`). Minimize new dependencies.
- Analysis: `CommonPlot/` for matplotlib checks; run from repo root so bundled Excel paths resolve.
- Assets: `Weight.xlsx`, `StripTable.xlsx`, `Pays.xlsx`; simulation outputs are `FortuneGems_sim*.xls` (not version-controlled).

## Build, Run, and Plot
- Python 3.10+ on Windows; create venv: `python -m venv .venv` and activate it.
- Install deps: `python -m pip install numpy numba pandas matplotlib openpyxl pytest`.
- Run sim: `python FortuneGems.py` and choose batch options in the tkinter dialog; review the generated workbook.
- Plot review: e.g., `python CommonPlot/multiplier_line.py` using bundled Excel inputs; update hard-coded paths only if folders move.

## Coding Style & Naming Conventions
- Follow PEP 8, four-space indents, snake_case functions; symbol constants stay uppercase per `DefineSymbols.py`.
- Keep docstrings short and specific for reel/payline loops; prefer NumPy vectorization or numba-friendly loops with minimal branching.
- Use `pathlib.Path` for new I/O; keep Excel sheet names CamelCase for `GetFromExcel` lookups.

## Testing Guidelines
- Framework: `pytest`. Add cases under `tests/`; place fixtures in `tests/data` (trimmed workbooks for determinism).
- Cover Excel parsing, RNG seeding, reward aggregation; track baseline RTP/trigger counts from current exports and assert tolerances.
- Document seeds, batch sizes, and toggled modes in docstrings or PR notes for reproducibility.

## Commit & Pull Request Guidelines
- Commit style: compact summaries, optional initials (e.g., `math: adjust wild table (YV)`).
- PRs should describe affected Excel sheets/plots, list run settings, headline metrics, and attach visuals when plots change.
- Request maths and tooling reviewers when touching `common/` helpers or shared spreadsheets.

## Data & Asset Management
- Version spreadsheet replacements with date-stamped names; archive superseded files in-repo.
- Exclude generated exports (`FortuneGems_sim*.xls`) via `.gitignore`.
- Validate workbook headers via `common.DataExport.GetFromExcel` in a Python shell before long runs.
- Keep partner odds/credentials outside the repo (use secure storage or env vars).

## 最新配置說明（同步 2025-11-19 版本差異）
- 強制倍數系統：InputSettings 新增「Force Multiplier」勾選。強制模式依 `Weight.xlsx::Multiplier_weight` 抽取倍率區間；押注 250 時整包 10 次 BaseGame 以同一區間判定，最多重試 10,000 次，命中才記錄統計。`arr_output_data[20]` 紀錄目標倍率區間抽取次數。
- 匯出檔名：含日期與模擬次數，強制模式加 `FM` 後綴，例如 `SG_sim<bet>_FM_<MMDD>_<rounds>_`。
- 報表倍率區間：`thresholdMultiple` 改為 `[0,0,1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50,60,70,80,90,100,120,140,160,180,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900,950,1000,2000,3000,4000,5000,6000,7000,9999]`。
- R4 重轉紀錄：`R4_result==0` 且該局有贏分時累計 `WinsReport[7]`；強制重試失敗會還原快照不計入。
- nudge 與 R4 統計：`arr_output_data[5]` 為 R4 結果，`arr_output_data[6]` 為 nudge 次數，`arr_output_data[7~17]` 為 nudge 倍數分布；調整 `nudge_num`、`nudge_multiplier` 權重時同步檢查分布與 DataExport。
- 仍請在調整權重後先做小批量驗證，再跑長模擬；Excel 報表以基礎遊戲贏分區間 `arr_output_data[18]` 為主，免費遊戲預留 `arr_output_data[19]`。
