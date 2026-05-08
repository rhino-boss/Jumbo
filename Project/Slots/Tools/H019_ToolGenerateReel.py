# %%

templates = [["C2", "C2", "A", "A", "K", "K", "Q", "Q"], ["C2", "C2", "Q", "Q", "TE", "TE", "M4", "M4"], ["C2", "C2", "J", "J", "TE", "TE", "M3", "M3"], ["C2", "C2", "K", "K", "M1", "M1"], ["C2", "C2", "K", "K", "M2", "M2"]]
# templates = [["A", "A", "K", "K", "M1", "M1"], ["Q", "Q", "TE", "TE", "M2", "M2"], ["M4", "M4", "J", "J", "TE", "TE", "M3", "M3"], ["C2", "C2"]]

# %%

import random
from collections import Counter


def generate_single_tape(symbol_counts):
    inventory = Counter(symbol_counts)
    all_elements = []

    # 核心組合模板
    templates = [["C2", "C2", "A", "A", "K", "K", "Q", "Q"], ["C2", "C2", "Q", "Q", "TE", "TE", "M4", "M4"], ["C2", "C2", "J", "J", "TE", "TE", "M3", "M3"], ["C2", "C2", "K", "K", "M1", "M1"], ["C2", "C2", "K", "K", "M2", "M2"]]
    # templates = [["A", "A", "K", "K", "M1", "M1"], ["Q", "Q", "TE", "TE", "M2", "M2"], ["M4", "M4", "J", "J", "TE", "TE", "M3", "M3"], ["C2", "C2", "J", "J", "TE", "TE"], ["C2", "C2", "K", "K", "M1", "M1"]]

    # 1. 提取核心組合 (視為一個 tuple 元素)
    while True:
        available = [t for t in templates if all(inventory[s] >= count for s, count in Counter(t).items())]
        if not available:
            break
        chosen = random.choice(available)
        for s in chosen:
            inventory[s] -= 1
        all_elements.append(tuple(chosen))

    # 2. 處理 C1 (強制單顆存放)
    if inventory.get("C1", 0) > 0:
        all_elements.extend([("C1",)] * inventory["C1"])
        inventory["C1"] = 0
    elif inventory.get("C2", 0) > 0:
        all_elements.extend([("C2",)] * inventory["C2"])
        inventory["C2"] = 0
    elif inventory.get("WW", 0) > 0:
        all_elements.extend([("WW",)] * inventory["WW"])
        inventory["WW"] = 0

    # 3. 其餘相同符號兩兩成對
    for sym in list(inventory.keys()):
        while inventory[sym] >= 2:
            all_elements.append((sym, sym))
            inventory[sym] -= 2
        if inventory[sym] == 1:
            all_elements.append((sym,))
            inventory[sym] -= 1

    # 4. 防重複排序演算法 (確保相鄰元素不重複)
    def shuffle_no_repeat(elems):
        result = []
        last_elem = None
        pool = elems.copy()
        random.shuffle(pool)

        while pool:
            found = False
            for i in range(len(pool)):
                if pool[i] != last_elem:
                    current = pool.pop(i)
                    result.append(current)
                    last_elem = current
                    found = True
                    break

            if not found:
                stuck_elem = pool.pop(0)
                inserted = False
                for i in range(1, len(result)):
                    if result[i - 1] != stuck_elem and result[i] != stuck_elem:
                        result.insert(i, stuck_elem)
                        inserted = True
                        break
                if not inserted:
                    result.append(stuck_elem)
        return result

    ordered_elements = shuffle_no_repeat(all_elements)

    # 5. 攤平為列表格式
    final_flat_list = []
    for elem in ordered_elements:
        final_flat_list.extend(elem)

    return final_flat_list


# --- 根據圖片輸入的 R1-R6 數據 ---
reels_data = [
    {"WW": 0, "C1": 0, "C2": 6, "M1": 10, "M2": 2, "M3": 12, "M4": 2, "A": 6, "K": 6, "Q": 6, "J": 22, "TE": 28},
    {"WW": 0, "C1": 4, "C2": 6, "M1": 2, "M2": 10, "M3": 2, "M4": 14, "A": 6, "K": 12, "Q": 24, "J": 6, "TE": 14},
    {"WW": 0, "C1": 0, "C2": 6, "M1": 6, "M2": 6, "M3": 6, "M4": 6, "A": 12, "K": 14, "Q": 2, "J": 14, "TE": 28},
    {"WW": 0, "C1": 4, "C2": 6, "M1": 2, "M2": 10, "M3": 2, "M4": 12, "A": 12, "K": 4, "Q": 4, "J": 22, "TE": 22},
    {"WW": 0, "C1": 0, "C2": 6, "M1": 14, "M2": 2, "M3": 10, "M4": 2, "A": 20, "K": 8, "Q": 30, "J": 4, "TE": 4},
    {"WW": 0, "C1": 4, "C2": 6, "M1": 6, "M2": 6, "M3": 6, "M4": 6, "A": 2, "K": 18, "Q": 10, "J": 8, "TE": 28},
]

# --- 執行生成 ---
final_reels_arr = []
for data in reels_data:
    final_reels_arr.append(generate_single_tape(data))

# --- 輸出結果 ---
import json

# print(f"// 已生成 6 條輪帶，共包含 {sum(len(r) for r in final_reels_arr)} 個符號")
# print("const final_reels_arr = " + json.dumps(final_reels_arr) + ";")

reel = len(final_reels_arr)
reel_len = len(final_reels_arr[0])
for j in range(reel_len):
    for i in range(reel):
        print(final_reels_arr[i][j], end="\t")
    print()


# %%
