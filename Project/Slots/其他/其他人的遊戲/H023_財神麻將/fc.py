#%%
import xlwings as xw

excel_path = r'D:\IGame\BMM送驗\101009\H023191R.xlsx'
js_path = r'D:\IGame\BMM送驗\101009\data.js'

app = xw.App(visible=False)
wb = app.books.open(excel_path)

output = {}

# 0. baseGameSurface: 保留相容性參數 (已不再使用，但需要提供)
output['baseGameSurface'] = [1.0, 0.0]  # BASE GAME全部使用高表

# 1. linkpoint: Overview B34:D42 (9x3 矩陣，M1~M9分數)
sht1 = wb.sheets['Overview']
output['linkpoint'] = [[50,125,250],[40,100,200],[30,75,150],[25,50,75],[15,25,60],[15,25,60],[10,20,50],[5,15,30],[5,15,30]]


# 6. baseGameHighSymbolWeight: Symbol Weight B5:F404

output['baseGameHighSymbolWeight'] = [ [1.0]*200 for _ in range(5) ]

# 7. baseGameLowSymbolWeight: Symbol Weight I5:M404

output['baseGameLowSymbolWeight'] = [ [1.0]*200 for _ in range(5) ]

# 8. freeGameHighSymbolWeight: Symbol Weight P5:T404

output['freeGameHighSymbolWeight'] = [ [1.0]*200 for _ in range(5) ]

# 9. freeGameLowSymbolWeight: Symbol Weight W5:AA404

output['freeGameLowSymbolWeight'] = [ [1.0]*200 for _ in range(5) ]

# 11. baseGameSymbolHigh: Base Game Symbol - High Q4:U403
sht4 = wb.sheets['Base Game Symbol']
val11 = sht4.range('Q4:U203').value
if not isinstance(val11[0], list):
    val11 = [val11]
val11 = [list(col) for col in zip(*val11)]
output['baseGameSymbolHigh'] = val11

# 13. baseGameSymbolLow: Base Game Symbol - Low Q4:U403
sht5 = wb.sheets['Base Game Symbol']
val13 = sht5.range('Q4:U203').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseGameSymbolLow'] = val13

val13 = sht5.range('AE3:AI23').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropWeights1st'] = val13

val13 = sht5.range('AE27:AI47').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropWeights2nd'] = val13

val13 = sht5.range('AE51:AI71').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropWeights3rd'] = val13

val13 = sht5.range('AE75:AI95').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropWeights4th'] = val13

val13 = sht5.range('AM3:AM11').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseMyConvertWeights'] = val13

val13 = sht5.range('AE3:AI23').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropLowWeights1st'] = val13

val13 = sht5.range('AE27:AI47').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropLowWeights2nd'] = val13

val13 = sht5.range('AE51:AI71').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropLowWeights3rd'] = val13

val13 = sht5.range('AE75:AI95').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseDropLowWeights4th'] = val13

val13 = sht5.range('AM3:AM11').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseMyConvertLowWeights'] = val13
##

# 15. freeGameSymbolHighA: Free Game Symbol - High - A Q4:U403
sht5 = wb.sheets['Free Game Symbol']
val15 = sht5.range('Q4:U203').value
if not isinstance(val15[0], list):
    val15 = [val15]
val15 = [list(col) for col in zip(*val15)]
output['freeGameSymbolHighA'] = val15

val13 = sht5.range('AE3:AI23').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeHighDropWeights1st'] = val13

val13 = sht5.range('AE27:AI47').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeHighDropWeights2nd'] = val13

val13 = sht5.range('AE51:AI71').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeHighDropWeights3rd'] = val13

val13 = sht5.range('AE75:AI95').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeHighDropWeights4th'] = val13

val13 = sht5.range('AM4:AM12').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeHighMyConvertWeights'] = val13


# 16. freeGameSymbolHighA: Free Game Symbol - High - A Q4:U403
sht5 = wb.sheets['Free Game Symbol']
val15 = sht5.range('Q4:U203').value
if not isinstance(val15[0], list):
    val15 = [val15]
val15 = [list(col) for col in zip(*val15)]
output['freeGameSymbolLow'] = val15

val13 = sht5.range('AE3:AI23').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeLowDropWeights1st'] = val13

val13 = sht5.range('AE27:AI47').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeLowDropWeights2nd'] = val13

val13 = sht5.range('AE51:AI71').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeLowDropWeights3rd'] = val13

val13 = sht5.range('AE75:AI95').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeLowDropWeights4th'] = val13

val13 = sht5.range('AM4:AM12').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['freeLowMyConvertWeights'] = val13

# 移除不需要的 batch_targets 處理
# - freeGameSymbolLow 已在第148行處理
# - RANDOMWILD 功能已移除，不需要相關參數
# - buyFeature 相關參數不在新參數清單中

wb.close()
app.quit()

# 驗證參數維度
print("=== 參數維度驗證 ===")
print(f"linkpoint: {len(output['linkpoint'])}x{len(output['linkpoint'][0])} (應為 9x3)")
print(f"baseGameHighSymbolWeight: {len(output['baseGameHighSymbolWeight'])}x{len(output['baseGameHighSymbolWeight'][0])} (應為 5xN)")

# 檢查掉落權重矩陣 (應為 21x5)
drop_weights = ['baseDropWeights1st', 'baseDropWeights2nd', 'baseDropWeights3rd', 'baseDropWeights4th']
for dw in drop_weights:
    if dw in output:
        print(f"{dw}: {len(output[dw])}x{len(output[dw][0])} (應為 21x5)")

# 檢查MY轉換權重 (應為 9x1)
my_weights = ['baseMyConvertWeights', 'freeHighMyConvertWeights', 'freeLowMyConvertWeights']
for mw in my_weights:
    if mw in output:
        print(f"{mw}: {len(output[mw])} (應為 9)")

# 處理None值
def clean_none(val):
    if isinstance(val, list):
        return [clean_none(x) for x in val]
    return val if val is not None else None

with open(js_path, 'w', encoding='utf-8') as f:
    for var, val in output.items():
        val = clean_none(val)
        f.write(f"const {var} = {val};\n\n")

print(f'已寫出 {js_path}')

# %%
