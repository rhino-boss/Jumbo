# %%


import os

run_path = r"C:\Users\rhinshen\Mine\Employee_0419\9_Output\BNFG (給瓦隆)\Jackpot\PARsheet"
os.chdir(run_path)

old_name = os.listdir()

print(old_name)

# %%


new_name = [
    "060101",
    "060102",
    "060103",
    "060201",
    "060202",
    "060203",
    "060301",
    "060302",
    "060303",
    "060304",
    "060401",
    "060402",
    "060403",
    "060404",
    "060405",
    "060701",
    "060901",
    "060902",
    "061003",
    "061004",
    "061101",
]
for i, file_name in enumerate(old_name):
    print("{0:}.xlsm".format(new_name[i]), file_name)
    os.rename(file_name, "{0:}.xlsm".format(new_name[i]))


# %%
