#%%
import re
import numpy as np
import math
from numba import jit, njit, types
from numba.typed import Dict
import numba

def extract_all_js_vars_numpy(filename):
    """智能加载JS数据，根据变量名自动选择数据类型"""
    with open(filename, encoding='utf-8') as f:
        js = f.read()
    results = {}
    
    # 定义需要使用整数类型的变量名模式
    int_patterns = ['Symbol', 'GameHigh', 'GameLow', 'FreeGameHigh', 'FreeGameLow', 'SuperFreeGame']
    
    for m in re.finditer(r'const (\w+) = (.*?);', js, re.DOTALL):
        name = m.group(1)
        arr_str = m.group(2)
        arr_str = arr_str.replace('null', 'np.nan').replace('true', 'True').replace('false', 'False')
        try:
            arr = eval(arr_str, {"np": np, "True": True, "False": False})
            
            # 根据变量名决定数据类型
            if any(pattern in name for pattern in int_patterns):
                # 符号表和游戏高低表使用int32
                np_arr = np.array(arr, dtype=np.int32)
            else:
                # 权重、linkpoint等使用float64
                np_arr = np.array(arr, dtype=np.float64)
            
            results[name] = np_arr
        except Exception:
            pass
    return results

# 使用
all_arrays = extract_all_js_vars_numpy('data.js')
globals().update(all_arrays)

# 動態獲取符號表長度
def get_reel_length():
    """從載入的數據中動態獲取符號表長度"""
    # 嘗試從已載入的全域變數中獲取長度
    for var_name in ['baseGameSymbolHigh', 'baseGameSymbolLow', 'freeGameSymbolHighA']:
        if var_name in globals() and globals()[var_name] is not None:
            return globals()[var_name].shape[1]  # 返回第2維度的長度
    # 如果都找不到，返回預設長度
    return 64

# 動態獲取實際的符號表長度
REEL_LENGTH = get_reel_length()

# 預處理數據：轉置drop weights以提高訪問效率
# 將從data.js載入的5x21權重矩陣轉置為21x5，這樣可以直接用row索引訪問
def preprocess_drop_weights():
    """預處理掉落權重數據，將5輪x21符號轉為符合使用需求的格式"""
    weight_vars = [
        'baseDropWeights1st', 'baseDropWeights2nd', 'baseDropWeights3rd', 'baseDropWeights4th',
        'baseDropLowWeights1st', 'baseDropLowWeights2nd', 'baseDropLowWeights3rd', 'baseDropLowWeights4th',
        'freeHighDropWeights1st', 'freeHighDropWeights2nd', 'freeHighDropWeights3rd', 'freeHighDropWeights4th',
        'freeLowDropWeights1st', 'freeLowDropWeights2nd', 'freeLowDropWeights3rd', 'freeLowDropWeights4th'
    ]
    
    for var_name in weight_vars:
        if var_name in globals() and globals()[var_name] is not None:
            arr = globals()[var_name]
            # 確保數據格式正確並轉為float32以節省內存
            if arr.shape == (5, 21):
                globals()[var_name] = arr.astype(np.float32)
            elif arr.shape == (21, 5):
                # 已經是正確格式，只需轉換類型
                globals()[var_name] = arr.T.astype(np.float32)

# 執行預處理
preprocess_drop_weights()

# 預編譯和緩存常用的數據結構
@njit
def get_precompiled_data():
    """預編譯常用數據結構以提升性能 - 新符號映射"""
    symbol_to_lp = np.full(21, -1, dtype=np.int32)  # 擴展到21個符號位置
    
    # M1~M9 普通符號 (2~10 → linkpoint 0~8)
    for i in range(9):
        symbol_to_lp[2+i] = i
    
    # M1G~M9G 黃金符號 (11~19 → linkpoint 0~8，與普通符號共用)
    for i in range(9):
        symbol_to_lp[11+i] = i
    
    # MY 符號 (20) 不需要 linkpoint 映射，因為會被轉換為其他符號
    # symbol_to_lp[20] = -1  # 保持預設的 -1
    
    return symbol_to_lp

# 全局預編譯數據
PRECOMPILED_SYMBOL_TO_LP = get_precompiled_data()

# 版面形狀配置 - 從 [4,4,4,4,4] 改為 [4,5,5,5,4]
BOARD_SHAPE = np.array([4, 5, 5, 5, 4], dtype=np.int32)

# SCATTER觸發場次配置矩陣 [scatter數量: [高表場次, 低表場次]]
# 索引對應scatter數量 (0-2不觸發, 3-23觸發)
a = 2
SCATTER_SPINS_MATRIX = np.array([
    [0, 0],   # 0個scatter - 不觸發
    [0, 0],   # 1個scatter - 不觸發  
    [0, 0],   # 2個scatter - 不觸發
    [a, 10-a],   # 3個scatter → 2高表8低表
    [a, 12-a],  # 4個scatter → 2高表10低表
    [a, 14-a],  # 5個scatter → 2高表12低表
    [a, 16-a],  # 6個scatter → 2高表14低表
    [a, 18-a],  # 7個scatter → 2高表16低表
    [a, 20-a],  # 8個scatter → 2高表18低表
    [a, 22-a],  # 9個scatter → 2高表20低表
    [a, 24-a],  # 10個scatter → 2高表22低表
    [a, 26-a],  # 11個scatter → 2高表24低表
    [a, 28-a],  # 12個scatter → 2高表26低表
    [a, 30-a],  # 13個scatter → 2高表28低表
    [a, 32-a],  # 14個scatter → 2高表30低表
    [a, 34-a],  # 15個scatter → 2高表32低表
    [a, 36-a],  # 16個scatter → 2高表34低表
    [a, 38-a],  # 17個scatter → 2高表36低表
    [a, 40-a],  # 18個scatter → 2高表38低表
    [a, 42-a],  # 19個scatter → 2高表40低表
    [a, 44-a],  # 20個scatter → 2高表42低表
    [a, 46-a],  # 21個scatter → 2高表44低表
    [a, 48-a],  # 22個scatter → 2高表46低表
    [a, 50-a],  # 23個scatter → 2高表48低表
], dtype=np.int32)

@njit
def get_scatter_spins(scatter_count):
    """
    根據 Scatter 數量從矩陣查找場次配置
    使用 SCATTER_SPINS_MATRIX 矩陣資料
    """
    if scatter_count < 3:
        return 0, 0  # 不觸發
    elif scatter_count > 23:
        scatter_count = 23  # 最大限制為23個
    
    # 從矩陣中查找對應的場次配置
    high_spins = SCATTER_SPINS_MATRIX[scatter_count, 0]
    low_spins = SCATTER_SPINS_MATRIX[scatter_count, 1]
    
    return high_spins, low_spins

@njit
def sample_sequences_weighted_numba(weight_array, content_array, n, seed=None):
    """
    Numba加速版本的加權抽樣函數
    """
    if seed is not None:
        np.random.seed(seed)
    
    lines, length = weight_array.shape
    output = np.zeros((lines, n), dtype=content_array.dtype)
    
    for i in range(lines):
        w = weight_array[i]
        w_sum = np.sum(w)
        if w_sum == 0:
            # 如果權重全為0，隨機選擇
            for j in range(n):
                start = np.random.randint(0, length)
                idx = (start + j) % length
                output[i, j] = content_array[i, idx]
        else:
            # 加權隨機抽一個位置
            prob = w / w_sum
            cumsum = np.cumsum(prob)
            r = np.random.random()
            start = 0
            for k in range(length):
                if r <= cumsum[k]:
                    start = k
                    break
            
            # 從start開始取n個連續元素
            for j in range(n):
                idx = (start + j) % length
                output[i, j] = content_array[i, idx]
    
    return output

@njit
def sample_sequences_weighted_irregular_numba(weight_array, content_array, row_lengths, seed=None):
    """
    Numba加速版本的不規則形狀加權抽樣函數
    支援每行不同的長度
    """
    if seed is not None:
        np.random.seed(seed)
    
    lines, reel_length = weight_array.shape
    max_cols = np.max(row_lengths)
    output = np.zeros((lines, max_cols), dtype=content_array.dtype)
    
    for i in range(lines):
        n = row_lengths[i]  # 該行的長度
        w = weight_array[i]
        w_sum = np.sum(w)
        if w_sum == 0:
            # 如果權重全為0，隨機選擇
            for j in range(n):
                start = np.random.randint(0, reel_length)
                idx = (start + j) % reel_length
                output[i, j] = content_array[i, idx]
        else:
            # 加權隨機抽一個位置
            prob = w / w_sum
            cumsum = np.cumsum(prob)
            r = np.random.random()
            start = 0
            for k in range(reel_length):
                if r <= cumsum[k]:
                    start = k
                    break
            
            # 從start開始取n個連續元素
            for j in range(n):
                idx = (start + j) % reel_length
                output[i, j] = content_array[i, idx]
    
    return output

@njit
def generate_drop_symbol_numba(row, col, eliminate_count, game_type,
                              drop_weights_1st, drop_weights_2nd, drop_weights_3rd, drop_weights_4th,
                              my_convert_weights, my_target_symbol):
    """
    根據消除次數和遊戲類型生成新的掉落符號
    
    參數:
        row: 行索引 (0-4)
        col: 列索引 (0-4)  
        eliminate_count: 消除次數 (1, 2, 3, 4+)
        game_type: 遊戲類型 (0=BASE, 1=FREE_HIGH, 2=FREE_LOW)
        drop_weights_*: 對應消除次數的21×5權重矩陣
        my_convert_weights: MY轉換為M1~M9的9×1權重向量 (用於預先決定轉換目標)
        my_target_symbol: 本輪MY統一轉換的目標符號 (2-10對應M1-M9)
    
    返回:
        symbol: 生成的符號 (0-20)
    """
    # 根據消除次數選擇權重矩陣
    # 修正索引：data.js格式是(5輪, 21符號)，所以使用[row, :]取得該輪的符號權重
    if eliminate_count == 1:
        weights = drop_weights_1st[row, :]
    elif eliminate_count == 2:
        weights = drop_weights_2nd[row, :]
    elif eliminate_count == 3:
        weights = drop_weights_3rd[row, :]
    else:  # 4次及以後
        weights = drop_weights_4th[row, :]
    
    # 正規化權重
    weight_sum = np.sum(weights)
    if weight_sum == 0:
        # 如果權重全為0，均勻隨機選擇 (排除WW=0和C1=1)
        return np.random.randint(2, 21)
    
    # 加權隨機選擇符號
    prob = weights / weight_sum
    cumsum = np.cumsum(prob)
    r = np.random.random()
    
    symbol = 0
    for i in range(21):
        if r <= cumsum[i]:
            symbol = i
            break
    
    # 如果選到MY(20)，統一轉換為預先決定的目標符號
    if symbol == 20:  # MY
        symbol = my_target_symbol  # 使用本輪統一的轉換目標
    
    return symbol

@njit
def build_symbol_to_linkpoint_numba():
    """
    Numba加速版本的符號映射建立函數 - 使用預編譯版本
    """
    return PRECOMPILED_SYMBOL_TO_LP

@njit
def waygame_fullscore_numba(board, linkpoint):
    """
    Numba加速版本的計分函數 - 支援新符號映射
    """
    symbol_to_lp = build_symbol_to_linkpoint_numba()
    total_score = 0
    details = np.zeros((10,3), dtype=np.int32)  # 擴展到10行 (M1~M9 + MY)
    rows, cols = board.shape
    
    for symbol_lp in range(10):  # 0~8:M1~M9, 9:MY
        valid_symbol = np.where(symbol_to_lp == symbol_lp)[0]
        
        for c0 in range(BOARD_SHAPE[0]):
            # 檢查起點是否有效
            symbol_idx = int(board[0, c0])
            can_start = False
            
            if symbol_idx == 0:  # Wild符號可以作為任何符號的起點
                can_start = True
            elif symbol_idx == 1:  # C1符號不能作為起點
                can_start = False
            elif symbol_idx < len(symbol_to_lp) and symbol_to_lp[symbol_idx] == symbol_lp:
                can_start = True
            
            if not can_start:
                continue
            
            # 建立匹配遮罩
            mask_lengths = np.zeros(rows, dtype=np.int32)
            mask = np.zeros((rows, np.max(BOARD_SHAPE)), dtype=np.int32)
            
            for r in range(rows):
                row_cols = BOARD_SHAPE[r]
                count = 0
                if r == 0:
                    if (board[0, c0] in valid_symbol) or (board[0, c0] == 0):  # Wild符號
                        mask[r, count] = c0
                        count = 1
                else:
                    for c in range(row_cols):
                        s = board[r, c]
                        if s == 0 or s in valid_symbol:  # Wild符號或有效符號
                            if s != 1:  # 排除C1符號
                                mask[r, count] = c
                                count += 1
                    if count == 0:
                        break
                mask_lengths[r] = count
            
            # 計算最大連線長度和路徑數
            max_conn = 0
            max_ways = 0
            for conn in range(3, 6):
                if conn <= len(mask_lengths) and np.all(mask_lengths[:conn] > 0):
                    ways = 1
                    for layer in range(conn):
                        ways *= mask_lengths[layer]
                    if ways > 0 and conn > max_conn:
                        max_conn = conn
                        max_ways = ways
            
            if max_conn >= 3:
                details[symbol_lp, max_conn-3] += max_ways
    
    # 計算總分 - 只使用前9行details (M1~M9)，忽略MY分數
    details_scoring = details[:9, :]  # 只取M1~M9的details
    
    if linkpoint.shape == (3,9):
        linkpoint_t = linkpoint.T
    elif linkpoint.shape == (9,3):
        linkpoint_t = linkpoint
    else:
        # 兼容舊格式 - 擴展到新格式
        if linkpoint.shape == (8,3):
            extended_linkpoint = np.zeros((9,3), dtype=linkpoint.dtype)
            extended_linkpoint[:8,:] = linkpoint
            linkpoint_t = extended_linkpoint
        elif linkpoint.shape == (10,3):  # 舊版本有MY分數的格式
            linkpoint_t = linkpoint[:9,:]  # 只取前9行，移除MY分數
        else:
            linkpoint_t = linkpoint
    
    total_score = np.sum(details_scoring * linkpoint_t)
    return total_score, details

@njit
def point_numba(weight_array, reel_array, initial_board, linkpoint, 
               drop_weights_1st, drop_weights_2nd, drop_weights_3rd, drop_weights_4th,
               my_convert_weights, game_type=0, seed=None):
    """
    Numba加速版本的遊戲主函數 - 已移除 RANDOMWILD 功能，新增掉落符號機制
    
    新增參數:
        drop_weights_*: 消除次數對應的21×5權重矩陣
        my_convert_weights: MY轉換權重9×1向量
        game_type: 遊戲類型 (0=BASE, 1=FREE_HIGH, 2=FREE_LOW)
    """
    if seed is not None:
        np.random.seed(seed)
    
    rows, cols = initial_board.shape
    board = initial_board.astype(np.int32).copy()
    total_score = 0
    golden_symbols_converted_this_round = 0
    cascade_count = 0
    
    # 【初始版面優化】預先決定初始版面MY符號的統一轉換目標
    my_weight_sum = np.sum(my_convert_weights)
    if my_weight_sum > 0:
        my_prob = my_convert_weights / my_weight_sum
        my_cumsum = np.cumsum(my_prob)
        my_r = np.random.random()
        initial_my_target = 2  # 預設M1
        for i in range(9):
            if my_r <= my_cumsum[i]:
                initial_my_target = 2 + i  # M1~M9 對應 2~10
                break
    else:
        initial_my_target = 2  # 權重全為0時預設M1
    
    # 將初始版面的所有MY符號統一轉換為目標符號
    for r in range(rows):
        row_cols = BOARD_SHAPE[r]
        for c in range(row_cols):
            if board[r, c] == 20:  # MY符號
                board[r, c] = initial_my_target
    
    while True:
        
        score, details = waygame_fullscore_numba(board, linkpoint)
        
        if score == 0:
            break
        
        cascade_count += 1
        
        # 【優化】每輪消除前預先決定本輪MY符號的統一轉換目標
        my_weight_sum = np.sum(my_convert_weights)
        if my_weight_sum > 0:
            my_prob = my_convert_weights / my_weight_sum
            my_cumsum = np.cumsum(my_prob)
            my_r = np.random.random()
            my_target_symbol = 2  # 預設M1
            for i in range(9):
                if my_r <= my_cumsum[i]:
                    my_target_symbol = 2 + i  # M1~M9 對應 2~10
                    break
        else:
            my_target_symbol = 2  # 權重全為0時預設M1
        
        # 計算乘倍效果
        if cascade_count == 1:
            multiplier = 1
        elif cascade_count == 2:
            multiplier = 2
        elif cascade_count == 3:
            multiplier = 3
        else:
            multiplier = 5
            
        multiplied_score = score * multiplier
        total_score += multiplied_score
        
        # 找出有得分的符號位置並處理消除
        symbol_to_lp = build_symbol_to_linkpoint_numba()
        elimination_mask = np.zeros_like(board, dtype=np.bool_)
        golden_symbols_to_convert = []
        
        for symbol_lp in range(10):  # 更新為10個符號類型 (M1~M9 + MY)
            valid_symbol = np.where(symbol_to_lp == symbol_lp)[0]
            for c0 in range(BOARD_SHAPE[0]):
                symbol_idx = int(board[0, c0])
                can_start = False
                
                if symbol_idx == 0:  # Wild符號
                    can_start = True
                elif symbol_idx == 1:  # C1符號不能作為起點
                    can_start = False
                elif symbol_idx < len(symbol_to_lp) and symbol_to_lp[symbol_idx] == symbol_lp:
                    can_start = True
                
                if not can_start:
                    continue
                
                # 建立匹配路徑
                mask_lengths = np.zeros(rows, dtype=np.int32)
                mask = np.zeros((rows, np.max(BOARD_SHAPE)), dtype=np.int32)
                
                for r in range(rows):
                    row_cols = BOARD_SHAPE[r]
                    count = 0
                    if r == 0:
                        if (board[0, c0] in valid_symbol) or (board[0, c0] == 0):  # Wild符號
                            mask[r, count] = c0
                            count = 1
                    else:
                        for c in range(row_cols):
                            s = board[r, c]
                            if s == 0 or s in valid_symbol:  # Wild符號或有效符號
                                if s != 1:  # 排除C1符號
                                    mask[r, count] = c
                                    count += 1
                        if count == 0:
                            break
                    mask_lengths[r] = count
                
                # 找出最大連線長度
                max_conn = 0
                for conn in range(3, 6):
                    if conn <= len(mask_lengths) and np.all(mask_lengths[:conn] > 0):
                        ways = 1
                        for layer in range(conn):
                            ways *= mask_lengths[layer]
                        if ways > 0 and conn > max_conn:
                            max_conn = conn
                
                if max_conn >= 3:
                    for r in range(max_conn):
                        for idx in range(mask_lengths[r]):
                            c = mask[r, idx]
                            symbol = board[r, c]
                            if 11 <= symbol <= 19:  # M1G~M9G
                                golden_symbols_to_convert.append((r, c))
                            else:
                                elimination_mask[r, c] = True
        
        # 處理黃金符號轉換 - 優化為numba兼容版本
        # 使用字典模擬set去重
        seen = {}
        for r, c in golden_symbols_to_convert:
            key = r * 1000 + c
            if key not in seen:
                seen[key] = True
                if board[r, c] >= 11 and board[r, c] <= 19:  # M1G~M9G
                    board[r, c] = 0
                    golden_symbols_converted_this_round += 1
        
        # 消除符號
        for r in range(rows):
            row_cols = BOARD_SHAPE[r]
            for c in range(row_cols):
                if elimination_mask[r, c]:
                    board[r, c] = -1
        
        # 重力下降 - 優化為數組操作
        for r in range(rows):
            row_cols = BOARD_SHAPE[r]
            # 計算非空符號數量
            non_empty_count = 0
            for c in range(row_cols):
                if board[r, c] != -1:
                    non_empty_count += 1
            
            # 創建臨時數組存儲非空符號
            if non_empty_count > 0:
                temp = np.empty(non_empty_count, dtype=np.int32)
                idx = 0
                for c in range(row_cols):
                    if board[r, c] != -1:
                        temp[idx] = board[r, c]
                        idx += 1
                # 重新填充
                for c in range(non_empty_count):
                    board[r, c] = temp[c]
            # 填充空位
            for c in range(non_empty_count, row_cols):
                board[r, c] = -1
        
        # 補充新符號 - 使用新的掉落機制
        for r in range(rows):
            row_cols = BOARD_SHAPE[r]
            for c in range(row_cols-1, -1, -1):
                if board[r, c] == -1:
                    # 使用新的掉落符號生成邏輯，傳入本輪統一的MY轉換目標
                    new_symbol = generate_drop_symbol_numba(
                        r, c, cascade_count, game_type,
                        drop_weights_1st, drop_weights_2nd, drop_weights_3rd, drop_weights_4th,
                        my_convert_weights, my_target_symbol
                    )
                    board[r, c] = new_symbol
    
    return total_score, board

@njit
def freegame_point_numba(weight_array, reel_array, initial_board, linkpoint,
                        drop_weights_1st, drop_weights_2nd, drop_weights_3rd, drop_weights_4th,
                        my_convert_weights, game_type=1, seed=None):
    """
    Numba加速版本的免費遊戲函數 - 已移除 RANDOMWILD 功能，新增掉落符號機制
    
    新增參數:
        drop_weights_*: 消除次數對應的21×5權重矩陣
        my_convert_weights: MY轉換權重9×1向量
        game_type: 遊戲類型 (預設1=FREE_HIGH，2=FREE_LOW)
    """
    if seed is not None:
        np.random.seed(seed)
    
    rows, cols = initial_board.shape
    board = initial_board.astype(np.int32).copy()
    total_score = 0
    golden_symbols_converted_this_round = 0
    cascade_count = 0
    
    # 【初始版面優化】預先決定初始版面MY符號的統一轉換目標
    my_weight_sum = np.sum(my_convert_weights)
    if my_weight_sum > 0:
        my_prob = my_convert_weights / my_weight_sum
        my_cumsum = np.cumsum(my_prob)
        my_r = np.random.random()
        initial_my_target = 2  # 預設M1
        for i in range(9):
            if my_r <= my_cumsum[i]:
                initial_my_target = 2 + i  # M1~M9 對應 2~10
                break
    else:
        initial_my_target = 2  # 權重全為0時預設M1
    
    # 將初始版面的所有MY符號統一轉換為目標符號
    for r in range(rows):
        row_cols = BOARD_SHAPE[r]
        for c in range(row_cols):
            if board[r, c] == 20:  # MY符號
                board[r, c] = initial_my_target
    
    while True:
        
        score, details = waygame_fullscore_numba(board, linkpoint)
        
        if score == 0:
            break
        
        cascade_count += 1
        
        # 【優化】每輪消除前預先決定本輪MY符號的統一轉換目標
        my_weight_sum = np.sum(my_convert_weights)
        if my_weight_sum > 0:
            my_prob = my_convert_weights / my_weight_sum
            my_cumsum = np.cumsum(my_prob)
            my_r = np.random.random()
            my_target_symbol = 2  # 預設M1
            for i in range(9):
                if my_r <= my_cumsum[i]:
                    my_target_symbol = 2 + i  # M1~M9 對應 2~10
                    break
        else:
            my_target_symbol = 2  # 權重全為0時預設M1
        
        # Free Game乘倍係數
        if cascade_count == 1:
            multiplier = 2
        elif cascade_count == 2:
            multiplier = 4
        elif cascade_count == 3:
            multiplier = 6
        else:
            multiplier = 10
            
        multiplied_score = score * multiplier
        total_score += multiplied_score
        
        # 找出有得分的符號位置並處理消除
        symbol_to_lp = build_symbol_to_linkpoint_numba()
        elimination_mask = np.zeros_like(board, dtype=np.bool_)
        golden_symbols_to_convert = []
        
        for symbol_lp in range(10):  # 更新為10個符號類型 (M1~M9 + MY)
            valid_symbol = np.where(symbol_to_lp == symbol_lp)[0]
            for c0 in range(BOARD_SHAPE[0]):
                symbol_idx = int(board[0, c0])
                can_start = False
                
                if symbol_idx == 0:  # Wild符號
                    can_start = True
                elif symbol_idx == 1:  # C1符號不能作為起點
                    can_start = False
                elif symbol_idx < len(symbol_to_lp) and symbol_to_lp[symbol_idx] == symbol_lp:
                    can_start = True
                
                if not can_start:
                    continue
                
                mask_lengths = np.zeros(rows, dtype=np.int32)
                mask = np.zeros((rows, np.max(BOARD_SHAPE)), dtype=np.int32)
                
                for r in range(rows):
                    row_cols = BOARD_SHAPE[r]
                    count = 0
                    if r == 0:
                        if (board[0, c0] in valid_symbol) or (board[0, c0] == 0):  # Wild符號
                            mask[r, count] = c0
                            count = 1
                    else:
                        for c in range(row_cols):
                            s = board[r, c]
                            if s == 0 or s in valid_symbol:  # Wild符號或有效符號
                                if s != 1:  # 排除C1符號
                                    mask[r, count] = c
                                    count += 1
                        if count == 0:
                            break
                    mask_lengths[r] = count
                
                max_conn = 0
                for conn in range(3, 6):
                    if conn <= len(mask_lengths) and np.all(mask_lengths[:conn] > 0):
                        ways = 1
                        for layer in range(conn):
                            ways *= mask_lengths[layer]
                        if ways > 0 and conn > max_conn:
                            max_conn = conn
                
                if max_conn >= 3:
                    for r in range(max_conn):
                        for idx in range(mask_lengths[r]):
                            c = mask[r, idx]
                            symbol = board[r, c]
                            if 11 <= symbol <= 19:  # M1G~M9G
                                golden_symbols_to_convert.append((r, c))
                            else:
                                elimination_mask[r, c] = True
        
        # 處理黃金符號轉換 - 優化為numba兼容版本
        # 使用字典模擬set去重
        seen = {}
        for r, c in golden_symbols_to_convert:
            key = r * 1000 + c
            if key not in seen:
                seen[key] = True
                if board[r, c] >= 11 and board[r, c] <= 19:  # M1G~M9G
                    board[r, c] = 0
                    golden_symbols_converted_this_round += 1
        
        # 消除符號
        for r in range(rows):
            row_cols = BOARD_SHAPE[r]
            for c in range(row_cols):
                if elimination_mask[r, c]:
                    board[r, c] = -1
        
        # 重力下降 - 優化為數組操作
        for r in range(rows):
            row_cols = BOARD_SHAPE[r]
            # 計算非空符號數量
            non_empty_count = 0
            for c in range(row_cols):
                if board[r, c] != -1:
                    non_empty_count += 1
            
            # 創建臨時數組存儲非空符號
            if non_empty_count > 0:
                temp = np.empty(non_empty_count, dtype=np.int32)
                idx = 0
                for c in range(row_cols):
                    if board[r, c] != -1:
                        temp[idx] = board[r, c]
                        idx += 1
                # 重新填充
                for c in range(non_empty_count):
                    board[r, c] = temp[c]
            # 填充空位
            for c in range(non_empty_count, row_cols):
                board[r, c] = -1
        
        # 補充新符號 - 使用新的掉落機制
        for r in range(rows):
            row_cols = BOARD_SHAPE[r]
            for c in range(row_cols-1, -1, -1):
                if board[r, c] == -1:
                    # 使用新的掉落符號生成邏輯，傳入本輪統一的MY轉換目標
                    new_symbol = generate_drop_symbol_numba(
                        r, c, cascade_count, game_type,
                        drop_weights_1st, drop_weights_2nd, drop_weights_3rd, drop_weights_4th,
                        my_convert_weights, my_target_symbol
                    )
                    board[r, c] = new_symbol
    
    return total_score, board

# 包裝函數以支持原有接口
def sample_sequences_weighted(weight_array, content_array, n):
    return sample_sequences_weighted_numba(weight_array, content_array, n)

def build_symbol_to_linkpoint():
    return build_symbol_to_linkpoint_numba()

def waygame_fullscore(board, linkpoint):
    return waygame_fullscore_numba(board.astype(np.int32), linkpoint)

def point(weight_array, reel_array, initial_board, linkpoint):
    """包裝函數 - 優化版，減少globals()調用並使用正確的數據類型"""
    g = globals()
    return point_numba(
        weight_array, reel_array, initial_board.astype(np.int32), linkpoint,
        g.get('baseDropWeights1st', np.ones((5,21), dtype=np.float32)), 
        g.get('baseDropWeights2nd', np.ones((5,21), dtype=np.float32)),
        g.get('baseDropWeights3rd', np.ones((5,21), dtype=np.float32)),
        g.get('baseDropWeights4th', np.ones((5,21), dtype=np.float32)),
        g.get('baseMyConvertWeights', np.ones(9, dtype=np.float32)),
        game_type=0
    )

def freegame_point(weight_array, reel_array, initial_board, linkpoint, is_freegame=True):
    """包裝函數 - 優化版，預設使用FREE HIGH的掉落權重"""
    g = globals()
    return freegame_point_numba(
        weight_array, reel_array, initial_board.astype(np.int32), linkpoint,
        g.get('freeHighDropWeights1st', np.ones((5,21), dtype=np.float32)),
        g.get('freeHighDropWeights2nd', np.ones((5,21), dtype=np.float32)),
        g.get('freeHighDropWeights3rd', np.ones((5,21), dtype=np.float32)),
        g.get('freeHighDropWeights4th', np.ones((5,21), dtype=np.float32)),
        g.get('freeHighMyConvertWeights', np.ones(9, dtype=np.float32)),
        game_type=1
    )

# @njit  # 暫時禁用以避免調用非numba函數的問題
def freegame_numba(n, configs, config_probs, symbol_names_data,
                   high_symbol_weight, high_symbol_reel_a,
                   low_symbol_weight, low_symbol_reel,
                   linkpoint, 
                   free_high_drop_weights_1st, free_high_drop_weights_2nd, 
                   free_high_drop_weights_3rd, free_high_drop_weights_4th,
                   free_high_my_convert_weights,
                   free_low_drop_weights_1st, free_low_drop_weights_2nd,
                   free_low_drop_weights_3rd, free_low_drop_weights_4th,
                   free_low_my_convert_weights,
                   max_spins=50, seed=None):
    """
    Numba加速版本的免費遊戲批量執行
    """
    if seed is not None:
        np.random.seed(seed)
    
    total_scores = np.zeros(n, dtype=np.float64)
    spin_counts = np.zeros((n, 2), dtype=np.int32)  # [高表場次, 低表場次]
    c1_appearance_counts = np.zeros(n, dtype=np.int32)  # 每個freegame中有C1的spin次數
    
    for game_round in range(n):
        # 每個遊戲使用對應的場次配置
        high_spins, low_spins = configs[game_round]
        
        # 建立場次序列並隨機排列
        spin_sequence = np.concatenate((np.ones(high_spins, dtype=np.int32),
                                      np.zeros(low_spins, dtype=np.int32)))
        # Fisher-Yates shuffle
        for i in range(len(spin_sequence)-1, 0, -1):
            j = np.random.randint(0, i+1)
            spin_sequence[i], spin_sequence[j] = spin_sequence[j], spin_sequence[i]
        
        total_score = 0
        current_spin = 0
        high_spin_count = 0
        low_spin_count = 0
        c1_appearance_this_game = 0  # 記錄本場freegame中有C1的spin次數
        
        while current_spin < len(spin_sequence) and current_spin < max_spins:
            spin_type = spin_sequence[current_spin]
            current_spin += 1
            
            if spin_type == 1:  # high table
                # 直接使用A高表
                initial_board = sample_sequences_weighted_irregular_numba(
                    high_symbol_weight, high_symbol_reel_a, BOARD_SHAPE
                ).astype(np.int32)
                
                # 執行遊戲
                spin_score, final_board = freegame_point_numba(
                    low_symbol_weight, high_symbol_reel_a, initial_board, linkpoint,
                    free_high_drop_weights_1st, free_high_drop_weights_2nd,
                    free_high_drop_weights_3rd, free_high_drop_weights_4th,
                    free_high_my_convert_weights, game_type=1
                )
                
                high_spin_count += 1
                
            else:  # low table
                initial_board = sample_sequences_weighted_irregular_numba(
                    low_symbol_weight, low_symbol_reel, BOARD_SHAPE
                ).astype(np.int32)
                
                spin_score, final_board = freegame_point_numba(
                    low_symbol_weight, low_symbol_reel, initial_board, linkpoint,
                    free_low_drop_weights_1st, free_low_drop_weights_2nd,
                    free_low_drop_weights_3rd, free_low_drop_weights_4th,
                    free_low_my_convert_weights, game_type=2
                )
                
                low_spin_count += 1
            
            total_score += spin_score
            
            # 檢查本次spin是否有C1出現（不管數量，只要有就計為1次）
            c1_count = np.sum(final_board == 1)  # C1符號現在是1
            if c1_count > 0:
                c1_appearance_this_game += 1
            
            # 檢查Retrigger
            if c1_count >= 3:
                # 根據 scatter 數量計算額外場次
                retrigger_high, retrigger_low = get_scatter_spins(c1_count)
                
                # 建立額外場次序列
                additional = np.concatenate((
                    np.ones(retrigger_high, dtype=np.int32),    # 高表場次
                    np.zeros(retrigger_low, dtype=np.int32)     # 低表場次
                ))
                
                # 隨機排列額外場次
                for i in range(len(additional)-1, 0, -1):
                    j = np.random.randint(0, i+1)
                    additional[i], additional[j] = additional[j], additional[i]
                
                # 擴展序列
                new_sequence = np.concatenate((spin_sequence, additional))
                spin_sequence = new_sequence
        
        total_scores[game_round] = total_score
        spin_counts[game_round, 0] = high_spin_count
        spin_counts[game_round, 1] = low_spin_count
        c1_appearance_counts[game_round] = c1_appearance_this_game  # 記錄本場freegame的C1出現次數
    
    return total_scores, spin_counts, c1_appearance_counts

def basegame_numba(n, surface_probs, high_symbol_weight, high_symbol_reel,
                   linkpoint, 
                   base_drop_weights_1st, base_drop_weights_2nd,
                   base_drop_weights_3rd, base_drop_weights_4th,
                   base_my_convert_weights,
                   seed=None, return_scatter_counts=False):
    """
    Numba加速版本的基本遊戲批量執行 - 全部使用高表
    注意：已移除 low_symbol_weight 和 low_symbol_reel 參數，因為全部使用高表
    
    Returns:
        total_scores: 每局遊戲的分數陣列
        c1_trigger_count: 觸發freegame的總次數
        scatter_counts: 每次觸發時的scatter數量陣列 (如果return_scatter_counts=True)
        trigger_vector: 每局遊戲是否觸發freegame的向量 (1=觸發，0=未觸發)
        c1_appearance_vector: 每局遊戲是否出現C1的向量 (1=有C1，0=無C1)
    """
    if seed is not None:
        np.random.seed(seed)
    
    total_scores = np.zeros(n, dtype=np.float64)
    c1_trigger_count = 0  # 計算C1>=3的遊戲場次
    scatter_counts = []  # 記錄每次觸發的 scatter 數量
    trigger_vector = np.zeros(n, dtype=np.int32)  # 記錄每次spin是否觸發freegame：1=觸發，0=未觸發
    c1_appearance_vector = np.zeros(n, dtype=np.int32)  # 記錄每次spin是否出現C1：1=有C1，0=無C1
    
    for i in range(n):
        # 全部使用高表，不再區分高低表
        initial_board = sample_sequences_weighted_irregular_numba(
            high_symbol_weight, high_symbol_reel, BOARD_SHAPE
        ).astype(np.int32)
        total_score, final_board = point_numba(
            high_symbol_weight, high_symbol_reel, initial_board, linkpoint,
            base_drop_weights_1st, base_drop_weights_2nd,
            base_drop_weights_3rd, base_drop_weights_4th,
            base_my_convert_weights, game_type=0
        )
        
        total_scores[i] = total_score
        
        # 檢查最終版面C1數量
        c1_count = np.sum(final_board == 1)  # C1符號現在是1
        
        # 記錄是否出現C1（不管數量，只要有就計為1次）
        if c1_count > 0:
            c1_appearance_vector[i] = 1
        else:
            c1_appearance_vector[i] = 0
        
        # 記錄是否觸發freegame（C1>=3）
        if c1_count >= 3:
            c1_trigger_count += 1
            trigger_vector[i] = 1  # 記錄此次spin觸發freegame
            if return_scatter_counts:
                scatter_counts.append(c1_count)
        else:
            trigger_vector[i] = 0  # 記錄此次spin未觸發freegame
    
    if return_scatter_counts:
        return total_scores, c1_trigger_count, np.array(scatter_counts, dtype=np.int32), trigger_vector, c1_appearance_vector
    else:
        return total_scores, c1_trigger_count, np.array([], dtype=np.int32), trigger_vector, c1_appearance_vector

# 包裝函數以支持原有接口
def freegame(n, trigger_c1_count=3, scatter_counts=None, freeGameSurface=None, configs=None,
             linkpoint=None,
             freeGameHighSymbolWeight=None, freeGameLowSymbolWeight=None,
             freeGameSymbolHighA=None, freeGameSymbolLow=None,
             # 掉落權重參數
             freeHighDropWeights1st=None, freeHighDropWeights2nd=None,
             freeHighDropWeights3rd=None, freeHighDropWeights4th=None,
             freeHighMyConvertWeights=None,
             freeLowDropWeights1st=None, freeLowDropWeights2nd=None,
             freeLowDropWeights3rd=None, freeLowDropWeights4th=None,
             freeLowMyConvertWeights=None,
             # 保留舊參數以保持向後相容性，但不使用
             freeGameHighSurface=None, freeGameSymbolHighK=None,
             freeGameSymbolHighQ=None, freeGameSymbolHighJ=None,
             freeGameHighRandomwildA=None, freeGameLowRandomwild=None,
             freeGameHighRandomwildK=None, freeGameHighRandomwildQ=None, 
             freeGameHighRandomwildJ=None):
    """
    原始接口的包裝函數 - 優化版本，減少globals()調用
    """
    # 預先獲取全局變量（只調用一次globals()）
    g = globals()
    
    # 預設值處理
    if linkpoint is None:
        linkpoint = g.get('linkpoint', np.ones((9,3), dtype=np.float64))
    
    # 處理 scatter_counts 參數
    if scatter_counts is None:
        scatter_counts_arr = np.full(n, 3, dtype=np.int32)
    else:
        # 確保是 NumPy 陣列
        if isinstance(scatter_counts, list):
            scatter_counts_arr = np.array(scatter_counts, dtype=np.int32)
        else:
            scatter_counts_arr = np.asarray(scatter_counts, dtype=np.int32)
        
        # 如果長度不匹配，重複或截斷
        if len(scatter_counts_arr) != n:
            scatter_counts_arr = np.tile(scatter_counts_arr, (n // len(scatter_counts_arr)) + 1)[:n]
    
    # 【優化】使用向量化操作替代 Python 循環
    # 將 scatter_count 限制在有效範圍 [3, 23]
    scatter_counts_arr = np.clip(scatter_counts_arr, 3, 23)
    
    # 直接從矩陣中查找所有配置（避免循環）
    configs = SCATTER_SPINS_MATRIX[scatter_counts_arr]  # 形狀為 (n, 2)，dtype=np.int32
    
    config_probs = np.ones(n, dtype=np.float64)
    
    # 處理符號參數預設值
    if freeGameSymbolHighA is None:
        freeGameSymbolHighA = g.get('freeGameSymbolHighA', np.zeros((5, REEL_LENGTH), dtype=np.int32))
    if freeGameLowSymbolWeight is None:
        freeGameLowSymbolWeight = g.get('freeGameLowSymbolWeight', np.ones((5, REEL_LENGTH), dtype=np.float64))
    if freeGameSymbolLow is None:
        freeGameSymbolLow = g.get('freeGameSymbolLow', np.zeros((5, REEL_LENGTH), dtype=np.int32))
    if freeGameHighSymbolWeight is None:
        freeGameHighSymbolWeight = g.get('freeGameHighSymbolWeight', np.ones((5, REEL_LENGTH), dtype=np.float64))
    
    # 數據準備
    low_symbol_weight = freeGameLowSymbolWeight
    low_symbol_reel = freeGameSymbolLow
    high_symbol_weight = freeGameHighSymbolWeight
    
    # 處理掉落權重參數預設值（使用float32以提高性能）
    if freeHighDropWeights1st is None:
        freeHighDropWeights1st = g.get('freeHighDropWeights1st', np.ones((5,21), dtype=np.float32))
    if freeHighDropWeights2nd is None:
        freeHighDropWeights2nd = g.get('freeHighDropWeights2nd', np.ones((5,21), dtype=np.float32))
    if freeHighDropWeights3rd is None:
        freeHighDropWeights3rd = g.get('freeHighDropWeights3rd', np.ones((5,21), dtype=np.float32))
    if freeHighDropWeights4th is None:
        freeHighDropWeights4th = g.get('freeHighDropWeights4th', np.ones((5,21), dtype=np.float32))
    if freeHighMyConvertWeights is None:
        freeHighMyConvertWeights = g.get('freeHighMyConvertWeights', np.ones(9, dtype=np.float32))
    
    if freeLowDropWeights1st is None:
        freeLowDropWeights1st = g.get('freeLowDropWeights1st', np.ones((5,21), dtype=np.float32))
    if freeLowDropWeights2nd is None:
        freeLowDropWeights2nd = g.get('freeLowDropWeights2nd', np.ones((5,21), dtype=np.float32))
    if freeLowDropWeights3rd is None:
        freeLowDropWeights3rd = g.get('freeLowDropWeights3rd', np.ones((5,21), dtype=np.float32))
    if freeLowDropWeights4th is None:
        freeLowDropWeights4th = g.get('freeLowDropWeights4th', np.ones((5,21), dtype=np.float32))
    if freeLowMyConvertWeights is None:
        freeLowMyConvertWeights = g.get('freeLowMyConvertWeights', np.ones(9, dtype=np.float32))
    
    total_scores, spin_counts, c1_appearance_counts = freegame_numba(
        n, configs, config_probs, None,
        high_symbol_weight, freeGameSymbolHighA,
        low_symbol_weight, low_symbol_reel,
        linkpoint,
        freeHighDropWeights1st, freeHighDropWeights2nd,
        freeHighDropWeights3rd, freeHighDropWeights4th,
        freeHighMyConvertWeights,
        freeLowDropWeights1st, freeLowDropWeights2nd,
        freeLowDropWeights3rd, freeLowDropWeights4th,
        freeLowMyConvertWeights
    )
    
    return total_scores, spin_counts, c1_appearance_counts

def basegame(n, baseGameSurface, baseGameHighSymbolWeight=None, baseGameSymbolHigh=None, 
             baseGameLowSymbolWeight=None, baseGameSymbolLow=None, linkpoint=None,
             # 保留舊參數以保持相容性，但不使用
             baseGameHighRandomwild=None, baseGameLowRandomwild=None,
             return_scatter_counts=False):
    """
    原始接口的包裝函數 - 已移除 RANDOMWILD 功能，全部使用高表
    支援返回每次觸發的 scatter 數量
    注意：現在 BASE GAME 全部使用高表，以下參數保留但不影響遊戲邏輯：
    - baseGameSurface: 保留相容性，但不再使用
    - baseGameLowSymbolWeight: 保留相容性，但不再使用  
    - baseGameSymbolLow: 保留相容性，但不再使用
    
    Returns:
        total_scores: 每局遊戲的分數陣列
        c1_trigger_count: 觸發freegame的總次數
        scatter_counts: 每次觸發時的scatter數量陣列 (如果return_scatter_counts=True)
        trigger_vector: 每局遊戲是否觸發freegame的向量 (1=觸發，0=未觸發)
        c1_appearance_vector: 每局遊戲是否出現C1的向量 (1=有C1，0=無C1)
    """
    surface_probs = np.array(baseGameSurface, dtype=np.float64)
    surface_probs = surface_probs / np.sum(surface_probs)
    
    # 處理參數預設值，優先使用輸入參數 (全部使用高表)
    if baseGameHighSymbolWeight is None:
        baseGameHighSymbolWeight = globals().get('baseGameHighSymbolWeight', np.ones((5, REEL_LENGTH), dtype=np.float64))
    if baseGameSymbolHigh is None:
        baseGameSymbolHigh = globals().get('baseGameSymbolHigh', np.zeros((5, REEL_LENGTH), dtype=np.int32))
    # 以下參數保留以維持相容性，但不再使用
    # if baseGameLowSymbolWeight is None: ...
    # if baseGameSymbolLow is None: ...
    if linkpoint is None:
        linkpoint = globals().get('linkpoint', np.ones((9,3), dtype=np.float64))
    
    # 使用輸入參數 (只需要高表參數)
    high_symbol_weight = baseGameHighSymbolWeight
    high_symbol_reel = baseGameSymbolHigh
    
    # 獲取drop weights參數（使用預處理過的數據）
    base_drop_weights_1st = globals().get('baseDropLowWeights1st', np.ones((5,21), dtype=np.float32))
    base_drop_weights_2nd = globals().get('baseDropLowWeights2nd', np.ones((5,21), dtype=np.float32))
    base_drop_weights_3rd = globals().get('baseDropLowWeights3rd', np.ones((5,21), dtype=np.float32))
    base_drop_weights_4th = globals().get('baseDropLowWeights4th', np.ones((5,21), dtype=np.float32))
    base_my_convert_weights = globals().get('baseMyConvertLowWeights', np.ones(9, dtype=np.float32))
    
    total_scores, c1_trigger_count, scatter_counts, trigger_vector, c1_appearance_vector = basegame_numba(
        n, surface_probs, high_symbol_weight, high_symbol_reel,
        linkpoint,
        base_drop_weights_1st, base_drop_weights_2nd,
        base_drop_weights_3rd, base_drop_weights_4th,
        base_my_convert_weights,
        seed=None, return_scatter_counts=return_scatter_counts
    )
    
    if return_scatter_counts:
        return total_scores, c1_trigger_count, scatter_counts, trigger_vector, c1_appearance_vector
    else:
        return total_scores, c1_trigger_count, trigger_vector, c1_appearance_vector

def fullgame(n, 
             baseGameSurface=None, baseGameHighSymbolWeight=None, baseGameSymbolHigh=None,
             linkpoint=None,
             freeGameHighSymbolWeight=None, freeGameLowSymbolWeight=None,
             freeGameSymbolHighA=None, freeGameSymbolLow=None,
             return_summary_only=False):
    """
    完整遊戲模擬函數 - 整合 basegame + freegame
    
    執行流程：
    1. 執行 n 次 basegame
    2. 每次 basegame 結束後檢查是否有 ≥3 個 C1（scatter）
    3. 如果觸發，執行對應的 freegame
    4. 返回每次的總分（basegame分數 + freegame分數）
    
    Parameters:
        n: 遊戲次數
        baseGameSurface: basegame surface 參數
        baseGameHighSymbolWeight: basegame 高表權重
        baseGameSymbolHigh: basegame 高表符號
        linkpoint: 連線分數表
        freeGameHighSymbolWeight: freegame 高表權重
        freeGameLowSymbolWeight: freegame 低表權重
        freeGameSymbolHighA: freegame 高表符號
        freeGameSymbolLow: freegame 低表符號
        return_summary_only: 若為True，只返回簡化的統計資訊（節省記憶體）
    
    Returns:
        當 return_summary_only=False（預設）:
            total_scores: 每次遊戲的總分數組（basegame + freegame）
            trigger_info: 觸發資訊字典，包含：
                - trigger_count: 觸發freegame的總次數
                - trigger_vector: 每次是否觸發的向量
                - scatter_counts: 每次觸發時的scatter數量
                - base_scores: 每次遊戲的最終分數（包含basegame + freegame）
                - free_scores: 每個freegame session的分數陣列
                - base_scores_sum: 純basegame總分數
                - free_scores_sum: freegame總分數
                - base_rtp: basegame RTP (%)，以每次spin成本100分計算
                - free_rtp: freegame RTP (%)，以每次spin成本100分計算
                - total_rtp: 總RTP (%)，base_rtp + free_rtp
                - base_c1_appearances: basegame中出現C1的總次數（每局有C1計數1次）
                - free_c1_appearances: freegame中出現C1的總次數（每次freegame spin有C1計數1次）
                - total_c1_appearances: C1總出現次數（basegame + freegame）
                - base_c1_appearance_vector: basegame每局是否出現C1的向量
                - free_c1_appearance_per_game: 每個freegame session中C1出現的次數陣列
        
        當 return_summary_only=True:
            summary_dict: 只包含以下統計值的字典：
                - base_rtp: basegame RTP (%)
                - free_rtp: freegame RTP (%)
                - total_rtp: 總RTP (%)
                - trigger_count: 觸發freegame的總次數
    """
    g = globals()
    
    # 處理參數預設值
    if baseGameSurface is None:
        baseGameSurface = g.get('baseGameSurface', [1, 0])
    if baseGameHighSymbolWeight is None:
        baseGameHighSymbolWeight = g.get('baseGameHighSymbolWeight')
    if baseGameSymbolHigh is None:
        baseGameSymbolHigh = g.get('baseGameSymbolHigh')
    if linkpoint is None:
        linkpoint = g.get('linkpoint')
    
    # 處理 freegame 參數
    if freeGameHighSymbolWeight is None:
        freeGameHighSymbolWeight = g.get('freeGameHighSymbolWeight')
    if freeGameLowSymbolWeight is None:
        freeGameLowSymbolWeight = g.get('freeGameLowSymbolWeight')
    if freeGameSymbolHighA is None:
        freeGameSymbolHighA = g.get('freeGameSymbolHighA')
    if freeGameSymbolLow is None:
        freeGameSymbolLow = g.get('freeGameSymbolLow')
    
    # 步驟1: 執行 n 次 basegame，並獲取觸發資訊
    base_scores, trigger_count, scatter_counts, trigger_vector, base_c1_appearance = basegame(
        n=n,
        baseGameSurface=baseGameSurface,
        baseGameHighSymbolWeight=baseGameHighSymbolWeight,
        baseGameSymbolHigh=baseGameSymbolHigh,
        linkpoint=linkpoint,
        return_scatter_counts=True
    )
    
    # 步驟2: 對於觸發freegame的spin，執行freegame並累加分數
    if trigger_count > 0:
        # 執行對應數量的freegame
        free_scores, free_spin_counts, free_c1_appearance = freegame(
            n=trigger_count,
            scatter_counts=scatter_counts,  # 直接傳遞 NumPy 陣列，不需要轉換為 list
            linkpoint=linkpoint,
            freeGameHighSymbolWeight=freeGameHighSymbolWeight,
            freeGameLowSymbolWeight=freeGameLowSymbolWeight,
            freeGameSymbolHighA=freeGameSymbolHighA,
            freeGameSymbolLow=freeGameSymbolLow
        )
        
        # 【優化】使用向量化操作替代 Python 循環
        # 找到所有觸發 freegame 的索引
        trigger_indices = np.nonzero(trigger_vector)[0]
        
        # 計算純 basegame 和 freegame 的總分數（用於 RTP 占比計算）
        base_scores_sum = np.sum(base_scores)
        free_scores_sum = np.sum(free_scores)
        
        # 直接在 base_scores 上加上 freegame 分數（避免 copy）
        base_scores[trigger_indices] += free_scores
        
        total_scores = base_scores  # 直接使用，不需要 copy
    else:
        free_scores = np.array([])
        free_spin_counts = np.array([])
        free_c1_appearance = np.array([])
        base_scores_sum = np.sum(base_scores)
        free_scores_sum = 0
        total_scores = base_scores  # 沒有觸發時也直接使用
    
    # 計算 RTP（以每次 spin 成本 100 分計算）
    total_bet = n * 100  # 總投注金額
    base_rtp = (base_scores_sum / total_bet) * 100  # basegame RTP (%)
    free_rtp = (free_scores_sum / total_bet) * 100  # freegame RTP (%)
    total_rtp = base_rtp + free_rtp  # 總 RTP (%)
    
    # 統計總C1出現次數
    # basegame中的C1出現次數
    base_c1_count = np.sum(base_c1_appearance)
    # freegame中的C1出現次數
    free_c1_count = np.sum(free_c1_appearance) if len(free_c1_appearance) > 0 else 0
    # 總C1出現次數
    total_c1_appearances = base_c1_count + free_c1_count
    
    # 建立詳細的觸發資訊
    trigger_info = {
        'trigger_count': trigger_count,
        'trigger_vector': trigger_vector,
        'scatter_counts': scatter_counts,
        'base_scores': base_scores,
        'free_scores': free_scores,
        'base_scores_sum': base_scores_sum,  # 純basegame總分數
        'free_scores_sum': free_scores_sum,  # freegame總分數
        'free_spin_counts': free_spin_counts,
        # RTP資訊（以每次spin成本100分計算）
        'base_rtp': base_rtp,  # basegame RTP (%)
        'free_rtp': free_rtp,  # freegame RTP (%)
        'total_rtp': total_rtp,  # 總 RTP (%)
        # 新增C1統計資訊
        'base_c1_appearances': base_c1_count,  # basegame中C1出現次數
        'free_c1_appearances': free_c1_count,  # freegame中C1出現次數
        'total_c1_appearances': total_c1_appearances,  # 總C1出現次數
        'base_c1_appearance_vector': base_c1_appearance,  # 每次basegame是否有C1
        'free_c1_appearance_per_game': free_c1_appearance  # 每個freegame中有C1的spin數
    }
    
    # 根據開關決定返回格式
    if return_summary_only:
        # 只返回簡化的統計資訊（節省記憶體）
        summary = {
            'base_rtp': base_rtp,
            'free_rtp': free_rtp,
            'total_rtp': total_rtp,
            'trigger_count': trigger_count
        }
        return summary
    else:
        # 返回完整資訊
        return total_scores, trigger_info


def _is_interactive():
    """檢測是否在 Interactive 環境中運行"""
    try:
        get_ipython()
        return True
    except NameError:
        return False


def _run_fullgame_via_subprocess(n, return_summary_only, n_workers, data_file):
    """通過 subprocess 運行 fullgame_parallel（用於 Interactive 環境）"""
    import subprocess
    import sys
    import pickle
    import tempfile
    import os
    import time
    
    # 獲取當前工作目錄
    current_dir = os.getcwd()
    
    # 確保 data_file 是絕對路徑
    if not os.path.isabs(data_file):
        data_file = os.path.join(current_dir, data_file)
    
    print(f"[DEBUG] 準備啟動 subprocess...")
    print(f"[DEBUG] n={n:,}, workers={n_workers}")
    print(f"[DEBUG] data_file={data_file}")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        script_path = f.name
        
        # 創建一個簡單的單進程版本（先不用多進程，避免復雜度）
        f.write(f'''
import sys
import os
import pickle
import time

sys.path.insert(0, r"{current_dir}")
os.chdir(r"{current_dir}")

print("[SUBPROCESS] 開始執行...")
print(f"[SUBPROCESS] Python: {{sys.executable}}")
print(f"[SUBPROCESS] CWD: {{os.getcwd()}}")

try:
    import simulation as sim
    print("[SUBPROCESS] ✓ simulation 模塊已導入")
    
    # 加載數據
    data_file_path = r"{data_file}"
    print(f"[SUBPROCESS] 加載數據: {{data_file_path}}")
    
    data = sim.extract_all_js_vars_numpy(data_file_path)
    sim_globals = sys.modules['simulation'].__dict__
    for key, value in data.items():
        sim_globals[key] = value
    print(f"[SUBPROCESS] ✓ 數據已加載 ({{len(data)}} 個變量)")
    
    # 執行模擬（使用單進程版本，避免嵌套多進程問題）
    n_total = {n}
    print(f"[SUBPROCESS] 開始執行 {{n_total:,}} 次模擬...")
    
    start_time = time.time()
    result = sim.fullgame(n_total, return_summary_only=True)
    elapsed = time.time() - start_time
    
    print(f"[SUBPROCESS] ✓ 模擬完成，耗時 {{elapsed:.2f}} 秒")
    print(f"[SUBPROCESS] Total RTP: {{result.get('total_rtp', 0):.2f}}%")
    
    # 保存結果
    with open(r"{script_path}.pkl", "wb") as pkl_file:
        pickle.dump(result, pkl_file)
    print("[SUBPROCESS] ✓ 結果已保存")
    
except Exception as e:
    print(f"[SUBPROCESS] ✗ 錯誤: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
''')
    
    try:
        print(f"[DEBUG] 啟動 subprocess (脚本: {script_path})...")
        start_time = time.time()
        
        # 設置超時（根據模擬次數動態調整）
        timeout_seconds = max(300, n // 1000)  # 至少5分鐘，或每1000次1秒
        print(f"[DEBUG] 超時設置: {timeout_seconds} 秒")
        
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=current_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=timeout_seconds
        )
        
        elapsed = time.time() - start_time
        print(f"[DEBUG] subprocess 完成，耗時 {elapsed:.2f} 秒")
        
        # 顯示輸出
        if result.stdout:
            print("\n--- Subprocess 輸出 ---")
            print(result.stdout)
            print("--- 輸出結束 ---\n")
        
        if result.returncode != 0:
            print("[ERROR] subprocess 返回非零狀態碼")
            if result.stderr:
                print("--- 錯誤輸出 ---")
                print(result.stderr)
                print("--- 錯誤結束 ---")
            raise RuntimeError(f"模擬失敗 (返回碼: {result.returncode})")
        
        # 讀取結果
        pkl_path = script_path + '.pkl'
        if not os.path.exists(pkl_path):
            raise RuntimeError(f"結果文件未生成: {pkl_path}")
        
        with open(pkl_path, 'rb') as f:
            results = pickle.load(f)
        
        os.unlink(pkl_path)
        print("[DEBUG] ✓ 結果讀取成功")
        return results
    
    except subprocess.TimeoutExpired:
        print(f"[ERROR] subprocess 超時 ({timeout_seconds} 秒)")
        print("[ERROR] 模擬可能陷入死循環或運行時間過長")
        raise RuntimeError(f"模擬超時 (>{timeout_seconds}秒)")
        
    except Exception as e:
        print(f"[ERROR] 發生異常: {e}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # 清理臨時文件
        if os.path.exists(script_path):
            try:
                os.unlink(script_path)
            except:
                pass


def fullgame_parallel(n, 
                     baseGameSurface=None, baseGameHighSymbolWeight=None, baseGameSymbolHigh=None,
                     linkpoint=None,
                     freeGameHighSymbolWeight=None, freeGameLowSymbolWeight=None,
                     freeGameSymbolHighA=None, freeGameSymbolLow=None,
                     return_summary_only=False,
                     n_workers=4,
                     data_file='data.js',
                     _force_standard=False):
    """
    使用多進程並行執行 fullgame 模擬，大幅提升速度
    自動檢測環境並選擇最佳執行方式
    
    Parameters:
        n: 遊戲總次數
        n_workers: 使用的進程數量（建議設置為 CPU 核心數）
        data_file: 數據文件路徑（預設為 'data.js'）
        return_summary_only: 是否只返回摘要統計
        其他參數同 fullgame()
        _force_standard: 內部參數，強制使用標準多進程（避免遞歸）
    
    Returns:
        與 fullgame() 相同的返回格式
    """
    import os
    
    # 如果在 Interactive 環境且未強制使用標準方式，則使用 subprocess
    if not _force_standard and _is_interactive():
        return _run_fullgame_via_subprocess(n, return_summary_only, n_workers, data_file)
    
    # 標準多進程執行方式
    from concurrent.futures import ProcessPoolExecutor
    
    # 獲取當前數據文件的絕對路徑（如果是相對路徑）
    if not os.path.isabs(data_file):
        # 嘗試從當前工作目錄或腳本目錄查找
        if os.path.exists(data_file):
            data_file = os.path.abspath(data_file)
        else:
            # 嘗試從當前文件所在目錄查找
            script_dir = os.path.dirname(os.path.abspath(__file__))
            potential_path = os.path.join(script_dir, data_file)
            if os.path.exists(potential_path):
                data_file = potential_path
    
    # 從主進程獲取所有必要的參數（如果未提供）
    g = globals()
    if baseGameSurface is None:
        baseGameSurface = g.get('baseGameSurface', [1, 0])
    if baseGameHighSymbolWeight is None:
        baseGameHighSymbolWeight = g.get('baseGameHighSymbolWeight')
    if baseGameSymbolHigh is None:
        baseGameSymbolHigh = g.get('baseGameSymbolHigh')
    if linkpoint is None:
        linkpoint = g.get('linkpoint')
    if freeGameHighSymbolWeight is None:
        freeGameHighSymbolWeight = g.get('freeGameHighSymbolWeight')
    if freeGameLowSymbolWeight is None:
        freeGameLowSymbolWeight = g.get('freeGameLowSymbolWeight')
    if freeGameSymbolHighA is None:
        freeGameSymbolHighA = g.get('freeGameSymbolHighA')
    if freeGameSymbolLow is None:
        freeGameSymbolLow = g.get('freeGameSymbolLow')
    
    # 計算每個 worker 的任務量
    tasks_per_worker = n // n_workers
    remaining = n % n_workers
    task_sizes = [tasks_per_worker] * n_workers
    # 將剩餘的任務分配給前幾個 worker
    for i in range(remaining):
        task_sizes[i] += 1
    
    # 準備每個 worker 的參數（包含所有必要數據）
    worker_args = []
    for task_size in task_sizes:
        if task_size > 0:  # 只添加有任務的 worker
            worker_args.append({
                'n': task_size,
                'data_file': data_file,
                'baseGameSurface': baseGameSurface,
                'baseGameHighSymbolWeight': baseGameHighSymbolWeight,
                'baseGameSymbolHigh': baseGameSymbolHigh,
                'linkpoint': linkpoint,
                'freeGameHighSymbolWeight': freeGameHighSymbolWeight,
                'freeGameLowSymbolWeight': freeGameLowSymbolWeight,
                'freeGameSymbolHighA': freeGameSymbolHighA,
                'freeGameSymbolLow': freeGameSymbolLow,
                'return_summary_only': return_summary_only
            })
    
    # 使用多進程執行
    with ProcessPoolExecutor(max_workers=len(worker_args)) as executor:
        results = list(executor.map(_worker_fullgame, worker_args))
    
    # 彙總結果
    if return_summary_only:
        # 簡化模式：重新計算 RTP 和累加觸發次數
        total_base_score = sum(r['base_scores_sum'] for r in results)
        total_free_score = sum(r['free_scores_sum'] for r in results)
        total_trigger_count = sum(r['trigger_count'] for r in results)
        
        # 重新計算 RTP（基於總投注）
        total_bet = n * 100
        base_rtp = (total_base_score / total_bet) * 100
        free_rtp = (total_free_score / total_bet) * 100
        total_rtp = base_rtp + free_rtp
        
        return {
            'base_rtp': base_rtp,
            'free_rtp': free_rtp,
            'total_rtp': total_rtp,
            'trigger_count': total_trigger_count
        }
    else:
        # 完整模式：合併所有數據
        all_scores = np.concatenate([r[0] for r in results])
        
        # 合併統計資訊
        total_base_score = sum(r[1]['base_scores_sum'] for r in results)
        total_free_score = sum(r[1]['free_scores_sum'] for r in results)
        total_trigger_count = sum(r[1]['trigger_count'] for r in results)
        
        # 重新計算 RTP
        total_bet = n * 100
        base_rtp = (total_base_score / total_bet) * 100
        free_rtp = (total_free_score / total_bet) * 100
        total_rtp = base_rtp + free_rtp
        
        # 合併其他統計資料
        all_trigger_vectors = np.concatenate([r[1]['trigger_vector'] for r in results])
        all_scatter_counts = np.concatenate([r[1]['scatter_counts'] for r in results]) if total_trigger_count > 0 else np.array([])
        all_base_scores = all_scores.copy()  # 這已經是包含 freegame 的分數
        all_free_scores = np.concatenate([r[1]['free_scores'] for r in results]) if total_trigger_count > 0 else np.array([])
        all_free_spin_counts = np.concatenate([r[1]['free_spin_counts'] for r in results]) if total_trigger_count > 0 else np.array([])
        
        # C1 統計
        total_base_c1 = sum(r[1]['base_c1_appearances'] for r in results)
        total_free_c1 = sum(r[1]['free_c1_appearances'] for r in results)
        all_base_c1_vector = np.concatenate([r[1]['base_c1_appearance_vector'] for r in results])
        all_free_c1_per_game = np.concatenate([r[1]['free_c1_appearance_per_game'] for r in results]) if total_trigger_count > 0 else np.array([])
        
        trigger_info = {
            'trigger_count': total_trigger_count,
            'trigger_vector': all_trigger_vectors,
            'scatter_counts': all_scatter_counts,
            'base_scores': all_base_scores,
            'free_scores': all_free_scores,
            'base_scores_sum': total_base_score,
            'free_scores_sum': total_free_score,
            'free_spin_counts': all_free_spin_counts,
            'base_rtp': base_rtp,
            'free_rtp': free_rtp,
            'total_rtp': total_rtp,
            'base_c1_appearances': total_base_c1,
            'free_c1_appearances': total_free_c1,
            'total_c1_appearances': total_base_c1 + total_free_c1,
            'base_c1_appearance_vector': all_base_c1_vector,
            'free_c1_appearance_per_game': all_free_c1_per_game
        }
        
        return all_scores, trigger_info


def _worker_fullgame(args):
    """
    Worker 函數，用於多進程執行
    注意：這個函數會在子進程中執行，需要重新載入全局變量
    """
    # 從參數中提取數據文件路徑
    data_file = args.pop('data_file', None)
    
    # 在子進程中重新載入數據到 globals()
    # 這是必要的，因為 Windows 的多進程不會 fork，而是重新導入模塊
    if data_file:
        try:
            import os
            if os.path.exists(data_file):
                # 重新載入數據
                data_dict = extract_all_js_vars_numpy(data_file)
                # 將數據設置到當前模塊的 globals() 中
                g = globals()
                for key, value in data_dict.items():
                    g[key] = value
        except Exception as e:
            # 如果載入失敗，嘗試繼續（假設參數已經完整傳遞）
            pass
    
    # Worker 始終執行完整模式以獲取詳細統計
    args_copy = args.copy()
    original_summary_only = args_copy.pop('return_summary_only', False)
    args_copy['return_summary_only'] = False  # Worker 始終獲取完整資訊
    
    total_scores, info = fullgame(**args_copy)
    
    # 如果原始請求是 summary_only，可以丟棄大陣列以節省記憶體傳輸
    if original_summary_only:
        return {
            'base_scores_sum': info['base_scores_sum'],
            'free_scores_sum': info['free_scores_sum'],
            'trigger_count': info['trigger_count']
        }
    else:
        return (total_scores, info)


g = globals()
# %% 模擬測試
# 預先獲取全局變量以提高性能

# ===============================================
# 注意: 以下测试代码已注释，避免每次导入模块时自动执行
# 如需测试，请在 Interactive 环境中手动运行
# ===============================================

# #%%
# # BASE GAME 模擬測試
# trt = basegame(
#         n=1000000,
#         baseGameSurface=g.get('baseGameSurface', [1, 0]),
#         baseGameHighSymbolWeight=g.get('baseGameHighSymbolWeight'),
#         baseGameSymbolHigh=g.get('baseGameSymbolLow'),
#         linkpoint=g.get('linkpoint'),
#         return_scatter_counts=True
#     )
# print(np.mean(trt[0]))

# #%%
# # FREE GAME 模擬測試
# trt1 = freegame(
#         n=100000,
#         scatter_counts=[3]*100000,  # 修正：與n保持一致
#         linkpoint=g.get('linkpoint'),
#         freeGameHighSymbolWeight=g.get('freeGameHighSymbolWeight'),
#         freeGameLowSymbolWeight=g.get('freeGameLowSymbolWeight'),
#         freeGameSymbolHighA=g.get('freeGameSymbolHighA'),
#         freeGameSymbolLow=g.get('freeGameSymbolLow'),
#         freeHighDropWeights1st=g.get('freeHighDropWeights1st'),
#         freeHighDropWeights2nd=g.get('freeHighDropWeights2nd'),
#         freeHighDropWeights3rd=g.get('freeHighDropWeights3rd'),
#         freeHighDropWeights4th=g.get('freeHighDropWeights4th'),
#         freeHighMyConvertWeights=g.get('freeHighMyConvertWeights'),
#         freeLowDropWeights1st=g.get('freeLowDropWeights1st'),
#         freeLowDropWeights2nd=g.get('freeLowDropWeights2nd'),
#         freeLowDropWeights3rd=g.get('freeLowDropWeights3rd'),
#         freeLowDropWeights4th=g.get('freeLowDropWeights4th'),
#         freeLowMyConvertWeights=g.get('freeLowMyConvertWeights')
#     )

# #%%
# # FULL GAME 模擬測試 (basegame + freegame 整合)
# trt2 = fullgame(
#         n=100000000,
#         baseGameSurface=g.get('baseGameSurface', [1, 0]),
#         baseGameHighSymbolWeight=g.get('baseGameHighSymbolWeight'),
#         baseGameSymbolHigh=g.get('baseGameSymbolLow'),
#         linkpoint=g.get('linkpoint'),
#         freeGameHighSymbolWeight=g.get('freeGameHighSymbolWeight'),
#         freeGameLowSymbolWeight=g.get('freeGameLowSymbolWeight'),
#         freeGameSymbolHighA=g.get('freeGameSymbolHighA'),
#         freeGameSymbolLow=g.get('freeGameSymbolLow')
#     )
# print(np.mean(trt2[0]))
# %%
