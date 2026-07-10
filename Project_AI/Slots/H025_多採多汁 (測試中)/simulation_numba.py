#%%
"""
Numba优化版本的游戏模拟
关键数值计算使用numba加速
"""
import numpy as np
import random
import json
import os
import sys
import io
import multiprocessing as mp
from numba import jit

# ==================== 自定义异常 ====================
class MegaPlacementImpossibleError(Exception):
    """当无法放置所有required的mega符号时抛出此异常"""
    pass

# 从data.js加载配置数据
def load_game_data():
    """加载游戏配置数据"""
    try:
        # 使用相对路径，加载同资料夹下的data.js
        file_path = os.path.join(os.path.dirname(__file__), 'data.js')
        print(f"正在加载数据文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            json_str = content.replace('const data = ', '').rstrip(';')
            data = json.loads(json_str)
            
            # 打印 DropWeight 的维度信息
            if 'DropWeight' in data:
                dw_array = np.array(data['DropWeight'])
                print(f"DropWeight 数据维度: {dw_array.shape}")
            if 'FreeDropWeight' in data:
                fdw_array = np.array(data['FreeDropWeight'])
                print(f"FreeDropWeight 数据维度: {fdw_array.shape}")
            
            return data
    except Exception as e:
        print(f"无法加载data.js: {e}")
        return None

GAME_DATA = load_game_data()

# ==================== 预计算数据缓存（性能优化）====================
class PrecomputedGameData:
    """预计算并缓存所有游戏配置数据，避免每轮重复转换"""
    def __init__(self):
        if GAME_DATA is None:
            self.available = False
            return
        
        self.available = True
        
        # 预计算BaseGame的Reel数据（1-6套）
        self.base_reel_symbols = {}
        self.base_reel_weights = {}
        self.base_my_weights = {}
        
        # 预计算FreeGame的Reel数据（1-6套）
        self.free_reel_symbols = {}
        self.free_reel_weights = {}
        self.free_my_weights = {}
        
        # 预计算BaseGame的Drop数据（1-6套）
        self.base_drop_symbols = {}
        self.base_drop_rweights = {}
        self.base_drop_pweights = {}
        self.base_drop_method_weights = {}
        self.base_drop_my_weights = {}
        
        # 预计算FreeGame的Drop数据（1-6套）
        self.free_drop_symbols = {}
        self.free_drop_rweights = {}
        self.free_drop_pweights = {}
        self.free_drop_method_weights = {}
        self.free_drop_my_weights = {}
        
        # 预计算权重选择数组
        self.base_reel_selection_weights = None
        self.free_reel_selection_weights = None
        self.base_drop_selection_weights = None  # [10, 6] 矩阵
        self.free_drop_selection_weights = None  # [10, 6] 矩阵
        
        # 预计算eliminate数据
        self.eliminate_symbol = None
        self.drop_my_weights = None
        
        self._precompute_all()
    
    def _precompute_all(self):
        """预计算所有数据"""
        # BaseGame Reel数据
        for i in range(1, 7):
            reel_key = f'baseGameSymbol{i}'
            weight_key = f'baseGameSymbolWeight{i}'
            my_key = f'baseGameMY{i}'
            
            if reel_key in GAME_DATA:
                self.base_reel_symbols[i] = np.array(GAME_DATA[reel_key], dtype=np.int32)
            if weight_key in GAME_DATA:
                weights = np.array(GAME_DATA[weight_key], dtype=np.float32)
                self.base_reel_weights[i] = (weights * 10000).astype(np.int32)
            if my_key in GAME_DATA:
                weights = np.array(GAME_DATA[my_key], dtype=np.float32)
                self.base_my_weights[i] = (weights * 10000).astype(np.int32)
        
        # FreeGame Reel数据
        for i in range(1, 7):
            reel_key = f'FreeGameSymbol{i}'
            weight_key = f'FreeGameSymbolWeight{i}'
            my_key = f'FreeGameMY{i}'
            
            if reel_key in GAME_DATA:
                self.free_reel_symbols[i] = np.array(GAME_DATA[reel_key], dtype=np.int32)
            if weight_key in GAME_DATA:
                weights = np.array(GAME_DATA[weight_key], dtype=np.float32)
                self.free_reel_weights[i] = (weights * 10000).astype(np.int32)
            if my_key in GAME_DATA:
                weights = np.array(GAME_DATA[my_key], dtype=np.float32)
                self.free_my_weights[i] = (weights * 10000).astype(np.int32)
        
        # BaseGame Drop数据
        for i in range(1, 7):
            drop_key = f'BaseGameDrop{i}'
            rweight_key = f'BaseGameDropRWeight{i}'
            pweight_key = f'BaseGameDropPWeight{i}'
            method_key = f'BaseGameDropmethod{i}'
            my_key = f'BaseGameDropMy{i}'
            
            if drop_key in GAME_DATA:
                self.base_drop_symbols[i] = np.array(GAME_DATA[drop_key], dtype=np.int32)
            if rweight_key in GAME_DATA:
                weights = np.array(GAME_DATA[rweight_key], dtype=np.float32)
                self.base_drop_rweights[i] = (weights * 10000).astype(np.int32)
            if pweight_key in GAME_DATA:
                weights = np.array(GAME_DATA[pweight_key], dtype=np.float32)
                self.base_drop_pweights[i] = (weights * 10000).astype(np.int32)
            if method_key in GAME_DATA:
                weights = np.array(GAME_DATA[method_key], dtype=np.float32)
                self.base_drop_method_weights[i] = (weights * 10000).astype(np.int32)
            if my_key in GAME_DATA:
                weights = np.array(GAME_DATA[my_key], dtype=np.float32)
                self.base_drop_my_weights[i] = (weights * 10000).astype(np.int32)
        
        # FreeGame Drop数据
        for i in range(1, 7):
            drop_key = f'FreeGameDrop{i}'
            rweight_key = f'FreeGameDropRWeight{i}'
            pweight_key = f'FreeGameDropPWeight{i}'
            method_key = f'FreeGameDropmethod{i}'
            my_key = f'FreeGameDropMy{i}'
            
            if drop_key in GAME_DATA:
                self.free_drop_symbols[i] = np.array(GAME_DATA[drop_key], dtype=np.int32)
            if rweight_key in GAME_DATA:
                weights = np.array(GAME_DATA[rweight_key], dtype=np.float32)
                self.free_drop_rweights[i] = (weights * 10000).astype(np.int32)
            if pweight_key in GAME_DATA:
                weights = np.array(GAME_DATA[pweight_key], dtype=np.float32)
                self.free_drop_pweights[i] = (weights * 10000).astype(np.int32)
            if method_key in GAME_DATA:
                weights = np.array(GAME_DATA[method_key], dtype=np.float32)
                self.free_drop_method_weights[i] = (weights * 10000).astype(np.int32)
            if my_key in GAME_DATA:
                weights = np.array(GAME_DATA[my_key], dtype=np.float32)
                self.free_drop_my_weights[i] = (weights * 10000).astype(np.int32)
        
        # Reel选择权重
        if 'ReelWeight' in GAME_DATA:
            weights = np.array(GAME_DATA['ReelWeight'], dtype=np.float32)
            self.base_reel_selection_weights = (weights * 10000).astype(np.int32)
        
        if 'FreeReelWeight' in GAME_DATA:
            weights = np.array(GAME_DATA['FreeReelWeight'], dtype=np.float32)
            self.free_reel_selection_weights = (weights * 10000).astype(np.int32)
        
        # Drop选择权重（10行×6列）
        if 'DropWeight' in GAME_DATA:
            weights = np.array(GAME_DATA['DropWeight'], dtype=np.float32)
            self.base_drop_selection_weights = (weights * 10000).astype(np.int32)
        
        if 'FreeDropWeight' in GAME_DATA:
            weights = np.array(GAME_DATA['FreeDropWeight'], dtype=np.float32)
            self.free_drop_selection_weights = (weights * 10000).astype(np.int32)
        
        # Eliminate数据
        self.base_eliminate_symbol = None
        self.free_eliminate_symbol = None
        
        if 'Eliminate' in GAME_DATA:
            weights = np.array(GAME_DATA['Eliminate'], dtype=np.float32)
            self.base_eliminate_symbol = (weights * 10000).astype(np.int32)
        
        if 'FreeEliminate' in GAME_DATA:
            weights = np.array(GAME_DATA['FreeEliminate'], dtype=np.float32)
            self.free_eliminate_symbol = (weights * 10000).astype(np.int32)

# 全局预计算数据实例
PRECOMPUTED_DATA = PrecomputedGameData()

# ==================== 游戏常量 ====================
WILD_SYMBOL = 0  # Wild符号ID（万能符号）

@jit(nopython=True, cache=True)
def get_wild_multiplier(eliminate_count):
    """获取Wild倍数（基于消除次数）
    
    序列：[1, 2, 4, 6, 8, 10, 12, ..., 100]
    - 第1次（index 0）：1
    - 第2次（index 1）：2
    - 之后每次+2：4, 6, 8, ...
    - 上限：100
    """
    if eliminate_count <= 0:
        return 1
    elif eliminate_count == 1:
        return 2
    else:
        # 从第2次开始：4, 6, 8, 10, ...
        mult = 2 + (eliminate_count - 1) * 2
        return min(mult, 100)

# ==================== 六角网格配置（Java版本对标）====================
# 六角网格布局：[4,5,6,7,6,5,4]
# 使用7×7矩形数组，用symbol=9标记无效位置
# 访问方式：board[col][row]，与Java版本一致

# 常量定义
ROWS = 7
COLS = 7
CENTER_COL = 3  # Java版本：centerCol = 3
CENTER_ROW = 3  # Java版本：centerRow = 3
EMPTY_MARKER = 9  # 用于标记六角网格外的无效位置

# 每个col（列）的有效row范围（基于六角网格布局[4,5,6,7,6,5,4]）
# col 0: rows [0,1,2,3] - 4格
# col 1: rows [0,1,2,3,4] - 5格
# col 2: rows [0,1,2,3,4,5] - 6格
# col 3: rows [0,1,2,3,4,5,6] - 7格（中央列）
# col 4: rows [1,2,3,4,5,6] - 6格
# col 5: rows [2,3,4,5,6] - 5格
# col 6: rows [3,4,5,6] - 4格

def get_valid_rows_for_col(col):
    """获取指定列的有效行范围"""
    if col == 0:
        return list(range(0, 4))  # [0,1,2,3]
    elif col == 1:
        return list(range(0, 5))  # [0,1,2,3,4]
    elif col == 2:
        return list(range(0, 6))  # [0,1,2,3,4,5]
    elif col == 3:
        return list(range(0, 7))  # [0,1,2,3,4,5,6]
    elif col == 4:
        return list(range(0, 6))  # [0,1,2,3,4,5]（Java上对齐）
    elif col == 5:
        return list(range(0, 5))  # [0,1,2,3,4]（Java上对齐）
    elif col == 6:
        return list(range(0, 4))  # [0,1,2,3]（Java上对齐）
    return []

@jit(nopython=True, cache=True)
def is_valid_hex_cell(col, row):
    """判断(col, row)是否是有效的六角网格位置（Java版本对标）
    
    Args:
        col: 列索引 (0-6)
        row: 行索引 (0-6)
    
    Returns:
        bool: 是否为有效位置
    """
    if col < 0 or col >= COLS or row < 0 or row >= ROWS:
        return False
    
    # 根据列判断有效行范围
    if col == 0:
        return 0 <= row <= 3
    elif col == 1:
        return 0 <= row <= 4
    elif col == 2:
        return 0 <= row <= 5
    elif col == 3:
        return 0 <= row <= 6  # 中央列，全部有效
    elif col == 4:
        return 0 <= row <= 5  # Java上对齐：None在底部(row6)
    elif col == 5:
        return 0 <= row <= 4  # Java上对齐：None在底部(row5,6)
    elif col == 6:
        return 0 <= row <= 3  # Java上对齐：None在底部(row4,5,6)

    return False

@jit(nopython=True, cache=True)
def get_hex_neighbors(col, row):
    """获取六角网格中(col, row)的6个相邻格子坐标（对标Java ScreenCalculator.dfsHelperNest）

    Java权威规则（centerCol=3，左右两路门槛不同）：
        上: (col, row-1)        下: (col, row+1)        ← 恒定
        左路 (col-1)：c <= centerCol → 左上(col-1,row-1) 左下(col-1,row)
                       c >  centerCol → 左上(col-1,row)   左下(col-1,row+1)
        右路 (col+1)：c <  centerCol → 右上(col+1,row)   右下(col+1,row+1)
                       c >= centerCol → 右上(col+1,row-1) 右下(col+1,row)

    注意：中央列 c=3 走「左路用<=分支、右路用>=分支」的混合，自成一格。
    此规则在Java上对齐布局上为对称无向六角图（0条单向边）。
    """
    neighbors = np.zeros((6, 2), dtype=np.int32)
    directions = np.zeros((6, 2), dtype=np.int32)

    # 上、下（同列，恒定）
    directions[0, 0] = 0;  directions[0, 1] = -1   # 上
    directions[1, 0] = 0;  directions[1, 1] = 1    # 下

    # 左路 (col-1)：Java门槛 c <= centerCol
    if col <= CENTER_COL:
        directions[2, 0] = -1; directions[2, 1] = -1   # 左上
        directions[3, 0] = -1; directions[3, 1] = 0    # 左下
    else:
        directions[2, 0] = -1; directions[2, 1] = 0    # 左上
        directions[3, 0] = -1; directions[3, 1] = 1    # 左下

    # 右路 (col+1)：Java门槛 c < centerCol
    if col < CENTER_COL:
        directions[4, 0] = 1;  directions[4, 1] = 0    # 右上
        directions[5, 0] = 1;  directions[5, 1] = 1    # 右下
    else:
        directions[4, 0] = 1;  directions[4, 1] = -1   # 右上
        directions[5, 0] = 1;  directions[5, 1] = 0    # 右下

    for i in range(6):
        neighbors[i, 0] = col + directions[i, 0]
        neighbors[i, 1] = row + directions[i, 1]

    return neighbors

# ==================== Numba加速的核心函数 ====================

@jit(nopython=True, cache=True)
def weighted_choice_numba(weights):
    """numba优化的加权随机选择（整数权重，整数运算）"""
    total = np.sum(weights)
    r = np.random.randint(0, total)
    cumulative = 0
    for i in range(len(weights)):
        cumulative += weights[i]
        if r < cumulative:
            return i
    return len(weights) - 1

@jit(nopython=True, cache=True)
def bfs_find_connected(board, start_col, start_row, visited):
    """使用BFS查找相连的相同符号（Java版本对标，六角网格）
    
    Args:
        board: 游戏版面，访问方式为board[col, row]
        start_col: 起始列 (0-6)
        start_row: 起始行 (0-6)
        visited: 访问标记数组，visited[col, row]
    
    Wild符号规则：
    - Wild(0)可以与任何符号连通，作为桥梁连接同种符号
    - Wild不会被标记为visited，可以参与多个符号组
    - 但Wild最终只会被清除一次（由fixed_mask保护）
    
    Returns:
        connected_cells: numpy array of shape (n, 2)，每行为[col, row]
    """
    cols_count, rows_count = board.shape
    
    # 检查起始位置
    if visited[start_col, start_row] or board[start_col, start_row] == 0:
        return np.zeros((0, 2), dtype=np.int32)
    
    if not is_valid_hex_cell(start_col, start_row):
        return np.zeros((0, 2), dtype=np.int32)
    
    symbol = board[start_col, start_row]
    
    # 使用数组模拟队列
    max_size = cols_count * rows_count
    queue = np.zeros((max_size, 2), dtype=np.int32)
    queue[0, 0] = start_col
    queue[0, 1] = start_row
    q_front = 0
    q_back = 1
    
    result = np.zeros((max_size, 2), dtype=np.int32)
    result_size = 0
    
    # 用于防止Wild被重复加入队列（在同一次BFS中）
    wild_in_queue = np.zeros((cols_count, rows_count), dtype=np.bool_)
    
    visited[start_col, start_row] = True
    
    while q_front < q_back:
        curr_c = queue[q_front, 0]
        curr_r = queue[q_front, 1]
        q_front += 1
        
        result[result_size, 0] = curr_c
        result[result_size, 1] = curr_r
        result_size += 1
        
        # 获取六角网格的六个相邻格子
        neighbors = get_hex_neighbors(curr_c, curr_r)
        
        for i in range(6):
            next_c = neighbors[i, 0]
            next_r = neighbors[i, 1]
            
            # 检查是否在有效范围内且是有效的六角格子
            if 0 <= next_c < cols_count and 0 <= next_r < rows_count:
                if is_valid_hex_cell(next_c, next_r):
                    next_symbol = board[next_c, next_r]
                    
                    # 处理相同符号
                    if next_symbol == symbol:
                        if not visited[next_c, next_r]:
                            visited[next_c, next_r] = True
                            queue[q_back, 0] = next_c
                            queue[q_back, 1] = next_r
                            q_back += 1
                    # 处理Wild符号
                    elif next_symbol == 0:
                        # Wild不标记visited（可以被多个组使用）
                        # 但在当前BFS中只加入队列一次
                        if not wild_in_queue[next_c, next_r]:
                            wild_in_queue[next_c, next_r] = True
                            queue[q_back, 0] = next_c
                            queue[q_back, 1] = next_r
                            q_back += 1
    
    return result[:result_size]

@jit(nopython=True, cache=True)
def select_my_targets_numba(my_weights):
    """按顺序抽选MY1→MY2→MY3目标符号，确保三种MY各不相同
    
    新逻辑（匹配最新Java版本）：
    - 只使用单一权重数组（my_weights[0] 或 my_weights 本身）
    - 每次抽选后将该符号权重归零，避免重复
    - MY1: 从完整权重抽选
    - MY2: 将MY1目标权重设为0后抽选（不与MY1重复）
    - MY3: 将MY1、MY2目标权重都设为0后抽选（不与MY1、MY2重复）
    """
    my_targets = np.full(3, -1, dtype=np.int32)
    
    # 判断是否为二维数组，如果是则只使用第一行
    if my_weights.ndim == 2:
        base_weights = my_weights[0].copy()
    else:
        base_weights = my_weights.copy()
    
    # 按顺序抽选3个不同的目标（权重归零机制）
    for my_idx in range(3):
        total = np.sum(base_weights)
        if total > 0:
            # 从当前权重中抽选
            my_targets[my_idx] = weighted_choice_numba(base_weights)
            # 将抽中的符号权重归零，避免下次重复
            base_weights[my_targets[my_idx]] = 0
        else:
            # fallback：找一个未使用的符号
            for s in range(len(base_weights)):
                already_used = False
                for prev_idx in range(my_idx):
                    if my_targets[prev_idx] == s:
                        already_used = True
                        break
                if not already_used:
                    my_targets[my_idx] = s
                    break

    return my_targets

@jit(nopython=True, cache=True)
def convert_my_numba(board, my_weights):
    """转换MY符号(10,11,12)为不同符号（Java版本对标）

    访问方式：board[col, row]
    """
    cols_count, rows_count = board.shape

    # 抽选3个不同的目标符号
    my_targets = select_my_targets_numba(my_weights)

    # 统一转换所有MY符号
    for col in range(cols_count):
        for row in range(rows_count):
            if is_valid_hex_cell(col, row):
                symbol = board[col, row]
                if 10 <= symbol <= 12:
                    my_idx = symbol - 10
                    if my_idx < 3 and my_targets[my_idx] >= 0:
                        board[col, row] = my_targets[my_idx]

@jit(nopython=True, cache=True)
def convert_my_numba_with_targets(board, my_targets):
    """使用预先确定的目标转换MY符号（Java版本对标）
    
    访问方式：board[col, row]
    """
    cols_count, rows_count = board.shape
    for col in range(cols_count):
        for row in range(rows_count):
            if is_valid_hex_cell(col, row):
                symbol = board[col, row]
                if 10 <= symbol <= 12:
                    my_idx = symbol - 10
                    if my_idx < len(my_targets):
                        board[col, row] = my_targets[my_idx]

@jit(nopython=True, cache=True)
def fix_c1_numba(board):
    """确保每个逻辑行最多1个C1（Java版本对标）

    多余的C1转换为M7(8)（对标Java ScreenGenerator mysteryIdx=7）
    坐标系统：board[col, row]，其中col=逻辑行索引，row=位置索引
    访问方式：对每个逻辑行（col）检查所有位置（row）
    """
    cols_count, rows_count = board.shape
    # 对每个逻辑行进行检查
    for logic_row_idx in range(cols_count):
        c1_count = 0
        # 扫描该逻辑行的所有位置
        for position in range(rows_count):
            if is_valid_hex_cell(logic_row_idx, position):
                if board[logic_row_idx, position] == 1:
                    if c1_count > 0:
                        board[logic_row_idx, position] = 8  # 转换为M7（对标Java mysteryIdx=8）
                    c1_count += 1

@jit(nopython=True, cache=True)
def fix_c1_preserve_existing_numba(board, existing_c1_mask):
    """确保每个逻辑行最多1个C1，优先保留已存在的C1

    规则：
    - 如果该行已有C1 → 保留已有的C1，转换新出现的C1为M7(8)
    - 如果该行没有已有C1 → 保留第一个新出现的C1
    
    Args:
        board: 游戏版面 board[col, row]
        existing_c1_mask: 标记已存在C1的位置 existing_c1_mask[col, row]=True
    """
    cols_count, rows_count = board.shape
    
    for logic_row_idx in range(cols_count):
        # 第一步：检查该行是否有已存在的C1
        has_existing_c1 = False
        existing_c1_position = -1
        
        for position in range(rows_count):
            if is_valid_hex_cell(logic_row_idx, position):
                if existing_c1_mask[logic_row_idx, position] and board[logic_row_idx, position] == 1:
                    has_existing_c1 = True
                    existing_c1_position = position
                    break
        
        # 第二步：根据是否有已存在的C1来处理
        if has_existing_c1:
            # 情况1：该行有已存在的C1 → 保留它，转换所有其他C1
            for position in range(rows_count):
                if is_valid_hex_cell(logic_row_idx, position):
                    if board[logic_row_idx, position] == 1 and position != existing_c1_position:
                        board[logic_row_idx, position] = 8  # 转换新出现的C1为7（对标Java mysteryIdx=8）
        else:
            # 情况2：该行没有已存在的C1 → 保留第一个出现的C1
            c1_count = 0
            for position in range(rows_count):
                if is_valid_hex_cell(logic_row_idx, position):
                    if board[logic_row_idx, position] == 1:
                        if c1_count > 0:
                            board[logic_row_idx, position] = 8  # 转换多余的C1为M7（对标Java mysteryIdx=8）
                        c1_count += 1

@jit(nopython=True, cache=True)
def drop_symbols_numba(board, fixed_mask):
    """符号垂直掉落（Java版本对标）
    
    每列独立处理掉落，符号向下移动填补空位
    访问方式：board[col, row]
    row=0是顶部，row=6是底部，符号向下掉落
    """
    cols_count, rows_count = board.shape
    
    # 每列独立处理掉落
    for col in range(cols_count):
        # 收集该列所有非空且非固定的符号（保持相对顺序）
        max_cells = rows_count
        non_empty_symbols = np.zeros(max_cells, dtype=np.int32)
        symbol_count = 0
        
        # 从上往下收集非空符号（保持它们的相对顺序）
        for row in range(rows_count):
            if is_valid_hex_cell(col, row):
                if not fixed_mask[col, row] and board[col, row] != 0 and board[col, row] != EMPTY_MARKER:
                    non_empty_symbols[symbol_count] = board[col, row]
                    symbol_count += 1
        
        # 从下往上填充符号（符号掉到底部，保持垂直相对顺序，对标Java fall-down）
        # non_empty_symbols 是按 row 0→6 收集的（上→下），最下面的 survivor 在末尾
        # 回填时从最底部开始放入末尾元素，保证原本在下的仍在下
        idx = symbol_count - 1  # 从最下面收集到的符号开始
        for row in range(rows_count - 1, -1, -1):  # 从底部往上扫描
            if is_valid_hex_cell(col, row):
                if not fixed_mask[col, row]:
                    if idx >= 0:
                        board[col, row] = non_empty_symbols[idx]
                        idx -= 1
                    else:
                        board[col, row] = 0  # 上部空位设为0

@jit(nopython=True, cache=True)
def initialize_board_numba(board, reel_symbols, reel_weights):
    """使用numba加速初始化版面（Java版本对标）
    
    坐标系统：board[col, row]，其中col=逻辑行索引，row=行内位置索引
    数据组织：reel_symbols[logic_row_idx] 表示第logic_row_idx个逻辑行的轮带数据
    填充方式：按逻辑行循环，填充每行的各个位置
    中央位置[CENTER_COL, CENTER_ROW]=[3,3]最后替换为WILD
    """
    cols_count, rows_count = board.shape
    
    # 初始化所有位置为空标记
    for col in range(cols_count):
        for row in range(rows_count):
            if not is_valid_hex_cell(col, row):
                board[col, row] = EMPTY_MARKER  # 无效位置标记为9
    
    # 按逻辑行填充（数据是按逻辑行组织的）
    # logic_row_idx对应board的col维度（逻辑行索引）
    for logic_row_idx in range(cols_count):
        # 获取该逻辑行的reel数据
        reel_data = reel_symbols[logic_row_idx]
        weight_data = reel_weights[logic_row_idx]
        
        start_idx = weighted_choice_numba(weight_data)
        reel_len = len(reel_data)
        
        # 确定该逻辑行的有效位置范围
        if logic_row_idx == 0:
            pos_start = 0
            pos_count = 4
        elif logic_row_idx == 1:
            pos_start = 0
            pos_count = 5
        elif logic_row_idx == 2:
            pos_start = 0
            pos_count = 6
        elif logic_row_idx == 3:
            pos_start = 0
            pos_count = 7
        elif logic_row_idx == 4:
            pos_start = 0   # Java上对齐
            pos_count = 6
        elif logic_row_idx == 5:
            pos_start = 0   # Java上对齐
            pos_count = 5
        elif logic_row_idx == 6:
            pos_start = 0   # Java上对齐
            pos_count = 4
        else:
            continue
        
        # 按位置顺序填充该逻辑行
        for idx in range(pos_count):
            position = pos_start + idx
            # 从轮带取连续符号
            symbol_value = reel_data[(start_idx + idx) % reel_len]
            # 0视为C1
            if symbol_value == 0:
                symbol_id = 1
            else:
                symbol_id = symbol_value
            # board[col, row] 其中 col=logic_row_idx, row=position
            board[logic_row_idx, position] = symbol_id
    
    # 中央位置替换为WILD
    board[CENTER_COL, CENTER_ROW] = 0  # WILD_SYMBOL at CENTER position
    
    # 中央位置替换为WILD
    board[CENTER_COL, CENTER_ROW] = 0  # WILD_SYMBOL at CENTER position

@jit(nopython=True, cache=True)
def fill_empty_method0_numba(board, fixed_mask, drop_table, drop_rweights):
    """填充方法0：每行独立加权抽取轮带起始位置（Java版本对标）
    
    坐标系统：board[col, row]，其中col=逻辑行索引，row=位置索引
    数据组织：drop_table[logic_row_idx] 表示第logic_row_idx个逻辑行的轮带数据
    填充方式：按逻辑行循环，扫描每行的各个位置
    """
    cols_count, rows_count = board.shape
    
    # 每个逻辑行独立抽取轮带的一段
    for logic_row_idx in range(cols_count):
        drop_data = drop_table[logic_row_idx]
        drop_weight = drop_rweights[logic_row_idx]
        drop_len = len(drop_data)
        
        # 为当前逻辑行抽取轮带的起始位置
        start_idx = weighted_choice_numba(drop_weight)
        offset = 0  # 轮带偏移量
        
        # 按位置顺序扫描该逻辑行，填充空位
        for position in range(rows_count):
            if is_valid_hex_cell(logic_row_idx, position):
                if board[logic_row_idx, position] == 0 and not fixed_mask[logic_row_idx, position]:
                    # 从轮带的起始位置开始顺序取符号
                    # Java边界对标：(start+offset)>=len 时改用 (offset-1)，而非取模回绕
                    raw = start_idx + offset
                    drop_idx = (offset - 1) if raw >= drop_len else raw
                    symbol_value = drop_data[drop_idx]
                    offset += 1  # 轮带移动一个位置
                    
                    # 0视为C1
                    if symbol_value == 0:
                        symbol_id = 1
                    else:
                        symbol_id = symbol_value
                    
                    board[logic_row_idx, position] = symbol_id

@jit(nopython=True, cache=True)
def fill_empty_method1_numba(board, fixed_mask, drop_table, position_idx):
    """填充方法1：所有行从相同起始位置开始（Java版本对标）
    
    坐标系统：board[col, row]，其中col=逻辑行索引，row=位置索引
    数据组织：drop_table[logic_row_idx] 表示第logic_row_idx个逻辑行的轮带数据
    填充方式：按逻辑行循环，扫描每行的各个位置
    """
    cols_count, rows_count = board.shape
    
    for logic_row_idx in range(cols_count):
        drop_data = drop_table[logic_row_idx]
        drop_len = len(drop_data)
        offset = 0  # 当前逻辑行的偏移量
        
        # 按位置顺序扫描该逻辑行
        for position in range(rows_count):
            if is_valid_hex_cell(logic_row_idx, position):
                if board[logic_row_idx, position] == 0 and not fixed_mask[logic_row_idx, position]:
                    # 使用 position_idx + offset；Java边界对标：溢位时改用 (offset-1)，非取模
                    raw = position_idx + offset
                    drop_idx = (offset - 1) if raw >= drop_len else raw
                    symbol_value = drop_data[drop_idx]
                    offset += 1  # 下一个空格使用下一个位置
                    
                    # 0视为C1
                    if symbol_value == 0:
                        symbol_id = 1
                    else:
                        symbol_id = symbol_value

                    board[logic_row_idx, position] = symbol_id

@jit(nopython=True, cache=True)
def calculate_match_score_numba(linkpoint, board, positions_flat, num_positions):
    """计算单个匹配的分数（numba优化）"""
    if num_positions == 0:
        return 0
    
    # 获取符号和计数
    symbol = board[positions_flat[0, 0], positions_flat[0, 1]]
    count = num_positions
    
    # 获取基础分数
    # linkpoint最后一列代表15+个符号的分数
    symbol_idx = symbol - 2
    count_idx = min(count - 6, linkpoint.shape[1] - 1)
    if 0 <= symbol_idx < linkpoint.shape[0] and 0 <= count_idx < linkpoint.shape[1]:
        base_score = linkpoint[symbol_idx, count_idx]
    else:
        base_score = 0
    
    return base_score

@jit(nopython=True, cache=True)
def clear_positions_numba(board, positions_flat, num_positions):
    """清除指定位置的符号（numba优化，保护中央Wild符号）
    
    访问方式：board[col, row]
    Wild位置：[CENTER_COL, CENTER_ROW] = [3, 3]
    """
    for i in range(num_positions):
        col = positions_flat[i, 0]
        row = positions_flat[i, 1]
        # 跳过中央Wild位置[3,3]
        if col == CENTER_COL and row == CENTER_ROW:
            continue
        board[col, row] = 0

@jit(nopython=True, cache=True)
def _dfs_nest(c, r, target_id, board, visited, result, size_arr, wild_arr):
    """递归 DFS，完全对标 Java ScreenCalculator.dfsHelperNest。

    board[c, r]；None=EMPTY_MARKER(9)；Wild=0；中心 [CENTER_COL, CENTER_ROW]=[3,3]。
    - 仅用边界 + 符号值判断（不使用 is_valid_hex_cell），与 Java 一致：
      None(9) 因 9!=target 且 9!=0 自然被挡。
    - Wild(0) 永远可进入（board==0 绕过 visited），可桥接多组同色；
      但中心 Wild 在同一 cluster 只加一次（wild_arr 旗标）。
    - 六向顺序与 Java directions 完全一致：上、下、左上、左下、右上、右下。

    size_arr[0]：当前 cluster 已加入的格数；wild_arr[0]：本 cluster 是否已含中心 Wild。
    """
    cols_count, rows_count = board.shape
    # 边界（对标 Java: c/r 越界 return）
    if c < 0 or c >= cols_count:
        return
    if r < 0 or r >= rows_count:
        return
    # 对标 Java: if ((visited || board!=target) && board!=0) return;
    if (visited[c, r] or board[c, r] != target_id) and board[c, r] != 0:
        return
    # 对标 Java: 中心 Wild [3,3] 在同一 cluster 只加一次
    if wild_arr[0] and c == CENTER_COL and r == CENTER_ROW:
        return

    visited[c, r] = True
    idx = size_arr[0]
    result[idx, 0] = c
    result[idx, 1] = r
    size_arr[0] = idx + 1
    if c == CENTER_COL and r == CENTER_ROW:
        wild_arr[0] = True

    # 六向（对标 Java directions 与递归顺序）
    _dfs_nest(c, r - 1, target_id, board, visited, result, size_arr, wild_arr)  # 上
    _dfs_nest(c, r + 1, target_id, board, visited, result, size_arr, wild_arr)  # 下
    if c <= CENTER_COL:
        _dfs_nest(c - 1, r - 1, target_id, board, visited, result, size_arr, wild_arr)  # 左上
        _dfs_nest(c - 1, r,     target_id, board, visited, result, size_arr, wild_arr)  # 左下
    else:
        _dfs_nest(c - 1, r,     target_id, board, visited, result, size_arr, wild_arr)  # 左上
        _dfs_nest(c - 1, r + 1, target_id, board, visited, result, size_arr, wild_arr)  # 左下
    if c < CENTER_COL:
        _dfs_nest(c + 1, r,     target_id, board, visited, result, size_arr, wild_arr)  # 右上
        _dfs_nest(c + 1, r + 1, target_id, board, visited, result, size_arr, wild_arr)  # 右下
    else:
        _dfs_nest(c + 1, r - 1, target_id, board, visited, result, size_arr, wild_arr)  # 右上
        _dfs_nest(c + 1, r,     target_id, board, visited, result, size_arr, wild_arr)  # 右下


@jit(nopython=True, cache=True)
def find_all_matches_numba(board):
    """查找所有匹配（完全对标 Java calculateScreenResult_WaysGame_ClusterMatchNest）

    访问方式：board[col, row]。外层扫描顺序 c=0..6, r=0..6，
    跳过 visited / C1(1=FreeGame) / None(9)；Wild(0) 允许作 seed（产生 size1，被 >=6 过滤）。
    """
    cols_count, rows_count = board.shape
    visited = np.zeros((cols_count, rows_count), dtype=np.bool_)

    max_matches = cols_count * rows_count
    match_symbols = np.zeros(max_matches, dtype=np.int32)
    match_counts = np.zeros(max_matches, dtype=np.int32)
    all_positions = np.zeros((max_matches * cols_count * rows_count, 2), dtype=np.int32)
    position_starts = np.zeros(max_matches, dtype=np.int32)

    num_matches = 0
    total_positions = 0

    # DFS 复用缓冲
    result = np.zeros((cols_count * rows_count, 2), dtype=np.int32)
    size_arr = np.zeros(1, dtype=np.int64)
    wild_arr = np.zeros(1, dtype=np.bool_)

    for c in range(cols_count):
        for r in range(rows_count):
            if visited[c, r]:
                continue
            target = board[c, r]
            # 对标 Java: 跳过 C1(1=FreeGame) 与 None(9=EMPTY_MARKER)
            if target == 1 or target == EMPTY_MARKER:
                continue

            size_arr[0] = 0
            wild_arr[0] = False
            _dfs_nest(c, r, target, board, visited, result, size_arr, wild_arr)
            n = size_arr[0]

            if n >= 6:
                match_symbols[num_matches] = target
                match_counts[num_matches] = n
                position_starts[num_matches] = total_positions
                for k in range(n):
                    all_positions[total_positions + k, 0] = result[k, 0]
                    all_positions[total_positions + k, 1] = result[k, 1]
                total_positions += n
                num_matches += 1

    return num_matches, match_symbols[:num_matches], match_counts[:num_matches], all_positions[:total_positions], position_starts[:num_matches]
    
@jit(nopython=True, cache=True)
def process_all_matches_numba(board, fixed_mask, linkpoint, match_symbols, match_counts, 
                               all_positions, position_starts, num_matches, wild_eliminate_count, enable_multiplier):
    """处理所有匹配：计算分数、清除符号、解除固定格子（numba优化）
    
    同一次cascade可能包含多组符号消除，每组独立判断：
    - 含Wild的组：使用 基底分数 × Wild倍数（如果enable_multiplier=True）
    - 不含Wild的组：使用 基底分数 × 1
    
    Args:
        wild_eliminate_count: Wild参与消除的累计次数（用于计算Wild倍数）
        enable_multiplier: 是否启用乘倍功能
    
    Returns:
        total_score, final_scores, wild_group_count（包含中央Wild的符号组数量）
    """
    total_score = 0
    final_scores = np.zeros(num_matches, dtype=np.int32)
    wild_group_count = 0  # 统计包含中央Wild的符号组数量
    
    # 遍历每个符号组，独立计算分数
    for match_idx in range(num_matches):
        symbol = match_symbols[match_idx]
        count = match_counts[match_idx]
        
        # 获取这个匹配的位置范围
        start_pos = position_starts[match_idx]
        if match_idx < num_matches - 1:
            end_pos = position_starts[match_idx + 1]
        else:
            end_pos = len(all_positions)
        
        # 检查当前这一组是否包含中央Wild [CENTER_COL, CENTER_ROW] = [3, 3]
        # 注意：每组独立判断，同一次cascade中不同组可能有不同结果
        has_central_wild = False
        for pos_idx in range(start_pos, end_pos):
            if all_positions[pos_idx, 0] == CENTER_COL and all_positions[pos_idx, 1] == CENTER_ROW:
                has_central_wild = True
                wild_group_count += 1  # 统计包含Wild的组数
                break
        
        # 获取基础分数
        # linkpoint最后一列代表15+个符号的分数
        symbol_idx = symbol - 2
        count_idx = min(count - 6, linkpoint.shape[1] - 1)
        if 0 <= symbol_idx < linkpoint.shape[0] and 0 <= count_idx < linkpoint.shape[1]:
            base_score = linkpoint[symbol_idx, count_idx]
        else:
            base_score = 0
        
        # 计算最终分数：
        # 新规则：所有消除都应用Wild倍数（不管是否包含Wild）
        # - 如果启用乘倍：基底分数 × Wild倍数
        # - 如果关闭乘倍：基底分数 × 1
        # 
        # 示例（同一次cascade，wild_eliminate_count=3时倍数为6）：
        #   组1: 7个M1含Wild，基底1000 → 1000 × 6 = 6000
        #   组2: 6个M2不含Wild，基底500 → 500 × 6 = 3000
        #   组3: 8个M3含Wild，基底1500 → 1500 × 6 = 9000
        if enable_multiplier:
            wild_mult = get_wild_multiplier(wild_eliminate_count)
            final_score = base_score * wild_mult
        else:
            final_score = base_score
        
        # 清除符号并解除固定状态（但保留中央Wild符号）
        for pos_idx in range(start_pos, end_pos):
            col = all_positions[pos_idx, 0]
            row = all_positions[pos_idx, 1]
            # 跳过中央Wild位置[CENTER_COL, CENTER_ROW] = [3, 3]
            if col == CENTER_COL and row == CENTER_ROW:
                continue
            board[col, row] = 0
            fixed_mask[col, row] = False  # 解除固定格子
        
        final_scores[match_idx] = final_score
        total_score += final_score
    
    return total_score, final_scores, wild_group_count

# ==================== 游戏类（使用numba加速函数）====================

class Game7x7:
    def __init__(self, symbols=None, linkpoint=None, reel_set=None, drop_set=None, is_free_game=False, enable_multiplier=True):
        """初始化六角网格游戏（Java版本对标）[4,5,6,7,6,5,4]
        
        Args:
            symbols: 符号列表
            linkpoint: 得分表
            reel_set: 指定使用的Reel参数集
            drop_set: 指定使用的Drop参数集
            is_free_game: 是否为Free Game模式（使用FreeGame参数）
            enable_multiplier: 是否启用Wild乘倍功能（默认True）
        
        坐标系统（Java版本对标）：
        - 使用7×7矩形数组，board[col, row]
        - 无效位置标记为EMPTY_MARKER(9)
        - 中心Wild位置：[CENTER_COL, CENTER_ROW] = [3, 3]
        """
        self.rows = ROWS  # 7
        self.cols = COLS  # 7
        self.symbols = symbols if symbols else list(range(2, 9))
        self.board = np.zeros((self.cols, self.rows), dtype=np.int32)  # board[col, row]
        self.fixed_mask = np.zeros((self.cols, self.rows), dtype=np.bool_)  # fixed_mask[col, row]
        self.score = 0
        self.fixed_cells = set()  # 存储 (col, row) 元组
        self.is_free_game = is_free_game  # Free Game模式标志
        self.enable_multiplier = enable_multiplier  # Wild乘倍开关
        
        # Wild符号倍数系统
        self.wild_eliminate_count = 0  # Wild参与消除的次数（用于倍数升级）
        
        # Mega Eliminate系统（新）
        self.mega_level = 0  # Mega等级（0, 1, 2），每次消除+1
        self.mega_eliminate_count = 0  # Mega消除计数（上限3），每完成2级（0->2）+1
        
        # 钻石形状统计
        self.eliminate_trigger_count = 0  # 触发判断次数
        self.eliminate_success_count = 0  # 成功放置次数
        self.eliminate_fail_count = 0     # 放置失败次数（无法放置任何block）
        self.score_before_eliminate = 0   # 触发钻石形状前的得分
        self.score_from_eliminate = 0     # 钻石形状带来的额外得分
        
        # 选择使用的Reel参数集
        if reel_set is None:
            self.reel_set = self.select_reel_by_weight()
        else:
            self.reel_set = reel_set
        
        # 选择使用的Drop参数集
        if drop_set is None:
            self.drop_set = self.select_drop_by_weight(eliminate_count=0)
        else:
            self.drop_set = drop_set
        
        # 加载linkpoint得分表
        if linkpoint is None:
            if GAME_DATA and 'linkpoint' in GAME_DATA:
                self.linkpoint = np.array(GAME_DATA['linkpoint'], dtype=np.int32)
            else:
                self.linkpoint = np.array([
                    [10000, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
                    [15000, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
                    [20000, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70],
                    [25000, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75],
                    [30000, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80],
                    [35000, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85],
                    [40000, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90],
                ], dtype=np.int32)
        else:
            self.linkpoint = np.array(linkpoint, dtype=np.int32)
        
        # 缓存变量（避免重复加载相同数据）
        self._cached_reel_set = None
        self._cached_drop_set = None
        
        self.load_reel_data()
        self.load_drop_data()
        self.load_eliminate_data()
        self.eliminate_count = 0
    
    def select_reel_by_weight(self):
        """按照ReelWeight权重选择使用哪一套参数(1-6) - 使用预计算数据"""
        if not PRECOMPUTED_DATA.available:
            return random.randint(1, 6)
        
        if self.is_free_game:
            weights = PRECOMPUTED_DATA.free_reel_selection_weights
        else:
            weights = PRECOMPUTED_DATA.base_reel_selection_weights
        
        if weights is not None:
            idx = weighted_choice_numba(weights)
            return idx + 1
        else:
            return random.randint(1, 6)
    
    def select_drop_by_weight(self, eliminate_count=0):
        """按照DropWeight权重选择使用哪一套掉落参数(1-6) - 使用预计算数据
        
        Args:
            eliminate_count: 当前消除次数，用于选择权重行
                - 第1次: 使用第0行
                - 第2次: 使用第1行
                - ...
                - 第10+次: 使用第9行
        """
        if not PRECOMPUTED_DATA.available:
            return random.randint(1, 6)
        
        if self.is_free_game:
            weights_2d = PRECOMPUTED_DATA.free_drop_selection_weights
        else:
            weights_2d = PRECOMPUTED_DATA.base_drop_selection_weights
        
        if weights_2d is not None:
            # 根据消除次数选择对应的权重行（10行格式）
            if eliminate_count <= 0:
                row_idx = 0  # 初始化时使用第0行（第1次）
            elif eliminate_count >= 10:
                row_idx = 9  # 第10+次消除使用第9行
            else:
                row_idx = eliminate_count - 1  # 第1次用第0行，第2次用第1行...
            
            # 获取对应行的权重（已经是int32格式）
            drop_weights = weights_2d[row_idx]
            idx = weighted_choice_numba(drop_weights)
            return idx + 1
        else:
            return random.randint(1, 6)
    
    def load_reel_data(self):
        """加载对应reel_set的数据（使用预计算数据，无需重复转换）"""
        # 如果reel_set没有改变，跳过重复加载
        if self._cached_reel_set == self.reel_set:
            return
        
        if not PRECOMPUTED_DATA.available:
            self.reel_symbols = None
            self.reel_weights = None
            self.my_weights = None
            return
        
        # 直接从预计算数据中获取（已经是正确的dtype）
        if self.is_free_game:
            self.reel_symbols = PRECOMPUTED_DATA.free_reel_symbols.get(self.reel_set)
            self.reel_weights = PRECOMPUTED_DATA.free_reel_weights.get(self.reel_set)
            self.my_weights = PRECOMPUTED_DATA.free_my_weights.get(self.reel_set)
        else:
            self.reel_symbols = PRECOMPUTED_DATA.base_reel_symbols.get(self.reel_set)
            self.reel_weights = PRECOMPUTED_DATA.base_reel_weights.get(self.reel_set)
            self.my_weights = PRECOMPUTED_DATA.base_my_weights.get(self.reel_set)
        
        # 更新缓存
        self._cached_reel_set = self.reel_set
    
    def load_drop_data(self):
        """加载对应drop_set的掉落数据（使用预计算数据，无需重复转换）"""
        # 如果drop_set没有改变，跳过重复加载
        if self._cached_drop_set == self.drop_set:
            return
        
        if not PRECOMPUTED_DATA.available:
            self.drop_symbol_table = None
            self.drop_rweights = None
            self.drop_pweights = None
            self.drop_method_weights = None
            self.drop_my_weights = None
            return
        
        # 直接从预计算数据中获取（已经是正确的dtype）
        if self.is_free_game:
            self.drop_symbol_table = PRECOMPUTED_DATA.free_drop_symbols.get(self.drop_set)
            self.drop_rweights = PRECOMPUTED_DATA.free_drop_rweights.get(self.drop_set)
            self.drop_pweights = PRECOMPUTED_DATA.free_drop_pweights.get(self.drop_set)
            self.drop_method_weights = PRECOMPUTED_DATA.free_drop_method_weights.get(self.drop_set)
            self.drop_my_weights = PRECOMPUTED_DATA.free_drop_my_weights.get(self.drop_set)
        else:
            self.drop_symbol_table = PRECOMPUTED_DATA.base_drop_symbols.get(self.drop_set)
            self.drop_rweights = PRECOMPUTED_DATA.base_drop_rweights.get(self.drop_set)
            self.drop_pweights = PRECOMPUTED_DATA.base_drop_pweights.get(self.drop_set)
            self.drop_method_weights = PRECOMPUTED_DATA.base_drop_method_weights.get(self.drop_set)
            self.drop_my_weights = PRECOMPUTED_DATA.base_drop_my_weights.get(self.drop_set)
        
        # 更新缓存
        self._cached_drop_set = self.drop_set
    
    def load_eliminate_data(self):
        """加载Eliminate特色数据（使用预计算数据）"""
        if not PRECOMPUTED_DATA.available:
            # 默认权重
            default_weights = np.array([1000.0] * 7, dtype=np.float32)
            self.eliminate_symbol = (default_weights * 10000).astype(np.int32)
            self.eliminate_trigger = None
            self.eliminate_time = None
            return
        
        # 直接从预计算数据中获取
        if self.is_free_game:
            self.eliminate_symbol = PRECOMPUTED_DATA.free_eliminate_symbol
        else:
            self.eliminate_symbol = PRECOMPUTED_DATA.base_eliminate_symbol
        
        # 如果没有对应数据，使用默认权重
        if self.eliminate_symbol is None:
            default_weights = np.array([1000.0] * 7, dtype=np.float32)
            self.eliminate_symbol = (default_weights * 10000).astype(np.int32)
            print(f"警告：未找到Eliminate数据，使用默认符号权重")
        
        # 保留旧的字段（向后兼容，但新系统不使用）
        self.eliminate_trigger = None
        self.eliminate_time = None
    
    def initialize_board(self):
        """初始化游戏版面（Java版本对标）
        
        访问方式：board[col, row]
        """
        if self.reel_symbols is None or self.reel_weights is None:
            # 简单随机初始化（按列遍历）
            for col in range(self.cols):
                for row in range(self.rows):
                    if is_valid_hex_cell(col, row):
                        self.board[col, row] = random.choice(self.symbols)
        else:
            # 使用numba加速初始化
            initialize_board_numba(self.board, self.reel_symbols, self.reel_weights)
            
            if self.my_weights is not None and len(self.my_weights) > 0:
                convert_my_numba(self.board, self.my_weights)
            
            # 确保每行最多1个C1
            fix_c1_numba(self.board)
        
        # 设置中央位置为固定Wild符号
        self.board[CENTER_COL, CENTER_ROW] = WILD_SYMBOL
        self.fixed_mask[CENTER_COL, CENTER_ROW] = True
        self.fixed_cells.add((CENTER_COL, CENTER_ROW))
        
        return self.board
    
    def find_connected_symbols(self, row, col, visited):
        """使用BFS查找从(row, col)开始的所有相连相同符号（numba加速）"""
        connected_array = bfs_find_connected(self.board, row, col, visited)
        return [(int(connected_array[i, 0]), int(connected_array[i, 1])) for i in range(len(connected_array))]
    
    def find_all_matches(self):
        """查找所有需要消除的符号组（6个或以上相连）- 使用numba加速"""
        num_matches, match_symbols, match_counts, all_positions, position_starts = find_all_matches_numba(self.board)
        
        if num_matches == 0:
            return []
        
        # 转换为原格式以兼容现有代码
        matches = []
        for i in range(num_matches):
            start_pos = position_starts[i]
            if i < num_matches - 1:
                end_pos = position_starts[i + 1]
            else:
                end_pos = len(all_positions)
            
            positions = [(int(all_positions[j, 0]), int(all_positions[j, 1])) 
                        for j in range(start_pos, end_pos)]
            
            matches.append((int(match_symbols[i]), int(match_counts[i]), positions))
        
        return matches
    
    def find_all_matches_fast(self):
        """快速查找所有匹配（返回numba格式，用于批处理）"""
        return find_all_matches_numba(self.board)
    
    def get_base_score(self, symbol, count):
        """从linkpoint获取基础分数"""
        # linkpoint最后一列代表15+个符号的分数
        symbol_idx = symbol - 2
        count_idx = min(count - 6, len(self.linkpoint[0]) - 1)
        
        if 0 <= symbol_idx < len(self.linkpoint) and 0 <= count_idx < len(self.linkpoint[0]):
            return int(self.linkpoint[symbol_idx, count_idx])
        return 0
    
    def remove_symbols_and_score(self, matches):
        """消除符号并计算得分（numba加速）"""
        total_removed = 0
        total_score = 0
        details = []
        
        for symbol, count, positions in matches:
            # 转换positions为numpy数组
            positions_array = np.array(positions, dtype=np.int32)
            
            # 使用numba计算分数
            score = calculate_match_score_numba(
                self.linkpoint, self.board,
                positions_array, len(positions)
            )
            
            # 清除符号
            clear_positions_numba(self.board, positions_array, len(positions))
            
            total_removed += len(positions)
            total_score += score
            
            details.append({
                'symbol': f'M{symbol-1}',
                'count': count,
                'score': score,
                'positions': positions
            })
        
        return total_removed, total_score, details
    
    def remove_symbols_and_score_fast(self, num_matches, match_symbols, match_counts, 
                                       all_positions, position_starts):
        """快速批处理版本：消除符号并计算得分（完全numba优化）"""
        if num_matches == 0:
            return 0, 0, [], 0
        
        total_score, final_scores, wild_group_count = process_all_matches_numba(
            self.board, self.fixed_mask, self.linkpoint,
            match_symbols, match_counts, all_positions, position_starts, num_matches,
            self.wild_eliminate_count, self.enable_multiplier
        )
        
        total_removed = np.sum(match_counts)
        
        # 构建详情（用于调试/记录）
        details = []
        for i in range(num_matches):
            start_pos = position_starts[i]
            if i < num_matches - 1:
                end_pos = position_starts[i + 1]
            else:
                end_pos = len(all_positions)
            
            positions = [(int(all_positions[j, 0]), int(all_positions[j, 1])) 
                        for j in range(start_pos, end_pos)]
            
            details.append({
                'symbol': f'M{int(match_symbols[i])-1}',
                'count': int(match_counts[i]),
                'score': int(final_scores[i]),
                'positions': positions
            })
        
        return int(total_removed), int(total_score), details, wild_group_count
    
    def drop_symbols(self):
        """让符号向下掉落填补空位（numba加速）"""
        drop_symbols_numba(self.board, self.fixed_mask)
    
    def fill_empty_spaces(self):
        """用新符号填充空位（Java版本对标）
        
        访问方式：board[col, row]
        """
        if self.drop_symbol_table is None or self.drop_method_weights is None:
            # 简单随机填充（按列遍历）
            for col in range(self.cols):
                for row in range(self.rows):
                    if is_valid_hex_cell(col, row):
                        if self.board[col, row] == 0 and not self.fixed_mask[col, row]:
                            self.board[col, row] = random.choice(self.symbols)
        else:
            # ⚠️ 补充符号前：记录已有的C1位置
            existing_c1_mask = np.zeros((self.cols, self.rows), dtype=np.bool_)
            for col in range(self.cols):
                for row in range(self.rows):
                    if is_valid_hex_cell(col, row) and self.board[col, row] == 1:
                        existing_c1_mask[col, row] = True
            
            # 每次填充都重新选择drop_set（1-6），根据当前消除次数
            self.drop_set = self.select_drop_by_weight(self.eliminate_count)
            self.load_drop_data()
            
            # 选择填充方法
            drop_method = weighted_choice_numba(self.drop_method_weights)
            
            if drop_method == 0:
                # 使用numba加速的方法0
                fill_empty_method0_numba(self.board, self.fixed_mask,
                                        self.drop_symbol_table, self.drop_rweights)
            else:
                # 使用numba加速的方法1
                position_idx = weighted_choice_numba(self.drop_pweights)
                fill_empty_method1_numba(self.board, self.fixed_mask,
                                        self.drop_symbol_table, position_idx)
            
            # 本次填充：按顺序抽选MY目标（MY1→MY2→MY3各不相同）
            if self.drop_my_weights is not None and len(self.drop_my_weights) > 0:
                my_targets = select_my_targets_numba(self.drop_my_weights)
                convert_my_numba_with_targets(self.board, my_targets)
            
            # ✅ 使用新函数：优先保留已存在的C1
            fix_c1_preserve_existing_numba(self.board, existing_c1_mask)
    
    def process_cascades(self):
        cascade_count = 0
        total_removed = 0
        total_score = 0
        all_details = []
        first_eliminate_triggered = False  # 标记是否已触发过2×2
        
        while True:
            # 使用快速版本查找匹配
            num_matches, match_symbols, match_counts, all_positions, position_starts = self.find_all_matches_fast()
            
            if num_matches == 0:
                # 只在第一次触发2×2前记录分数
                if not first_eliminate_triggered:
                    self.score_before_eliminate = total_score
                    first_eliminate_triggered = True
                
                if self.try_eliminate_feature():
                    continue
                else:
                    break
            
            # 使用快速版本处理匹配
            removed, score, details, wild_group_count = self.remove_symbols_and_score_fast(
                num_matches, match_symbols, match_counts, all_positions, position_starts
            )
            
            # 清除被消除位置的 fixed_cells 标记（匹配 Java 的 occupied 重置逻辑）
            # 这样被消除的位置可以再次放置 Mega 符号
            for i in range(num_matches):
                start_pos = position_starts[i]
                if i < num_matches - 1:
                    end_pos = position_starts[i + 1]
                else:
                    end_pos = len(all_positions)
                
                for j in range(start_pos, end_pos):
                    pos = (int(all_positions[j, 0]), int(all_positions[j, 1]))
                    # 跳过中央 Wild 位置 (col, row)
                    if pos == (CENTER_COL, CENTER_ROW):
                        continue
                    # 如果该位置在 fixed_cells 中，移除它
                    if pos in self.fixed_cells:
                        self.fixed_cells.discard(pos)
            
            # 只要有消除就升级Wild倍数（不管是否包含Wild）
            self.wild_eliminate_count += 1
            
            # Mega系统：只有包含Wild的消除才升级mega_level
            # 当mega_eliminate_count达到3时，维持在0不再提升，保证每次循环上限为3个mega符号
            if wild_group_count > 0 and self.mega_eliminate_count < 3:
                # 计算增加量（wild帮助1组=+1，2+组=+2）
                mega_increase = min(wild_group_count, 2)
                
                # 提升mega_level，但不超过上限2
                self.mega_level = min(self.mega_level + mega_increase, 2)
                
                # 如果达到2级，完成一个循环
                if self.mega_level == 2:
                    self.mega_eliminate_count += 1
                    self.mega_level = 0  # 重置为0
                    # 注意：如果此时mega_eliminate_count达到3，下次消除将不再提升mega_level
            
            total_removed += removed
            total_score += score
            cascade_count += 1
            self.eliminate_count += 1
            
            all_details.append({
                'cascade': cascade_count,
                'matches': details
            })
            
            self.drop_symbols()
            self.fill_empty_spaces()
        
        return cascade_count, total_removed, total_score, all_details
    
    def play_round(self, keep_multipliers=False):
        """执行一轮游戏
        
        Args:
            keep_multipliers: 是否保留倍数（Free Game模式下为True）
        """
        self.eliminate_count = 0
        self.fixed_cells.clear()
        self.fixed_mask[:] = False
        
        # Base Game模式下重置Wild倍数和Mega系统，Free Game模式下保留累积
        if not keep_multipliers:
            # Base Game: 重置所有累积状态
            self.wild_eliminate_count = 0
            self.mega_level = 0
            self.mega_eliminate_count = 0
        # Free Game: 保留 wild_eliminate_count, mega_level, mega_eliminate_count 跨spin累积
        
        # 恢复中央Wild符号的固定状态
        self.board[CENTER_COL, CENTER_ROW] = WILD_SYMBOL
        self.fixed_mask[CENTER_COL, CENTER_ROW] = True
        self.fixed_cells.add((CENTER_COL, CENTER_ROW))
        
        cascade_count, total_removed, round_score, details = self.process_cascades()
        self.score += round_score
        
        return cascade_count, total_removed, round_score, details
    
    def try_eliminate_feature(self):
        """尝试触发Mega Eliminate特色（Java版本对标）
        
        新规则：
        - 只有当无法消除时才检查
        - 根据 mega_eliminate_count 放置对应数量的钻石形状
        - 所有钻石形状使用同一符号（只抽选一次）
        - 抽选符号使用 Base Eliminate Symbol
        - 使用智能位置筛选而非随机尝试
        
        钻石形状定义（Java版本对标）：
        对于中心点 (centerCol, centerRow)：
        - 如果 centerCol < CENTER_COL (3)：
          block = [(0,0), (0,1), (1,0), (1,1)]
        - 如果 centerCol >= CENTER_COL (3)：
          block = [(0,0), (0,1), (1,-1), (1,0)]
        
        访问方式：board[col, row], fixed_mask[col, row]
        Wild位置：[CENTER_COL, CENTER_ROW] = [3, 3]
        """
        # 检查是否有 mega_eliminate_count
        if self.mega_eliminate_count <= 0:
            return False
        
        # 检查 eliminate_symbol 是否有效
        if self.eliminate_symbol is None or len(self.eliminate_symbol) == 0 or np.sum(self.eliminate_symbol) == 0:
            print("警告：eliminate_symbol无效，跳过mega符号放置")
            self.mega_eliminate_count = 0
            self.mega_level = 0
            return False
        
        # 记录触发判断
        self.eliminate_trigger_count += 1
        
        # 使用 mega_eliminate_count 作为放置数量
        num_blocks = self.mega_eliminate_count
        
        # 只抽选一次符号，所有mega symbol使用同一符号
        try:
            mega_symbol_id = weighted_choice_numba(self.eliminate_symbol)
        except Exception as e:
            print(f"错误：无法选择mega符号")
            self.mega_eliminate_count = 0
            self.mega_level = 0
            return False
        
        placed_blocks = 0
        occupied_cells = set(self.fixed_cells)
        
        for _ in range(num_blocks):
            # 动态遍历所有可能的中心点位置（Java版本对标）
            # Java遍历范围：col [0, COLS-1), row [0, ROWS-1)
            # 也就是 col [0, 6), row [0, 6)，因为钻石需要col+1和row+1
            valid_centers = []
            
            for center_col in range(self.cols - 1):  # 0-5，因为需要col+1
                for center_row in range(self.rows - 1):  # 0-5，因为需要row+1
                    # 根据centerCol确定钻石形状的4格（Java版本逻辑）
                    if center_col < CENTER_COL:
                        # 左侧：[(0,0), (0,1), (1,0), (1,1)]
                        block_cells = [
                            (center_col, center_row),
                            (center_col, center_row + 1),
                            (center_col + 1, center_row),
                            (center_col + 1, center_row + 1)
                        ]
                    else:
                        # 右侧（包括中央列）：[(0,0), (0,1), (1,-1), (1,0)]
                        block_cells = [
                            (center_col, center_row),
                            (center_col, center_row + 1),
                            (center_col + 1, center_row - 1),
                            (center_col + 1, center_row)
                        ]
                    
                    # 检查所有4格是否都有效且在范围内
                    if not all(0 <= c < self.cols and 0 <= r < self.rows and is_valid_hex_cell(c, r) 
                              for c, r in block_cells):
                        continue
                    
                    # 限制1: 不能覆盖中央Wild位置[CENTER_COL, CENTER_ROW]
                    if any(c == CENTER_COL and r == CENTER_ROW for c, r in block_cells):
                        continue
                    
                    # 限制2: 不能放在空标记或Wild位置（Java版本检查）
                    # Java: if (screenSymbol[bc][br] == 9 || screenSymbol[bc][br] == 0) return false;
                    if any(self.board[c, r] == EMPTY_MARKER or self.board[c, r] == WILD_SYMBOL 
                          for c, r in block_cells):
                        continue
                    
                    # 限制3: 不能互相覆盖（occupied_cells包含所有已固定的格子）
                    if any(cell in occupied_cells for cell in block_cells):
                        continue
                    
                    # 这个中心点可用
                    valid_centers.append((center_col, center_row, block_cells))
            
            # 没有可放置位置 → 对标Java dropMegaSymbols：直接停止（放较少个），不抛错、不重试整轮
            if len(valid_centers) == 0:
                break
            
            # 从可放置位置中随机选择一个
            selected_idx = random.randint(0, len(valid_centers) - 1)
            center_col, center_row, block_cells = valid_centers[selected_idx]
            
            # 放置4格钻石形状（如果是C1则跳过，保持C1不变）
            for c, r in block_cells:
                if self.board[c, r] == 1:  # 如果是C1，跳过不修改
                    continue
                
                self.board[c, r] = mega_symbol_id
                occupied_cells.add((c, r))
                self.fixed_cells.add((c, r))
                self.fixed_mask[c, r] = True
            
            placed_blocks += 1
        
        # 对标Java：实际放下几个就扣几个，剩余的保留到下一个 dry point（不重试整轮、不强制清零）
        self.mega_eliminate_count -= placed_blocks
        if placed_blocks > 0:
            self.eliminate_success_count += 1
            return True
        else:
            # 一个都放不下：结束本轮消除循环（对标Java：playerWin 仍为 0 则结束）
            self.eliminate_fail_count += 1
            return False

# ==================== 主函数 ====================

def basegame(rounds, enable_multiplier=True):
    """
    运行指定次数的基础游戏（numba优化版）
    
    Args:
        rounds: 游戏轮数
        enable_multiplier: 是否启用Wild乘倍功能（默认True）
    
    Returns:
        (分数列表, C1数量列表, 初始C1数量列表, Wild倍数列表)
    """
    scores = np.zeros(rounds, dtype=np.int64)
    c1_counts = np.zeros(rounds, dtype=np.int32)
    initial_c1_counts = np.zeros(rounds, dtype=np.int32)  # 初始版面C1数量
    wild_multipliers = np.zeros(rounds, dtype=np.int32)   # 每轮结束时的Wild倍数计数
    
    # 预先创建一个游戏实例来触发numba编译
    if rounds > 0:
        print("预热numba编译...")
        warmup_game = Game7x7(enable_multiplier=enable_multiplier)
        warmup_game.initialize_board()
        warmup_game.play_round()
        print("编译完成，开始模拟...\n")
    
    # 创建一个可重用的游戏实例，避免重复初始化
    game = Game7x7(enable_multiplier=enable_multiplier)
    
    # 初始化统计变量
    total_trigger_count = 0
    total_success_count = 0
    total_fail_count = 0
    games_with_eliminate = []  # 触发2×2的游戏得分
    games_without_eliminate = []  # 未触发2×2的游戏得分
    
    # 预分配用于C1计数的临时数组（避免重复创建）
    board_flat = game.board.ravel()
    
    for i in range(rounds):
        # 使用循环重试机制，防止mega符号无法放置
        retry_count = 0
        max_retries = 100  # 最多重试100次
        
        while retry_count < max_retries:
            try:
                # 批量重置游戏状态（更高效）
                game.board.fill(0)
                game.fixed_mask.fill(False)
                game.fixed_cells.clear()
                game.score = 0
                game.eliminate_count = 0
                game.eliminate_trigger_count = 0
                game.eliminate_success_count = 0
                game.eliminate_fail_count = 0
                game.score_before_eliminate = 0
                game.score_from_eliminate = 0
                
                # 每轮重新选择参数集（保持随机性）
                game.reel_set = game.select_reel_by_weight()
                game.drop_set = game.select_drop_by_weight(eliminate_count=0)
                game.load_reel_data()
                game.load_drop_data()
                
                # 初始化并游戏
                game.initialize_board()
                initial_c1_counts[i] = np.sum(game.board == 1)  # 记录初始版面C1数量
                cascade, removed, score, details = game.play_round()
                
                # 成功完成，跳出重试循环
                break
                
            except MegaPlacementImpossibleError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"警告：第{i+1}轮在{max_retries}次重试后仍无法放置mega符号，跳过此轮")
                    score = 0
                    cascade = 0
                    break
                # 否则继续重试
        
        scores[i] = score
        c1_counts[i] = np.count_nonzero(game.board == 1)  # 记录消除结束后C1数量（count_nonzero更快）
        wild_multipliers[i] = game.wild_eliminate_count  # 记录Wild倍数计数
        
        # 累积统计
        total_trigger_count += game.eliminate_trigger_count
        total_success_count += game.eliminate_success_count
        total_fail_count += game.eliminate_fail_count
        
        # 分类统计
        if game.eliminate_success_count > 0:
            games_with_eliminate.append({
                'total_score': score,
                'score_before': game.score_before_eliminate,
                'score_after': score - game.score_before_eliminate
            })
        else:
            games_without_eliminate.append(score)
        
        # 显示进度
        if rounds >= 1000 and (i + 1) % 1000 == 0:
            print(f"完成 {i + 1}/{rounds} 轮...")
    
    # 输出2×2统计
    print("\n=== 2×2 Eliminate Feature 统计 ===")
    print(f"触发判断次数: {total_trigger_count}")
    print(f"成功放置次数: {total_success_count}")
    print(f"放置失败次数: {total_fail_count}")
    if total_trigger_count > 0:
        fail_rate = (total_fail_count / total_trigger_count) * 100
        print(f"失败率: {fail_rate:.2f}%")
        print(f"平均每轮触发: {total_trigger_count / rounds:.2f} 次")
    
    print("\n--- 分类统计 ---")
    print(f"触发2×2的游戏数: {len(games_with_eliminate)}")
    print(f"未触发2×2的游戏数: {len(games_without_eliminate)}")
    
    if games_with_eliminate:
        avg_total_with = np.mean([g['total_score'] for g in games_with_eliminate])
        avg_before = np.mean([g['score_before'] for g in games_with_eliminate])
        avg_after = np.mean([g['score_after'] for g in games_with_eliminate])
        print(f"\n触发2×2的游戏:")
        print(f"  平均总得分: {avg_total_with:.2f}")
        print(f"  平均触发前得分: {avg_before:.2f}")
        print(f"  平均2×2后增加: {avg_after:.2f}")
    
    if games_without_eliminate:
        avg_without = np.mean(games_without_eliminate)
        print(f"\n未触发2×2的游戏:")
        print(f"  平均得分: {avg_without:.2f}")
    
    if games_with_eliminate and games_without_eliminate:
        avg_total_with = np.mean([g['total_score'] for g in games_with_eliminate])
        avg_without = np.mean(games_without_eliminate)
        diff = avg_without - avg_total_with
        print(f"\n差异: 未触发比触发高 {diff:.2f} 分")
    
    # Wild倍数统计
    if enable_multiplier:
        print("\n=== Wild倍数统计 ===")
    else:
        print("\n=== Wild倍数统计（乘倍已关闭）===")
    non_zero_wilds = wild_multipliers[wild_multipliers > 0]
    print(f"触发Wild倍数的轮数: {len(non_zero_wilds)} / {rounds} ({len(non_zero_wilds)/rounds*100:.2f}%)")
    if len(non_zero_wilds) > 0:
        print(f"Wild倍数计数统计:")
        print(f"  平均: {np.mean(non_zero_wilds):.2f}")
        print(f"  最小: {np.min(non_zero_wilds)}")
        print(f"  最大: {np.max(non_zero_wilds)}")
        print(f"  中位数: {np.median(non_zero_wilds):.2f}")
        
        # 倍数分布
        print(f"\nWild倍数分布:")
        for i in range(1, max(6, int(np.max(non_zero_wilds))+1)):
            count = np.sum(wild_multipliers == i)
            if count > 0:
                actual_mult = 1 if i <= 1 else (2 if i == 2 else min(2 + (i-2)*2, 1000))
                print(f"  计数{i} (倍数{actual_mult}x): {count} 次 ({count/rounds*100:.2f}%)")
    
    print("=" * 40)
    
    return scores, c1_counts, initial_c1_counts, wild_multipliers

def freegame(initial_spins, rounds):
    """
    运行指定次数的Free Game模拟（numba优化版）
    
    Args:
        initial_spins: 每场Free Game的初始spin次数
        rounds: 模拟的Free Game场次
    
    Returns:
        (total_scores, total_spins, wild_multipliers): 
            - total_scores: 每场Free Game的总得分数组
            - total_spins: 每场Free Game的总spin数数组
            - wild_multipliers: 每场Free Game结束时的Wild倍数计数
    
    Free Game规则:
        - 乘倍在整场Free Game期间累积保留
        - 每次spin结束检查C1数量，获得额外spin:
          * 3个C1: +10次spin
          * 4个C1: +12次spin
          * 5个C1: +15次spin
          * 6个C1: +20次spin
          * 7个C1: +30次spin
    """
    total_scores = np.zeros(rounds, dtype=np.int64)
    total_spins = np.zeros(rounds, dtype=np.int32)
    wild_multipliers = np.zeros(rounds, dtype=np.int32)  # 每场结束时的Wild倍数计数
    
    # 预热numba编译
    if rounds > 0:
        print("预热numba编译（Free Game模式）...")
        warmup_game = Game7x7(is_free_game=True)
        warmup_game.initialize_board()
        warmup_game.play_round(keep_multipliers=True)
        print("编译完成，开始Free Game模拟...\n")
    
    # Retrigger规则: C1数量 -> 额外spin数（使用NumPy数组替代字典，速度更快）
    # [3,4,5,6,7] -> [8,10,15,20,30]
    retrigger_spins = np.zeros(8, dtype=np.int32)
    retrigger_spins[3] = 8
    retrigger_spins[4] = 10
    retrigger_spins[5] = 15
    retrigger_spins[6] = 20
    retrigger_spins[7] = 30
    
    # 创建Free Game实例（复用，不在循环内重复创建）
    game = Game7x7(is_free_game=True)
    
    for round_idx in range(rounds):
        # 重置倍数累积（每场Free Game开始时）
        game.wild_eliminate_count = 0
        
        remaining_spins = initial_spins
        total_score = 0
        spin_count = 0
        
        while remaining_spins > 0:
            # 使用重试机制防止mega符号无法放置
            retry_count = 0
            max_retries = 100
            
            while retry_count < max_retries:
                try:
                    # 批量重置游戏状态（更高效）
                    game.board.fill(0)
                    game.fixed_mask.fill(False)
                    game.fixed_cells.clear()
                    game.eliminate_count = 0
                    
                    # 每次spin重新选择参数集
                    game.reel_set = game.select_reel_by_weight()
                    game.drop_set = game.select_drop_by_weight(eliminate_count=0)
                    game.load_reel_data()
                    game.load_drop_data()
                    
                    # 初始化版面并游戏
                    game.initialize_board()
                    cascade, removed, score, details = game.play_round(keep_multipliers=True)
                    
                    # 成功完成，跳出重试循环
                    break
                    
                except MegaPlacementImpossibleError as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"警告：Free Game第{round_idx+1}场第{spin_count+1}次spin在{max_retries}次重试后仍无法放置mega符号，跳过此spin")
                        score = 0
                        cascade = 0
                        break
                    # 否则继续重试
            
            total_score += score
            spin_count += 1
            remaining_spins -= 1
            
            # 检查C1数量，判断是否retrigger（使用NumPy数组查找，比字典更快）
            c1_count = np.count_nonzero(game.board == 1)
            if c1_count < len(retrigger_spins):
                extra_spins = retrigger_spins[c1_count]
                if extra_spins > 0:
                    remaining_spins += extra_spins
        
        total_scores[round_idx] = total_score
        total_spins[round_idx] = spin_count
        wild_multipliers[round_idx] = game.wild_eliminate_count  # 记录Free Game结束时的Wild倍数计数
        
        # 显示进度
        if rounds >= 100 and (round_idx + 1) % 100 == 0:
            print(f"完成 {round_idx + 1}/{rounds} 场Free Game...")
    
    # Wild倍数统计
    print("\n=== Free Game Wild倍数统计 ===")
    print(f"总场次: {rounds}")
    if len(wild_multipliers) > 0:
        print(f"Wild倍数计数统计:")
        print(f"  平均: {np.mean(wild_multipliers):.2f}")
        print(f"  最小: {np.min(wild_multipliers)}")
        print(f"  最大: {np.max(wild_multipliers)}")
        print(f"  中位数: {np.median(wild_multipliers):.2f}")
        
        # 倍数分布
        print(f"\nWild倍数分布:")
        max_count = int(np.max(wild_multipliers))
        for i in range(0, max_count + 1):
            count = np.sum(wild_multipliers == i)
            if count > 0:
                if i == 0:
                    print(f"  计数0 (倍数1x): {count} 次 ({count/rounds*100:.2f}%)")
                else:
                    actual_mult = 1 if i <= 1 else (2 if i == 2 else min(2 + (i-2)*2, 1000))
                    print(f"  计数{i} (倍数{actual_mult}x): {count} 次 ({count/rounds*100:.2f}%)")
    
    print("=" * 40)
    
    return total_scores, total_spins, wild_multipliers


# ==================== 多进程并行（默认 8 worker）====================

@jit(nopython=True, cache=True)
def _numba_seed(s):
    """为 numba 内部的 np.random 设定种子（与 numpy Python 层的种子独立）"""
    np.random.seed(s)


def _seed_all(seed):
    """同时为 Python random / numpy / numba np.random 播种，确保每个 worker 独立 RNG 流"""
    seed = int(seed) & 0xFFFFFFFF
    random.seed(seed)
    np.random.seed(seed)
    _numba_seed(seed)


def _basegame_chunk(args):
    """worker：跑一段 base game，回传 (scores, c1, init_c1, wild_mult)。stdout 静音。"""
    rounds, enable_multiplier, seed = args
    _seed_all(seed)
    _old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        return basegame(rounds, enable_multiplier=enable_multiplier)
    finally:
        sys.stdout = _old


def _freegame_chunk(args):
    """worker：跑一段 free game，回传 (total_scores, total_spins, wild_mult)。stdout 静音。"""
    initial_spins, rounds, seed = args
    _seed_all(seed)
    _old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        return freegame(initial_spins, rounds)
    finally:
        sys.stdout = _old


def _split_rounds(rounds, n_workers):
    """把 rounds 平均切给 n_workers（余数前几个 worker 各 +1）"""
    base = rounds // n_workers
    rem = rounds % n_workers
    return [base + (1 if i < rem else 0) for i in range(n_workers)]


def basegame_parallel(rounds, n_workers=8, enable_multiplier=True, seed_base=None, verbose=True):
    """多进程并行版 basegame。

    把 rounds 平均切给 n_workers 个进程同时跑，各自独立 RNG，最后合并。
    回传与 basegame 相同：(scores, c1_counts, initial_c1_counts, wild_multipliers)。

    注意：若写成 .py 脚本执行，调用必须放在 `if __name__ == '__main__':` 之下
          （Windows 用 spawn，否则子进程会重复执行而无限衍生）。互动模式可直接调用。

    Args:
        rounds: 总轮数
        n_workers: 进程数（默认 8）
        enable_multiplier: 是否启用 Wild 乘倍
        seed_base: RNG 基础种子（None=用系统熵随机；指定整数可复现）
        verbose: 是否打印汇总
    """
    n_workers = max(1, int(n_workers))
    if seed_base is None:
        seed_base = int.from_bytes(os.urandom(4), 'little')

    chunks = _split_rounds(rounds, n_workers)
    args = [(chunks[i], enable_multiplier, (seed_base + i * 7919 + 1) & 0xFFFFFFFF)
            for i in range(n_workers) if chunks[i] > 0]

    if verbose:
        print(f"并行 base game：{len(args)} workers，总 {rounds} 轮，seed_base={seed_base}")

    # 主进程先预热一次，填充 numba 编译缓存，避免子进程同时首编译竞争
    _warm = Game7x7(enable_multiplier=enable_multiplier)
    _warm.initialize_board()
    _warm.play_round()

    with mp.Pool(processes=len(args)) as pool:
        results = pool.map(_basegame_chunk, args)

    scores = np.concatenate([r[0] for r in results])
    c1 = np.concatenate([r[1] for r in results])
    init_c1 = np.concatenate([r[2] for r in results])
    wild_mult = np.concatenate([r[3] for r in results])

    if verbose:
        print(f"完成：共 {len(scores)} 轮，平均分 {np.mean(scores):.4f}")

    return scores, c1, init_c1, wild_mult


def freegame_parallel(initial_spins, rounds, n_workers=8, seed_base=None, verbose=True):
    """多进程并行版 freegame。回传 (total_scores, total_spins, wild_multipliers)。

    脚本执行时同样需放在 `if __name__ == '__main__':` 之下。
    """
    n_workers = max(1, int(n_workers))
    if seed_base is None:
        seed_base = int.from_bytes(os.urandom(4), 'little')

    chunks = _split_rounds(rounds, n_workers)
    args = [(initial_spins, chunks[i], (seed_base + i * 7919 + 1) & 0xFFFFFFFF)
            for i in range(n_workers) if chunks[i] > 0]

    if verbose:
        print(f"并行 free game：{len(args)} workers，总 {rounds} 场，seed_base={seed_base}")

    _warm = Game7x7(is_free_game=True)
    _warm.initialize_board()
    _warm.play_round(keep_multipliers=True)

    with mp.Pool(processes=len(args)) as pool:
        results = pool.map(_freegame_chunk, args)

    total_scores = np.concatenate([r[0] for r in results])
    total_spins = np.concatenate([r[1] for r in results])
    wild_mult = np.concatenate([r[2] for r in results])

    if verbose:
        print(f"完成：共 {len(total_scores)} 场，平均分 {np.mean(total_scores):.4f}")

    return total_scores, total_spins, wild_mult


# ==================== 执行入口 ====================
if __name__ == '__main__':
    import argparse
    
    """
    使用方式：
    1. 使用默认参数：
       python simulation_numba.py
    
    2. 自定义参数：
       python simulation_numba.py --rounds 1000000 --workers 4
       python simulation_numba.py -r 500000 -w 8 --no-multiplier
       python simulation_numba.py -r 100000 --seed 12345
    
    3. 查看帮助：
       python simulation_numba.py --help
    """
    
    # === 命令行参数解析 ===
    parser = argparse.ArgumentParser(
        description='瘋狂果醬罐 Base Game 模拟器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python simulation_numba.py                              # 使用默认参数 (10万轮, 8进程)
  python simulation_numba.py -r 1000000                   # 模拟100万轮
  python simulation_numba.py -r 500000 -w 4               # 50万轮, 4进程
  python simulation_numba.py -r 100000 --no-multiplier    # 关闭Wild乘倍
  python simulation_numba.py -r 100000 --seed 12345       # 指定种子以复现结果
        """
    )
    
    parser.add_argument('-r', '--rounds', 
                        type=int, 
                        default=100000,
                        help='模拟轮数 (默认: 100000)')
    
    parser.add_argument('-w', '--workers', 
                        type=int, 
                        default=8,
                        help='并行进程数 (默认: 8)')
    
    parser.add_argument('--no-multiplier', 
                        action='store_false',
                        dest='enable_multiplier',
                        help='关闭Wild乘倍功能 (默认: 开启)')
    
    parser.add_argument('--seed', 
                        type=int, 
                        default=None,
                        help='随机种子，用于复现结果 (默认: None, 随机)')
    
    parser.add_argument('-q', '--quiet', 
                        action='store_true',
                        help='静音模式，减少输出信息')
    
    args = parser.parse_args()
    
    # === 执行模拟 ===
    if not args.quiet:
        print(f"开始 Base Game 模拟...")
        print(f"配置：轮数={args.rounds:,}, 进程数={args.workers}, Wild乘倍={'开启' if args.enable_multiplier else '关闭'}")
        if args.seed is not None:
            print(f"随机种子：{args.seed}")
        print("=" * 60)
    
    scores, c1_counts, initial_c1_counts, wild_multipliers = basegame_parallel(
        rounds=args.rounds,
        n_workers=args.workers,
        enable_multiplier=args.enable_multiplier,
        seed_base=args.seed,
        verbose=not args.quiet
    )
    
    # === 结果统计 ===
    print("\n" + "=" * 60)
    print("模拟结果统计：")
    print(f"总轮数：{len(scores):,}")
    print(f"平均分：{np.mean(scores):.2f}")
    print(f"中位数：{np.median(scores):.2f}")
    print(f"最高分：{np.max(scores):,.0f}")
    print(f"最低分：{np.min(scores):,.0f}")
    print(f"标准差：{np.std(scores):.2f}")
    
    if not args.quiet:
        print(f"\n零分轮数：{np.sum(scores == 0):,} ({np.sum(scores == 0) / len(scores) * 100:.2f}%)")
        print(f"有分轮数：{np.sum(scores > 0):,} ({np.sum(scores > 0) / len(scores) * 100:.2f}%)")
    
    # Wild倍数统计
    non_zero_wilds = wild_multipliers[wild_multipliers > 0]
    if len(non_zero_wilds) > 0:
        print(f"\nWild倍数统计：")
        print(f"触发Wild的轮数：{len(non_zero_wilds):,} ({len(non_zero_wilds) / len(scores) * 100:.2f}%)")
        print(f"平均Wild倍数：{np.mean(non_zero_wilds):.2f}")
        print(f"最高Wild倍数：{np.max(non_zero_wilds)}")
        
        # 倍数分布（详细模式）
        if not args.quiet:
            print(f"\nWild倍数分布（前10档）：")
            for i in range(1, min(11, np.max(wild_multipliers) + 1)):
                count = np.sum(wild_multipliers == i)
                if count > 0:
                    print(f"  {i}倍: {count:,} 次")
    
    # C1统计
    if not args.quiet:
        print(f"\n初始C1统计：")
        print(f"平均初始C1数量：{np.mean(initial_c1_counts):.2f}")
        print(f"平均结束C1数量：{np.mean(c1_counts):.2f}")
    
    print("\n" + "=" * 60)
    print("模拟完成！")


# %%

# %%
