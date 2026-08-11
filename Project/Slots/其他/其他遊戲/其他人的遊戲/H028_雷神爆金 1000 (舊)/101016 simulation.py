#%%
import json
import numpy as np
from numba import njit
from multiprocessing import Pool, cpu_count
import time

# 讀取 data.js
with open(r'D:\IGame\H017\data.js', 'r', encoding='utf-8') as f:
    content = f.read()
    # 移除 "const data = " 和結尾的 ";"
    json_str = content.replace('const data = ', '').rstrip(';')
    data = json.loads(json_str)

# ========== 預處理參數為 numpy 數組 ==========
# 將所有參數轉為 numpy 數組以便 numba 使用

# ReelWeight
REEL_WEIGHT = np.array(data['ReelWeight'], dtype=np.float64)

# linkpoint: [11符號][4連線] M1-M6,A,K,Q,J,TE 的 3,4,5,6 連線得分
LINKPOINT = np.array(data['linkpoint'], dtype=np.float64)

# MegaWay 15種情況 (轉為固定大小數組，用-1填充)
MEGAWAY_PATTERNS = np.array([
    [4, 1, -1, -1, -1], [1, 4, -1, -1, -1], [3, 2, -1, -1, -1], [2, 3, -1, -1, -1],
    [3, 1, 1, -1, -1], [1, 3, 1, -1, -1], [1, 1, 3, -1, -1],
    [2, 2, 1, -1, -1], [2, 1, 2, -1, -1], [1, 2, 2, -1, -1],
    [2, 1, 1, 1, -1], [1, 2, 1, 1, -1], [1, 1, 2, 1, -1], [1, 1, 1, 2, -1],
    [1, 1, 1, 1, 1]
], dtype=np.int32)

# 盤面高度: R1-R6=5, R7=4 (與後端 "5555554" 版面一致)
TARGET_HEIGHTS = np.array([5, 5, 5, 5, 5, 5, 4], dtype=np.int32)

def prepare_param_arrays(suffix):
    """準備指定參數組的 numpy 數組 (BaseGame)"""
    # Symbol reels: 7條輪帶，每條最多121個符號
    symbol_reels_list = data[f'BaseGameSymbol{suffix}']
    max_len = max(len(r) for r in symbol_reels_list)
    symbol_reels = np.full((7, max_len), -1, dtype=np.int32)
    reel_lengths = np.zeros(7, dtype=np.int32)
    for i, reel in enumerate(symbol_reels_list):
        symbol_reels[i, :len(reel)] = np.array(reel, dtype=np.int32)
        reel_lengths[i] = len(reel)
    
    # Weight reels
    weight_reels_list = data[f'BaseGameSymbolWeight{suffix}']
    weight_reels = np.full((7, max_len), 0.0, dtype=np.float64)
    for i, reel in enumerate(weight_reels_list):
        weight_reels[i, :len(reel)] = np.array(reel, dtype=np.float64)
    
    # MegaWay weights: 6x15
    megaway_weights = np.array(data[f'BaseGameMegaWay{suffix}'], dtype=np.float64)
    
    # MY weights
    my_weights = np.array(data[f'BaseGameMY{suffix}'], dtype=np.float64)
    
    # PostC1 weights (取第二行的權重，第一行是值但恰好等於索引)
    post_c1_data = data[f'BaseGame{suffix}PostC1']
    post_c1_weights = np.array(post_c1_data[1], dtype=np.float64)
    
    # Drop weights: 5組，每組7條輪帶x26符號
    drop_weights = np.zeros((5, 7, 26), dtype=np.float64)
    for d in range(5):
        drop_data = data[f'BaseGame{suffix}Drop{d+1}']
        for r in range(7):
            arr = np.array(drop_data[r], dtype=np.float64)
            drop_weights[d, r, :len(arr)] = arr
    
    return symbol_reels, reel_lengths, weight_reels, megaway_weights, my_weights, post_c1_weights, drop_weights

def prepare_freegame_param_arrays(suffix):
    """準備指定參數組的 numpy 數組 (FreeGame)"""
    # Symbol reels: 7條輪帶
    symbol_reels_list = data[f'FreeGameSymbol{suffix}']
    max_len = max(len(r) for r in symbol_reels_list)
    symbol_reels = np.full((7, max_len), -1, dtype=np.int32)
    reel_lengths = np.zeros(7, dtype=np.int32)
    for i, reel in enumerate(symbol_reels_list):
        symbol_reels[i, :len(reel)] = np.array(reel, dtype=np.int32)
        reel_lengths[i] = len(reel)
    
    # Weight reels
    weight_reels_list = data[f'FreeGameSymbolWeight{suffix}']
    weight_reels = np.full((7, max_len), 0.0, dtype=np.float64)
    for i, reel in enumerate(weight_reels_list):
        weight_reels[i, :len(reel)] = np.array(reel, dtype=np.float64)
    
    # MegaWay weights: 6x15
    megaway_weights = np.array(data[f'FreeGameMegaWay{suffix}'], dtype=np.float64)
    
    # MY weights
    my_weights = np.array(data[f'FreeGameMY{suffix}'], dtype=np.float64)
    
    # PostC1 weights (處理不同格式: 1D 或 2D)
    post_c1_data = data[f'FreeGame{suffix}PostC1']
    if isinstance(post_c1_data[0], list):
        # 2D 格式 [[values], [weights]]
        post_c1_weights = np.array(post_c1_data[1], dtype=np.float64)
    else:
        # 1D 格式 [weights]
        post_c1_weights = np.array(post_c1_data, dtype=np.float64)
    
    # Drop weights: 5組，每組7條輪帶x26符號
    drop_weights = np.zeros((5, 7, 26), dtype=np.float64)
    for d in range(5):
        drop_data = data[f'FreeGame{suffix}Drop{d+1}']
        for r in range(7):
            arr = np.array(drop_data[r], dtype=np.float64)
            drop_weights[d, r, :len(arr)] = arr
    
    return symbol_reels, reel_lengths, weight_reels, megaway_weights, my_weights, post_c1_weights, drop_weights

# 預先準備兩套參數 (展開為獨立全局變量)
_p1 = prepare_param_arrays(1)
_p2 = prepare_param_arrays(2)

# 參數組1
SYMBOL_REELS_1 = _p1[0]
REEL_LENGTHS_1 = _p1[1]
WEIGHT_REELS_1 = _p1[2]
MEGAWAY_WEIGHTS_1 = _p1[3]
MY_WEIGHTS_1 = _p1[4]
POST_C1_WEIGHTS_1 = _p1[5]
DROP_WEIGHTS_1 = _p1[6]

# 參數組2
SYMBOL_REELS_2 = _p2[0]
REEL_LENGTHS_2 = _p2[1]
WEIGHT_REELS_2 = _p2[2]
MEGAWAY_WEIGHTS_2 = _p2[3]
MY_WEIGHTS_2 = _p2[4]
POST_C1_WEIGHTS_2 = _p2[5]
DROP_WEIGHTS_2 = _p2[6]

# FreeGame 參數組
_fp1 = prepare_freegame_param_arrays(1)
_fp2 = prepare_freegame_param_arrays(2)
_fp3 = prepare_freegame_param_arrays(3)

# FreeGame 參數組1
FG_SYMBOL_REELS_1 = _fp1[0]
FG_REEL_LENGTHS_1 = _fp1[1]
FG_WEIGHT_REELS_1 = _fp1[2]
FG_MEGAWAY_WEIGHTS_1 = _fp1[3]
FG_MY_WEIGHTS_1 = _fp1[4]
FG_POST_C1_WEIGHTS_1 = _fp1[5]
FG_DROP_WEIGHTS_1 = _fp1[6]

# FreeGame 參數組2
FG_SYMBOL_REELS_2 = _fp2[0]
FG_REEL_LENGTHS_2 = _fp2[1]
FG_WEIGHT_REELS_2 = _fp2[2]
FG_MEGAWAY_WEIGHTS_2 = _fp2[3]
FG_MY_WEIGHTS_2 = _fp2[4]
FG_POST_C1_WEIGHTS_2 = _fp2[5]
FG_DROP_WEIGHTS_2 = _fp2[6]

# FreeGame 參數組3
FG_SYMBOL_REELS_3 = _fp3[0]
FG_REEL_LENGTHS_3 = _fp3[1]
FG_WEIGHT_REELS_3 = _fp3[2]
FG_MEGAWAY_WEIGHTS_3 = _fp3[3]
FG_MY_WEIGHTS_3 = _fp3[4]
FG_POST_C1_WEIGHTS_3 = _fp3[5]
FG_DROP_WEIGHTS_3 = _fp3[6]

# FreeReelWeight 權重 (用於初始場次選擇參數組)
FREE_REEL_WEIGHT = np.array(data['FreeReelWeight'], dtype=np.float64)

# FreeTriggerReel 權重 (用於 retrigger 時選擇參數組)
FREE_TRIGGER_REEL = np.array(data['FreeTriggerReel'], dtype=np.float64)

# ========== Numba 加速函數 ==========

@njit
def weighted_choice_numba(weights):
    """根據權重隨機選擇索引 (numba 版本)"""
    total = np.sum(weights)
    n = len(weights)
    if total == 0:
        return np.int32(np.random.randint(0, n))
    r = np.random.random() * total
    cumsum = 0.0
    for i in range(n):
        cumsum += weights[i]
        if r < cumsum:
            return np.int32(i)
    return np.int32(n - 1)

@njit
def comb_count_numba(n, k):
    """C(n, k) 組合數 (整數)，等價後端 buildCombinations 列舉出的組合總數"""
    if k < 0 or k > n:
        return 0
    if k > n - k:
        k = n - k
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result

@njit
def pick_combination_numba(n, k, out):
    """依字典序列舉 C(n,k) 後等機率抽一組，結果(升冪)寫入 out[0..k-1]。
    等價後端 applyPostScatter 的選輪流程：buildCombinations(字典序列舉) + pickEvenly(均權抽 index)。
    此處以組合 unranking 直接算出第 m 組，避免建整份清單(結果分布完全相同)。"""
    total = comb_count_numba(n, k)
    m = np.random.randint(0, total)   # 均勻抽 rank(0..total-1)，等同 pickEvenly 均權
    x = 0
    rem = k
    for i in range(k):
        while True:
            cnt = comb_count_numba(n - x - 1, rem - 1)   # 以 x 開頭的組合數
            if m < cnt:
                out[i] = np.int32(x)
                x += 1
                rem -= 1
                break
            else:
                m -= cnt
                x += 1

@njit
def single_spin_core(symbol_reels, reel_lengths, weight_reels,
                     megaway_weights, my_weights, post_c1_weights, drop_weights,
                     megaway_patterns, linkpoint, target_heights,
                     enable_m1_multiplier):
    """執行單次 spin 核心計算 (numba 版本)"""
    # 生成初始盤面
    board = np.full((7, 6), -1, dtype=np.int32)
    lengths = np.full((7, 6), 0, dtype=np.int32)
    
    # R1-R6
    for reel_idx in range(6):
        pattern_idx = int(weighted_choice_numba(megaway_weights[reel_idx]))
        pattern = megaway_patterns[pattern_idx]
        start_pos = int(weighted_choice_numba(weight_reels[reel_idx, :reel_lengths[reel_idx]]))
        
        pos = 0
        symbol_pos = start_pos
        for p in range(5):
            length = int(pattern[p])
            if length < 0:
                break
            symbol = symbol_reels[reel_idx, symbol_pos % reel_lengths[reel_idx]]
            # head 存高度，延續格存 0 (與後端 linkScreenSymbol 一致)
            for k in range(length):
                if pos < 6:
                    board[reel_idx, pos] = symbol
                    lengths[reel_idx, pos] = np.int32(length) if k == 0 else 0
                    pos += 1
            symbol_pos += length
    
    # R7: 4個符號
    r7_start = int(weighted_choice_numba(weight_reels[6, :reel_lengths[6]]))
    for i in range(4):
        symbol = symbol_reels[6, (r7_start + i) % reel_lengths[6]]
        board[6, i] = symbol
        lengths[6, i] = np.int32(1)
    
    # 模擬後端 convertToMegaWaysScreenLabel：R1-R6 符號下移一行，R7 移到 row0
    # 1. R1-R6 所有符號下移一行
    for reel_idx in range(6):
        for pos in range(5, 0, -1):  # 5,4,3,2,1
            board[reel_idx, pos] = board[reel_idx, pos - 1]
            lengths[reel_idx, pos] = lengths[reel_idx, pos - 1]
        board[reel_idx, 0] = np.int32(-1)  # row0 先清空
        lengths[reel_idx, 0] = 0
    
    # 2. R7 的 4 個符號移到 R2-R5 的 row0
    for i in range(4):
        board[i + 1, 0] = board[6, i]
        lengths[i + 1, 0] = 1
    
    # 轉換 MY 符號
    # MY 權重索引對應: 0=Wild, 1=C1, 2=M1, 3=M2, ..., 12=TE
    target_idx = int(weighted_choice_numba(my_weights))
    my_target_symbol = np.int32(target_idx)  # 索引直接就是符號 ID (用獨立變數避免被消除循環覆蓋)
    for r in range(7):
        for c in range(6):
            if board[r, c] == 24:
                board[r, c] = my_target_symbol
            elif board[r, c] == 25:
                board[r, c] = np.int32(my_target_symbol + 11)
    
    # C1 替換：從 C(7, N) 隨機選擇輪帶替換
    # 注意：MegaWay 符號現在在 row 1-5，row 0 是 R7
    c1_count = int(weighted_choice_numba(post_c1_weights))
    if c1_count > 0:
        # 與後端 applyPostScatter 同步：列舉 C(7, c1_count) 所有組合(字典序)後等機率抽一組
        # (等價後端 buildCombinations 字典序列舉 + pickEvenly 均權抽 index)
        chosen_reels = np.full(7, -1, dtype=np.int32)
        pick_combination_numba(7, c1_count, chosen_reels)
        
        # 某輪若無可替換符號則該顆 C1 不補 (與後端選定 C(7,N) 後 continue 的行為一致)
        for idx in range(c1_count):
            r = chosen_reels[idx]
            if r == 6:
                # R7：算分/觸發都以「已併入 R2~R5 row0」的盤面為準，
                # 因此 C1 必須寫進合併後的計分格 board[1..4, 0]，而非 R7 原始輪 board[6, *]，
                # 否則替換對算分與 c1_final(觸發判定) 都不生效，原符號還會照樣計分。
                # (R7 符號皆為 1x1，最短長度恆為 1；複數候選時等機率隨機抽)
                cand_reels = np.full(4, -1, dtype=np.int32)
                n_cand = 0
                for i in range(4):
                    if board[i + 1, 0] != -1:  # 有效符號即可 (與後端一致：只檢查 link>0)
                        cand_reels[n_cand] = i + 1
                        n_cand += 1
                if n_cand == 0:
                    continue  # R7 無有效符號
                target_reel = cand_reels[np.random.randint(0, n_cand)]
                board[target_reel, 0] = np.int32(1)
                continue
            # R1~R6：在 pos 1~5 的 MegaWay 符號中替換 (row 0 是 R7)
            # 找出該輪帶最短長度 (與後端一致：只檢查 link>0，不排除任何符號)
            min_len = 99
            c = 1  # 從 row 1 開始
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L < min_len:
                    min_len = L
                c += L
            if min_len == 99:
                continue  # 該輪帶無有效符號
            # 收集所有「最短長度」大符號 block 的起始位置 (head)
            cand_heads = np.full(6, -1, dtype=np.int32)
            n_cand = 0
            c = 1  # 從 row 1 開始 (row 0 是 R7)
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L == min_len:
                    cand_heads[n_cand] = c
                    n_cand += 1
                c += L
            # 複數最短長度時，等機率隨機抽一個 block (與後端一致)
            head = cand_heads[np.random.randint(0, n_cand)]
            # 將整個大符號 block 替換為 C1 (等同後端 head 變 C1、維持高度)
            for cc in range(head, head + min_len):
                if cc < 6:
                    board[r, cc] = np.int32(1)
    
    # 記錄初始盤面 C1 數量和長度分布 (C1 替換後、消除前)
    init_c1_count = 0
    init_c1_len_counts = np.zeros(4, dtype=np.int32)  # [len1, len2, len3, len4]
    for reel_idx in range(6):
        # 依 lengths 逐 block 走訪，每個 C1 block head 各算 1 個 (與後端 link>0 計 head 一致)
        c = 0
        while c < 6:
            sym = board[reel_idx, c]
            L = lengths[reel_idx, c]
            if sym == -1 or L <= 0:
                c += 1
                continue
            if sym == 1:  # C1
                init_c1_count += 1
                if 1 <= L <= 4:
                    init_c1_len_counts[L - 1] += 1
            c += L
    
    # R7 的 C1 已於上方主迴圈 (reels 1~4 的 row0) 計入，與 c1_final 計數方式一致，
    # 不再額外掃描 R7 原始輪 board[6, *] (該處在 PostScatter 後仍為原符號，不會是 C1)。

    # M1 倍數累加 (初始盤面)
    # M1=2, GM1=13, 長度1=+2, 長度2=+3, 長度3=+4, 長度4=+5
    # 第一個 M1 只加 +1 (即 +2-1)
    multiplier = 1.0
    m1_count = 0
    
    if enable_m1_multiplier:
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1 or L <= 0:
                    pos += 1
                    continue
                if sym == 2 or sym == 13:  # M1 或 GM1
                    bonus = L + 1  # 長度1=+2, 長度2=+3...
                    if m1_count == 0:
                        bonus -= 1  # 第一個 M1 扣 1
                    multiplier += bonus
                    m1_count += 1
                pos += L
    
    # R7 的 M1 已於上方主迴圈 (reels 1~4 的 row 0，R7 移位後位置) 計入，
    # 此處不再額外累加，避免同一顆 R7 的 M1 被重複計算兩次倍數。

    total_win = 0.0
    drop_count = 0
    max_drops = 50  # 安全上限
    cascade_scores = np.zeros(5, dtype=np.float64)
    
    # 消除循環
    while drop_count < max_drops:
        # 檢查消除
        score = 0.0
        wins = np.zeros((11, 3), dtype=np.int32)
        win_count = 0
        
        for target_symbol in range(2, 13):
            consecutive_reels = 0
            ways = 1
            gold_symbol = target_symbol + 11
            
            for reel_idx in range(6):
                matching = 0
                # 依 lengths 逐 MegaWay block 走訪，每個 block head 各算 1 個
                # (與後端以 link>0 計 head 一致：同一輪相鄰兩個大符號即使同符號也算 2 個)
                c = 0
                while c < 6:
                    sym = board[reel_idx, c]
                    L = lengths[reel_idx, c]
                    if sym == -1 or L <= 0:
                        c += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        matching += 1
                    c += L

                if matching > 0:
                    consecutive_reels += 1
                    ways *= matching
                else:
                    break
            
            if consecutive_reels >= 3:
                symbol_idx = target_symbol - 2
                line_idx = consecutive_reels - 3
                base_score = linkpoint[symbol_idx, line_idx]
                score += base_score * ways
                wins[win_count, 0] = target_symbol
                wins[win_count, 1] = consecutive_reels
                wins[win_count, 2] = ways
                win_count += 1

        if win_count == 0:
            break

        # 得分乘以倍數
        cascade_round = min(drop_count, 4)
        cascade_scores[cascade_round] += score * multiplier
        total_win += score * multiplier
        drop_count += 1
        drop_idx = min(drop_count, 5) - 1
        
        # 移除並補充
        to_remove = np.zeros((7, 6), dtype=np.int32)
        gold_win_head = np.zeros((7, 6), dtype=np.int32)   # 兩階段修正:記錄中獎金框head
        # Pass1: 用原始盤面標記所有消除(不即時mutate board),避免中獎金框轉Wild後被後面符號誤消
        for w in range(win_count):
            target_symbol = wins[w, 0]
            reels_count = wins[w, 1]
            gold_symbol = target_symbol + 11
            for reel_idx in range(reels_count):
                pos = 0
                while pos < 6:
                    sym = board[reel_idx, pos]
                    L = lengths[reel_idx, pos]
                    if sym == -1 or L <= 0:
                        pos += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        for k in range(L):
                            if pos + k < 6:
                                to_remove[reel_idx, pos + k] = 1
                        if sym >= 13 and sym <= 23:
                            gold_win_head[reel_idx, pos] = 1
                    pos += L
        # Pass2: 中獎金框整塊轉Wild並取消其消除(存活),對齊後端 calculateChangeWildScreen
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                L = lengths[reel_idx, pos]
                if L > 0:
                    if gold_win_head[reel_idx, pos] == 1:
                        for k in range(L):
                            if pos + k < 6:
                                board[reel_idx, pos + k] = 0
                                to_remove[reel_idx, pos + k] = 0
                    pos += L
                else:
                    pos += 1
        
        # 記錄補充前的位置，用於檢測新 M1
        old_fill_pos = np.zeros(7, dtype=np.int32)
        
        # R1-R6 主盤面垂直掉落 (row 1-5，row 0 是 R7)
        # Java 順序: 新符號在底部 (row 1-消除數量)，保留符號在頂部 (row 消除數量+1 到末尾)
        for reel_idx in range(6):
            target_height = target_heights[reel_idx]
            
            # 收集存活符號列表 (row 1-5)，以區塊為單位
            survive_symbols = np.full(6, -1, dtype=np.int32)
            survive_lens = np.zeros(6, dtype=np.int32)
            survive_count = 0
            pos = 1
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1:
                    pos += 1
                    continue
                if L > 0:  # 是 head
                    if to_remove[reel_idx, pos] == 0:  # 未被移除
                        # 複製整個區塊
                        for k in range(L):
                            if pos + k < 6:
                                survive_symbols[survive_count] = board[reel_idx, pos + k]
                                survive_lens[survive_count] = L if k == 0 else 0
                                survive_count += 1
                    pos += L
                else:
                    pos += 1

            # 計算消除數量 (要補充的新符號數量)
            # MegaWays 填充區域是 row 1-5 (5格)，row 0 由 R7 水平掉落邏輯單獨處理
            eliminate_count = target_height - survive_count

            new_reel = np.full(6, -1, dtype=np.int32)
            new_len = np.zeros(6, dtype=np.int32)

            # 按 Java 順序填充: 先新符號 (row 1 到 eliminate_count)，再保留符號
            new_pos = 1

            # 先填充新符號
            for _ in range(eliminate_count):
                if new_pos >= 6:
                    break
                new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, reel_idx]))
                # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
                if new_symbol == 24:
                    new_symbol = my_target_symbol
                elif new_symbol == 25:
                    new_symbol = np.int32(my_target_symbol + 11)
                new_reel[new_pos] = new_symbol
                new_len[new_pos] = 1  # 補充符號皆 1x1
                # 檢查新補充的 M1 (補充符號長度都是 1)
                if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                    bonus = 2  # 長度1=+2
                    if m1_count == 0:
                        bonus -= 1
                    multiplier += bonus
                    m1_count += 1
                new_pos += 1

            old_fill_pos[reel_idx] = new_pos  # 記錄補充結束位置
            
            # 再填充保留符號
            for si in range(survive_count):
                if new_pos >= 6:
                    break
                new_reel[new_pos] = survive_symbols[si]
                new_len[new_pos] = survive_lens[si]
                new_pos += 1

            # 保留 R7 位置的符號 (R2-R5 的 row 0)
            if reel_idx in (1, 2, 3, 4):
                new_reel[0] = board[reel_idx, 0]
                new_len[0] = lengths[reel_idx, 0]  # R7 格長度保留(=1)

            board[reel_idx] = new_reel
            lengths[reel_idx] = new_len
        
        # R7 水平掉落 (往左靠攏，右邊補充) - R7 在 row 0
        r7_symbols = np.full(4, -1, dtype=np.int32)
        r7_pos = 0
        for i in range(4):
            reel_idx = i + 1  # R2-R5
            sym = board[reel_idx, 0]
            if sym != -1 and to_remove[reel_idx, 0] == 0:
                r7_symbols[r7_pos] = sym
                r7_pos += 1
        
        r7_old_pos = r7_pos  # 記錄 R7 補充開始位置
        
        # 補充 R7 (從右邊補充)
        while r7_pos < 4:
            new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, 6]))
            # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
            if new_symbol == 24:
                new_symbol = my_target_symbol
            elif new_symbol == 25:
                new_symbol = np.int32(my_target_symbol + 11)
            r7_symbols[r7_pos] = new_symbol
            # 檢查新補充的 M1
            if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                bonus = 2  # 長度1=+2
                if m1_count == 0:
                    bonus -= 1
                multiplier += bonus
                m1_count += 1
            r7_pos += 1
        
        # 更新 R7 位置 (row 0)
        for i in range(4):
            board[i + 1, 0] = r7_symbols[i]
            board[6, i] = r7_symbols[i]
            lengths[i + 1, 0] = 1  # R7 皆 1x1
    
    # 計算最終盤面的 C1 數量：依 lengths 逐 block head 計 (與後端 link>0 計 head 一致)
    # lengths 已在消除/掉落過程中維護(存活保留長度、補充=1)，故可信。
    c1_final_count = 0
    for reel_idx in range(6):
        c = 0
        while c < 6:
            sym = board[reel_idx, c]
            L = lengths[reel_idx, c]
            if sym == -1 or L <= 0:
                c += 1
                continue
            if sym == 1:  # C1
                c1_final_count += 1
            c += L
    
    return total_win, c1_final_count, np.int32(multiplier), np.int32(init_c1_count), init_c1_len_counts, cascade_scores

# ========== FreeGame Spin 核心函數 ==========

@njit
def freegame_spin_core(symbol_reels, reel_lengths, weight_reels, 
                       megaway_weights, my_weights, post_c1_weights, drop_weights,
                       megaway_patterns, linkpoint, target_heights,
                       current_multiplier, current_m1_count, enable_m1_multiplier):
    """執行 FreeGame 單次 spin 核心計算 (numba 版本)
    
    參數:
    - current_multiplier: 當前累計倍數
    - current_m1_count: 當前已累計的 M1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色
    
    返回:
    - total_win: 本次 spin 得分
    - c1_final_count: 結束時 C1 數量
    - new_multiplier: 更新後的倍數
    - new_m1_count: 更新後的 M1 數量
    """
    # 生成初始盤面
    board = np.full((7, 6), -1, dtype=np.int32)
    lengths = np.full((7, 6), 0, dtype=np.int32)
    
    # R1-R6
    for reel_idx in range(6):
        pattern_idx = int(weighted_choice_numba(megaway_weights[reel_idx]))
        pattern = megaway_patterns[pattern_idx]
        start_pos = int(weighted_choice_numba(weight_reels[reel_idx, :reel_lengths[reel_idx]]))
        
        pos = 0
        symbol_pos = start_pos
        for p in range(5):
            length = int(pattern[p])
            if length < 0:
                break
            symbol = symbol_reels[reel_idx, symbol_pos % reel_lengths[reel_idx]]
            # head 存高度，延續格存 0 (與後端 linkScreenSymbol 一致)
            for k in range(length):
                if pos < 6:
                    board[reel_idx, pos] = symbol
                    lengths[reel_idx, pos] = np.int32(length) if k == 0 else 0
                    pos += 1
            symbol_pos += length
    
    # R7: 4個符號
    r7_start = int(weighted_choice_numba(weight_reels[6, :reel_lengths[6]]))
    for i in range(4):
        symbol = symbol_reels[6, (r7_start + i) % reel_lengths[6]]
        board[6, i] = symbol
        lengths[6, i] = np.int32(1)
    
    # 模擬後端 convertToMegaWaysScreenLabel：R1-R6 符號下移一行，R7 移到 row0
    # 1. R1-R6 所有符號下移一行
    for reel_idx in range(6):
        for pos in range(5, 0, -1):  # 5,4,3,2,1
            board[reel_idx, pos] = board[reel_idx, pos - 1]
            lengths[reel_idx, pos] = lengths[reel_idx, pos - 1]
        board[reel_idx, 0] = np.int32(-1)  # row0 先清空
        lengths[reel_idx, 0] = 0
    
    # 2. R7 的 4 個符號移到 R2-R5 的 row0
    for i in range(4):
        board[i + 1, 0] = board[6, i]
        lengths[i + 1, 0] = 1
    
    # 轉換 MY 符號
    # MY 權重索引對應: 0=Wild, 1=C1, 2=M1, 3=M2, ..., 12=TE
    target_idx = int(weighted_choice_numba(my_weights))
    my_target_symbol = np.int32(target_idx)  # 索引直接就是符號 ID (用獨立變數避免被消除循環覆蓋)
    for r in range(7):
        for c in range(6):
            if board[r, c] == 24:
                board[r, c] = my_target_symbol
            elif board[r, c] == 25:
                board[r, c] = np.int32(my_target_symbol + 11)
    
    # C1 替換：從 C(7, N) 隨機選擇輪帶替換
    # 注意：MegaWay 符號現在在 row 1-5，row 0 是 R7
    c1_count = int(weighted_choice_numba(post_c1_weights))
    if c1_count > 0:
        # 與後端 applyPostScatter 同步：列舉 C(7, c1_count) 所有組合(字典序)後等機率抽一組
        # (等價後端 buildCombinations 字典序列舉 + pickEvenly 均權抽 index)
        chosen_reels = np.full(7, -1, dtype=np.int32)
        pick_combination_numba(7, c1_count, chosen_reels)
        
        # 某輪若無可替換符號則該顆 C1 不補 (與後端選定 C(7,N) 後 continue 的行為一致)
        for idx in range(c1_count):
            r = chosen_reels[idx]
            if r == 6:
                # R7：算分/觸發都以「已併入 R2~R5 row0」的盤面為準，
                # 因此 C1 必須寫進合併後的計分格 board[1..4, 0]，而非 R7 原始輪 board[6, *]，
                # 否則替換對算分與 c1_final(觸發判定) 都不生效，原符號還會照樣計分。
                # (R7 符號皆為 1x1，最短長度恆為 1；複數候選時等機率隨機抽)
                cand_reels = np.full(4, -1, dtype=np.int32)
                n_cand = 0
                for i in range(4):
                    if board[i + 1, 0] != -1:  # 有效符號即可 (與後端一致：只檢查 link>0)
                        cand_reels[n_cand] = i + 1
                        n_cand += 1
                if n_cand == 0:
                    continue  # R7 無有效符號
                target_reel = cand_reels[np.random.randint(0, n_cand)]
                board[target_reel, 0] = np.int32(1)
                continue
            # R1~R6：在 pos 1~5 的 MegaWay 符號中替換 (row 0 是 R7)
            # 找出該輪帶最短長度 (與後端一致：只檢查 link>0，不排除任何符號)
            min_len = 99
            c = 1  # 從 row 1 開始
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L < min_len:
                    min_len = L
                c += L
            if min_len == 99:
                continue  # 該輪帶無有效符號
            # 收集所有「最短長度」大符號 block 的起始位置 (head)
            cand_heads = np.full(6, -1, dtype=np.int32)
            n_cand = 0
            c = 1  # 從 row 1 開始 (row 0 是 R7)
            while c < 6:
                L = lengths[r, c]
                if L <= 0:
                    c += 1
                    continue
                if L == min_len:
                    cand_heads[n_cand] = c
                    n_cand += 1
                c += L
            # 複數最短長度時，等機率隨機抽一個 block (與後端一致)
            head = cand_heads[np.random.randint(0, n_cand)]
            # 將整個大符號 block 替換為 C1 (等同後端 head 變 C1、維持高度)
            for cc in range(head, head + min_len):
                if cc < 6:
                    board[r, cc] = np.int32(1)
    
    # M1 倍數累加 (使用傳入的倍數)
    multiplier = float(current_multiplier)
    m1_count = int(current_m1_count)
    
    if enable_m1_multiplier:
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1 or L <= 0:
                    pos += 1
                    continue
                if sym == 2 or sym == 13:  # M1 或 GM1
                    bonus = L + 1
                    if m1_count == 0:
                        bonus -= 1
                    multiplier += bonus
                    m1_count += 1
                pos += L
    
    # R7 的 M1 已於上方主迴圈 (reels 1~4 的 row 0，R7 移位後位置) 計入，
    # 此處不再額外累加，避免同一顆 R7 的 M1 被重複計算兩次倍數。

    total_win = 0.0
    drop_count = 0
    max_drops = 50
    cascade_scores = np.zeros(5, dtype=np.float64)
    
    # 消除循環
    while drop_count < max_drops:
        score = 0.0
        wins = np.zeros((11, 3), dtype=np.int32)
        win_count = 0
        
        for target_symbol in range(2, 13):
            consecutive_reels = 0
            ways = 1
            gold_symbol = target_symbol + 11
            
            for reel_idx in range(6):
                matching = 0
                # 依 lengths 逐 MegaWay block 走訪，每個 block head 各算 1 個
                # (與後端以 link>0 計 head 一致：同一輪相鄰兩個大符號即使同符號也算 2 個)
                c = 0
                while c < 6:
                    sym = board[reel_idx, c]
                    L = lengths[reel_idx, c]
                    if sym == -1 or L <= 0:
                        c += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        matching += 1
                    c += L

                if matching > 0:
                    consecutive_reels += 1
                    ways *= matching
                else:
                    break
            
            if consecutive_reels >= 3:
                symbol_idx = target_symbol - 2
                line_idx = consecutive_reels - 3
                base_score = linkpoint[symbol_idx, line_idx]
                score += base_score * ways
                wins[win_count, 0] = target_symbol
                wins[win_count, 1] = consecutive_reels
                wins[win_count, 2] = ways
                win_count += 1
        
        if win_count == 0:
            break
        
        # 得分乘以倍數
        cascade_round = min(drop_count, 4)
        cascade_scores[cascade_round] += score * multiplier
        total_win += score * multiplier
        drop_count += 1
        drop_idx = min(drop_count, 5) - 1
        
        # 移除並補充
        to_remove = np.zeros((7, 6), dtype=np.int32)
        gold_win_head = np.zeros((7, 6), dtype=np.int32)   # 兩階段修正:記錄中獎金框head
        # Pass1: 用原始盤面標記所有消除(不即時mutate board),避免中獎金框轉Wild後被後面符號誤消
        for w in range(win_count):
            target_symbol = wins[w, 0]
            reels_count = wins[w, 1]
            gold_symbol = target_symbol + 11
            for reel_idx in range(reels_count):
                pos = 0
                while pos < 6:
                    sym = board[reel_idx, pos]
                    L = lengths[reel_idx, pos]
                    if sym == -1 or L <= 0:
                        pos += 1
                        continue
                    if sym == target_symbol or sym == gold_symbol or sym == 0:
                        for k in range(L):
                            if pos + k < 6:
                                to_remove[reel_idx, pos + k] = 1
                        if sym >= 13 and sym <= 23:
                            gold_win_head[reel_idx, pos] = 1
                    pos += L
        # Pass2: 中獎金框整塊轉Wild並取消其消除(存活),對齊後端 calculateChangeWildScreen
        for reel_idx in range(6):
            pos = 0
            while pos < 6:
                L = lengths[reel_idx, pos]
                if L > 0:
                    if gold_win_head[reel_idx, pos] == 1:
                        for k in range(L):
                            if pos + k < 6:
                                board[reel_idx, pos + k] = 0
                                to_remove[reel_idx, pos + k] = 0
                    pos += L
                else:
                    pos += 1
        
        # R1-R6 垂直掉落
        # Java 順序: 新符號在底部 (row 1-消除數量)，保留符號在頂部 (row 消除數量+1 到末尾)
        for reel_idx in range(6):
            target_height = target_heights[reel_idx]
            
            # 收集存活符號列表 (row 1-5)，以區塊為單位
            survive_symbols = np.full(6, -1, dtype=np.int32)
            survive_lens = np.zeros(6, dtype=np.int32)
            survive_count = 0
            pos = 1
            while pos < 6:
                sym = board[reel_idx, pos]
                L = lengths[reel_idx, pos]
                if sym == -1:
                    pos += 1
                    continue
                if L > 0:  # 是 head
                    if to_remove[reel_idx, pos] == 0:  # 未被移除
                        # 複製整個區塊
                        for k in range(L):
                            if pos + k < 6:
                                survive_symbols[survive_count] = board[reel_idx, pos + k]
                                survive_lens[survive_count] = L if k == 0 else 0
                                survive_count += 1
                    pos += L
                else:
                    pos += 1

            # 計算消除數量 (要補充的新符號數量)
            eliminate_count = target_height - survive_count
            
            new_reel = np.full(6, -1, dtype=np.int32)
            new_len = np.zeros(6, dtype=np.int32)
            
            # 按 Java 順序填充: 先新符號 (row 1 到 eliminate_count)，再保留符號
            new_pos = 1
            
            # 先填充新符號
            for _ in range(eliminate_count):
                if new_pos >= 6:
                    break
                new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, reel_idx]))
                # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
                if new_symbol == 24:
                    new_symbol = my_target_symbol
                elif new_symbol == 25:
                    new_symbol = np.int32(my_target_symbol + 11)
                new_reel[new_pos] = new_symbol
                new_len[new_pos] = 1  # 補充符號皆 1x1
                if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                    bonus = 2
                    if m1_count == 0:
                        bonus -= 1
                    multiplier += bonus
                    m1_count += 1
                new_pos += 1
            
            # 再填充保留符號
            for si in range(survive_count):
                if new_pos >= 6:
                    break
                new_reel[new_pos] = survive_symbols[si]
                new_len[new_pos] = survive_lens[si]
                new_pos += 1

            # 保留 R7 位置的符號 (R2-R5 的 row 0)
            if reel_idx in (1, 2, 3, 4):
                new_reel[0] = board[reel_idx, 0]
                new_len[0] = lengths[reel_idx, 0]  # R7 格長度保留(=1)

            board[reel_idx] = new_reel
            lengths[reel_idx] = new_len
        
        # R7 水平掉落 - R7 在 row 0
        r7_symbols = np.full(4, -1, dtype=np.int32)
        r7_pos = 0
        for i in range(4):
            reel_idx = i + 1
            sym = board[reel_idx, 0]
            if sym != -1 and to_remove[reel_idx, 0] == 0:
                r7_symbols[r7_pos] = sym
                r7_pos += 1
        
        while r7_pos < 4:
            new_symbol = np.int32(weighted_choice_numba(drop_weights[drop_idx, 6]))
            # cascade掉落若補到MY/G_MY，沿用本局抽到的轉換symbol(與後端 replaceMysterySymbol 一致)
            if new_symbol == 24:
                new_symbol = my_target_symbol
            elif new_symbol == 25:
                new_symbol = np.int32(my_target_symbol + 11)
            r7_symbols[r7_pos] = new_symbol
            if enable_m1_multiplier and (new_symbol == 2 or new_symbol == 13):
                bonus = 2
                if m1_count == 0:
                    bonus -= 1
                multiplier += bonus
                m1_count += 1
            r7_pos += 1

        # 更新 R7 位置 (row 0)
        for i in range(4):
            board[i + 1, 0] = r7_symbols[i]
            board[6, i] = r7_symbols[i]
            lengths[i + 1, 0] = 1  # R7 皆 1x1
    
    # 計算最終 C1 數量：依 lengths 逐 block head 計 (與後端 link>0 計 head 一致)
    c1_final_count = 0
    for reel_idx in range(6):
        c = 0
        while c < 6:
            sym = board[reel_idx, c]
            L = lengths[reel_idx, c]
            if sym == -1 or L <= 0:
                c += 1
                continue
            if sym == 1:  # C1
                c1_final_count += 1
            c += L
    
    return total_win, c1_final_count, np.int32(multiplier), np.int32(m1_count), cascade_scores

# ========== 多進程支持 ==========

def single_spin(param_set, enable_m1_multiplier=True):
    """執行單次 spin (Python wrapper)，返回 (win, c1_count, multiplier, init_c1_count, c1_len_stats, cascade_scores)
    
    參數:
    - param_set: 參數組 (1 或 2)
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    if param_set == 1:
        return single_spin_core(
            SYMBOL_REELS_1, REEL_LENGTHS_1, WEIGHT_REELS_1,
            MEGAWAY_WEIGHTS_1, MY_WEIGHTS_1, POST_C1_WEIGHTS_1, DROP_WEIGHTS_1,
            MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS,
            enable_m1_multiplier
        )
    else:
        return single_spin_core(
            SYMBOL_REELS_2, REEL_LENGTHS_2, WEIGHT_REELS_2,
            MEGAWAY_WEIGHTS_2, MY_WEIGHTS_2, POST_C1_WEIGHTS_2, DROP_WEIGHTS_2,
            MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS,
            enable_m1_multiplier
        )

# 全域變數，用於 worker 傳遞參數
ENABLE_M1_MULTIPLIER_GLOBAL = True

def run_simulations(n_sims, enable_m1_multiplier=True):
    """執行多次模擬 (Python 版本)，返回 (results, c1_counts, multipliers, init_c1_counts, c1_len_stats)
    
    參數:
    - n_sims: 模擬次數
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    results = np.zeros(n_sims, dtype=np.float64)
    c1_counts = np.zeros(n_sims, dtype=np.int32)
    multipliers = np.zeros(n_sims, dtype=np.int32)
    init_c1_counts = np.zeros(n_sims, dtype=np.int32)
    c1_len_stats = np.zeros(4, dtype=np.int64)  # [len1_total, len2_total, len3_total, len4_total]
    cascade_score_stats = np.zeros(5, dtype=np.float64)
    reel_weight_sum = np.sum(REEL_WEIGHT)
    
    for i in range(n_sims):
        # 選擇參數組
        r = np.random.random() * reel_weight_sum
        param_set = 1 if r < REEL_WEIGHT[0] else 2
        win, c1, mult, init_c1, c1_lens, cascade_scores = single_spin(param_set, enable_m1_multiplier)
        results[i] = win
        c1_counts[i] = c1
        multipliers[i] = mult
        init_c1_counts[i] = init_c1
        c1_len_stats += c1_lens
        cascade_score_stats += cascade_scores
    
    return results, c1_counts, multipliers, init_c1_counts, c1_len_stats, cascade_score_stats

def worker_simulate(args):
    """單個 worker 執行的模擬任務"""
    n_sims, seed, enable_m1 = args
    np.random.seed(seed)
    return run_simulations(n_sims, enable_m1)

def basegame(n_simulations, n_cores=None, enable_m1_multiplier=True):
    """
    執行 Base Game 模擬
    
    參數:
    - n_simulations: 總模擬次數
    - n_cores: 使用的 CPU 核心數，預設為全部核心
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    
    返回:
    - avg_score: 平均得分
    - std_score: 標準差
    - total_time: 執行時間
    """
    global ENABLE_M1_MULTIPLIER_GLOBAL
    ENABLE_M1_MULTIPLIER_GLOBAL = enable_m1_multiplier
    
    if n_cores is None:
        n_cores = cpu_count()
    
    n_cores = min(n_cores, cpu_count())
    
    print(f"開始模擬...")
    print(f"總模擬次數: {n_simulations:,}")
    print(f"使用核心數: {n_cores}")
    print(f"M1 倍數特色: {'開啟' if enable_m1_multiplier else '關閉'}")
    
    start_time = time.time()
    
    # JIT 編譯預熱
    print("JIT 編譯中...")
    _ = run_simulations(10, enable_m1_multiplier)
    compile_time = time.time() - start_time
    print(f"JIT 編譯完成，耗時: {compile_time:.2f}秒")
    
    start_time = time.time()
    
    if n_cores == 1:
        # 單進程模式
        results, c1_counts, multipliers, init_c1_counts, c1_len_stats, cascade_score_stats = run_simulations(n_simulations, enable_m1_multiplier)
    else:
        # 多進程模式
        sims_per_core = n_simulations // n_cores
        remainder = n_simulations % n_cores
        
        tasks = []
        for i in range(n_cores):
            n = sims_per_core + (1 if i < remainder else 0)
            seed = np.random.randint(0, 2**31) + i
            tasks.append((n, seed, enable_m1_multiplier))
        
        with Pool(n_cores) as pool:
            all_results = pool.map(worker_simulate, tasks)
        
        results = np.concatenate([r[0] for r in all_results])
        c1_counts = np.concatenate([r[1] for r in all_results])
        multipliers = np.concatenate([r[2] for r in all_results])
        init_c1_counts = np.concatenate([r[3] for r in all_results])
        c1_len_stats = np.sum([r[4] for r in all_results], axis=0)
        cascade_score_stats = np.sum([r[5] for r in all_results], axis=0)
    
    total_time = time.time() - start_time
    
    # 計算統計
    avg_score = np.mean(results)
    std_score = np.std(results)
    total_score = np.sum(results)
    non_zero = np.sum(results > 0)
    hit_rate = non_zero / n_simulations * 100
    
    # 初始 C1 統計 (0, 1, 2, 3, 4, 5, 6, 7+)
    init_c1_stats = np.zeros(8, dtype=np.int64)
    for i in range(8):
        if i < 7:
            init_c1_stats[i] = np.sum(init_c1_counts == i)
        else:
            init_c1_stats[i] = np.sum(init_c1_counts >= 7)
    
    # 結束 C1 統計 (0, 1, 2, 3, 4, 5, 6, 7+)
    c1_stats = np.zeros(8, dtype=np.int64)
    for i in range(8):
        if i < 7:
            c1_stats[i] = np.sum(c1_counts == i)
        else:
            c1_stats[i] = np.sum(c1_counts >= 7)
    
    # 倍數統計 (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15+)
    mult_stats = np.zeros(15, dtype=np.int64)
    for i in range(15):
        if i < 14:
            mult_stats[i] = np.sum(multipliers == (i + 1))
        else:
            mult_stats[i] = np.sum(multipliers >= 15)
    
    # 得分分布統計 (以 100 為基底)
    # 區間邊界 (乘以 100 得到實際分數邊界)
    score_boundaries = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                        15, 20, 25, 30, 35, 40, 45, 50,
                        60, 70, 80, 90, 100,
                        120, 140, 160, 180, 200,
                        250, 300, 350, 400, 450, 500,
                        550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
                        2000, 3000]
    score_labels = ["[0]", "(0~1]", "(1~2]", "(2~3]", "(3~4]", "(4~5]", "(5~6]", "(6~7]", "(7~8]", "(8~9]", "(9~10]",
                    "(10~15]", "(15~20]", "(20~25]", "(25~30]", "(30~35]", "(35~40]", "(40~45]", "(45~50]",
                    "(50~60]", "(60~70]", "(70~80]", "(80~90]", "(90~100]",
                    "(100~120]", "(120~140]", "(140~160]", "(160~180]", "(180~200]",
                    "(200~250]", "(250~300]", "(300~350]", "(350~400]", "(400~450]", "(450~500]",
                    "(500~550]", "(550~600]", "(600~650]", "(650~700]", "(700~750]", "(750~800]", "(800~850]", "(850~900]", "(900~950]", "(950~1000]",
                    "(1000~2000]", "(2000~3000]", "[3000+]"]
    
    score_stats = np.zeros(len(score_labels), dtype=np.int64)
    normalized_results = results / 100.0  # 以 100 為基底
    
    # [0]
    score_stats[0] = np.sum(normalized_results == 0)
    # (0~1], (1~2], ... (2000~3000]
    for i in range(1, len(score_boundaries)):
        lower = score_boundaries[i - 1]
        upper = score_boundaries[i]
        score_stats[i] = np.sum((normalized_results > lower) & (normalized_results <= upper))
    # [3000+]
    score_stats[-1] = np.sum(normalized_results > 3000)
    
    print(f"\n---------- Cascade 消除平均得分 (BaseGame) ----------")
    cascade_avgs = cascade_score_stats / n_simulations if n_simulations > 0 else np.zeros(5)
    labels = ["第1次", "第2次", "第3次", "第4次", "第5次+"]
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {cascade_avgs[i]:.4f}")
    print(f"  總和(應等於平均總得分): {np.sum(cascade_avgs):.4f}")
    print(f"\n========== 模擬結果 ==========")
    print(f"模擬次數: {n_simulations:,}")
    print(f"總得分: {total_score:,.0f}")
    print(f"平均得分: {avg_score:.4f}")
    print(f"標準差: {std_score:.4f}")
    print(f"中獎率: {hit_rate:.2f}%")
    print(f"RTP: {avg_score:.4f} ({avg_score*100:.2f}%)")
    print(f"執行時間: {total_time:.2f}秒")
    print(f"速度: {n_simulations/total_time:,.0f} spins/秒")
    print(f"\n---------- 初始C1(Scatter) 統計 ----------")
    for i in range(8):
        label = f"{i}" if i < 7 else "7+"
        count = init_c1_stats[i]
        pct = count / n_simulations * 100
        print(f"  初始C1={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"\n---------- 初始C1 長度分布 ----------")
    total_c1 = np.sum(c1_len_stats)
    for i in range(4):
        count = c1_len_stats[i]
        pct = count / total_c1 * 100 if total_c1 > 0 else 0
        print(f"  長度={i+1}: {count:,} 個 ({pct:.4f}%)")
    print(f"  C1 總數: {total_c1:,} 個")
    print(f"\n---------- 結束C1(Scatter) 統計 ----------")
    for i in range(8):
        label = f"{i}" if i < 7 else "7+"
        count = c1_stats[i]
        pct = count / n_simulations * 100
        print(f"  結束C1={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"\n---------- 倍數統計 ----------")
    for i in range(15):
        label = f"{i + 1}" if i < 14 else "15+"
        count = mult_stats[i]
        pct = count / n_simulations * 100
        print(f"  倍數={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"\n---------- 得分分布 (基底=100) ----------")
    for i, label in enumerate(score_labels):
        count = score_stats[i]
        pct = count / n_simulations * 100
        print(f"  {label}: {count:,} 次 ({pct:.4f}%)")
    print(f"===============================")
    
    return avg_score, std_score, total_time, init_c1_stats, c1_stats, mult_stats, score_stats, c1_len_stats

# ========== FreeGame 函數 ==========

def freegame_single_spin(param_set, current_multiplier, current_m1_count, enable_m1_multiplier=True):
    """執行 FreeGame 單次 spin，返回 (win, c1_count, new_multiplier, new_m1_count, cascade_scores)
    
    參數:
    - param_set: 參數組 (1, 2, 或 3)
    - current_multiplier: 當前累計倍數
    - current_m1_count: 當前已累計的 M1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    if param_set == 1:
        return freegame_spin_core(
            FG_SYMBOL_REELS_1, FG_REEL_LENGTHS_1, FG_WEIGHT_REELS_1,
            FG_MEGAWAY_WEIGHTS_1, FG_MY_WEIGHTS_1, FG_POST_C1_WEIGHTS_1, FG_DROP_WEIGHTS_1,
            MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS,
            current_multiplier, current_m1_count, enable_m1_multiplier
        )
    elif param_set == 2:
        return freegame_spin_core(
            FG_SYMBOL_REELS_2, FG_REEL_LENGTHS_2, FG_WEIGHT_REELS_2,
            FG_MEGAWAY_WEIGHTS_2, FG_MY_WEIGHTS_2, FG_POST_C1_WEIGHTS_2, FG_DROP_WEIGHTS_2,
            MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS,
            current_multiplier, current_m1_count, enable_m1_multiplier
        )
    else:
        return freegame_spin_core(
            FG_SYMBOL_REELS_3, FG_REEL_LENGTHS_3, FG_WEIGHT_REELS_3,
            FG_MEGAWAY_WEIGHTS_3, FG_MY_WEIGHTS_3, FG_POST_C1_WEIGHTS_3, FG_DROP_WEIGHTS_3,
            MEGAWAY_PATTERNS, LINKPOINT, TARGET_HEIGHTS,
            current_multiplier, current_m1_count, enable_m1_multiplier
        )

def freegame(trigger_c1_count, verbose=False, enable_m1_multiplier=True):
    """
    執行 FreeGame 模擬
    
    參數:
    - trigger_c1_count: 觸發時的 C1 數量 (4, 5, 6, ...)
    - verbose: 是否輸出詳細信息
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    
    返回:
    - total_win: 總得分
    - final_multiplier: 結束時倍數
    - total_spins: 總 spin 數 (含 retrigger)
    - retrigger_count: retrigger 次數
    """
    # 計算初始場次: 4→10, 5→12, 每多1加2
    initial_spins = 10 + (trigger_c1_count - 4) * 2
    remaining_spins = initial_spins
    initial_remaining = initial_spins  # 追蹤初始場次剩餘
    total_rounds = initial_spins  # 追蹤總場次 (用於最大場次限制)
    max_rounds = 50  # 後端 maxRound 設定
    
    # 初始化
    total_win = 0.0
    multiplier = 1
    m1_count = 0
    total_spins_done = 0
    retrigger_count = 0
    cascade_score_stats = np.zeros(5, dtype=np.float64)
    
    # 權重
    reel_weight_sum = np.sum(FREE_REEL_WEIGHT)
    trigger_weight_sum = np.sum(FREE_TRIGGER_REEL)
    
    while remaining_spins > 0:
        # 選擇參數組：初始場次用 FreeReelWeight，retrigger 用 FreeTriggerReel
        if initial_remaining > 0:
            # 初始場次
            r = np.random.random() * reel_weight_sum
            cumsum = 0.0
            param_set = 1
            for i in range(len(FREE_REEL_WEIGHT)):
                cumsum += FREE_REEL_WEIGHT[i]
                if r < cumsum:
                    param_set = i + 1
                    break
            initial_remaining -= 1
        else:
            # Retrigger 場次
            r = np.random.random() * trigger_weight_sum
            cumsum = 0.0
            param_set = 1
            for i in range(len(FREE_TRIGGER_REEL)):
                cumsum += FREE_TRIGGER_REEL[i]
                if r < cumsum:
                    param_set = i + 1
                    break
        
        # 執行 spin
        win, c1_final, new_mult, new_m1_count, cascade_scores = freegame_single_spin(param_set, multiplier, m1_count, enable_m1_multiplier)
        
        total_win += win
        multiplier = new_mult
        m1_count = new_m1_count
        total_spins_done += 1
        remaining_spins -= 1
        cascade_score_stats += cascade_scores
        
        if verbose:
            print(f"  Spin {total_spins_done}: win={win:.0f}, C1={c1_final}, mult={multiplier}, param={param_set}")
        
        # 檢查 retrigger
        if c1_final >= 4:
            retrigger_spins = 10 + (c1_final - 4) * 2
            # 後端 maxRound 限制：不超過 50 場
            available_rounds = max_rounds - total_rounds
            if available_rounds > 0:
                add_rounds = min(retrigger_spins, available_rounds)
                remaining_spins += add_rounds
                total_rounds += add_rounds
                retrigger_count += 1
                if verbose:
                    print(f"  *** Retrigger! C1={c1_final}, +{add_rounds} spins (total={total_rounds}) ***")
    
    return total_win, multiplier, total_spins_done, retrigger_count, cascade_score_stats

def run_freegame_simulations(n_sims, trigger_c1_count=4, enable_m1_multiplier=True):
    """執行多次 FreeGame 模擬，返回統計數據
    
    參數:
    - n_sims: 模擬次數
    - trigger_c1_count: 觸發時的 C1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    results = np.zeros(n_sims, dtype=np.float64)
    final_multipliers = np.zeros(n_sims, dtype=np.int32)
    total_spins_list = np.zeros(n_sims, dtype=np.int32)
    retrigger_counts = np.zeros(n_sims, dtype=np.int32)
    cascade_score_stats = np.zeros(5, dtype=np.float64)
    total_spins_total = 0
    
    for i in range(n_sims):
        win, mult, spins, retrigs, cascade_scores = freegame(trigger_c1_count, False, enable_m1_multiplier)
        results[i] = win
        final_multipliers[i] = mult
        total_spins_list[i] = spins
        retrigger_counts[i] = retrigs
        cascade_score_stats += cascade_scores
        total_spins_total += spins
    
    return results, final_multipliers, total_spins_list, retrigger_counts, cascade_score_stats, total_spins_total

def simulate_freegame(n_simulations, trigger_c1_count=4, enable_m1_multiplier=True):
    """
    執行 FreeGame 模擬並輸出統計
    
    參數:
    - n_simulations: 模擬次數
    - trigger_c1_count: 觸發時的 C1 數量
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    print(f"開始 FreeGame 模擬...")
    print(f"觸發 C1 數量: {trigger_c1_count}")
    print(f"初始場次: {10 + (trigger_c1_count - 4) * 2}")
    print(f"模擬次數: {n_simulations:,}")
    print(f"M1 倍數特色: {'開啟' if enable_m1_multiplier else '關閉'}")
    
    start_time = time.time()
    
    # JIT 預熱
    print("JIT 編譯中...")
    _ = freegame(4, False, enable_m1_multiplier)
    compile_time = time.time() - start_time
    print(f"JIT 編譯完成，耗時: {compile_time:.2f}秒")
    
    start_time = time.time()
    results, final_mults, total_spins, retrig_counts, cascade_score_stats, total_spins_total = run_freegame_simulations(n_simulations, trigger_c1_count, enable_m1_multiplier)
    total_time = time.time() - start_time
    
    # 統計
    avg_win = np.mean(results)
    std_win = np.std(results)
    avg_mult = np.mean(final_mults)
    avg_spins = np.mean(total_spins)
    avg_retrigs = np.mean(retrig_counts)
    retrig_rate = np.sum(retrig_counts > 0) / n_simulations * 100
    
    # 倍數分布
    mult_stats = np.zeros(15, dtype=np.int64)
    for i in range(15):
        if i < 14:
            mult_stats[i] = np.sum(final_mults == (i + 1))
        else:
            mult_stats[i] = np.sum(final_mults >= 15)
    
    print(f"\n---------- FreeGame Cascade 消除平均得分 ----------")
    if total_spins_total > 0:
        cascade_avgs = cascade_score_stats / total_spins_total
    else:
        cascade_avgs = np.zeros(5, dtype=np.float64)
    labels = ["第1次", "第2次", "第3次", "第4次", "第5次+"]
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {cascade_avgs[i]:.4f}")
    print(f"  總和(應等於 FreeGame 平均每 spin 得分): {np.sum(cascade_avgs):.4f}")
    print(f"\n========== FreeGame 模擬結果 ==========")
    print(f"模擬次數: {n_simulations:,}")
    print(f"平均得分: {avg_win:.4f}")
    print(f"標準差: {std_win:.4f}")
    print(f"平均結束倍數: {avg_mult:.2f}")
    print(f"平均 spin 數: {avg_spins:.2f}")
    print(f"平均 retrigger 次數: {avg_retrigs:.4f}")
    print(f"Retrigger 機率: {retrig_rate:.4f}%")
    print(f"執行時間: {total_time:.2f}秒")
    print(f"速度: {n_simulations/total_time:,.0f} FG/秒")
    print(f"\n---------- 結束倍數統計 ----------")
    for i in range(15):
        label = f"{i + 1}" if i < 14 else "15+"
        count = mult_stats[i]
        pct = count / n_simulations * 100
        print(f"  倍數={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"=======================================")
    
    return avg_win, std_win, avg_mult, avg_spins, mult_stats

# ========== Full Game 函數 ==========

def single_full_game(enable_m1_multiplier=True):
    """
    執行單次完整遊戲 (BaseGame + 可能的 FreeGame)
    
    參數:
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    
    返回:
    - total_win: 總得分
    - bg_win: BaseGame 得分
    - fg_win: FreeGame 得分
    - fg_triggered: 是否觸發 FreeGame (0/1)
    - fg_retrigger: FreeGame 中是否有 retrigger (0/1)
    - c1_count: 結束時 C1 數量
    """
    # 執行 BaseGame
    reel_weight_sum = np.sum(REEL_WEIGHT)
    r = np.random.random() * reel_weight_sum
    param_set = 1 if r < REEL_WEIGHT[0] else 2
    
    bg_win, c1_count, mult, init_c1, _, bg_cascade_scores = single_spin(param_set, enable_m1_multiplier)
    
    fg_win = 0.0
    fg_triggered = 0
    fg_retrigger = 0
    fg_cascade_scores = np.zeros(5, dtype=np.float64)
    
    # 檢查是否觸發 FreeGame
    if c1_count >= 4:
        fg_triggered = 1
        fg_total_win, fg_mult, fg_spins, retrig_count, fg_cascade_scores = freegame(c1_count, False, enable_m1_multiplier)
        fg_win = fg_total_win
        if retrig_count > 0:
            fg_retrigger = 1
    
    total_win = bg_win + fg_win
    return total_win, bg_win, fg_win, fg_triggered, fg_retrigger, c1_count, bg_cascade_scores, fg_cascade_scores

def run_full_game_simulations(n_sims, enable_m1_multiplier=True):
    """執行多次完整遊戲模擬
    
    參數:
    - n_sims: 模擬次數
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    """
    total_wins = np.zeros(n_sims, dtype=np.float64)
    bg_wins = np.zeros(n_sims, dtype=np.float64)
    fg_wins = np.zeros(n_sims, dtype=np.float64)
    fg_triggered = np.zeros(n_sims, dtype=np.int32)
    fg_retriggered = np.zeros(n_sims, dtype=np.int32)
    c1_counts = np.zeros(n_sims, dtype=np.int32)
    bg_cascade_stats = np.zeros(5, dtype=np.float64)
    fg_cascade_stats = np.zeros(5, dtype=np.float64)
    
    for i in range(n_sims):
        total, bg, fg, trig, retrig, c1, bg_cascade_scores, fg_cascade_scores = single_full_game(enable_m1_multiplier)
        total_wins[i] = total
        bg_wins[i] = bg
        fg_wins[i] = fg
        fg_triggered[i] = trig
        fg_retriggered[i] = retrig
        c1_counts[i] = c1
        bg_cascade_stats += bg_cascade_scores
        fg_cascade_stats += fg_cascade_scores
    
    return total_wins, bg_wins, fg_wins, fg_triggered, fg_retriggered, c1_counts, bg_cascade_stats, fg_cascade_stats

def worker_full_game(args):
    """單個 worker 執行的完整遊戲模擬任務"""
    n_sims, seed, enable_m1 = args
    np.random.seed(seed)
    return run_full_game_simulations(n_sims, enable_m1)

def full_game(n_simulations, n_cores=None, enable_m1_multiplier=True):
    """
    執行完整遊戲模擬 (BaseGame + FreeGame)
    
    參數:
    - n_simulations: 總模擬次數
    - n_cores: 使用的 CPU 核心數，預設為全部核心
    - enable_m1_multiplier: 是否開啟 M1 倍數特色 (預設 True)
    
    返回:
    - avg_total: 總平均得分
    - avg_bg: BaseGame 平均得分
    - avg_fg: FreeGame 平均得分
    - fg_trigger_rate: FreeGame 觸發機率
    - fg_retrigger_rate: FreeGame 中 retrigger 比例
    """
    global ENABLE_M1_MULTIPLIER_GLOBAL
    ENABLE_M1_MULTIPLIER_GLOBAL = enable_m1_multiplier
    
    if n_cores is None:
        n_cores = cpu_count()
    
    n_cores = min(n_cores, cpu_count())
    
    print(f"開始完整遊戲模擬...")
    print(f"總模擬次數: {n_simulations:,}")
    print(f"使用核心數: {n_cores}")
    print(f"M1 倍數特色: {'開啟' if enable_m1_multiplier else '關閉'}")
    
    start_time = time.time()
    
    # JIT 編譯預熱
    print("JIT 編譯中...")
    _ = run_full_game_simulations(10, enable_m1_multiplier)
    compile_time = time.time() - start_time
    print(f"JIT 編譯完成，耗時: {compile_time:.2f}秒")
    
    start_time = time.time()
    
    if n_cores == 1:
        # 單進程模式
        total_wins, bg_wins, fg_wins, fg_triggered, fg_retriggered, c1_counts, bg_cascade_stats, fg_cascade_stats = run_full_game_simulations(n_simulations, enable_m1_multiplier)
    else:
        # 多進程模式
        sims_per_core = n_simulations // n_cores
        remainder = n_simulations % n_cores
        
        tasks = []
        for i in range(n_cores):
            n = sims_per_core + (1 if i < remainder else 0)
            seed = np.random.randint(0, 2**31) + i
            tasks.append((n, seed, enable_m1_multiplier))
        
        with Pool(n_cores) as pool:
            all_results = pool.map(worker_full_game, tasks)
        
        total_wins = np.concatenate([r[0] for r in all_results])
        bg_wins = np.concatenate([r[1] for r in all_results])
        fg_wins = np.concatenate([r[2] for r in all_results])
        fg_triggered = np.concatenate([r[3] for r in all_results])
        fg_retriggered = np.concatenate([r[4] for r in all_results])
        c1_counts = np.concatenate([r[5] for r in all_results])
        bg_cascade_stats = np.sum([r[6] for r in all_results], axis=0)
        fg_cascade_stats = np.sum([r[7] for r in all_results], axis=0)
    
    total_time = time.time() - start_time
    
    # 統計
    avg_total = np.mean(total_wins)
    avg_bg = np.mean(bg_wins)
    avg_fg = np.mean(fg_wins)
    std_total = np.std(total_wins)
    
    fg_trigger_count = np.sum(fg_triggered)
    fg_trigger_rate = fg_trigger_count / n_simulations * 100
    
    fg_retrig_count = np.sum(fg_retriggered)
    fg_retrig_rate = fg_retrig_count / fg_trigger_count * 100 if fg_trigger_count > 0 else 0
    
    # C1 統計
    c1_stats = np.zeros(8, dtype=np.int64)
    for i in range(8):
        if i < 7:
            c1_stats[i] = np.sum(c1_counts == i)
        else:
            c1_stats[i] = np.sum(c1_counts >= 7)
    
    print(f"\n---------- BaseGame Cascade 消除平均得分 ----------")
    bg_cascade_avgs = bg_cascade_stats / n_simulations if n_simulations > 0 else np.zeros(5)
    labels = ["第1次", "第2次", "第3次", "第4次", "第5次+"]
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {bg_cascade_avgs[i]:.4f}")
    print(f"  總和(應等於 BaseGame 平均總得分): {np.sum(bg_cascade_avgs):.4f}")

    print(f"\n---------- FreeGame Cascade 消除平均得分 ----------")
    fg_cascade_avgs = fg_cascade_stats / n_simulations if n_simulations > 0 else np.zeros(5)
    for i in range(5):
        print(f"  {labels[i]}消除平均得分: {fg_cascade_avgs[i]:.4f}")
    print(f"  總和(應等於 FreeGame 平均總得分): {np.sum(fg_cascade_avgs):.4f}")
    print(f"\n========== 完整遊戲模擬結果 ==========")
    print(f"模擬次數: {n_simulations:,}")
    print(f"")
    print(f"---------- 得分統計 ----------")
    print(f"總平均得分: {avg_total:.4f}")
    print(f"  BaseGame: {avg_bg:.4f} ({avg_bg/avg_total*100:.2f}%)")
    print(f"  FreeGame: {avg_fg:.4f} ({avg_fg/avg_total*100:.2f}%)")
    print(f"標準差: {std_total:.4f}")
    print(f"")
    print(f"---------- FreeGame 統計 ----------")
    print(f"FreeGame 觸發次數: {fg_trigger_count:,}")
    print(f"FreeGame 觸發機率: {fg_trigger_rate:.4f}%")
    print(f"有 Retrigger 的 FreeGame: {fg_retrig_count:,} / {fg_trigger_count:,}")
    print(f"Retrigger 比例: {fg_retrig_rate:.4f}%")
    print(f"")
    print(f"---------- C1(Scatter) 統計 ----------")
    for i in range(8):
        label = f"{i}" if i < 7 else "7+"
        count = c1_stats[i]
        pct = count / n_simulations * 100
        print(f"  C1={label}: {count:,} 次 ({pct:.4f}%)")
    print(f"")
    print(f"執行時間: {total_time:.2f}秒")
    print(f"速度: {n_simulations/total_time:,.0f} games/秒")
    print(f"==========================================")
    
    return avg_total, avg_bg, avg_fg, fg_trigger_rate, fg_retrig_rate

# ========== 符號名稱對照 (用於除錯顯示) ==========
SYMBOL_NAMES = {
    0: 'WD', 1: 'SP',
    2: 'M1', 3: 'M2', 4: 'M3', 5: 'M4', 6: 'M5', 7: 'M6',
    8: 'A', 9: 'K', 10: 'Q', 11: 'J', 12: 'TE',
    13: 'GM1', 14: 'GM2', 15: 'GM3', 16: 'GM4', 17: 'GM5', 18: 'GM6',
    19: 'GA', 20: 'GK', 21: 'GQ', 22: 'GJ', 23: 'GTE',
    24: 'MY', 25: 'GMY'
}

#python "101016 simulation.py" 100000 10 full    # 完整遊戲
#python "101016 simulation.py" 100000 10 bg      # 只有 BaseGame
#python "101016 simulation.py" 1000 1 fg 4       # 只有 FreeGame (4個C1觸發)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("用法:")
        print("  python simulation.py <次數> <核心數> <模式> [M1開關] [觸發C1數]")
        print("模式: bg=BaseGame, fg=FreeGame, full=完整遊戲")
        print("M1開關: 1=開啟(預設), 0=關閉")
        print("範例:")
        print("  python simulation.py 100000 10 bg        # M1開啟")
        print("  python simulation.py 100000 10 bg 0      # M1關閉")
        print("  python simulation.py 100000 10 full")
        print("  python simulation.py 1000 1 fg 1 4       # FreeGame, M1開啟, 觸發C1=4")
        print("  python simulation.py 1000 1 fg 0 5       # FreeGame, M1關閉, 觸發C1=5")
        sys.exit(1)
    
    n_sims = int(sys.argv[1])
    n_cores = int(sys.argv[2])
    mode = sys.argv[3].lower()
    
    if mode == "bg":
        enable_m1 = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
        basegame(n_sims, n_cores, enable_m1)
    elif mode == "full":
        enable_m1 = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
        full_game(n_sims, n_cores, enable_m1)
    elif mode == "fg":
        enable_m1 = bool(int(sys.argv[4])) if len(sys.argv) > 4 else True
        trigger_c1 = int(sys.argv[5]) if len(sys.argv) > 5 else 4
        simulate_freegame(n_sims, trigger_c1, enable_m1)
    else:
        print(f"未知模式: {mode}")
        print("可用模式: bg, fg, full")
        sys.exit(1)

# %%
