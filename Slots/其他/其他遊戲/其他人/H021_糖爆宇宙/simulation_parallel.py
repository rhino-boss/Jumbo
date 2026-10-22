#%%
import numpy as np
from multiprocessing import Pool, cpu_count
import time
from functools import partial
import json
from numba import njit
import subprocess
import pickle
import tempfile
import os
import sys

# ============================================================================
# Data Loading Functions
# ============================================================================

def load_data(json_path='data.js'):
    """Load game parameters from data.js"""
    with open(json_path, 'r', encoding='utf-8') as f:
        content = f.read()
        json_str = content.replace('const data = ', '').rstrip(';\n')
        data = json.loads(json_str)
    
    game_data = {}
    game_data['linkpoint'] = np.array(data['linkpoint'], dtype=np.int32)
    game_data['basewheel'] = np.array(data['basewheel'], dtype=np.int32)
    game_data['Freewheel'] = np.array(data['Freewheel'], dtype=np.int32)
    
    for i in range(1, 7):
        game_data[f'baseGameSymbol{i}'] = np.array(data[f'baseGameSymbol{i}'], dtype=np.int32)
        game_data[f'baseGameSymbolWeight{i}'] = np.array(data[f'baseGameSymbolWeight{i}'], dtype=np.int32)
        game_data[f'baseGameMY{i}'] = np.array(data[f'baseGameMY{i}'], dtype=np.int32)
        game_data[f'baseGameEX{i}'] = np.array(data[f'baseGameEX{i}'], dtype=np.int32)
        for j in range(1, 5):
            game_data[f'BaseGameDrop{i}_{j}'] = np.array(data[f'BaseGameDrop{i}_{j}'], dtype=np.int32)
    
    for i in range(1, 7):
        game_data[f'FreeGameSymbol{i}'] = np.array(data[f'FreeGameSymbol{i}'], dtype=np.int32)
        game_data[f'FreeGameSymbolWeight{i}'] = np.array(data[f'FreeGameSymbolWeight{i}'], dtype=np.int32)
        game_data[f'FreeGameMY{i}'] = np.array(data[f'FreeGameMY{i}'], dtype=np.int32)
        game_data[f'FreeGameEX{i}'] = np.array(data[f'FreeGameEX{i}'], dtype=np.int32)
        for j in range(1, 5):
            game_data[f'FreeGameDrop{i}_{j}'] = np.array(data[f'FreeGameDrop{i}_{j}'], dtype=np.int32)
    
    return game_data

_cached_data = None

def _get_game_data():
    """Get or cache game data"""
    global _cached_data
    if _cached_data is None:
        _cached_data = load_data()
    return _cached_data

# ============================================================================
# Interactive Environment Helper Functions
# ============================================================================

def _is_interactive():
    """Detect if running in interactive environment"""
    try:
        # Check if in IPython/Jupyter environment
        get_ipython()
        return True
    except NameError:
        return False

def _run_via_subprocess(function_name, args_dict):
    """
    Run function via subprocess (for Interactive environment)
    
    Args:
        function_name: Name of function to run ('basegame', 'freegame')
        args_dict: Function arguments dictionary
    
    Returns:
        Function return value
    """
    # Get current working directory (not __file__, as it may not exist in Interactive)
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # If __file__ is undefined (e.g. in Interactive), use current working directory
        current_dir = os.getcwd()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        script_path = f.name
        
        # Build arguments string
        args_str = ', '.join([f'{k}={repr(v)}' for k, v in args_dict.items()])
        
        f.write(f'''
import sys
import os
import pickle
import numpy as np

# Add current directory to path
sys.path.insert(0, r"{current_dir}")
os.chdir(r"{current_dir}")

from simulation_parallel import basegame_parallel, freegame_parallel, fullgame_parallel

if __name__ == '__main__':
    if '{function_name}' == 'basegame':
        results = basegame_parallel({args_str}, _force_multiprocess=True)
    elif '{function_name}' == 'freegame':
        results = freegame_parallel({args_str}, _force_multiprocess=True)
    elif '{function_name}' == 'fullgame':
        results = fullgame_parallel({args_str}, _force_multiprocess=True)
    
    with open(r"{script_path}.pkl", "wb") as pkl_file:
        pickle.dump(results, pkl_file)
''')
    
    try:
        verbose = args_dict.get('verbose', True)
        if verbose:
            n = args_dict.get('n', 'unknown')
            num_workers = args_dict.get('num_workers', 'auto')
            print(f"Starting multiprocess simulation via subprocess... (n={n:,}, workers={num_workers})")
        
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=current_dir,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print("Error output:")
            print(result.stderr)
            raise RuntimeError(f"Simulation failed: {result.stderr}")
        
        if verbose and result.stdout:
            print(result.stdout)
        
        pkl_path = script_path + '.pkl'
        with open(pkl_path, 'rb') as f:
            results = pickle.load(f)
        
        os.unlink(pkl_path)
        return results
        
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)

# ============================================================================
# Numba-Accelerated Core Game Logic Functions
# ============================================================================

@njit
def weighted_choice(weights):
    """Random selection using weights, returns index"""
    total = np.sum(weights)
    if total == 0:
        return 0
    r = np.random.randint(0, total)
    cumsum = 0
    for i in range(len(weights)):
        cumsum += weights[i]
        if r < cumsum:
            return i
    return len(weights) - 1

@njit
def generate_initial_board(symbols, weights):
    """Generate initial 4x5 board"""
    board = np.zeros((4, 5), dtype=np.int32)
    for col in range(5):
        start_pos = weighted_choice(weights[col])
        reel_len = len(symbols[col])
        for row in range(4):
            board[row, col] = symbols[col][(start_pos + row) % reel_len]
    return board

@njit
def normalize_symbol(symbol):
    """Normalize symbol: convert golden version to corresponding normal version"""
    if 10 <= symbol <= 17:
        return symbol - 8
    elif 26 <= symbol <= 33:
        return symbol - 8
    else:
        return symbol

@njit
def check_matches(board):
    """Check ways game match eliminations"""
    matches = np.zeros((4, 5), dtype=np.bool_)
    for symbol in range(2, 34):
        if symbol == 0 or symbol == 34:
            continue
        if 10 <= symbol <= 17:
            continue
        if 26 <= symbol <= 33:
            continue
        
        col_counts = np.zeros(5, dtype=np.int32)
        for row in range(4):
            for col in range(5):
                board_symbol = board[row, col]
                norm_symbol = normalize_symbol(board_symbol)
                if norm_symbol == symbol or board_symbol == 0 or board_symbol == 34:
                    col_counts[col] += 1
        
        length = 0
        for col in range(5):
            if col_counts[col] > 0:
                length += 1
            else:
                break
        
        if length >= 3:
            for row in range(4):
                for col in range(length):
                    board_symbol = board[row, col]
                    norm_symbol = normalize_symbol(board_symbol)
                    if norm_symbol == symbol or board_symbol == 0 or board_symbol == 34:
                        matches[row, col] = True
    return matches

@njit
def calculate_win(board, matches, linkpoint, exploded_cols):
    """Calculate ways game score"""
    explosion_values = np.array([4, 4, 4, 4, 4], dtype=np.int32)
    total_win = 0
    symbol_wins = np.zeros(8, dtype=np.int32)  # Separate scores for M1~M8
    
    for symbol in range(2, 10):
        col_counts = np.zeros(5, dtype=np.int32)
        for row in range(4):
            for col in range(5):
                if matches[row, col]:
                    board_symbol = board[row, col]
                    norm_symbol = normalize_symbol(board_symbol)
                    if norm_symbol == symbol or board_symbol == 0 or board_symbol == 34:
                        col_counts[col] += 1
        
        length = 0
        for col in range(5):
            if col_counts[col] > 0:
                length += 1
            else:
                break
        
        if length >= 3:
            ways = 1
            for col in range(length):
                if exploded_cols[col]:
                    ways *= explosion_values[col]
                else:
                    ways *= col_counts[col]
            
            link_idx = min(length - 3, 2)
            symbol_idx = symbol - 2
            base_win = linkpoint[link_idx, symbol_idx]
            win = ways * base_win
            total_win += win
            symbol_wins[symbol_idx] += win
    
    return total_win, symbol_wins

@njit
def calculate_win_freegame(board, matches, linkpoint, exploded_cols):
    """Calculate ways game score (FreeGame version)"""
    explosion_cumulative_values = np.array([5, 6, 8, 10, 15], dtype=np.int32)
    total_win = 0
    symbol_wins = np.zeros(8, dtype=np.int32)  # Separate scores for M1~M8
    
    for symbol in range(2, 10):
        col_counts = np.zeros(5, dtype=np.int32)
        for row in range(4):
            for col in range(5):
                if matches[row, col]:
                    board_symbol = board[row, col]
                    norm_symbol = normalize_symbol(board_symbol)
                    if norm_symbol == symbol or board_symbol == 0 or board_symbol == 34:
                        col_counts[col] += 1
        
        length = 0
        for col in range(5):
            if col_counts[col] > 0:
                length += 1
            else:
                break
        
        if length >= 3:
            ways = 1
            exploded_in_match = 0
            for col in range(length):
                if exploded_cols[col]:
                    ways *= explosion_cumulative_values[exploded_in_match]
                    exploded_in_match += 1
                else:
                    ways *= col_counts[col]
            
            link_idx = min(length - 3, 2)
            symbol_idx = symbol - 2
            base_win = linkpoint[link_idx, symbol_idx]
            win = ways * base_win
            total_win += win
            symbol_wins[symbol_idx] += win
    
    return total_win, symbol_wins

@njit
def trigger_wild1_explosion(board):
    """Convert WILD1 markers on board to full column explosion"""
    exploded_cols = np.zeros(5, dtype=np.bool_)
    for col in range(5):
        has_wild1 = False
        for row in range(4):
            if board[row, col] == 34:
                has_wild1 = True
                break
        if has_wild1:
            exploded_cols[col] = True
            for row in range(4):
                if board[row, col] != 1:
                    board[row, col] = 0
    return board, exploded_cols

@njit
def apply_gravity_and_fill(board, matches, drop_weights, cascade_count, ex_weights):
    """Apply gravity and fill with new symbols"""
    wild_positions = np.zeros((4, 5), dtype=np.int32)
    wild1_positions = np.zeros((4, 5), dtype=np.int32)
    cascade_idx = min(cascade_count, 3) + 1
    
    for col in range(5):
        has_golden = False
        for row in range(4):
            if matches[row, col]:
                symbol = board[row, col]
                if (10 <= symbol <= 17) or (26 <= symbol <= 33):
                    has_golden = True
                    break
        
        if has_golden:
            trigger_weight = ex_weights[col, cascade_idx]
            no_trigger_weight = ex_weights[col, 0]
            weights = np.array([trigger_weight, no_trigger_weight], dtype=np.int32)
            result = weighted_choice(weights)
            
            for row in range(4):
                if matches[row, col]:
                    symbol = board[row, col]
                    if (10 <= symbol <= 17) or (26 <= symbol <= 33):
                        if result == 0:
                            wild1_positions[row, col] = 1
                        else:
                            wild_positions[row, col] = 1
    
    for col in range(5):
        remaining = []
        for row in range(4):
            if not matches[row, col]:
                remaining.append(board[row, col])
        
        wild_count = 0
        wild1_count = 0
        for row in range(4):
            if wild_positions[row, col] == 1:
                wild_count += 1
            if wild1_positions[row, col] == 1:
                wild1_count += 1
        
        has_c1 = False
        for symbol in remaining:
            if symbol == 1:
                has_c1 = True
                break
        
        need_fill = 4 - len(remaining)
        new_symbols = []
        
        for _ in range(wild1_count):
            new_symbols.append(34)
        for _ in range(wild_count):
            new_symbols.append(0)
        
        remaining_fill = need_fill - wild1_count - wild_count
        for _ in range(remaining_fill):
            symbol_id = weighted_choice(drop_weights[col])
            if has_c1 and symbol_id == 1:
                symbol_id = 18
            elif symbol_id == 1:
                has_c1 = True
            new_symbols.append(symbol_id)
        
        new_col = new_symbols + remaining
        for row in range(4):
            board[row, col] = new_col[row]
    
    return board

@njit
def generate_my_mapping(my_weights):
    """Generate MY1~MY8 to M1~M8 mapping for one spin"""
    my_to_m = np.zeros(8, dtype=np.int32)
    available = np.ones(8, dtype=np.bool_)
    for my_idx in range(8):
        valid_weights = my_weights.copy()
        for m_idx in range(8):
            if not available[m_idx]:
                valid_weights[m_idx] = 0
        m_idx = weighted_choice(valid_weights)
        my_to_m[my_idx] = m_idx
        available[m_idx] = False
    return my_to_m

@njit
def convert_my_symbols(board, my_to_m):
    """Convert my symbols to m symbols using predefined mapping"""
    for row in range(4):
        for col in range(5):
            symbol = board[row, col]
            if 18 <= symbol <= 25:
                my_idx = symbol - 18
                m_idx = my_to_m[my_idx]
                board[row, col] = 2 + m_idx
            elif 26 <= symbol <= 33:
                my_idx = symbol - 26
                m_idx = my_to_m[my_idx]
                board[row, col] = 10 + m_idx
    return board

@njit
def count_c1(board):
    """Count C1 symbols on board"""
    count = 0
    for row in range(4):
        for col in range(5):
            if board[row, col] == 1:
                count += 1
    return count

@njit
def play_one_spin(symbols, weights, drop_weights_list, linkpoint, my_weights, ex_weights):
    """Execute one game spin"""
    board = generate_initial_board(symbols, weights)
    my_to_m = generate_my_mapping(my_weights)
    board = convert_my_symbols(board, my_to_m)
    
    total_win = 0
    cascade_count = 0
    max_cascades = 50
    cascade_wins = np.zeros(4, dtype=np.int32)
    golden_appeared = 0
    golden_eliminated = 0
    has_wild1 = 0
    wild1_combos = np.zeros(5, dtype=np.int32)
    initial_symbol_wins = np.zeros(8, dtype=np.int32)  # Initial board elimination M1~M8 scores
    subsequent_symbol_wins = np.zeros(8, dtype=np.int32)  # Subsequent elimination M1~M8 scores
    scatter_appeared = 0  # Whether scatter has appeared
    
    # Check if scatter (C1) exists on initial board
    for row in range(4):
        for col in range(5):
            if board[row, col] == 1:
                scatter_appeared = 1
                break
        if scatter_appeared:
            break
    
    while cascade_count < max_cascades:
        for row in range(4):
            for col in range(5):
                symbol = board[row, col]
                if (10 <= symbol <= 17) or (26 <= symbol <= 33):
                    golden_appeared += 1
        
        board, exploded_cols = trigger_wild1_explosion(board)
        
        wild1_count = 0
        if exploded_cols[1]:
            wild1_count += 1
        if exploded_cols[2]:
            wild1_count += 1
        if exploded_cols[3]:
            wild1_count += 1
        
        if wild1_count == 1:
            wild1_combos[0] += 1
        elif wild1_count == 3:
            wild1_combos[4] += 1
        elif wild1_count == 2:
            if exploded_cols[1] and exploded_cols[2]:
                wild1_combos[1] += 1
            elif exploded_cols[2] and exploded_cols[3]:
                wild1_combos[2] += 1
            elif exploded_cols[1] and exploded_cols[3]:
                wild1_combos[3] += 1
        
        if np.any(exploded_cols):
            has_wild1 = 1
        
        matches = check_matches(board)
        if not np.any(matches):
            break
        
        for row in range(4):
            for col in range(5):
                if matches[row, col]:
                    symbol = board[row, col]
                    if (10 <= symbol <= 17) or (26 <= symbol <= 33):
                        golden_eliminated += 1
        
        win, symbol_wins = calculate_win(board, matches, linkpoint, exploded_cols)
        
        if cascade_count == 0:
            multiplier = 1
        elif cascade_count == 1:
            multiplier = 2
        elif cascade_count == 2:
            multiplier = 3
        else:
            multiplier = 5
        
        win_with_multiplier = win * multiplier
        total_win += win_with_multiplier
        cascade_idx = min(cascade_count, 3)
        cascade_wins[cascade_idx] += win_with_multiplier
        
        # Accumulate symbol scores (with multiplier) - separate initial and subsequent
        if cascade_count == 0:
            for i in range(8):
                initial_symbol_wins[i] += symbol_wins[i] * multiplier
        else:
            for i in range(8):
                subsequent_symbol_wins[i] += symbol_wins[i] * multiplier
        
        drop_idx = min(cascade_count, 3)
        drop_weights = drop_weights_list[drop_idx]
        board = apply_gravity_and_fill(board, matches, drop_weights, cascade_count, ex_weights)
        board = convert_my_symbols(board, my_to_m)
        cascade_count += 1
    
    c1_count = np.sum(board == 1)
    return total_win, cascade_count, c1_count, cascade_wins, golden_appeared, golden_eliminated, has_wild1, wild1_combos, initial_symbol_wins, subsequent_symbol_wins, scatter_appeared

@njit
def play_one_spin_freegame(symbols, weights, drop_weights_list, linkpoint, my_weights, ex_weights, cascade_multipliers):
    """Execute one FreeGame spin"""
    board = generate_initial_board(symbols, weights)
    my_to_m = generate_my_mapping(my_weights)
    board = convert_my_symbols(board, my_to_m)
    
    total_win = 0
    cascade_count = 0
    max_cascades = 50
    wild1_combos = np.zeros(5, dtype=np.int32)
    initial_symbol_wins = np.zeros(8, dtype=np.int32)  # Initial board elimination M1~M8 scores
    subsequent_symbol_wins = np.zeros(8, dtype=np.int32)  # Subsequent elimination M1~M8 scores
    scatter_appeared = 0  # Whether scatter has appeared
    
    # Check if scatter (C1) exists on initial board
    for row in range(4):
        for col in range(5):
            if board[row, col] == 1:
                scatter_appeared = 1
                break
        if scatter_appeared:
            break
    
    while cascade_count < max_cascades:
        board, exploded_cols = trigger_wild1_explosion(board)
        
        wild1_count = 0
        if exploded_cols[1]:
            wild1_count += 1
        if exploded_cols[2]:
            wild1_count += 1
        if exploded_cols[3]:
            wild1_count += 1
        
        if wild1_count == 1:
            wild1_combos[0] += 1
        elif wild1_count == 3:
            wild1_combos[4] += 1
        elif wild1_count == 2:
            if exploded_cols[1] and exploded_cols[2]:
                wild1_combos[1] += 1
            elif exploded_cols[2] and exploded_cols[3]:
                wild1_combos[2] += 1
            elif exploded_cols[1] and exploded_cols[3]:
                wild1_combos[3] += 1
        
        matches = check_matches(board)
        if not np.any(matches):
            break
        
        win, symbol_wins = calculate_win_freegame(board, matches, linkpoint, exploded_cols)
        multiplier_idx = min(cascade_count, 3)
        multiplier = cascade_multipliers[multiplier_idx]
        total_win += win * multiplier
        
        # Accumulate symbol scores (with multiplier) - separate initial and subsequent
        if cascade_count == 0:
            for i in range(8):
                initial_symbol_wins[i] += symbol_wins[i] * multiplier
        else:
            for i in range(8):
                subsequent_symbol_wins[i] += symbol_wins[i] * multiplier
        
        drop_idx = min(cascade_count, 3)
        drop_weights = drop_weights_list[drop_idx]
        board = apply_gravity_and_fill(board, matches, drop_weights, cascade_count, ex_weights)
        board = convert_my_symbols(board, my_to_m)
        cascade_count += 1
    
    return total_win, cascade_count, board, wild1_combos, initial_symbol_wins, subsequent_symbol_wins, scatter_appeared

@njit
def run_simulation(num_spins, basewheel, all_symbols, all_weights, all_drop_weights_list, 
                   linkpoint, all_my_weights, all_ex_weights):
    """Run N simulations"""
    wins = np.zeros(num_spins, dtype=np.int32)
    cascades = np.zeros(num_spins, dtype=np.int32)
    c1_counts = np.zeros(num_spins, dtype=np.int32)
    cascade_wins_matrix = np.zeros((num_spins, 4), dtype=np.int32)
    golden_stats_matrix = np.zeros((num_spins, 2), dtype=np.int32)
    wild1_triggered = np.zeros(num_spins, dtype=np.int32)
    wild1_combos_matrix = np.zeros((num_spins, 5), dtype=np.int32)
    
    game_set_indices = np.zeros(num_spins, dtype=np.int32)
    for i in range(num_spins):
        game_set_indices[i] = weighted_choice(basewheel)
    
    for i in range(num_spins):
        game_set_idx = game_set_indices[i]
        symbols = all_symbols[game_set_idx]
        weights = all_weights[game_set_idx]
        drop_weights_list = all_drop_weights_list[game_set_idx]
        my_weights = all_my_weights[game_set_idx]
        ex_weights = all_ex_weights[game_set_idx]
        
        result = play_one_spin(symbols, weights, drop_weights_list, 
                              linkpoint, my_weights, ex_weights)
        wins[i] = result[0]
        cascades[i] = result[1]
        c1_counts[i] = result[2]
        cascade_wins_matrix[i, 0] = result[3][0]
        cascade_wins_matrix[i, 1] = result[3][1]
        cascade_wins_matrix[i, 2] = result[3][2]
        cascade_wins_matrix[i, 3] = result[3][3]
        golden_stats_matrix[i, 0] = result[4]
        golden_stats_matrix[i, 1] = result[5]
        wild1_triggered[i] = result[6]
        wild1_combos_matrix[i, 0] = result[7][0]
        wild1_combos_matrix[i, 1] = result[7][1]
        wild1_combos_matrix[i, 2] = result[7][2]
        wild1_combos_matrix[i, 3] = result[7][3]
        wild1_combos_matrix[i, 4] = result[7][4]
        # result[8] = total_symbol_wins, result[9] = scatter_appeared (not used here)
    
    return wins, cascades, c1_counts, cascade_wins_matrix, golden_stats_matrix, wild1_triggered, wild1_combos_matrix

# ============================================================================
# Multiprocess Parallel Functions
# ============================================================================

def basegame_parallel(n, game_set=None, verbose=True, num_workers=None, c=1, _force_multiprocess=False):
    """
    Execute n base game simulations (multiprocess parallel version)
    
    Auto-detect running environment:
    - In Interactive environment with num_workers > 1, use subprocess method
    - In normal script or num_workers == 1, use standard multiprocessing
    
    Args:
        n: Number of simulations
        game_set: Specify which dataset to use (1-6), None means randomly select for each spin using basewheel
        verbose: Whether to display statistics
        num_workers: Number of processes to use, None means use CPU core count
        c: Number of batches, for avoiding memory issues in large-scale simulations (default 1, no batching)
        _force_multiprocess: Internal parameter, force using multiprocessing (for subprocess calls)
    
    Returns:
        wins: numpy array [n] - Total score per spin
        c1_counts: numpy array [n] - C1 count on final board per spin
        cascade_wins_matrix: numpy array [n][4] - Score per cascade stage per spin
        golden_stats_matrix: numpy array [n][2] - [appeared count, eliminated count]
        cascades: numpy array [n] - Cascade count per spin
        wild1_triggered: numpy array [n] - Whether WILD1 was triggered per spin
        wild1_combos_matrix: numpy array [n][5] - WILD1 column combo count per spin
    """
    if num_workers is None:
        num_workers = cpu_count()
    
    # If c > 1, batch run
    if c > 1:
        batch_size = n // c
        remaining = n % c
        
        all_wins = []
        all_c1_counts = []
        all_cascade_wins = []
        all_golden_stats = []
        all_cascades = []
        all_wild1_triggered = []
        all_wild1_combos = []
        
        if verbose:
            print(f"Batch run: Total {n:,} simulations, divided into {c} batches")
            overall_start_time = time.time()
        
        for i in range(c):
            current_batch = batch_size + (1 if i < remaining else 0)
            if verbose:
                print(f"\n=== Batch {i+1}/{c}: {current_batch:,} simulations ===")
            
            # Recursive call with c=1 to avoid infinite recursion
            wins, c1_counts, cascade_wins, golden_stats, cascades, wild1_triggered, wild1_combos = \
                basegame_parallel(current_batch, game_set=game_set, verbose=verbose, 
                                num_workers=num_workers, c=1, _force_multiprocess=_force_multiprocess)
            
            all_wins.append(wins)
            all_c1_counts.append(c1_counts)
            all_cascade_wins.append(cascade_wins)
            all_golden_stats.append(golden_stats)
            all_cascades.append(cascades)
            all_wild1_triggered.append(wild1_triggered)
            all_wild1_combos.append(wild1_combos)
        
        # Merge all batch results
        final_wins = np.concatenate(all_wins)
        final_c1_counts = np.concatenate(all_c1_counts)
        final_cascade_wins = np.vstack(all_cascade_wins)
        final_golden_stats = np.vstack(all_golden_stats)
        final_cascades = np.concatenate(all_cascades)
        final_wild1_triggered = np.concatenate(all_wild1_triggered)
        final_wild1_combos = np.vstack(all_wild1_combos)
        
        if verbose:
            overall_end_time = time.time()
            overall_elapsed = overall_end_time - overall_start_time
            print(f"\n{'='*60}")
            print(f"All batches completed!")
            print(f"Total simulations: {n:,}")
            print(f"Total time: {overall_elapsed:.2f}s")
            print(f"Simulations per second: {n/overall_elapsed:,.0f}")
            print(f"Total score: {np.sum(final_wins):,}")
            print(f"Average score: {np.mean(final_wins):.2f}")
            print(f"Max score: {np.max(final_wins):,}")
            print(f"Min score: {np.min(final_wins):,}")
            print(f"Average C1 count: {np.mean(final_c1_counts):.2f}")
            print(f"WILD1 trigger rate: {np.sum(final_wild1_triggered)/n*100:.2f}%")
            print(f"{'='*60}")
        
        return final_wins, final_c1_counts, final_cascade_wins, final_golden_stats, \
               final_cascades, final_wild1_triggered, final_wild1_combos
    
    # In Interactive environment with multiprocess needs, use subprocess method
    if not _force_multiprocess and _is_interactive() and num_workers > 1:
        return _run_via_subprocess('basegame', {
            'n': n,
            'game_set': game_set,
            'verbose': verbose,
            'num_workers': num_workers
        })
    
    # Prepare data
    data = _get_game_data()
    linkpoint = data['linkpoint']
    
    if game_set is not None:
        # Specified parameter set
        symbols = data[f'baseGameSymbol{game_set}']
        weights = data[f'baseGameSymbolWeight{game_set}']
        my_weights = data[f'baseGameMY{game_set}']
        ex_weights = data[f'baseGameEX{game_set}']
        
        drop_weights_list = np.zeros((4, 5, 34), dtype=np.int32)
        for i in range(4):
            drop_weights_list[i] = data[f'BaseGameDrop{game_set}_{i+1}']
        
        all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        all_my_weights = np.zeros((6, 8), dtype=np.int32)
        all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        all_symbols[game_set-1] = symbols
        all_weights[game_set-1] = weights
        all_drop_weights_list[game_set-1] = drop_weights_list
        all_my_weights[game_set-1] = my_weights
        all_ex_weights[game_set-1] = ex_weights
        
        basewheel = np.zeros(6, dtype=np.int32)
        basewheel[game_set-1] = 1
        
        if verbose:
            print(f"Execute {n:,} base game simulations (dataset {game_set}) - using {num_workers} processes")
    else:
        # Random selection per spin using basewheel
        all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        all_my_weights = np.zeros((6, 8), dtype=np.int32)
        all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        for game_idx in range(6):
            game_num = game_idx + 1
            all_symbols[game_idx] = data[f'baseGameSymbol{game_num}']
            all_weights[game_idx] = data[f'baseGameSymbolWeight{game_num}']
            all_my_weights[game_idx] = data[f'baseGameMY{game_num}']
            all_ex_weights[game_idx] = data[f'baseGameEX{game_num}']
            
            for i in range(4):
                all_drop_weights_list[game_idx][i] = data[f'BaseGameDrop{game_num}_{i+1}']
        
        basewheel = data['basewheel']
        
        if verbose:
            print(f"Execute {n:,} base game simulations (random selection per spin using basewheel) - using {num_workers} processes")
    
    if verbose:
        start_time = time.time()
    
    # If using only 1 process, call single-process version directly (avoid multiprocessing issues)
    if num_workers == 1:
        if verbose:
            print("  (Using single-process mode)")
        wins, cascades, c1_counts, cascade_wins_matrix, golden_stats_matrix, wild1_triggered, wild1_combos_matrix = \
            run_simulation(n, basewheel, all_symbols, all_weights, 
                          all_drop_weights_list, linkpoint, all_my_weights, all_ex_weights)
    else:
        # Multi-process mode
        # Split tasks to multiple processes
        batch_size = max(1, n // num_workers)
        batches = []
        remaining = n
        
        for i in range(num_workers):
            if i == num_workers - 1:
                # Last process handles all remaining tasks
                batch_n = remaining
            else:
                batch_n = batch_size
                remaining -= batch_n
            
            if batch_n > 0:
                batches.append(batch_n)
        
        # Create process pool and execute
        worker_func = partial(
            _run_basegame_batch,
            basewheel=basewheel,
            all_symbols=all_symbols,
            all_weights=all_weights,
            all_drop_weights_list=all_drop_weights_list,
            linkpoint=linkpoint,
            all_my_weights=all_my_weights,
            all_ex_weights=all_ex_weights
        )
        
        with Pool(processes=num_workers) as pool:
            results = pool.map(worker_func, batches)
        
        # Merge results
        wins = np.concatenate([r[0] for r in results])
        cascades = np.concatenate([r[1] for r in results])
        c1_counts = np.concatenate([r[2] for r in results])
        cascade_wins_matrix = np.vstack([r[3] for r in results])
        golden_stats_matrix = np.vstack([r[4] for r in results])
        wild1_triggered = np.concatenate([r[5] for r in results])
        wild1_combos_matrix = np.vstack([r[6] for r in results])
    
    if verbose:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Simulation complete, duration: {elapsed:.2f}s")
        print(f"Simulations per second: {n/elapsed:,.0f}")
        print(f"Total score: {np.sum(wins):,}")
        print(f"Average score: {np.mean(wins):.2f}")
        print(f"Max score: {np.max(wins):,}")
        print(f"Min score: {np.min(wins):,}")
        print(f"Average C1 count: {np.mean(c1_counts):.2f}")
        print(f"WILD1 trigger rate: {np.sum(wild1_triggered)/n*100:.2f}%")
    
    return wins, c1_counts, cascade_wins_matrix, golden_stats_matrix, cascades, wild1_triggered, wild1_combos_matrix


def _run_basegame_batch(batch_n, basewheel, all_symbols, all_weights, 
                        all_drop_weights_list, linkpoint, all_my_weights, all_ex_weights):
    """
    Execute a batch of base game simulations in a single process
    
    Returns: (wins, cascades, c1_counts, cascade_wins_matrix, golden_stats_matrix, wild1_triggered, wild1_combos_matrix)
    """
    return run_simulation(
        batch_n, basewheel, all_symbols, all_weights,
        all_drop_weights_list, linkpoint, all_my_weights, all_ex_weights
    )


def freegame_parallel(n, cascade_multipliers=None, game_set=None, verbose=True, num_workers=None, c=1, _force_multiprocess=False):
    """
    Execute n Free Game simulations (multiprocess parallel version)
    
    Auto-detect running environment:
    - In Interactive environment with num_workers > 1, use subprocess method
    - In normal script or num_workers == 1, use standard multiprocessing
    
    Args:
        n: Number of executions
        cascade_multipliers: Cascade multipliers [4] - [0th, 1st, 2nd, 3rd+], default [2,4,6,10]
        game_set: Specify which dataset to use (1-6), None means randomly select per spin using Freewheel
        verbose: Whether to display statistics
        num_workers: Number of processes to use, None means use CPU core count
        c: Number of batches, for avoiding memory issues in large-scale simulations (default 1, no batching)
        _force_multiprocess: Internal parameter, force using multiprocessing
    
    Returns:
        wins: numpy array [n] - Total score per session
        spins: numpy array [n] - Total spin count per session
        cascades_matrix: numpy array [n][50] - Cascade count per spin per session
        wild1_combos_matrix: numpy array [n][5] - WILD1 combo count per session
    """
    if num_workers is None:
        num_workers = cpu_count()
    
    # Default cascade multipliers
    if cascade_multipliers is None:
        cascade_multipliers = np.array([2, 4, 6, 10], dtype=np.int32)
    else:
        cascade_multipliers = np.array(cascade_multipliers, dtype=np.int32)
    
    # If c > 1, batch run
    if c > 1:
        batch_size = n // c
        remaining = n % c
        
        all_wins = []
        all_spins = []
        all_cascades = []
        all_wild1_combos = []
        
        if verbose:
            print(f"Batch run: Total {n:,} simulations, divided into {c} batches")
            overall_start_time = time.time()
        
        for i in range(c):
            current_batch = batch_size + (1 if i < remaining else 0)
            if verbose:
                print(f"\n=== Batch {i+1}/{c}: {current_batch:,} simulations ===")
            
            # Recursive call with c=1 to avoid infinite recursion
            wins, spins, cascades, wild1_combos = \
                freegame_parallel(current_batch, cascade_multipliers=cascade_multipliers, 
                                game_set=game_set, verbose=verbose, num_workers=num_workers, 
                                c=1, _force_multiprocess=_force_multiprocess)
            
            all_wins.append(wins)
            all_spins.append(spins)
            all_cascades.append(cascades)
            all_wild1_combos.append(wild1_combos)
        
        # Merge all batch results
        final_wins = np.concatenate(all_wins)
        final_spins = np.concatenate(all_spins)
        final_cascades = np.vstack(all_cascades)
        final_wild1_combos = np.vstack(all_wild1_combos)
        
        if verbose:
            overall_end_time = time.time()
            overall_elapsed = overall_end_time - overall_start_time
            print(f"\n{'='*60}")
            print(f"All batches completed!")
            print(f"Total simulations: {n:,}")
            print(f"Total time: {overall_elapsed:.2f}s")
            print(f"Simulations per second: {n/overall_elapsed:,.0f}")
            print(f"Total score: {np.sum(final_wins):,}")
            print(f"Average score: {np.mean(final_wins):.2f}")
            print(f"Max score: {np.max(final_wins):,}")
            print(f"Min score: {np.min(final_wins):,}")
            print(f"Average spin count: {np.mean(final_spins):.2f}")
            print(f"{'='*60}")
        
        return final_wins, final_spins, final_cascades, final_wild1_combos
    
    # In Interactive environment with multiprocess needs, use subprocess method
    if not _force_multiprocess and _is_interactive() and num_workers > 1:
        return _run_via_subprocess('freegame', {
            'n': n,
            'cascade_multipliers': cascade_multipliers.tolist() if isinstance(cascade_multipliers, np.ndarray) else cascade_multipliers,
            'game_set': game_set,
            'verbose': verbose,
            'num_workers': num_workers
        })
    
    data = _get_game_data()
    linkpoint = data['linkpoint']
    
    # Prepare parameters
    if game_set is not None:
        # Specified parameter set
        symbols = data[f'FreeGameSymbol{game_set}']
        weights = data[f'FreeGameSymbolWeight{game_set}']
        my_weights = data[f'FreeGameMY{game_set}']
        ex_weights = data[f'FreeGameEX{game_set}']
        
        drop_weights_list = np.zeros((4, 5, 34), dtype=np.int32)
        for i in range(4):
            drop_weights_list[i] = data[f'FreeGameDrop{game_set}_{i+1}']
        
        all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        all_my_weights = np.zeros((6, 8), dtype=np.int32)
        all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        all_symbols[game_set-1] = symbols
        all_weights[game_set-1] = weights
        all_drop_weights_list[game_set-1] = drop_weights_list
        all_my_weights[game_set-1] = my_weights
        all_ex_weights[game_set-1] = ex_weights
        
        freewheel = np.zeros(6, dtype=np.int32)
        freewheel[game_set-1] = 1
        
        if verbose:
            print(f"Execute {n:,} Free Game simulations (dataset {game_set}) - using {num_workers} processes")
    else:
        # Random selection per spin using Freewheel
        all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        all_my_weights = np.zeros((6, 8), dtype=np.int32)
        all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        for game_idx in range(6):
            game_num = game_idx + 1
            all_symbols[game_idx] = data[f'FreeGameSymbol{game_num}']
            all_weights[game_idx] = data[f'FreeGameSymbolWeight{game_num}']
            all_my_weights[game_idx] = data[f'FreeGameMY{game_num}']
            all_ex_weights[game_idx] = data[f'FreeGameEX{game_num}']
            
            for i in range(4):
                all_drop_weights_list[game_idx][i] = data[f'FreeGameDrop{game_num}_{i+1}']
        
        freewheel = data['Freewheel']
        
        if verbose:
            print(f"Execute {n:,} Free Game simulations (random selection per spin using Freewheel) - using {num_workers} processes")
    
    if verbose:
        start_time = time.time()
    
    # If using only 1 process, call single-process version directly (avoid multiprocessing issues)
    if num_workers == 1:
        if verbose:
            print("  (Using single-process mode)")
        wins, spins, cascades_matrix, wild1_combos_matrix = \
            _run_freegame_batch(n, freewheel, all_symbols, all_weights,
                               all_drop_weights_list, linkpoint, all_my_weights,
                               all_ex_weights, cascade_multipliers)
    else:
        # Multi-process mode
        # Split tasks to multiple processes
        batch_size = max(1, n // num_workers)
        batches = []
        remaining = n
        
        for i in range(num_workers):
            if i == num_workers - 1:
                batch_n = remaining
            else:
                batch_n = batch_size
                remaining -= batch_n
            
            if batch_n > 0:
                batches.append(batch_n)
        
        # Create process pool and execute
        worker_func = partial(
            _run_freegame_batch,
            freewheel=freewheel,
            all_symbols=all_symbols,
            all_weights=all_weights,
            all_drop_weights_list=all_drop_weights_list,
            linkpoint=linkpoint,
            all_my_weights=all_my_weights,
            all_ex_weights=all_ex_weights,
            cascade_multipliers=cascade_multipliers
        )
        
        with Pool(processes=num_workers) as pool:
            results = pool.map(worker_func, batches)
        
        # Merge results
        wins = np.concatenate([r[0] for r in results])
        spins = np.concatenate([r[1] for r in results])
        cascades_matrix = np.vstack([r[2] for r in results])
        wild1_combos_matrix = np.vstack([r[3] for r in results])
    
    if verbose:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Simulation complete, duration: {elapsed:.2f}s")
        print(f"Simulations per second: {n/elapsed:,.2f}")
        print(f"Total score: {np.sum(wins):,}")
        print(f"Average score: {np.mean(wins):.2f}")
        print(f"Max score: {np.max(wins):,}")
        print(f"Min score: {np.min(wins):,}")
        print(f"Average spin count: {np.mean(spins):.2f}")
        print(f"Max spin count: {np.max(spins)}")
        print(f"Min spin count: {np.min(spins)}")
    
    return wins, spins, cascades_matrix, wild1_combos_matrix


def _run_freegame_batch(batch_n, freewheel, all_symbols, all_weights,
                        all_drop_weights_list, linkpoint, all_my_weights, 
                        all_ex_weights, cascade_multipliers):
    """
    Execute a batch of free game simulations in a single process
    
    Returns: (wins, spins, cascades_matrix, wild1_combos_matrix)
    """
    wins = np.zeros(batch_n, dtype=np.int32)
    spins = np.zeros(batch_n, dtype=np.int32)
    cascades_matrix = np.full((batch_n, 50), -1, dtype=np.int32)
    wild1_combos_matrix = np.zeros((batch_n, 5), dtype=np.int32)
    
    for fg_idx in range(batch_n):
        # Initial settings for each Free Game session
        remaining_spins = 10
        fg_total_spins = 0
        fg_total_win = 0
        
        # Execute this Free Game session
        while remaining_spins > 0 and fg_total_spins < 50:
            # Select parameter set
            game_set_idx = weighted_choice(freewheel)
            
            symbols = all_symbols[game_set_idx]
            weights = all_weights[game_set_idx]
            drop_weights_list = all_drop_weights_list[game_set_idx]
            my_weights = all_my_weights[game_set_idx]
            ex_weights = all_ex_weights[game_set_idx]
            
            # Execute one spin
            win, cascade, final_board, wild1_combos, init_sym_wins, subseq_sym_wins, scatter_appeared = play_one_spin_freegame(
                symbols, weights, drop_weights_list,
                linkpoint, my_weights, ex_weights, cascade_multipliers
            )
            
            fg_total_win += win
            cascades_matrix[fg_idx, fg_total_spins] = cascade
            wild1_combos_matrix[fg_idx] += wild1_combos
            fg_total_spins += 1
            remaining_spins -= 1
            
            # Check for retrigger
            c1_count = count_c1(final_board)
            if c1_count >= 3:
                remaining_spins += 5
        
        wins[fg_idx] = fg_total_win
        spins[fg_idx] = fg_total_spins
    
    return wins, spins, cascades_matrix, wild1_combos_matrix


# ============================================================================
# Full Game Parallel Functions (Base Game + Free Game Complete Flow)
# ============================================================================

def fullgame_parallel(n, cascade_multipliers=None, game_set=None, basewheel=None, freewheel=None, verbose=True, num_workers=None, c=1, _force_multiprocess=False):
    """
    Execute n complete game simulations (Base Game + triggered Free Game)
    
    Complete game flow:
    1. Execute one Base Game spin
    2. Check C1 count on final board
    3. If C1 >= 3, trigger Free Game (initial 10 spins)
    4. In Free Game if C1 >= 3, retrigger adds 5 spins
    
    Args:
        n: Number of simulations
        cascade_multipliers: Free Game cascade multipliers [4], default [2,4,6,10]
        game_set: Specify which dataset to use (1-6), None means randomly select using basewheel/freewheel
        basewheel: Base Game parameter set weights [6], None uses default from data.js
        freewheel: Free Game parameter set weights [6], None uses default from data.js
        verbose: Whether to display statistics
        num_workers: Number of processes to use, None means use CPU core count
        c: Number of batches (default 1, no batching)
        _force_multiprocess: Internal parameter, force using multiprocessing
    
    Returns:
        stats: dict containing the following statistics:
            - total_win: int - Total score
            - total_spins: int - Total spin count (BG + FG all spins)
            - bg_win: int - Base Game total score
            - bg_spins: int - Base Game count (equals n)
            - fg_win: int - Free Game total score
            - fg_spins: int - Free Game total spin count
            - fg_times: int - Free Game trigger count
            - scatter_count: int - Scatter appearance count (increments per spin appearance)
            - bg_initial_symbol_wins: numpy array [8] - BG initial cascade symbol (M1~M8) scores
            - bg_subsequent_symbol_wins: numpy array [8] - BG subsequent cascade symbol (M1~M8) scores
            - fg_initial_symbol_wins: numpy array [8] - FG initial cascade symbol (M1~M8) scores
            - fg_subsequent_symbol_wins: numpy array [8] - FG subsequent cascade symbol (M1~M8) scores
    """
    if num_workers is None:
        num_workers = cpu_count()
    
    if cascade_multipliers is None:
        cascade_multipliers = np.array([2, 4, 6, 10], dtype=np.int32)
    else:
        cascade_multipliers = np.array(cascade_multipliers, dtype=np.int32)
    
    # Batch run
    if c > 1:
        batch_size = n // c
        remaining = n % c
        
        # Cumulative statistics
        total_win = 0
        bg_win = 0
        fg_win = 0
        fg_spins = 0
        fg_times = 0
        scatter_count = 0
        bg_initial_symbol_wins = np.zeros(8, dtype=np.int64)
        bg_subsequent_symbol_wins = np.zeros(8, dtype=np.int64)
        fg_initial_symbol_wins = np.zeros(8, dtype=np.int64)
        fg_subsequent_symbol_wins = np.zeros(8, dtype=np.int64)
        
        if verbose:
            print(f"Batch run: Total {n:,} complete game simulations, divided into {c} batches")
            overall_start_time = time.time()
        
        for i in range(c):
            current_batch = batch_size + (1 if i < remaining else 0)
            if verbose:
                print(f"\n=== Batch {i+1}/{c}: {current_batch:,} simulations ===")
            
            stats = fullgame_parallel(current_batch, cascade_multipliers=cascade_multipliers,
                                game_set=game_set, basewheel=basewheel, freewheel=freewheel,
                                verbose=verbose, num_workers=num_workers,
                                c=1, _force_multiprocess=_force_multiprocess)
            
            total_win += stats['total_win']
            bg_win += stats['bg_win']
            fg_win += stats['fg_win']
            fg_spins += stats['fg_spins']
            fg_times += stats['fg_times']
            scatter_count += stats['scatter_count']
            bg_initial_symbol_wins += stats['bg_initial_symbol_wins']
            bg_subsequent_symbol_wins += stats['bg_subsequent_symbol_wins']
            fg_initial_symbol_wins += stats['fg_initial_symbol_wins']
            fg_subsequent_symbol_wins += stats['fg_subsequent_symbol_wins']
        
        total_spins = n + fg_spins
        
        final_stats = {
            'total_win': total_win,
            'total_spins': total_spins,
            'bg_win': bg_win,
            'bg_spins': n,
            'fg_win': fg_win,
            'fg_spins': fg_spins,
            'fg_times': fg_times,
            'scatter_count': scatter_count,
            'bg_initial_symbol_wins': bg_initial_symbol_wins,
            'bg_subsequent_symbol_wins': bg_subsequent_symbol_wins,
            'fg_initial_symbol_wins': fg_initial_symbol_wins,
            'fg_subsequent_symbol_wins': fg_subsequent_symbol_wins
        }
        
        if verbose:
            overall_end_time = time.time()
            overall_elapsed = overall_end_time - overall_start_time
            print(f"\n{'='*60}")
            print(f"All batches completed!")
            print(f"Total simulations: {n:,}")
            print(f"Total time: {overall_elapsed:.2f}s")
            print(f"Simulations per second: {n/overall_elapsed:,.0f}")
            _print_fullgame_stats(final_stats, n)
            print(f"{'='*60}")
        
        return final_stats
    
    # Interactive environment uses subprocess
    if not _force_multiprocess and _is_interactive() and num_workers > 1:
        return _run_via_subprocess('fullgame', {
            'n': n,
            'cascade_multipliers': cascade_multipliers.tolist() if isinstance(cascade_multipliers, np.ndarray) else cascade_multipliers,
            'game_set': game_set,
            'basewheel': basewheel.tolist() if isinstance(basewheel, np.ndarray) else basewheel,
            'freewheel': freewheel.tolist() if isinstance(freewheel, np.ndarray) else freewheel,
            'verbose': verbose,
            'num_workers': num_workers
        })
    
    # Prepare data
    data = _get_game_data()
    linkpoint = data['linkpoint']
    
    # Prepare Base Game parameters
    if game_set is not None:
        bg_all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        bg_all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        bg_all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        bg_all_my_weights = np.zeros((6, 8), dtype=np.int32)
        bg_all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        bg_all_symbols[game_set-1] = data[f'baseGameSymbol{game_set}']
        bg_all_weights[game_set-1] = data[f'baseGameSymbolWeight{game_set}']
        bg_all_my_weights[game_set-1] = data[f'baseGameMY{game_set}']
        bg_all_ex_weights[game_set-1] = data[f'baseGameEX{game_set}']
        for i in range(4):
            bg_all_drop_weights_list[game_set-1][i] = data[f'BaseGameDrop{game_set}_{i+1}']
        
        basewheel_arr = np.zeros(6, dtype=np.int32)
        basewheel_arr[game_set-1] = 1
        
        # Free Game parameters
        fg_all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        fg_all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        fg_all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        fg_all_my_weights = np.zeros((6, 8), dtype=np.int32)
        fg_all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        fg_all_symbols[game_set-1] = data[f'FreeGameSymbol{game_set}']
        fg_all_weights[game_set-1] = data[f'FreeGameSymbolWeight{game_set}']
        fg_all_my_weights[game_set-1] = data[f'FreeGameMY{game_set}']
        fg_all_ex_weights[game_set-1] = data[f'FreeGameEX{game_set}']
        for i in range(4):
            fg_all_drop_weights_list[game_set-1][i] = data[f'FreeGameDrop{game_set}_{i+1}']
        
        freewheel_arr = np.zeros(6, dtype=np.int32)
        freewheel_arr[game_set-1] = 1
        
        if verbose:
            print(f"Execute {n:,} complete game simulations (dataset {game_set}) - using {num_workers} processes")
    else:
        # All parameter sets
        bg_all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        bg_all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        bg_all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        bg_all_my_weights = np.zeros((6, 8), dtype=np.int32)
        bg_all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        fg_all_symbols = np.zeros((6, 5, 150), dtype=np.int32)
        fg_all_weights = np.zeros((6, 5, 150), dtype=np.int32)
        fg_all_drop_weights_list = np.zeros((6, 4, 5, 34), dtype=np.int32)
        fg_all_my_weights = np.zeros((6, 8), dtype=np.int32)
        fg_all_ex_weights = np.zeros((6, 5, 5), dtype=np.int32)
        
        for game_idx in range(6):
            game_num = game_idx + 1
            bg_all_symbols[game_idx] = data[f'baseGameSymbol{game_num}']
            bg_all_weights[game_idx] = data[f'baseGameSymbolWeight{game_num}']
            bg_all_my_weights[game_idx] = data[f'baseGameMY{game_num}']
            bg_all_ex_weights[game_idx] = data[f'baseGameEX{game_num}']
            for i in range(4):
                bg_all_drop_weights_list[game_idx][i] = data[f'BaseGameDrop{game_num}_{i+1}']
            
            fg_all_symbols[game_idx] = data[f'FreeGameSymbol{game_num}']
            fg_all_weights[game_idx] = data[f'FreeGameSymbolWeight{game_num}']
            fg_all_my_weights[game_idx] = data[f'FreeGameMY{game_num}']
            fg_all_ex_weights[game_idx] = data[f'FreeGameEX{game_num}']
            for i in range(4):
                fg_all_drop_weights_list[game_idx][i] = data[f'FreeGameDrop{game_num}_{i+1}']
        
        # Use user-provided weights, or use data.js default values
        if basewheel is not None:
            basewheel_arr = np.array(basewheel, dtype=np.int32)
        else:
            basewheel_arr = np.array(data['basewheel'], dtype=np.int32)
        
        if freewheel is not None:
            freewheel_arr = np.array(freewheel, dtype=np.int32)
        else:
            freewheel_arr = np.array(data['Freewheel'], dtype=np.int32)
        
        if verbose:
            if basewheel is not None or freewheel is not None:
                print(f"Execute {n:,} complete game simulations (using custom weights) - using {num_workers} processes")
                if basewheel is not None:
                    print(f"  basewheel: {basewheel_arr.tolist()}")
                if freewheel is not None:
                    print(f"  freewheel: {freewheel_arr.tolist()}")
            else:
                print(f"Execute {n:,} complete game simulations (random selection using basewheel/freewheel) - using {num_workers} processes")
    
    if verbose:
        start_time = time.time()
    
    if num_workers == 1:
        if verbose:
            print("  (Using single-process mode)")
        stats = _run_fullgame_batch(n, basewheel_arr, freewheel_arr,
                               bg_all_symbols, bg_all_weights, bg_all_drop_weights_list,
                               bg_all_my_weights, bg_all_ex_weights,
                               fg_all_symbols, fg_all_weights, fg_all_drop_weights_list,
                               fg_all_my_weights, fg_all_ex_weights,
                               linkpoint, cascade_multipliers)
    else:
        # Multi-process mode
        batch_size = max(1, n // num_workers)
        batches = []
        remaining = n
        
        for i in range(num_workers):
            if i == num_workers - 1:
                batch_n = remaining
            else:
                batch_n = batch_size
                remaining -= batch_n
            if batch_n > 0:
                batches.append(batch_n)
        
        worker_func = partial(
            _run_fullgame_batch,
            basewheel=basewheel_arr,
            freewheel=freewheel_arr,
            bg_all_symbols=bg_all_symbols,
            bg_all_weights=bg_all_weights,
            bg_all_drop_weights_list=bg_all_drop_weights_list,
            bg_all_my_weights=bg_all_my_weights,
            bg_all_ex_weights=bg_all_ex_weights,
            fg_all_symbols=fg_all_symbols,
            fg_all_weights=fg_all_weights,
            fg_all_drop_weights_list=fg_all_drop_weights_list,
            fg_all_my_weights=fg_all_my_weights,
            fg_all_ex_weights=fg_all_ex_weights,
            linkpoint=linkpoint,
            cascade_multipliers=cascade_multipliers
        )
        
        # Use imap_unordered to accumulate results, avoiding memory issues from collecting all results at once
        total_win = 0
        bg_win = 0
        fg_win = 0
        fg_spins = 0
        fg_times = 0
        scatter_count = 0
        bg_initial_symbol_wins = np.zeros(8, dtype=np.int64)
        bg_subsequent_symbol_wins = np.zeros(8, dtype=np.int64)
        fg_initial_symbol_wins = np.zeros(8, dtype=np.int64)
        fg_subsequent_symbol_wins = np.zeros(8, dtype=np.int64)
        
        with Pool(processes=num_workers) as pool:
            for r in pool.imap_unordered(worker_func, batches):
                total_win += r['total_win']
                bg_win += r['bg_win']
                fg_win += r['fg_win']
                fg_spins += r['fg_spins']
                fg_times += r['fg_times']
                scatter_count += r['scatter_count']
                bg_initial_symbol_wins += r['bg_initial_symbol_wins']
                bg_subsequent_symbol_wins += r['bg_subsequent_symbol_wins']
                fg_initial_symbol_wins += r['fg_initial_symbol_wins']
                fg_subsequent_symbol_wins += r['fg_subsequent_symbol_wins']
        
        stats = {
            'total_win': total_win,
            'total_spins': n + fg_spins,
            'bg_win': bg_win,
            'bg_spins': n,
            'fg_win': fg_win,
            'fg_spins': fg_spins,
            'fg_times': fg_times,
            'scatter_count': scatter_count,
            'bg_initial_symbol_wins': bg_initial_symbol_wins,
            'bg_subsequent_symbol_wins': bg_subsequent_symbol_wins,
            'fg_initial_symbol_wins': fg_initial_symbol_wins,
            'fg_subsequent_symbol_wins': fg_subsequent_symbol_wins
        }
    
    if verbose:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"Simulation complete, duration: {elapsed:.2f}s")
        print(f"Simulations per second: {n/elapsed:,.0f}")
        _print_fullgame_stats(stats, n)
    
    return stats


def _print_fullgame_stats(stats, n):
    """Output fullgame statistics"""
    print(f"--- Score Statistics ---")
    print(f"Total score: {stats['total_win']:,}")
    print(f"Total spin count: {stats['total_spins']:,}")
    print(f"Average total score: {stats['total_win']/n:.4f}")
    print(f"--- Base Game ---")
    print(f"BG score: {stats['bg_win']:,}")
    print(f"BG count: {stats['bg_spins']:,}")
    print(f"BG average score: {stats['bg_win']/stats['bg_spins']:.4f}")
    print(f"BG initial cascade symbol scores (M1~M8): {stats['bg_initial_symbol_wins'].tolist()}")
    print(f"BG subsequent cascade symbol scores (M1~M8): {stats['bg_subsequent_symbol_wins'].tolist()}")
    print(f"--- Free Game ---")
    print(f"FG score: {stats['fg_win']:,}")
    print(f"FG spin count: {stats['fg_spins']:,}")
    if stats['fg_spins'] > 0:
        print(f"FG average score (per spin): {stats['fg_win']/stats['fg_spins']:.4f}")
    print(f"FG initial cascade symbol scores (M1~M8): {stats['fg_initial_symbol_wins'].tolist()}")
    print(f"FG subsequent cascade symbol scores (M1~M8): {stats['fg_subsequent_symbol_wins'].tolist()}")
    print(f"--- Scatter Statistics ---")
    print(f"Scatter count: {stats['scatter_count']:,}")
    print(f"Scatter rate: {stats['scatter_count']/stats['total_spins']*100:.4f}%")


def _run_fullgame_batch(batch_n, basewheel, freewheel,
                        bg_all_symbols, bg_all_weights, bg_all_drop_weights_list,
                        bg_all_my_weights, bg_all_ex_weights,
                        fg_all_symbols, fg_all_weights, fg_all_drop_weights_list,
                        fg_all_my_weights, fg_all_ex_weights,
                        linkpoint, cascade_multipliers):
    """
    Execute a batch of complete game simulations in a single process
    Returns statistics summary dict
    """
    total_win = 0
    bg_win = 0
    fg_win = 0
    fg_spins = 0
    fg_times = 0  # FG trigger count
    scatter_count = 0
    bg_initial_symbol_wins = np.zeros(8, dtype=np.int64)  # BG initial cascade
    bg_subsequent_symbol_wins = np.zeros(8, dtype=np.int64)  # BG subsequent cascade
    fg_initial_symbol_wins = np.zeros(8, dtype=np.int64)  # FG initial cascade
    fg_subsequent_symbol_wins = np.zeros(8, dtype=np.int64)  # FG subsequent cascade
    
    for idx in range(batch_n):
        # === Base Game ===
        bg_game_set_idx = weighted_choice(basewheel)
        bg_symbols = bg_all_symbols[bg_game_set_idx]
        bg_weights = bg_all_weights[bg_game_set_idx]
        bg_drop_weights_list = bg_all_drop_weights_list[bg_game_set_idx]
        bg_my_weights = bg_all_my_weights[bg_game_set_idx]
        bg_ex_weights = bg_all_ex_weights[bg_game_set_idx]
        
        bg_result = play_one_spin(bg_symbols, bg_weights, bg_drop_weights_list,
                                  linkpoint, bg_my_weights, bg_ex_weights)
        bg_win_this = bg_result[0]
        c1_count = bg_result[2]
        bg_init_sym_wins = bg_result[8]  # Initial cascade M1~M8 scores
        bg_subseq_sym_wins = bg_result[9]  # Subsequent cascade M1~M8 scores
        bg_scatter_appeared = bg_result[10]  # Whether scatter appeared
        
        bg_win += bg_win_this
        total_win += bg_win_this
        scatter_count += bg_scatter_appeared
        for i in range(8):
            bg_initial_symbol_wins[i] += bg_init_sym_wins[i]
            bg_subsequent_symbol_wins[i] += bg_subseq_sym_wins[i]
        
        # === Free Game (if triggered) ===
        if c1_count >= 3:
            fg_times += 1  # Count FG trigger
            remaining_spins = 10
            fg_total_spins = 0
            fg_total_win = 0
            
            while remaining_spins > 0 and fg_total_spins < 50:
                fg_game_set_idx = weighted_choice(freewheel)
                fg_symbols = fg_all_symbols[fg_game_set_idx]
                fg_weights = fg_all_weights[fg_game_set_idx]
                fg_drop_weights_list = fg_all_drop_weights_list[fg_game_set_idx]
                fg_my_weights = fg_all_my_weights[fg_game_set_idx]
                fg_ex_weights = fg_all_ex_weights[fg_game_set_idx]
                
                win, cascade, final_board, wild1_combos, fg_init_sym_wins, fg_subseq_sym_wins, fg_scatter_appeared = play_one_spin_freegame(
                    fg_symbols, fg_weights, fg_drop_weights_list,
                    linkpoint, fg_my_weights, fg_ex_weights, cascade_multipliers
                )
                
                fg_total_win += win
                fg_total_spins += 1
                remaining_spins -= 1
                scatter_count += fg_scatter_appeared
                
                for i in range(8):
                    fg_initial_symbol_wins[i] += fg_init_sym_wins[i]
                    fg_subsequent_symbol_wins[i] += fg_subseq_sym_wins[i]
                
                # Check for retrigger
                fg_c1_count = count_c1(final_board)
                if fg_c1_count >= 3:
                    remaining_spins += 5
            
            fg_win += fg_total_win
            fg_spins += fg_total_spins
            total_win += fg_total_win
    
    return {
        'total_win': total_win,
        'total_spins': batch_n + fg_spins,
        'bg_win': bg_win,
        'bg_spins': batch_n,
        'fg_win': fg_win,
        'fg_spins': fg_spins,
        'fg_times': fg_times,
        'scatter_count': scatter_count,
        'bg_initial_symbol_wins': bg_initial_symbol_wins,
        'bg_subsequent_symbol_wins': bg_subsequent_symbol_wins,
        'fg_initial_symbol_wins': fg_initial_symbol_wins,
        'fg_subsequent_symbol_wins': fg_subsequent_symbol_wins
    }


# %%
