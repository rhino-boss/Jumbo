# %%

import xlwings as xw


# %%


li_jp = ["030404D"]
li_multiplier = [1, 2, 5, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 150, 200, 300, 500, 1000, 1500, 3000, 5000, 7500, 10000, 15000, 25000]


# 連到已開啟的 Excel 與活頁簿
app = xw.apps.active  # 若沒有開著的 Excel 會是 None
if app is None:
    raise RuntimeError("請先打開一個 Excel 活頁簿再執行這支程式。")

wb = xw.books["H005197D.xlsx"]  # 改

sht = wb.sheets["Overview"]
sht2 = wb.sheets["FB_Description"]  # 改

for i in li_jp:
    for j in li_multiplier:
        version = "A5"  # 改
        multiplier = "G5"  # 改
        major_chance_weight = "B5"

        sht.range(version).value = i
        sht.range(multiplier).value = j
        wb.app.calculate()

        print(f"JP: {sht.range(version).value}, Multiplier: {sht.range(multiplier).value}, Major Chance Weight: {sht2.range(major_chance_weight).value}")

print(f"已將 {sht.name}!A1 由 {0} 改為 {0}")


# %%
