#%%
import xlwings as xw
import json

excel_path = r'D:\IGame\H017\Lucky Neko.xlsx'
js_path = r'D:\IGame\H017\data.js'
js_path1 = r'D:\IGame\H017\data.js'
def extract_range(sheet, range_str, key_name):
    """抓取指定范围的数据并转置"""
    val = sheet.range(range_str).value
    if not isinstance(val[0], list):
        val = [val]
    val = [list(col) for col in zip(*val)]
    
    # 如果转置后每个元素都是单元素列表，则展平为一维向量
    if all(isinstance(col, list) and len(col) == 1 for col in val):
        val = [col[0] for col in val]
    
    return {key_name: val}

def extract_range_no_transpose(sheet, range_str, key_name):
    """抓取指定范围的数据，不转置"""
    val = sheet.range(range_str).value
    if not isinstance(val, list):
        val = [val]
    elif not isinstance(val[0], list):
        val = [val]
    return {key_name: val}

app = xw.App(visible=False)
wb = app.books.open(excel_path)

output = {}

# Overview sheet
sht1 = wb.sheets['Overview']
output.update(extract_range_no_transpose(sht1, 'C32:F42', 'linkpoint'))
# BaseGameSymbol sheet
sht2 = wb.sheets['Base Game Symbol']
# Symbol 1-5
output.update(extract_range(sht2, 'T4:Z124', 'BaseGameSymbol1'))
output.update(extract_range(sht2, 'AB4:AH124', 'BaseGameSymbolWeight1'))
output.update(extract_range(sht2, 'B33:G47', 'BaseGameMegaWay1'))
output.update(extract_range(sht2, 'B50:B62', 'BaseGameMY1'))
output.update(extract_range(sht2, 'A65:B72', 'BaseGame1PostC1'))
output.update(extract_range(sht2, 'AK5:AQ30', 'BaseGame1Drop1'))
output.update(extract_range(sht2, 'AK34:AQ59', 'BaseGame1Drop2'))
output.update(extract_range(sht2, 'AK63:AQ88', 'BaseGame1Drop3'))
output.update(extract_range(sht2, 'AK92:AQ117', 'BaseGame1Drop4'))
output.update(extract_range(sht2, 'AK121:AQ146', 'BaseGame1Drop5'))



output.update(extract_range(sht2, 'BM4:BS124', 'BaseGameSymbol2'))
output.update(extract_range(sht2, 'BU4:CA124', 'BaseGameSymbolWeight2'))
output.update(extract_range(sht2, 'AU33:AZ47', 'BaseGameMegaWay2'))
output.update(extract_range(sht2, 'AU50:AU62', 'BaseGameMY2'))
output.update(extract_range(sht2, 'AT65:AU72', 'BaseGame2PostC1'))
output.update(extract_range(sht2, 'CD5:CJ30', 'BaseGame2Drop1'))
output.update(extract_range(sht2, 'CD34:CJ59', 'BaseGame2Drop2'))
output.update(extract_range(sht2, 'CD63:CJ88', 'BaseGame2Drop3'))
output.update(extract_range(sht2, 'CD92:CJ117', 'BaseGame2Drop4'))
output.update(extract_range(sht2, 'CD121:CJ146', 'BaseGame2Drop5'))
# BaseGameSymbolDrop sheet
sht4 = wb.sheets['Description']

output.update(extract_range(sht4, 'D5:D6', 'ReelWeight'))
output.update(extract_range(sht4, 'G5:G7', 'FreeReelWeight'))
output.update(extract_range(sht4, 'D18:D20', 'FreeTriggerReel'))

sht5 = wb.sheets['Free Game Symbol']
output.update(extract_range(sht5, 'T4:Z124', 'FreeGameSymbol1'))
output.update(extract_range(sht5, 'AB4:AH124', 'FreeGameSymbolWeight1'))
output.update(extract_range(sht5, 'B33:G47', 'FreeGameMegaWay1'))
output.update(extract_range(sht5, 'B50:B62', 'FreeGameMY1'))
output.update(extract_range(sht5, 'A65:B72', 'FreeGame1PostC1'))
output.update(extract_range(sht5, 'AK5:AQ30', 'FreeGame1Drop1'))
output.update(extract_range(sht5, 'AK34:AQ59', 'FreeGame1Drop2'))
output.update(extract_range(sht5, 'AK63:AQ88', 'FreeGame1Drop3'))
output.update(extract_range(sht5, 'AK92:AQ117', 'FreeGame1Drop4'))
output.update(extract_range(sht5, 'AK121:AQ146', 'FreeGame1Drop5'))



output.update(extract_range(sht5, 'BM4:BS124', 'FreeGameSymbol2'))
output.update(extract_range(sht5, 'BU4:CA124', 'FreeGameSymbolWeight2'))
output.update(extract_range(sht5, 'AU33:AZ47', 'FreeGameMegaWay2'))
output.update(extract_range(sht5, 'AU50:AU62', 'FreeGameMY2'))
output.update(extract_range(sht5, 'AU65:AU72', 'FreeGame2PostC1'))
output.update(extract_range(sht5, 'CD5:CJ30', 'FreeGame2Drop1'))
output.update(extract_range(sht5, 'CD34:CJ59', 'FreeGame2Drop2'))
output.update(extract_range(sht5, 'CD63:CJ88', 'FreeGame2Drop3'))
output.update(extract_range(sht5, 'CD92:CJ117', 'FreeGame2Drop4'))
output.update(extract_range(sht5, 'CD121:CJ146', 'FreeGame2Drop5'))

output.update(extract_range(sht5, 'DF4:DL124', 'FreeGameSymbol3'))
output.update(extract_range(sht5, 'DN4:DT124', 'FreeGameSymbolWeight3'))
output.update(extract_range(sht5, 'CN33:CS47', 'FreeGameMegaWay3'))
output.update(extract_range(sht5, 'CN50:CN62', 'FreeGameMY3'))
output.update(extract_range(sht5, 'CM65:CN72', 'FreeGame3PostC1'))
output.update(extract_range(sht5, 'DW5:EC30', 'FreeGame3Drop1'))
output.update(extract_range(sht5, 'DW34:EC59', 'FreeGame3Drop2'))
output.update(extract_range(sht5, 'DW63:EC88', 'FreeGame3Drop3'))
output.update(extract_range(sht5, 'DW92:EC117', 'FreeGame3Drop4'))
output.update(extract_range(sht5, 'DW121:EC146', 'FreeGame3Drop5'))



#sht7 = wb.sheets['工作表1']
#output.update(extract_range(sht7, 'B1:B59', 'baseredraw'))
#output.update(extract_range(sht7, 'C1:C58', 'freeredraw'))
#output.update(extract_range(sht7, 'A1:A57', 'multipleRange'))
#output.update(extract_range(sht7, 'E1:E59', 'baseredrawB'))
#output.update(extract_range(sht7, 'F1:F58', 'freeredrawB'))
#output.update(extract_range(sht7, 'P1:P58', 'basemultiple'))
#output.update(extract_range(sht7, 'Q1:Q58', 'freemultiple'))

wb.close()
app.quit()

# 将数据写入 data.js
with open(js_path, 'w', encoding='utf-8') as f:
    f.write('const data = ')
    json.dump(output, f, indent=2, ensure_ascii=False)
    f.write(';')
with open(js_path1, 'w', encoding='utf-8') as f:
    f.write('const data = ')
    json.dump(output, f, indent=2, ensure_ascii=False)
    f.write(';')
print(f'数据已保存到 {js_path}')
# %%
