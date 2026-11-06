#%%
import xlwings as xw
import os

# 使用完整的絕對路徑並檢查文件是否存在
excel_file_path = r'D:\IGame\金埃及\卡片系統\H016193.xlsx'
js_output_path = r'D:\IGame\金埃及\卡片系統\data.js'

# 檢查文件是否存在
if not os.path.exists(excel_file_path):
    print(f"錯誤：找不到Excel文件: {excel_file_path}")
    print("目錄中的文件:")
    for f in os.listdir(os.path.dirname(excel_file_path)):
        if f.endswith('.xlsx'):
            print(f"  {f}")
    exit(1)

app = xw.App(visible=False)
wb = app.books.open(excel_file_path)

output = {}

# 1. linkpoint: Overview D36:F43
sht1 = wb.sheets['Overview']
val1 = sht1.range('D41:F48').value
if not isinstance(val1[0], list):
    val1 = [val1]
val1 = [list(col) for col in zip(*val1)]
output['linkpoint'] = val1

# 2. baseGameSurface: Description F5:F6
sht2 = wb.sheets['Description']
val2 = sht2.range('F5:F6').value
if not isinstance(val2, list):
    val2 = [val2]
output['baseGameSurface'] = [1,0]

# 3. freeGameSurface: Description C35:E38
val3 = sht2.range('C35:F45').value
if not isinstance(val3[0], list):
    val3 = [val3]
val3 = [list(col) for col in zip(*val3)]
output['freeGameSurface'] = [[0,3,4,5,6,10],[10,7,6,5,4,0],[1,0,0,0,0,0],[0,0,0,0,0,1]]

# 4. freeGameHighSurface: Description E41:E44
val4 = sht2.range('E31:E34').value
if not isinstance(val4, list):
    val4 = [val4]
output['freeGameHighSurface'] = val4

# 5. buyFeatureSurface: Description C76:E79
val5 = sht2.range('C85:E95').value
if not isinstance(val5[0], list):
    val5 = [val5]
val5 = [list(col) for col in zip(*val5)]
output['buyFeatureSurface'] = [[0,3,4,5,6,10],[10,7,6,5,4,0],[1,0,0,0,0,0]]

# 6. baseGameHighSymbolWeight: Symbol Weight B5:F404
sht3 = wb.sheets['Symbol Weight']
val6 = sht3.range('B5:F404').value
if not isinstance(val6[0], list):
    val6 = [val6]
val6 = [list(col) for col in zip(*val6)]
output['baseGameHighSymbolWeight'] = val6

# 7. baseGameLowSymbolWeight: Symbol Weight I5:M404
val7 = sht3.range('I5:M404').value
if not isinstance(val7[0], list):
    val7 = [val7]
val7 = [list(col) for col in zip(*val7)]
output['baseGameLowSymbolWeight'] = val7

# 8. freeGameHighSymbolWeight: Symbol Weight P5:T404
val8 = sht3.range('P5:T404').value
if not isinstance(val8[0], list):
    val8 = [val8]
val8 = [list(col) for col in zip(*val8)]
output['freeGameHighSymbolWeight'] = val8

# 9. freeGameLowSymbolWeight: Symbol Weight W5:AA404
val9 = sht3.range('W5:AA404').value
if not isinstance(val9[0], list):
    val9 = [val9]
val9 = [list(col) for col in zip(*val9)]
output['freeGameLowSymbolWeight'] = val9

# 10. buyFeatureSymbolWeight: Symbol Weight AD5:AH404
val10 = sht3.range('AD5:AH404').value
if not isinstance(val10[0], list):
    val10 = [val10]
val10 = [list(col) for col in zip(*val10)]
output['buyFeatureSymbolWeight'] = val10

val10 = sht3.range('AK5:AO404').value
if not isinstance(val10[0], list):
    val10 = [val10]
val10 = [list(col) for col in zip(*val10)]
output['SuperbuyFeatureSymbolWeight'] = val10
# 11. baseGameSymbolHigh: Base Game Symbol - High Q4:U403
sht4 = wb.sheets['Base Game Symbol - High']
val11 = sht4.range('Q4:U403').value
if not isinstance(val11[0], list):
    val11 = [val11]
val11 = [list(col) for col in zip(*val11)]
output['baseGameSymbolHigh'] = val11

# 12. baseGameHighRandomwild: Base Game Symbol - High AC3:AD6
val12 = sht4.range('AC3:AD6').value
if not isinstance(val12[0], list):
    val12 = [val12]
val12 = [list(col) for col in zip(*val12)]
output['baseGameHighRandomwild'] = val12

# 13. baseGameSymbolLow: Base Game Symbol - Low Q4:U403
sht5 = wb.sheets['Base Game Symbol - Low']
val13 = sht5.range('Q4:U403').value
if not isinstance(val13[0], list):
    val13 = [val13]
val13 = [list(col) for col in zip(*val13)]
output['baseGameSymbolLow'] = val13

# 14. baseGameLowRandomwild: Base Game Symbol - Low AC3:AD6
val14 = sht5.range('AC3:AD6').value
if not isinstance(val14[0], list):
    val14 = [val14]
val14 = [list(col) for col in zip(*val14)]
output['baseGameLowRandomwild'] = val14

# 15. freeGameSymbolHighA: Free Game Symbol - High - A Q4:U403
sht6 = wb.sheets['Free Game Symbol - High - A']
val15 = sht6.range('Q4:U403').value
if not isinstance(val15[0], list):
    val15 = [val15]
val15 = [list(col) for col in zip(*val15)]
output['freeGameSymbolHighA'] = val15

# 16. freeGameHighRandomwildA: Free Game Symbol - High - A AC3:AD6
val16 = sht6.range('AC3:AD6').value
if not isinstance(val16[0], list):
    val16 = [val16]
val16 = [list(col) for col in zip(*val16)]
output['freeGameHighRandomwildA'] = val16

# 17. Free Game Symbol - High - K
shtK = wb.sheets['Free Game Symbol - High - K']
valK1 = shtK.range('Q4:U403').value
if not isinstance(valK1[0], list):
    valK1 = [valK1]
valK1 = [list(col) for col in zip(*valK1)]
output['freeGameSymbolHighK'] = valK1

valK2 = shtK.range('AC3:AD6').value
if not isinstance(valK2[0], list):
    valK2 = [valK2]
valK2 = [list(col) for col in zip(*valK2)]
output['freeGameHighRandomwildK'] = valK2

# 18. Free Game Symbol - High - Q
shtQ = wb.sheets['Free Game Symbol - High - Q']
valQ1 = shtQ.range('Q4:U403').value
if not isinstance(valQ1[0], list):
    valQ1 = [valQ1]
valQ1 = [list(col) for col in zip(*valQ1)]
output['freeGameSymbolHighQ'] = valQ1

valQ2 = shtQ.range('AC3:AD6').value
if not isinstance(valQ2[0], list):
    valQ2 = [valQ2]
valQ2 = [list(col) for col in zip(*valQ2)]
output['freeGameHighRandomwildQ'] = valQ2

# 19. Free Game Symbol - High - J
shtJ = wb.sheets['Free Game Symbol - High - J']
valJ1 = shtJ.range('Q4:U403').value
if not isinstance(valJ1[0], list):
    valJ1 = [valJ1]
valJ1 = [list(col) for col in zip(*valJ1)]
output['freeGameSymbolHighJ'] = valJ1

valJ2 = shtJ.range('AC3:AD6').value
if not isinstance(valJ2[0], list):
    valJ2 = [valJ2]
valJ2 = [list(col) for col in zip(*valJ2)]
output['freeGameHighRandomwildJ'] = valJ2

#
shtJ = wb.sheets['Super Free Game Symbol']
valJ1 = shtJ.range('Q4:U403').value
if not isinstance(valJ1[0], list):
    valJ1 = [valJ1]
valJ1 = [list(col) for col in zip(*valJ1)]
output['superfreeGameSymbol'] = valJ1

valJ2 = shtJ.range('AC3:AD6').value
if not isinstance(valJ2[0], list):
    valJ2 = [valJ2]
valJ2 = [list(col) for col in zip(*valJ2)]
output['superfreeGameRandomwild'] = valJ2


batch_targets = [
    # sheet,  Q4:U403變數名,            AC3:AD6變數名
    ('Free Game Symbol - Low', 'freeGameSymbolLow', 'freeGameLowRandomwild'),
    ('Buy Feature Symbol',     'buyFeatureSymbol',  'buyFeatureRandomwild'),
]

# 首先列出所有可用的工作表
print("Excel文件中的工作表:")
for sheet in wb.sheets:
    print(f"  {sheet.name}")

for sheet_name, var_name1, var_name2 in batch_targets:
    try:
        sht = wb.sheets[sheet_name]
        print(f"正在處理工作表: {sheet_name}")
        
        val1 = sht.range('Q4:U403').value
        if not isinstance(val1[0], list):
            val1 = [val1]
        val1 = [list(col) for col in zip(*val1)]
        output[var_name1] = val1

        val2 = sht.range('AC3:AD6').value
        if not isinstance(val2[0], list):
            val2 = [val2]
        val2 = [list(col) for col in zip(*val2)]
        output[var_name2] = val2
        
    except Exception as e:
        print(f"錯誤：無法訪問工作表 '{sheet_name}': {e}")
        continue
    
wb.close()
app.quit()

# 處理None值
def clean_none(val):
    if isinstance(val, list):
        return [clean_none(x) for x in val]
    return val if val is not None else None

with open(js_output_path, 'w', encoding='utf-8') as f:
    for var, val in output.items():
        val = clean_none(val)
        f.write(f"const {var} = {val};\n\n")

print(f'已寫出 {js_output_path}')

# %%
