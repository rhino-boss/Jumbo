#%%
import numpy as np
import random
import json
from numba import jit
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import os


def load_game_data():
    
    try:
        
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(script_dir, 'data.js')
        
        with open(data_path, 'r', encoding='utf-8') as f:
            content = f.read()
            json_str = content.replace('const data = ', '').rstrip(';')
            data = json.loads(json_str)
            return data
    except Exception as e:
        print(f"Failed to load data.js: {e}")
        return None

GAME_DATA = load_game_data()



@jit(nopython=True, cache=True)
def weighted_choice_numba(weights):
    
    total = np.sum(weights)
    r = np.random.randint(0, total)
    cumulative = 0
    for i in range(len(weights)):
        cumulative += weights[i]
        if r < cumulative:
            return i
    return len(weights) - 1

@jit(nopython=True, cache=True)
def precompute_cumsum(weights):
    
    n = len(weights)
    cumsum = np.zeros(n, dtype=np.int32)
    cumsum[0] = weights[0]
    for i in range(1, n):
        cumsum[i] = cumsum[i-1] + weights[i]
    return cumsum

@jit(nopython=True, cache=True)
def weighted_choice_cumsum(cumsum_weights):
    
    if len(cumsum_weights) == 0:
        return 0
    if len(cumsum_weights) == 1:
        return 0
    
    total = cumsum_weights[-1]
    r = np.random.randint(0, total)
    
    
    left, right = 0, len(cumsum_weights) - 1
    while left < right:
        mid = (left + right) // 2
        if r < cumsum_weights[mid]:
            right = mid
        else:
            left = mid + 1
    
    return left

@jit(nopython=True, cache=True)
def bfs_find_connected(board, start_row, start_col, visited):
    
    rows, cols = board.shape
    
    if visited[start_row, start_col] or board[start_row, start_col] <= 1:
        return np.zeros((0, 2), dtype=np.int32)  
    
    symbol = board[start_row, start_col]
    
    
    max_size = rows * cols
    queue = np.zeros((max_size, 2), dtype=np.int32)
    queue[0, 0] = start_row
    queue[0, 1] = start_col
    q_front = 0
    q_back = 1
    
    result = np.zeros((max_size, 2), dtype=np.int32)
    result_size = 0
    
    visited[start_row, start_col] = True
    
    
    directions = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]], dtype=np.int32)
    
    while q_front < q_back:
        curr_r = queue[q_front, 0]
        curr_c = queue[q_front, 1]
        q_front += 1
        
        result[result_size, 0] = curr_r
        result[result_size, 1] = curr_c
        result_size += 1
        
        for d in range(4):
            next_r = curr_r + directions[d, 0]
            next_c = curr_c + directions[d, 1]
            
            if 0 <= next_r < rows and 0 <= next_c < cols:
                if not visited[next_r, next_c] and board[next_r, next_c] == symbol:
                    visited[next_r, next_c] = True
                    queue[q_back, 0] = next_r
                    queue[q_back, 1] = next_c
                    q_back += 1
    
    return result[:result_size]

@jit(nopython=True, cache=True)
def convert_my_numba(board, my_weights):
    
    rows, cols = board.shape
    
    
    my_targets = np.zeros(3, dtype=np.int32)  
    for my_idx in range(min(3, len(my_weights))):
        my_targets[my_idx] = weighted_choice_numba(my_weights[my_idx])
    
    
    for i in range(rows):
        for j in range(cols):
            symbol = board[i, j]
            if 9 <= symbol <= 11:
                my_idx = symbol - 9
                if my_idx < len(my_weights):
                    board[i, j] = my_targets[my_idx]

@jit(nopython=True, cache=True)
def convert_my_numba_with_targets(board, my_targets):
    
    rows, cols = board.shape
    for i in range(rows):
        for j in range(cols):
            symbol = board[i, j]
            if 9 <= symbol <= 11:
                my_idx = symbol - 9
                if my_idx < len(my_targets):
                    board[i, j] = my_targets[my_idx]

@jit(nopython=True, cache=True)
def fix_c1_numba(board):
    
    rows, cols = board.shape
    for row in range(rows):
        c1_count = 0
        for col in range(cols):
            if board[row, col] == 1:
                if c1_count > 0:
                    board[row, col] = 9
                c1_count += 1

@jit(nopython=True, cache=True)
def drop_symbols_numba(board, multipliers, fixed_mask):
    
    rows, cols = board.shape
    
    
    for row in range(rows):
        non_empty_symbols = np.zeros(cols, dtype=np.int32)
        count = 0
        
        
        for col in range(cols):
            if not fixed_mask[row, col] and board[row, col] != 0:
                non_empty_symbols[count] = board[row, col]
                count += 1
        
        
        idx = 0
        for col in range(cols - 1, -1, -1):
            if not fixed_mask[row, col]:
                if idx < count:
                    board[row, col] = non_empty_symbols[count - 1 - idx]
                    
                    idx += 1
                else:
                    board[row, col] = 0
                    

@jit(nopython=True, cache=True)
def initialize_board_numba(board, reel_symbols, reel_weights):
    
    rows, cols = board.shape
    
    for row in range(rows):
        reel_row = reel_symbols[row]
        weight_row = reel_weights[row]
        
        start_idx = weighted_choice_numba(weight_row)
        reel_len = len(reel_row)
        
        for col in range(cols):
            symbol_value = reel_row[(start_idx + col) % reel_len]
            
            if symbol_value == 0:
                symbol_id = 1
            else:
                symbol_id = symbol_value
            board[row, col] = symbol_id

@jit(nopython=True, cache=True)
def fill_empty_method0_numba(board, multipliers, fixed_mask, drop_table, drop_rweights):
    
    rows, cols = board.shape
    
    
    for row in range(rows):
        drop_row = drop_table[row]
        drop_weight_row = drop_rweights[row]
        drop_len = len(drop_row)
        
        
        start_idx = weighted_choice_numba(drop_weight_row)
        offset = 0  
        
        
        for col in range(cols):
            if board[row, col] == 0 and not fixed_mask[row, col]:
                
                symbol_value = drop_row[(start_idx + offset) % drop_len]
                offset += 1  
                
                
                if symbol_value == 0:
                    symbol_id = 1
                else:
                    symbol_id = symbol_value
                
                board[row, col] = symbol_id
                

@jit(nopython=True, cache=True)
def fill_empty_method1_numba(board, multipliers, fixed_mask, drop_table, position_idx):
    
    rows, cols = board.shape
    
    for row in range(rows):
        drop_row = drop_table[row]
        drop_len = len(drop_row)
        offset = 0  
        
        for col in range(cols):
            if board[row, col] == 0 and not fixed_mask[row, col]:
                
                symbol_value = drop_row[(position_idx + offset) % drop_len]
                offset += 1  
                
                
                if symbol_value == 0:
                    symbol_id = 1
                else:
                    symbol_id = symbol_value
                
                board[row, col] = symbol_id
                

@jit(nopython=True, cache=True)
def calculate_scores_batch(linkpoint, match_symbols, match_counts, multipliers_list):
    
    num_matches = len(match_symbols)
    total_score = 0
    
    for i in range(num_matches):
        symbol = match_symbols[i]
        count = match_counts[i]
        mults = multipliers_list[i]
        
        
        symbol_idx = symbol - 2
        count_idx = min(count - 5, 10)
        if 0 <= symbol_idx < linkpoint.shape[0] and 0 <= count_idx < linkpoint.shape[1]:
            base_score = linkpoint[symbol_idx, count_idx]
        else:
            base_score = 0
        
        
        all_one = True
        mult_sum = 0
        for m in mults:
            if m > 1:
                mult_sum += m
                all_one = False
        
        multiplier = 1 if all_one else mult_sum
        total_score += base_score * multiplier
    
    return total_score

@jit(nopython=True, cache=True)
def upgrade_multipliers_with_times_numba(multipliers, eliminate_times, positions_flat, num_positions):
    
    for i in range(num_positions):
        row = positions_flat[i, 0]
        col = positions_flat[i, 1]
        eliminate_times[row, col] += 1  
        times = eliminate_times[row, col]
        
        if times == 1:
            multipliers[row, col] = 1  
        elif times >= 2:
            
            current = multipliers[row, col]
            if current < 1024:
                multipliers[row, col] = min(current * 2, 1024)

@jit(nopython=True, cache=True)
def upgrade_multipliers_numba(multipliers, positions_flat, num_positions):
    
    for i in range(num_positions):
        row = positions_flat[i, 0]
        col = positions_flat[i, 1]
        current = multipliers[row, col]
        if current < 1024:
            multipliers[row, col] = min(current * 2, 1024)

@jit(nopython=True, cache=True)
def calculate_match_score_numba(linkpoint, board, multipliers, positions_flat, num_positions):
    
    if num_positions == 0:
        return 0, 0, 1
    
    
    symbol = board[positions_flat[0, 0], positions_flat[0, 1]]
    count = num_positions
    
    
    symbol_idx = symbol - 2
    count_idx = min(count - 5, 10)
    if 0 <= symbol_idx < linkpoint.shape[0] and 0 <= count_idx < linkpoint.shape[1]:
        base_score = linkpoint[symbol_idx, count_idx]
    else:
        base_score = 0
    
    
    all_one = True
    mult_sum = 0
    for i in range(num_positions):
        m = multipliers[positions_flat[i, 0], positions_flat[i, 1]]
        if m > 1:
            mult_sum += m
            all_one = False
    
    multiplier = 1 if all_one else mult_sum
    final_score = base_score * multiplier
    
    return base_score, multiplier, final_score

@jit(nopython=True, cache=True)
def clear_positions_numba(board, positions_flat, num_positions):
    
    for i in range(num_positions):
        board[positions_flat[i, 0], positions_flat[i, 1]] = 0

@jit(nopython=True, cache=True)
def find_all_matches_numba(board):
    
    rows, cols = board.shape
    visited = np.zeros((rows, cols), dtype=np.bool_)
    
    
    max_matches = rows * cols
    match_symbols = np.zeros(max_matches, dtype=np.int32)
    match_counts = np.zeros(max_matches, dtype=np.int32)
    
    all_positions = np.zeros((max_matches * rows * cols, 2), dtype=np.int32)
    position_starts = np.zeros(max_matches, dtype=np.int32)
    
    num_matches = 0
    total_positions = 0
    
    for i in range(rows):
        for j in range(cols):
            if not visited[i, j] and board[i, j] > 1:  
                connected = bfs_find_connected(board, i, j, visited)
                
                if len(connected) >= 5:
                    match_symbols[num_matches] = board[i, j]
                    match_counts[num_matches] = len(connected)
                    position_starts[num_matches] = total_positions
                    
                    
                    for k in range(len(connected)):
                        all_positions[total_positions + k, 0] = connected[k, 0]
                        all_positions[total_positions + k, 1] = connected[k, 1]
                    
                    total_positions += len(connected)
                    num_matches += 1
    
    return num_matches, match_symbols[:num_matches], match_counts[:num_matches], all_positions[:total_positions], position_starts[:num_matches]
    
@jit(nopython=True, cache=True)
def process_all_matches_numba(board, multipliers, eliminate_times, fixed_mask, linkpoint, match_symbols, match_counts, 
                               all_positions, position_starts, num_matches, is_super_free=False, enable_multiplier=True):
    
    total_score = 0
    base_scores = np.zeros(num_matches, dtype=np.int32)
    multipliers_out = np.zeros(num_matches, dtype=np.int32)
    final_scores = np.zeros(num_matches, dtype=np.int32)
    
    for match_idx in range(num_matches):
        symbol = match_symbols[match_idx]
        count = match_counts[match_idx]
        
        
        start_pos = position_starts[match_idx]
        if match_idx < num_matches - 1:
            end_pos = position_starts[match_idx + 1]
        else:
            end_pos = len(all_positions)
        
        
        symbol_idx = symbol - 2
        count_idx = min(count - 5, 10)
        if 0 <= symbol_idx < linkpoint.shape[0] and 0 <= count_idx < linkpoint.shape[1]:
            base_score = linkpoint[symbol_idx, count_idx]
        else:
            base_score = 0
        
        
        all_one = True
        mult_sum = 0
        for pos_idx in range(start_pos, end_pos):
            m = multipliers[all_positions[pos_idx, 0], all_positions[pos_idx, 1]]
            if m > 1:
                mult_sum += m
                all_one = False
        
        multiplier = 1 if all_one else mult_sum
        final_score = base_score * multiplier
        
        
        
        
        for pos_idx in range(start_pos, end_pos):
            row = all_positions[pos_idx, 0]
            col = all_positions[pos_idx, 1]
            eliminate_times[row, col] += 1  
            times = eliminate_times[row, col]
            
            
            if enable_multiplier:
                if times == 1:
                    if is_super_free:
                        
                        current = multipliers[row, col]
                        if current < 1024:
                            multipliers[row, col] = min(current * 2, 1024)
                    else:
                        
                        multipliers[row, col] = 1
                elif times >= 2:
                    current = multipliers[row, col]
                    if current < 1024:
                        multipliers[row, col] = min(current * 2, 1024)
        
        
        for pos_idx in range(start_pos, end_pos):
            row = all_positions[pos_idx, 0]
            col = all_positions[pos_idx, 1]
            board[row, col] = 0
            fixed_mask[row, col] = False  
        
        base_scores[match_idx] = base_score
        multipliers_out[match_idx] = multiplier
        final_scores[match_idx] = final_score
        total_score += final_score
    
    return total_score, base_scores, multipliers_out, final_scores



class Game7x7:
    def __init__(self, symbols=None, linkpoint=None, reel_set=None, drop_set=None, is_free_game=False, is_super_free_game=False, enable_multiplier=True):
        
        self.rows = 7
        self.cols = 7
        self.symbols = symbols if symbols else list(range(2, 9))
        self.board = np.zeros((self.rows, self.cols), dtype=np.int32)
        
        initial_multiplier = 2 if is_super_free_game else 1
        self.multipliers = np.full((self.rows, self.cols), initial_multiplier, dtype=np.int32)
        self.eliminate_times = np.zeros((self.rows, self.cols), dtype=np.int32)
        self.fixed_mask = np.zeros((self.rows, self.cols), dtype=np.bool_)
        self.score = 0
        self.fixed_cells = set()
        self.is_free_game = is_free_game  
        self.is_super_free_game = is_super_free_game  
        self.enable_multiplier = enable_multiplier  
        
        
        self.eliminate_trigger_count = 0  
        self.eliminate_success_count = 0  
        self.eliminate_fail_count = 0     
        self.score_before_eliminate = 0   
        self.score_from_eliminate = 0     
        
        
        if reel_set is None:
            self.reel_set = self.select_reel_by_weight()
        else:
            self.reel_set = reel_set
        
        
        if drop_set is None:
            self.drop_set = self.select_drop_by_weight(eliminate_count=0)
        else:
            self.drop_set = drop_set
        
        
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
        
        self.load_reel_data()
        self.load_drop_data()
        self.load_eliminate_data()
        self.eliminate_count = 0
    
    def select_reel_by_weight(self):
        
        if self.is_super_free_game:
            weight_key = 'SuperFreeReelWeight'
        elif self.is_free_game:
            weight_key = 'FreeReelWeight'
        else:
            weight_key = 'ReelWeight'
        
        if GAME_DATA and weight_key in GAME_DATA:
            
            reel_weights = np.array(GAME_DATA[weight_key], dtype=np.float32)
            reel_weights = (reel_weights * 10000).astype(np.int32)
            idx = weighted_choice_numba(reel_weights)
            return idx + 1
        else:
            return random.randint(1, 5)
    
    def select_drop_by_weight(self, eliminate_count=0):
        
        if self.is_super_free_game:
            weight_key = 'SuperFreeDropWeight'
        elif self.is_free_game:
            weight_key = 'FreeDropWeight'
        else:
            weight_key = 'DropWeight'
        
        if GAME_DATA and weight_key in GAME_DATA:
            drop_weights_2d = np.array(GAME_DATA[weight_key], dtype=np.float32)
            
            
            if eliminate_count <= 0:
                row_idx = 0  
            elif 1 <= eliminate_count <= 3:
                row_idx = 0
            elif 4 <= eliminate_count <= 6:
                row_idx = 1
            elif 7 <= eliminate_count <= 9:
                row_idx = 2
            else:  
                row_idx = 3
            
            
            drop_weights = drop_weights_2d[row_idx]
            drop_weights = (drop_weights * 10000).astype(np.int32)
            idx = weighted_choice_numba(drop_weights)
            return idx + 1
        else:
            return random.randint(1, 6)
    
    def load_reel_data(self):
        
        
        if hasattr(self, '_cached_reel_set') and self._cached_reel_set == self.reel_set:
            return  
        
        if GAME_DATA:
            if self.is_super_free_game:
                prefix = 'SuperFreeGame'
            elif self.is_free_game:
                prefix = 'FreeGame'
            else:
                prefix = 'baseGame'
            reel_key = f'{prefix}Symbol{self.reel_set}'
            weight_key = f'{prefix}SymbolWeight{self.reel_set}'
            my_key = f'{prefix}MY{self.reel_set}'
            
            
            self.reel_symbols = np.array(GAME_DATA.get(reel_key, []), dtype=np.int32)
            
            reel_weights = np.array(GAME_DATA.get(weight_key, []), dtype=np.float32)
            self.reel_weights = (reel_weights * 10000).astype(np.int32)
            my_weights = np.array(GAME_DATA.get(my_key, []), dtype=np.float32)
            self.my_weights = (my_weights * 10000).astype(np.int32)
            
            
            self._cached_reel_set = self.reel_set
        else:
            self.reel_symbols = None
            self.reel_weights = None
            self.my_weights = None
    
    def load_drop_data(self):
        
        
        if hasattr(self, '_cached_drop_set') and self._cached_drop_set == self.drop_set:
            return  
        
        if GAME_DATA:
            if self.is_super_free_game:
                prefix = 'SuperFreeGameDrop'
            elif self.is_free_game:
                prefix = 'FreeGameDrop'
            else:
                prefix = 'BaseGameDrop'
            drop_key = f'{prefix}{self.drop_set}'
            drop_rweight_key = f'{prefix}RWeight{self.drop_set}'
            drop_pweight_key = f'{prefix}PWeight{self.drop_set}'
            drop_method_key = f'{prefix}method{self.drop_set}'
            drop_my_key = f'{prefix}My{self.drop_set}'
            
            
            self.drop_symbol_table = np.array(GAME_DATA.get(drop_key, []), dtype=np.int32)
            
            drop_rweights = np.array(GAME_DATA.get(drop_rweight_key, []), dtype=np.float32)
            self.drop_rweights = (drop_rweights * 10000).astype(np.int32)
            drop_pweights = np.array(GAME_DATA.get(drop_pweight_key, []), dtype=np.float32)
            self.drop_pweights = (drop_pweights * 10000).astype(np.int32)
            drop_method_weights = np.array(GAME_DATA.get(drop_method_key, []), dtype=np.float32)
            self.drop_method_weights = (drop_method_weights * 10000).astype(np.int32)
            drop_my_weights = np.array(GAME_DATA.get(drop_my_key, []), dtype=np.float32)
            self.drop_my_weights = (drop_my_weights * 10000).astype(np.int32)
            
            
            self._cached_drop_set = self.drop_set
        else:
            self.drop_symbol_table = None
            self.drop_rweights = None
            self.drop_pweights = None
            self.drop_method_weights = None
            self.drop_my_weights = None
    
    def load_eliminate_data(self):
        
        if GAME_DATA:
            
            if self.is_super_free_game:
                prefix = 'SuperFree'
            elif self.is_free_game:
                prefix = 'Free'
            else:
                prefix = ''
            
            
            eliminate_trigger = np.array(GAME_DATA.get(f'{prefix}Eliminate', []), dtype=np.float32)
            self.eliminate_trigger = (eliminate_trigger * 10000).astype(np.int32)
            eliminate_time = np.array(GAME_DATA.get(f'{prefix}EliminateTime', []), dtype=np.float32)
            self.eliminate_time = (eliminate_time * 10000).astype(np.int32)
            eliminate_symbol = np.array(GAME_DATA.get(f'{prefix}EliminateSymbol', []), dtype=np.float32)
            self.eliminate_symbol = (eliminate_symbol * 10000).astype(np.int32)
        else:
            self.eliminate_trigger = None
            self.eliminate_time = None
            self.eliminate_symbol = None
    
    def initialize_board(self):
        
        if self.reel_symbols is None or self.reel_weights is None:
            for i in range(self.rows):
                for j in range(self.cols):
                    self.board[i][j] = random.choice(self.symbols)
        else:
            
            initialize_board_numba(self.board, self.reel_symbols, self.reel_weights)
            
            if self.my_weights is not None and len(self.my_weights) > 0:
                convert_my_numba(self.board, self.my_weights)
            
            
            fix_c1_numba(self.board)
        
        
        if not self.is_free_game and not self.is_super_free_game:
            self.multipliers[:] = 1
        
        return self.board
    
    def find_connected_symbols(self, row, col, visited):
        
        connected_array = bfs_find_connected(self.board, row, col, visited)
        return [(int(connected_array[i, 0]), int(connected_array[i, 1])) for i in range(len(connected_array))]
    
    def find_all_matches(self):
        
        num_matches, match_symbols, match_counts, all_positions, position_starts = find_all_matches_numba(self.board)
        
        if num_matches == 0:
            return []
        
        
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
        
        return find_all_matches_numba(self.board)
    
    def calculate_multiplier(self, positions):
        
        multipliers = [self.multipliers[r, c] for r, c in positions]
        
        if all(m == 1 for m in multipliers):
            return 1
        
        return sum(multipliers)
    
    def get_base_score(self, symbol, count):
        
        symbol_idx = symbol - 2
        count_idx = min(count - 5, 10)
        
        if 0 <= symbol_idx < len(self.linkpoint) and 0 <= count_idx < len(self.linkpoint[0]):
            return int(self.linkpoint[symbol_idx, count_idx])
        return 0
    
    def upgrade_multipliers(self, positions):
        
        for row, col in positions:
            current = self.multipliers[row, col]
            if current < 1024:
                self.multipliers[row, col] = min(current * 2, 1024)
    
    def remove_symbols_and_score(self, matches):
        
        total_removed = 0
        total_score = 0
        details = []
        
        for symbol, count, positions in matches:
            
            positions_array = np.array(positions, dtype=np.int32)
            
            
            base_score, multiplier, final_score = calculate_match_score_numba(
                self.linkpoint, self.board, self.multipliers, 
                positions_array, len(positions)
            )
            
            
            upgrade_multipliers_numba(self.multipliers, positions_array, len(positions))
            
            
            clear_positions_numba(self.board, positions_array, len(positions))
            
            total_removed += len(positions)
            total_score += final_score
            
            details.append({
                'symbol': f'M{symbol-1}',
                'count': count,
                'base_score': base_score,
                'multiplier': multiplier,
                'final_score': final_score,
                'positions': positions
            })
        
        return total_removed, total_score, details
    
    def remove_symbols_and_score_fast(self, num_matches, match_symbols, match_counts, 
                                       all_positions, position_starts):
        
        if num_matches == 0:
            return 0, 0, []
        
        total_score, base_scores, multipliers, final_scores = process_all_matches_numba(
            self.board, self.multipliers, self.eliminate_times, self.fixed_mask, self.linkpoint,
            match_symbols, match_counts, all_positions, position_starts, num_matches, self.is_super_free_game, self.enable_multiplier
        )
        
        total_removed = np.sum(match_counts)
        
        
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
                'base_score': int(base_scores[i]),
                'multiplier': int(multipliers[i]),
                'final_score': int(final_scores[i]),
                'positions': positions
            })
        
        return int(total_removed), int(total_score), details
    
    def drop_symbols(self):
        
        drop_symbols_numba(self.board, self.multipliers, self.fixed_mask)
    
    def fill_empty_spaces(self):
        
        if self.drop_symbol_table is None or self.drop_method_weights is None:
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.board[i, j] == 0 and not self.fixed_mask[i, j]:
                        self.board[i, j] = random.choice(self.symbols)
                        self.multipliers[i, j] = 1
        else:
            
            self.drop_set = self.select_drop_by_weight(self.eliminate_count)
            self.load_drop_data()
            
            
            drop_method = weighted_choice_numba(self.drop_method_weights)
            
            if drop_method == 0:
                
                fill_empty_method0_numba(self.board, self.multipliers, self.fixed_mask,
                                        self.drop_symbol_table, self.drop_rweights)
            else:
                
                position_idx = weighted_choice_numba(self.drop_pweights)
                fill_empty_method1_numba(self.board, self.multipliers, self.fixed_mask,
                                        self.drop_symbol_table, position_idx)
            
            
            if self.drop_my_weights is not None and len(self.drop_my_weights) > 0:
                my_targets = np.zeros(3, dtype=np.int32)
                for my_idx in range(min(3, len(self.drop_my_weights))):
                    my_targets[my_idx] = weighted_choice_numba(self.drop_my_weights[my_idx])
                convert_my_numba_with_targets(self.board, my_targets)
            
            fix_c1_numba(self.board)
    
    def process_cascades(self):
        
        cascade_count = 0
        total_removed = 0
        total_score = 0
        all_details = []
        first_eliminate_triggered = False  
        
        while True:
            
            num_matches, match_symbols, match_counts, all_positions, position_starts = self.find_all_matches_fast()
            
            if num_matches == 0:
                
                if not first_eliminate_triggered:
                    self.score_before_eliminate = total_score
                    first_eliminate_triggered = True
                
                if self.try_eliminate_feature():
                    continue
                else:
                    break
            
            
            removed, score, details = self.remove_symbols_and_score_fast(
                num_matches, match_symbols, match_counts, all_positions, position_starts
            )
            
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
        
        self.eliminate_count = 0
        self.fixed_cells.clear()
        self.fixed_mask[:] = False
        
        if not keep_multipliers:
            self.multipliers[:] = 1  
            self.eliminate_times[:] = 0  
        
        
        cascade_count, total_removed, round_score, details = self.process_cascades()
        self.score += round_score
        
        return cascade_count, total_removed, round_score, details
    
    def try_eliminate_feature(self):
        
        if self.eliminate_trigger is None or self.eliminate_time is None or self.eliminate_symbol is None:
            return False
        
        
        if self.eliminate_count == 0:
            col_idx = 0
        elif 1 <= self.eliminate_count <= 3:
            col_idx = 1
        elif 4 <= self.eliminate_count <= 6:
            col_idx = 2
        elif 7 <= self.eliminate_count <= 9:
            col_idx = 3
        else:
            col_idx = 4
        
        
        if col_idx >= self.eliminate_trigger.shape[1]:
            return False
        
        
        weights = np.array([
            self.eliminate_trigger[0, col_idx],  
            self.eliminate_trigger[1, col_idx]   
        ], dtype=np.int32)
        
        if weighted_choice_numba(weights) != 0:  
            return False
        
        
        self.eliminate_trigger_count += 1
        
        num_blocks = weighted_choice_numba(self.eliminate_time) + 1
        
        placed_blocks = 0
        max_attempts = 100
        attempts = 0
        occupied_cells = set(self.fixed_cells)
        
        while placed_blocks < num_blocks and attempts < max_attempts:
            attempts += 1
            
            start_row = random.randint(0, self.rows - 2)
            start_col = random.randint(0, self.cols - 2)
            
            block_cells = [(start_row + dr, start_col + dc) for dr in range(2) for dc in range(2)]
            if any(cell in occupied_cells for cell in block_cells):
                continue
            
            has_c1 = any(self.board[r, c] == 1 for r, c in block_cells)
            if has_c1:
                continue
            
            symbol_id = weighted_choice_numba(self.eliminate_symbol)
            
            if placed_blocks == 0:
                adjacent_positions = [
                    (start_row - 1, start_col), (start_row - 1, start_col + 1),
                    (start_row + 2, start_col), (start_row + 2, start_col + 1),
                    (start_row, start_col - 1), (start_row + 1, start_col - 1),
                    (start_row, start_col + 2), (start_row + 1, start_col + 2)
                ]
                
                has_adjacent = False
                for nr, nc in adjacent_positions:
                    if (0 <= nr < self.rows and 0 <= nc < self.cols and 
                        self.board[nr, nc] == symbol_id):
                        has_adjacent = True
                        break
                
                if not has_adjacent:
                    continue
            
            for dr in range(2):
                for dc in range(2):
                    r, c = start_row + dr, start_col + dc
                    self.board[r, c] = symbol_id
                    occupied_cells.add((r, c))
                    self.fixed_cells.add((r, c))
                    self.fixed_mask[r, c] = True
            
            placed_blocks += 1
        
        
        if placed_blocks > 0:
            self.eliminate_success_count += 1
        else:
            self.eliminate_fail_count += 1
        
        return placed_blocks > 0



def basegame(rounds):
    
    scores = np.zeros(rounds, dtype=np.int64)
    c1_counts = np.zeros(rounds, dtype=np.int32)
    initial_c1_counts = np.zeros(rounds, dtype=np.int32)  
    
    
    if rounds > 0:
        print("Warming up numba compilation...")
        warmup_game = Game7x7()
        warmup_game.initialize_board()
        warmup_game.play_round()
        print("Compilation complete, starting simulation...\n")
    
    
    game = Game7x7()
    
    
    total_trigger_count = 0
    total_success_count = 0
    total_fail_count = 0
    games_with_eliminate = []  
    games_without_eliminate = []  
    
    for i in range(rounds):
        
        game.board[:] = 0
        game.multipliers[:] = 1
        game.fixed_mask[:] = False
        game.fixed_cells.clear()
        game.score = 0
        game.eliminate_count = 0
        game.eliminate_trigger_count = 0
        game.eliminate_success_count = 0
        game.eliminate_fail_count = 0
        game.score_before_eliminate = 0
        game.score_from_eliminate = 0
        
        
        game.reel_set = game.select_reel_by_weight()
        game.drop_set = game.select_drop_by_weight(eliminate_count=0)
        game.load_reel_data()
        game.load_drop_data()
        
        
        game.initialize_board()
        initial_c1_counts[i] = np.sum(game.board == 1)  
        cascade, removed, score, details = game.play_round()
        
        scores[i] = score
        c1_counts[i] = np.sum(game.board == 1)  
        
        
        total_trigger_count += game.eliminate_trigger_count
        total_success_count += game.eliminate_success_count
        total_fail_count += game.eliminate_fail_count
        
        
        if game.eliminate_success_count > 0:
            games_with_eliminate.append({
                'total_score': score,
                'score_before': game.score_before_eliminate,
                'score_after': score - game.score_before_eliminate
            })
        else:
            games_without_eliminate.append(score)
        
        
        if rounds >= 1000 and (i + 1) % 1000 == 0:
            print(f"Completed {i + 1}/{rounds} rounds...")
    
    
    print("\n=== 2×2 Eliminate Feature Statistics ===")
    print(f"Trigger check count: {total_trigger_count}")
    print(f"Successful placement count: {total_success_count}")
    print(f"Failed placement count: {total_fail_count}")
    if total_trigger_count > 0:
        fail_rate = (total_fail_count / total_trigger_count) * 100
        print(f"Failure rate: {fail_rate:.2f}%")
        print(f"Average triggers per round: {total_trigger_count / rounds:.2f} times")
    
    print("\n--- Category Statistics ---")
    print(f"Games with 2×2 triggered: {len(games_with_eliminate)}")
    print(f"Games without 2×2 triggered: {len(games_without_eliminate)}")
    
    if games_with_eliminate:
        avg_total_with = np.mean([g['total_score'] for g in games_with_eliminate])
        avg_before = np.mean([g['score_before'] for g in games_with_eliminate])
        avg_after = np.mean([g['score_after'] for g in games_with_eliminate])
        print(f"\nGames with 2×2 triggered:")
        print(f"  Average total score: {avg_total_with:.2f}")
        print(f"  Average score before trigger: {avg_before:.2f}")
        print(f"  Average score increase after 2×2: {avg_after:.2f}")
    
    if games_without_eliminate:
        avg_without = np.mean(games_without_eliminate)
        print(f"\nGames without 2×2 triggered:")
        print(f"  Average score: {avg_without:.2f}")
    
    if games_with_eliminate and games_without_eliminate:
        avg_total_with = np.mean([g['total_score'] for g in games_with_eliminate])
        avg_without = np.mean(games_without_eliminate)
        diff = avg_without - avg_total_with
        print(f"\nDifference: Without trigger is higher by {diff:.2f} points")
    
    print("=" * 40)
    
    return scores, c1_counts, initial_c1_counts

def freegame(initial_spins, rounds):
    
    total_scores = np.zeros(rounds, dtype=np.int64)
    total_spins = np.zeros(rounds, dtype=np.int32)
    
    
    if rounds > 0:
        print("Warming up numba compilation (Free Game mode)...")
        warmup_game = Game7x7(is_free_game=True)
        warmup_game.initialize_board()
        warmup_game.play_round(keep_multipliers=True)
        print("Compilation complete, starting Free Game simulation...\n")
    
    
    retrigger_map = {3: 10, 4: 12, 5: 15, 6: 20, 7: 30}
    
    for round_idx in range(rounds):
        
        game = Game7x7(is_free_game=True)
        
        
        game.multipliers[:] = 1
        game.eliminate_times[:] = 0
        
        remaining_spins = initial_spins
        total_score = 0
        spin_count = 0
        
        while remaining_spins > 0:
            
            game.board[:] = 0
            game.fixed_mask[:] = False
            game.fixed_cells.clear()
            game.eliminate_count = 0
            
            
            game.reel_set = game.select_reel_by_weight()
            game.drop_set = game.select_drop_by_weight(eliminate_count=0)
            game.load_reel_data()
            game.load_drop_data()
            
            
            game.initialize_board()
            cascade, removed, score, details = game.play_round(keep_multipliers=True)
            
            total_score += score
            spin_count += 1
            remaining_spins -= 1
            
            
            c1_count = int(np.sum(game.board == 1))
            if c1_count in retrigger_map:
                extra_spins = retrigger_map[c1_count]
                remaining_spins += extra_spins
        
        total_scores[round_idx] = total_score
        total_spins[round_idx] = spin_count
        
        
        if rounds >= 100 and (round_idx + 1) % 100 == 0:
            print(f"Completed {round_idx + 1}/{rounds} Free Game sessions...")
    
    return total_scores, total_spins

def fullgame(spins, enable_multiplier=True):
    
    scores = np.zeros(spins, dtype=np.int64)
    c1_occurrences = 0  
    freegame_triggered = 0  
    freegame_total_spins = 0  
    basegame_total_score = 0  
    freegame_total_score = 0  
    
    
    if spins > 0:
        print("Warming up numba compilation...")
        warmup_base = Game7x7(enable_multiplier=enable_multiplier)
        warmup_base.initialize_board()
        warmup_base.play_round()
        warmup_free = Game7x7(is_free_game=True, enable_multiplier=enable_multiplier)
        warmup_free.initialize_board()
        warmup_free.play_round(keep_multipliers=True)
        print("Compilation complete, starting full game simulation...\n")
    
    
    base_game = Game7x7(enable_multiplier=enable_multiplier)
    free_game = Game7x7(is_free_game=True, enable_multiplier=enable_multiplier)  
    
    
    freegame_trigger_map = {3: 10, 4: 12, 5: 15, 6: 20, 7: 30}
    
    for spin_idx in range(spins):
        
        
        base_game.board[:] = 0
        base_game.multipliers[:] = 1
        base_game.eliminate_times[:] = 0
        base_game.fixed_mask[:] = False
        base_game.fixed_cells.clear()
        base_game.score = 0
        base_game.eliminate_count = 0
        
        
        base_game.reel_set = base_game.select_reel_by_weight()
        base_game.drop_set = base_game.select_drop_by_weight(eliminate_count=0)
        base_game.load_reel_data()
        base_game.load_drop_data()
        
        
        base_game.initialize_board()
        cascade, removed, base_score, details = base_game.play_round()
        
        
        base_c1_count = int(np.sum(base_game.board == 1))
        if base_c1_count > 0:
            c1_occurrences += 1
        
        total_score = base_score
        basegame_total_score += base_score  
        
        
        if base_c1_count >= 3 and base_c1_count in freegame_trigger_map:
            freegame_triggered += 1
            initial_free_spins = freegame_trigger_map[base_c1_count]
            
            
            free_game.multipliers[:] = 1
            free_game.eliminate_times[:] = 0
            
            remaining_spins = initial_free_spins
            free_score = 0
            free_spin_count = 0
            
            
            while remaining_spins > 0:
                
                free_game.board[:] = 0
                free_game.fixed_mask[:] = False
                free_game.fixed_cells.clear()
                free_game.eliminate_count = 0
                
                
                free_game.reel_set = free_game.select_reel_by_weight()
                free_game.drop_set = free_game.select_drop_by_weight(eliminate_count=0)
                free_game.load_reel_data()
                free_game.load_drop_data()
                
                
                free_game.initialize_board()
                cascade, removed, spin_score, details = free_game.play_round(keep_multipliers=True)
                
                free_score += spin_score
                free_spin_count += 1
                remaining_spins -= 1
                
                
                free_c1_count = int(np.sum(free_game.board == 1))
                if free_c1_count > 0:
                    c1_occurrences += 1
                
                
                if free_c1_count >= 3 and free_c1_count in freegame_trigger_map:
                    extra_spins = freegame_trigger_map[free_c1_count]
                    remaining_spins += extra_spins
            
            total_score += free_score
            freegame_total_spins += free_spin_count
            freegame_total_score += free_score  
        
        scores[spin_idx] = total_score
        
        
        if spins >= 1000 and (spin_idx + 1) % 1000 == 0:
            print(f"Completed {spin_idx + 1}/{spins} Base Game spins...")
    
    return scores, c1_occurrences, freegame_triggered, freegame_total_spins, basegame_total_score, freegame_total_score

def _fullgame_worker(args):
    
    start_idx, num_spins, seed, reel_weights, enable_multiplier, upper_limit = args
    
    
    np.random.seed(seed)
    random.seed(seed)
    
    
    if reel_weights is not None:
        try:
            
            import json
            import os
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(script_dir, 'data.js')
            with open(data_path, 'r', encoding='utf-8') as f:
                content = f.read()
                json_str = content.replace('const data = ', '').rstrip(';')
                local_game_data = json.loads(json_str)
            
            local_game_data['ReelWeight'] = list(reel_weights)
            
            global GAME_DATA
            GAME_DATA = local_game_data
        except Exception as e:
            print(f"Warning: Failed to apply custom reel_weights in worker: {e}")
    
    
    total_spin_score = 0  
    c1_occurrences = 0
    freegame_triggered = 0
    freegame_total_spins = 0
    basegame_total_score = 0
    freegame_total_score = 0
    
    
    bg_eliminate_counts = np.zeros(11, dtype=np.int64)  
    fg_eliminate_counts = np.zeros(11, dtype=np.int64)  
    
    
    basegame_highamount_score = 0  
    basegame_highamount_count = 0  
    freegame_highamount_score = 0  
    freegame_highamount_count = 0  
    
    
    base_game = Game7x7(enable_multiplier=enable_multiplier)
    free_game = Game7x7(is_free_game=True, enable_multiplier=enable_multiplier)
    
    
    freegame_trigger_map = {3: 10, 4: 12, 5: 15, 6: 20, 7: 30}
    
    
    score_limit = -1 if upper_limit == -1 else upper_limit * 100
    
    for spin_idx in range(num_spins):
        
        need_redraw = True
        
        while need_redraw:
            
            base_game.board[:] = 0
            base_game.multipliers[:] = 1
            base_game.eliminate_times[:] = 0
            base_game.fixed_mask[:] = False
            base_game.fixed_cells.clear()
            base_game.score = 0
            base_game.eliminate_count = 0
            
            base_game.reel_set = base_game.select_reel_by_weight()
            base_game.drop_set = base_game.select_drop_by_weight(eliminate_count=0)
            base_game.load_reel_data()  
            base_game.load_drop_data()  
            
            base_game.initialize_board()
            cascade, removed, base_score, details = base_game.play_round()
        
            
            bg_eliminate_idx = min(cascade, 10)  
            bg_eliminate_counts[bg_eliminate_idx] += 1
            
            
            if base_score >= 1000000:
                basegame_highamount_score += base_score
                basegame_highamount_count += 1
            
            base_c1_count = int(np.sum(base_game.board == 1))
            if base_c1_count > 0:
                c1_occurrences += 1
            
            total_score = base_score
            basegame_total_score += base_score
            
            
            if base_c1_count >= 3 and base_c1_count in freegame_trigger_map:
                freegame_triggered += 1
                initial_free_spins = freegame_trigger_map[base_c1_count]
                
                free_game.multipliers[:] = 1
                free_game.eliminate_times[:] = 0
                
                remaining_spins = initial_free_spins
                free_score = 0
                free_spin_count = 0
                
                while remaining_spins > 0:
                    free_game.board[:] = 0
                    free_game.fixed_mask[:] = False
                    free_game.fixed_cells.clear()
                    free_game.eliminate_count = 0
                    
                    free_game.reel_set = free_game.select_reel_by_weight()
                    free_game.drop_set = free_game.select_drop_by_weight(eliminate_count=0)
                    free_game.load_reel_data()  
                    free_game.load_drop_data()  
                    
                    free_game.initialize_board()
                    cascade, removed, spin_score, details = free_game.play_round(keep_multipliers=True)
                    
                    
                    fg_eliminate_idx = min(cascade, 10)  
                    fg_eliminate_counts[fg_eliminate_idx] += 1
                    
                    free_score += spin_score
                    free_spin_count += 1
                    remaining_spins -= 1
                    
                    free_c1_count = int(np.sum(free_game.board == 1))
                    if free_c1_count > 0:
                        c1_occurrences += 1
                    
                    if free_c1_count >= 3 and free_c1_count in freegame_trigger_map:
                        extra_spins = freegame_trigger_map[free_c1_count]
                        remaining_spins += extra_spins
                
                
                if free_score >= 1000000:
                    freegame_highamount_score += free_score
                    freegame_highamount_count += 1
                
                total_score += free_score
                freegame_total_spins += free_spin_count
                freegame_total_score += free_score
            
            
            if score_limit != -1 and total_score > score_limit:
                
                bg_eliminate_counts[bg_eliminate_idx] -= 1
                if base_score >= 1000000:
                    basegame_highamount_score -= base_score
                    basegame_highamount_count -= 1
                if base_c1_count > 0:
                    c1_occurrences -= 1
                basegame_total_score -= base_score
                
                if base_c1_count >= 3 and base_c1_count in freegame_trigger_map:
                    freegame_triggered -= 1
                    
                    for i in range(11):
                        
                        pass
                    if free_score >= 1000000:
                        freegame_highamount_score -= free_score
                        freegame_highamount_count -= 1
                    freegame_total_spins -= free_spin_count
                    freegame_total_score -= free_score
                    
                
                need_redraw = True  
            else:
                need_redraw = False  
        
        
        total_spin_score += total_score
    
    
    bg_highamount = np.array([basegame_highamount_score, basegame_highamount_count], dtype=np.int64)
    fg_highamount = np.array([freegame_highamount_score, freegame_highamount_count], dtype=np.int64)
    
    
    return total_spin_score, c1_occurrences, freegame_triggered, freegame_total_spins, basegame_total_score, freegame_total_score, bg_eliminate_counts, fg_eliminate_counts, bg_highamount, fg_highamount

def fullgame_parallel(spins, reel_weights=None, num_workers=None, enable_multiplier=True, upper_limit=-1):
    
    
    if reel_weights is not None:
        if len(reel_weights) != 5:
            raise ValueError("reel_weights must contain 5 elements")
        if GAME_DATA is not None:
            GAME_DATA['ReelWeight'] = list(reel_weights)
            print(f"Using custom ReelWeight: {reel_weights}")
    
    if num_workers is None:
        num_workers = 4  
    
    print(f"Using {num_workers} parallel processes for simulation...")
    
    
    print("Warming up numba compilation...")
    warmup_base = Game7x7(enable_multiplier=enable_multiplier)
    warmup_base.initialize_board()
    warmup_base.play_round()
    warmup_free = Game7x7(is_free_game=True, enable_multiplier=enable_multiplier)
    warmup_free.initialize_board()
    warmup_free.play_round(keep_multipliers=True)
    print("Compilation complete\n")
    
    
    spins_per_worker = spins // num_workers
    remaining = spins % num_workers
    
    tasks = []
    start_idx = 0
    for i in range(num_workers):
        
        chunk_size = spins_per_worker + (1 if i < remaining else 0)
        if chunk_size > 0:
            
            seed = random.randint(0, 2**31 - 1)
            tasks.append((start_idx, chunk_size, seed, reel_weights, enable_multiplier, upper_limit))
            start_idx += chunk_size
    
    
    print(f"Starting parallel simulation for {spins} spins...")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(_fullgame_worker, tasks))
    
    
    total_score = 0
    total_c1 = 0
    total_fg_triggered = 0
    total_fg_spins = 0
    total_basegame_score = 0
    total_freegame_score = 0
    total_bg_eliminate_counts = np.zeros(11, dtype=np.int64)
    total_fg_eliminate_counts = np.zeros(11, dtype=np.int64)
    total_basegame_highamount = np.zeros(2, dtype=np.int64)  
    total_freegame_highamount = np.zeros(2, dtype=np.int64)  
    
    for spin_total, c1_count, fg_triggered, fg_spins, bg_score, fg_score, bg_elim, fg_elim, bg_high, fg_high in results:
        total_score += spin_total  
        total_c1 += c1_count
        total_fg_triggered += fg_triggered
        total_fg_spins += fg_spins
        total_basegame_score += bg_score
        total_freegame_score += fg_score
        total_bg_eliminate_counts += bg_elim
        total_fg_eliminate_counts += fg_elim
        total_basegame_highamount += bg_high  
        total_freegame_highamount += fg_high  
    
    
    avg_score = total_score / spins
    
    print("Parallel simulation complete!\n")
    
    return avg_score, total_c1, total_fg_triggered, total_fg_spins, total_basegame_score, total_freegame_score, total_bg_eliminate_counts, total_fg_eliminate_counts, total_basegame_highamount, total_freegame_highamount

def fullgame_parallel_stats(spins, reel_weights=None, num_workers=None, enable_multiplier=True, upper_limit=-1):
    
    
    if reel_weights is not None:
        if len(reel_weights) != 5:
            raise ValueError("reel_weights must contain 5 elements")
        if GAME_DATA is not None:
            GAME_DATA['ReelWeight'] = list(reel_weights)
            print(f"Using custom ReelWeight: {reel_weights}")
    
    if num_workers is None:
        num_workers = max(1, mp.cpu_count() - 1)
    
    print(f"Using {num_workers} parallel processes for simulation (memory-friendly mode)...")
    
    
    print("Warming up numba compilation...")
    warmup_base = Game7x7(enable_multiplier=enable_multiplier)
    warmup_base.initialize_board()
    warmup_base.play_round()
    warmup_free = Game7x7(is_free_game=True, enable_multiplier=enable_multiplier)
    warmup_free.initialize_board()
    warmup_free.play_round(keep_multipliers=True)
    print("Compilation complete\n")
    
    
    spins_per_worker = spins // num_workers
    remaining = spins % num_workers
    
    tasks = []
    start_idx = 0
    for i in range(num_workers):
        chunk_size = spins_per_worker + (1 if i < remaining else 0)
        if chunk_size > 0:
            seed = random.randint(0, 2**31 - 1)
            tasks.append((start_idx, chunk_size, seed, reel_weights, enable_multiplier, upper_limit))
            start_idx += chunk_size
    
    
    print(f"Starting parallel simulation for {spins} spins (statistics only)...")
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(_fullgame_worker, tasks))
    
    
    total_score = 0
    total_c1 = 0
    total_fg_triggered = 0
    total_fg_spins = 0
    total_basegame_score = 0
    total_freegame_score = 0
    total_bg_eliminate_counts = np.zeros(11, dtype=np.int64)
    total_fg_eliminate_counts = np.zeros(11, dtype=np.int64)
    total_basegame_highamount = np.zeros(2, dtype=np.int64)  
    total_freegame_highamount = np.zeros(2, dtype=np.int64)  
    
    for spin_total, c1_count, fg_triggered, fg_spins, bg_score, fg_score, bg_elim, fg_elim, bg_high, fg_high in results:
        total_score += spin_total  
        total_c1 += c1_count
        total_fg_triggered += fg_triggered
        total_fg_spins += fg_spins
        total_basegame_score += bg_score
        total_freegame_score += fg_score
        total_bg_eliminate_counts += bg_elim
        total_fg_eliminate_counts += fg_elim
        total_basegame_highamount += bg_high  
        total_freegame_highamount += fg_high  
    
    avg_score = total_score / spins
    
    print("Parallel simulation complete!\n")
    print(f"Average score: {avg_score:.2f}")
    print(f"Total score: {total_score:,}")
    print(f"RTP: {(total_score / spins) * 100:.2f}%")
    
    return avg_score, total_score, total_c1, total_fg_triggered, total_fg_spins, total_basegame_score, total_freegame_score, total_bg_eliminate_counts, total_fg_eliminate_counts, total_basegame_highamount, total_freegame_highamount


def print_fullgame_stats(scores, c1_count, fg_triggered, fg_spins, basegame_score=None, freegame_score=None):
    
    print("\n" + "="*50)
    print("Full Game Statistics")
    print("="*50)
    print(f"Total Base Game Spins: {len(scores):,}")
    print(f"Total score: {np.sum(scores):,}")
    if basegame_score is not None:
        avg_bg = basegame_score / len(scores)
        print(f"  - Base Game average score: {avg_bg:.2f} (total: {basegame_score:,})")
    if freegame_score is not None:
        avg_fg_per_spin = freegame_score / len(scores)
        print(f"  - Free Game average score: {avg_fg_per_spin:.2f} (total: {freegame_score:,})")
        if fg_triggered > 0:
            avg_fg_per_game = freegame_score / fg_triggered
            print(f"  - Average score per Free Game session: {avg_fg_per_game:.2f}")
    print(f"Average score per spin: {np.mean(scores):.2f}")
    print(f"Highest single score: {np.max(scores):,}")
    print(f"Lowest single score: {np.min(scores):,}")
    
    print(f"\n{'C1 Statistics':-^50}")
    print(f"C1 occurrence count: {c1_count:,}")
    print(f"C1 occurrence rate: {(c1_count / len(scores)) * 100:.2f}%")
    
    print(f"\n{'Free Game Statistics':-^50}")
    print(f"Free Game trigger count: {fg_triggered:,}")
    print(f"Trigger rate: {(fg_triggered / len(scores)) * 100:.2f}%")
    print(f"Total Free Game spins: {fg_spins:,}")
    if fg_triggered > 0:
        print(f"Average spins per Free Game session: {fg_spins / fg_triggered:.2f}")
    
    print(f"\n{'Score Distribution':-^50}")
    print(f"Median: {np.median(scores):.2f}")
    print(f"Standard deviation: {np.std(scores):.2f}")
    percentiles = [50, 75, 90, 95, 99]
    for p in percentiles:
        print(f"{p}th percentile: {np.percentile(scores, p):.2f}")
    
    
    print(f"\n{'RTP Analysis':-^50}")
    total_bet = len(scores)  
    total_win = np.sum(scores)
    rtp = (total_win / total_bet) * 100 if total_bet > 0 else 0
    print(f"RTP: {rtp:.2f}%")
    if basegame_score is not None and freegame_score is not None:
        base_rtp = (basegame_score / total_bet) * 100 if total_bet > 0 else 0
        free_rtp = (freegame_score / total_bet) * 100 if total_bet > 0 else 0
        print(f"  - Base Game RTP: {base_rtp:.2f}%")
        print(f"  - Free Game RTP: {free_rtp:.2f}%")
    print(f"Hit rate: {np.count_nonzero(scores) / len(scores) * 100:.2f}%")
    print("="*50)







# %%
