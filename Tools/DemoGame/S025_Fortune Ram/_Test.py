# %%


aa = [
    4,
    2,
    5,
    5,
    4,
    3,
    3,
    5,
    7,
    3,
    3,
    3,
    6,
    1,
    1,
    1,
    7,
    5,
    5,
    3,
    4,
    4,
    2,
    2,
    2,
    6,
    6,
    1,
    1,
    6,
    4,
    2,
    2,
    6,
    6,
    5,
    4,
    4,
    5,
    3,
    3,
    5,
    5,
    5,
    4,
    4,
    6,
    6,
    2,
    2,
    6,
    6,
    3,
    4,
    4,
    3,
    5,
    5,
    2,
    4,
    7,
    7,
    0,
    6,
    4,
    4,
    3,
    7,
    6,
    6,
    4,
    7,
    7,
]

dd = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: []}

tt = -1
cc = 1
for i in range(1, len(aa)):
    s_id = aa[i]
    if s_id == aa[i - 1]:
        cc += 1
    else:
        dd[s_id].append(cc)
        cc = 1

print(dd)

# %%

for i, v in enumerate(dd.values()):
    print(i, len(v), v)

# %%


import numpy as np

aa = np.array([[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]])

aa[aa == 1] = 10
aa

# %%
