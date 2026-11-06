# %% import


import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import sys
import os

# sys.path
# os.getcwd()
os.chdir("c:\\Users\\rhinshen\\Mine\\Employee_0419\\3_Tools\\Code")


# %%

# names = os.listdir(r"C:\Users\rhinshen\Mine\Employee_0419\9_Else (其他)\1_插件\230830_LYF 8000 活動")
# for i, na in enumerate(names):
#     names[i] = names[i][:-5]

# names

# %%

# dirr = r"C:/Users/rhinshen/Mine/Employee_0419/9_Else (其他)/1_插件/230830_LYF 8000 活動/"

# data = pd.DataFrame([])
# for i, na in enumerate(names):
#     print(i, na)
#     data = pd.concat([data, pd.read_excel(dirr + names[i] + ".xlsx", index_col=0)], axis=1)

# data.columns = names
# interval = list(data.index)
# interval[0] = "0< X <0"

# interval = [i.split("<")[0] for i in interval]
# data.index = interval
# data.to_excel("LYF8000.xlsx")

# data

# %%


aa = [
    4000.00,
    1777.78,
    842.11,
    470.59,
    363.64,
    2000.00,
    888.89,
    421.05,
    235.29,
    181.82,
    1333.33,
    592.59,
    280.70,
    156.86,
    121.21,
    666.67,
    296.30,
    140.35,
    78.43,
    60.61,
    400.00,
    177.78,
    84.21,
    47.06,
    36.36,
    2000.00,
    888.89,
    421.05,
    235.29,
    181.82,
    1000.00,
    444.44,
    210.53,
    117.65,
    90.91,
    666.67,
    296.30,
    140.35,
    78.43,
    60.61,
    333.33,
    148.15,
    70.18,
    39.22,
    30.30,
    200.00,
    88.89,
    42.11,
    23.53,
    18.18,
    1000.00,
    444.44,
    210.53,
    117.65,
    90.91,
    500.00,
    222.22,
    105.26,
    58.82,
    45.45,
    333.33,
    148.15,
    70.18,
    39.22,
    30.30,
    166.67,
    74.07,
    35.09,
    19.61,
    15.15,
    100.00,
    44.44,
    21.05,
    11.76,
    9.09,
    500.00,
    222.22,
    105.26,
    58.82,
    45.45,
    250.00,
    111.11,
    52.63,
    29.41,
    22.73,
    166.67,
    74.07,
    35.09,
    19.61,
    15.15,
    83.33,
    37.04,
    17.54,
    9.80,
    7.58,
    50.00,
    22.22,
    10.53,
    5.88,
    4.55,
]

bb = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    15,
    20,
    25,
    30,
    35,
    40,
    45,
    50,
    60,
    70,
    80,
    90,
    100,
    125,
    150,
    175,
    200,
    225,
    250,
    275,
    300,
    325,
    350,
    375,
    400,
    425,
    450,
    475,
    500,
    600,
    700,
    800,
    900,
    1000,
    2000,
    3000,
    5000,
    9999999,
]

cc = 0
for i in aa:
    cc += 1
    for idx, j in enumerate(bb):
        if i < j:
            print(idx + 1)
            # print(idx+1, ' - ', i, j)
            break

cc
# %%
