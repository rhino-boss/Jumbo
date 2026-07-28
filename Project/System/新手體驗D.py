#%%
import numpy as np
import random
from numba import njit

# 倍率權重 (Multiplier Weights)
weights = np.array([
    195166480,
    1221030,
    1983581,
    1400402,
    1843384,
    1261039,
    1254493,
    316037,
    3291012,
    717711,
    892300,
    4477577,
    1124732,
    1457788,
    541256
], dtype=np.float64)

# 倍率 (Multipliers)
multipliers = np.array([
0,
75,
172,
275,
370,
481,
595,
653,
771,
892,
975,
1273,
1785,
2324,
2844,
], dtype=np.float64)

# JP 權重和獎金
JP_weights = np.array([0.9988, 0.001, 0.0002], dtype=np.float64)
JP_values = np.array([0, 1000, 5000], dtype=np.float64)

# 將權重歸一化為概率
weights_prob = weights / weights.sum()
JP_prob = JP_weights / JP_weights.sum()

# 救援獎勵
raise1 = np.array([1500, 1000, 0], dtype=np.float64)  # 第1次救援的獎勵
raise2 = np.array([3000, 1500], dtype=np.float64)  # 第2次救援的獎勵

# 救援觸發閾值（RTP百分比）
tet1 = np.array([50, 70, 100], dtype=np.float64)  # 第1次救援的RTP閾值
tet2 = np.array([65, 85], dtype=np.float64)  # 第2次救援的RTP閾值 
#%%
@njit
def simulate_mode1_core(n_players, n_rounds, multipliers, weights_prob, JP_values, JP_prob):
    """
    使用 Numba 加速的核心模擬函數
    """
    results = np.zeros((n_players, n_rounds), dtype=np.float64)
    
    # 計算累積概率分布
    weights_cumsum = np.cumsum(weights_prob)
    JP_cumsum = np.cumsum(JP_prob)
    
    for player in range(n_players):
        for round_num in range(n_rounds):
            # 按照weights_prob概率抽選multipliers
            rand_val = np.random.random()
            idx = np.searchsorted(weights_cumsum, rand_val)
            multiplier = multipliers[idx]
            
            # 從JP_prob概率抽選JP獎金
            rand_val = np.random.random()
            idx = np.searchsorted(JP_cumsum, rand_val)
            jp_bonus = JP_values[idx]
            
            # 計算該局總分數
            results[player, round_num] = multiplier + jp_bonus
    
    return results

def simulate_mode1(n_players, n_rounds=200):
    """
    模擬模式1: n個玩家各玩200局（無機制）
    
    Parameters:
    -----------
    n_players : int
        玩家數量
    n_rounds : int
        每個玩家的局數 (預設200)
    
    Returns:
    --------
    results : numpy.ndarray
        shape (n_players, n_rounds)，包含每個玩家每局的總分數
    """
    return simulate_mode1_core(n_players, n_rounds, multipliers, weights_prob, JP_values, JP_prob)

def simulate_mode1_with_rescue(n_players, n_rounds=200):
    """
    模擬模式1（含救援機制）
    
    每個玩家隨機在41-60局和140-160局各觸發一次救援機制
    根據前面局數的RTP決定救援分數
    
    救援條件：
    - 第1次救援：使用 tet1 閾值 [60, 80, 100]
      * RTP% < tet1[0] → raise1[0]
      * tet1[0] ≤ RTP% < tet1[1] → raise1[1]
      * tet1[1] ≤ RTP% < tet1[2] → raise1[2]
      * RTP% ≥ tet1[2] → 不觸發
    
    - 第2次救援：使用 tet2 閾值 [60, 80]
      * RTP% < tet2[0] → raise2[0]
      * tet2[0] ≤ RTP% < tet2[1] → raise2[1]
      * RTP% ≥ tet2[1] → 不觸發
    
    Parameters:
    -----------
    n_players : int
        玩家數量
    n_rounds : int
        每個玩家的局數 (預設200)
    
    Returns:
    --------
    results_no_rescue : numpy.ndarray
        無救援機制的結果，shape (n_players, n_rounds)
    results_with_rescue : numpy.ndarray
        有救援機制的結果，shape (n_players, n_rounds)
    rescue_stats : dict
        救援統計信息，包含：
        - 'rescue_triggered': (n_players, 2) array, 1表示觸發，0表示未觸發
        - 'rescue_rewards': (n_players, 2) array, 記錄獲得的救援分數（0表示未觸發）
        - 'rescue_rounds': (n_players, 2) array, 記錄救援觸發的局數
        - 'rescue_rtp': (n_players, 2) array, 記錄觸發時的RTP
    """
    # 先生成無機制的模擬結果
    results_no_rescue = simulate_mode1_core(n_players, n_rounds, multipliers, weights_prob, JP_values, JP_prob)
    
    # 複製一份用於有機制的結果
    results_with_rescue = results_no_rescue.copy()
    
    # 初始化統計數據
    rescue_triggered = np.zeros((n_players, 2), dtype=np.int32)  # (第1次, 第2次)
    rescue_rewards = np.zeros((n_players, 2), dtype=np.float64)  # 獲得的救援分數
    rescue_rounds = np.zeros((n_players, 2), dtype=np.int32)  # 救援觸發的局數
    rescue_rtp = np.zeros((n_players, 2), dtype=np.float64)  # 觸發時的RTP
    
    # 對每個玩家應用救援機制
    for player in range(n_players):
        # 隨機抽取兩個救援觸發局數（轉為0-based index）
        rescue_round1 = np.random.randint(49, 50)  # 第41-60局，對應index 40-59
        rescue_round2 = np.random.randint(149, 150)  # 第141-160局，對應index 139-159
        
        rescue_rounds[player, 0] = rescue_round1 + 1  # 記錄為1-based（第幾局）
        rescue_rounds[player, 1] = rescue_round2 + 1
        
        # 第一次救援（raise1）
        if rescue_round1 > 0:
            # 計算前面局數的RTP（總得分/局數/100）
            total_score_before = np.sum(results_with_rescue[player, :rescue_round1])
            rtp = total_score_before / rescue_round1 / 100
            rescue_rtp[player, 0] = rtp
            
            # 根據RTP決定救援分數（使用tet1閾值）
            rtp_percent = rtp * 100
            if rtp_percent < tet1[0]:
                results_with_rescue[player, rescue_round1] = raise1[0]
                rescue_triggered[player, 0] = 1
                rescue_rewards[player, 0] = raise1[0]
            elif rtp_percent < tet1[1]:
                results_with_rescue[player, rescue_round1] = raise1[1]
                rescue_triggered[player, 0] = 1
                rescue_rewards[player, 0] = raise1[1]
            elif rtp_percent < tet1[2]:
                results_with_rescue[player, rescue_round1] = raise1[2]
                rescue_triggered[player, 0] = 1
                rescue_rewards[player, 0] = raise1[2]
            # rtp_percent >= tet1[2] 保持原本的隨機值，不觸發救援
        
        # 第二次救援（raise2）
        if rescue_round2 < n_rounds:
            # 計算前面局數的RTP
            total_score_before = np.sum(results_with_rescue[player, :rescue_round2])
            rtp = total_score_before / rescue_round2 / 100
            rescue_rtp[player, 1] = rtp
            
            # 根據RTP決定救援分數（使用tet2閾值）
            rtp_percent = rtp * 100
            if rtp_percent < tet2[0]:
                results_with_rescue[player, rescue_round2] = raise2[0]
                rescue_triggered[player, 1] = 1
                rescue_rewards[player, 1] = raise2[0]
            elif rtp_percent < tet2[1]:
                results_with_rescue[player, rescue_round2] = raise2[1]
                rescue_triggered[player, 1] = 1
                rescue_rewards[player, 1] = raise2[1]
            # rtp_percent >= tet2[1] 保持原本的隨機值，不觸發救援
    
    rescue_stats = {
        'rescue_triggered': rescue_triggered,
        'rescue_rewards': rescue_rewards,
        'rescue_rounds': rescue_rounds,
        'rescue_rtp': rescue_rtp
    }
    
    return results_no_rescue, results_with_rescue, rescue_stats

def count_breakeven(scores_matrix, start_round=16):
    """
    計算每個玩家打平的次數
    
    打平定義：RTP從<1變為>=1
    RTP計算：累計得分 / 局數 / 100
    
    Parameters:
    -----------
    scores_matrix : numpy.ndarray
        shape (n_players, n_rounds)，每個玩家每局的得分
    start_round : int
        開始計算打平的局數（預設從第16局開始，即索引15）
    
    Returns:
    --------
    breakeven_counts : numpy.ndarray
        shape (n_players,)，每個玩家打平的次數
    """
    n_players, n_rounds = scores_matrix.shape
    breakeven_counts = np.zeros(n_players, dtype=np.int32)
    
    for player in range(n_players):
        cumsum = 0
        prev_rtp = 0
        
        for round_num in range(n_rounds):
            cumsum += scores_matrix[player, round_num]
            current_rtp = cumsum / (round_num + 1) / 100
            
            # 只從 start_round 開始計算打平（round_num 是0-based，所以要 >= start_round-1）
            if round_num >= start_round - 1:
                # 檢測從 <1 到 >=1 的轉變
                if prev_rtp < 1 and current_rtp >= 1:
                    breakeven_counts[player] += 1
            
            prev_rtp = current_rtp
    
    return breakeven_counts

def analyze_rescue_stats(rescue_stats):
    """
    分析救援統計數據
    
    Parameters:
    -----------
    rescue_stats : dict
        從 simulate_mode1_with_rescue 返回的救援統計數據
    
    Returns:
    --------
    analysis : dict
        包含各種統計信息
    """
    rescue_triggered = rescue_stats['rescue_triggered']
    rescue_rewards = rescue_stats['rescue_rewards']
    n_players = rescue_triggered.shape[0]
    
    # 統計4種救援組合
    rescue_patterns = {
        '(0,0)': 0,  # 都未觸發
        '(1,0)': 0,  # 只第1次觸發
        '(0,1)': 0,  # 只第2次觸發
        '(1,1)': 0   # 兩次都觸發
    }
    
    # 統計每種救援獎項的使用次數（動態根據raise1和raise2）
    rescue1_rewards_count = {0: 0}
    for reward in raise1:
        if reward not in rescue1_rewards_count:
            rescue1_rewards_count[reward] = 0
    
    rescue2_rewards_count = {0: 0}
    for reward in raise2:
        if reward not in rescue2_rewards_count:
            rescue2_rewards_count[reward] = 0
    
    for player in range(n_players):
        r1, r2 = rescue_triggered[player]
        pattern = f"({r1},{r2})"
        rescue_patterns[pattern] += 1
        
        # 統計第1次救援獎項
        reward1 = rescue_rewards[player, 0]
        if reward1 in rescue1_rewards_count:
            rescue1_rewards_count[reward1] += 1
        
        # 統計第2次救援獎項
        reward2 = rescue_rewards[player, 1]
        if reward2 in rescue2_rewards_count:
            rescue2_rewards_count[reward2] += 1
    
    analysis = {
        'rescue_patterns': rescue_patterns,
        'rescue1_rewards': rescue1_rewards_count,
        'rescue2_rewards': rescue2_rewards_count,
        'total_players': n_players
    }
    
    return analysis

def print_rescue_analysis(analysis):
    """
    打印救援分析結果
    """
    total = analysis['total_players']
    
    print("\n" + "=" * 60)
    print("救援機制統計分析")
    print("=" * 60)
    
    print(f"\n總玩家數: {total}")
    
    print("\n【救援觸發組合統計】")
    for pattern, count in analysis['rescue_patterns'].items():
        percentage = count / total * 100
        print(f"  {pattern}: {count:6d} 次 ({percentage:5.2f}%)")
    
    print("\n【第1次救援獎項統計】(raise1)")
    for reward, count in sorted(analysis['rescue1_rewards'].items()):
        if reward == 0:
            print(f"  未觸發:    {count:6d} 次 ({count/total*100:5.2f}%)")
        else:
            print(f"  {reward:4.0f}分:  {count:6d} 次 ({count/total*100:5.2f}%)")
    
    print("\n【第2次救援獎項統計】(raise2)")
    for reward, count in sorted(analysis['rescue2_rewards'].items()):
        if reward == 0:
            print(f"  未觸發:    {count:6d} 次 ({count/total*100:5.2f}%)")
        else:
            print(f"  {reward:4.0f}分:  {count:6d} 次 ({count/total*100:5.2f}%)")
    
    print("=" * 60)

#%%
# 範例使用
if __name__ == "__main__":
    # 示例1：無救援機制的模擬
    print("=" * 50)
    print("示例1：無救援機制")
    print("=" * 50)
    n = 10
    results_no_rescue = simulate_mode1(n)
    print(f"模擬 {n} 個玩家，每人玩 200 局")
    print(f"結果形狀: {results_no_rescue.shape}")
    for i in range(min(3, n)):
        avg_score = np.mean(results_no_rescue[i])
        total_score = np.sum(results_no_rescue[i])
        print(f"玩家 {i+1}: 平均分數 = {avg_score:.2f}, 總分 = {total_score:.2f}")
    
    # 示例2：有救援機制的模擬（少量玩家）
    print("\n" + "=" * 50)
    print("示例2：有救援機制（10個玩家）")
    print("=" * 50)
    results_no_rescue, results_with_rescue, rescue_stats = simulate_mode1_with_rescue(n)
    print(f"模擬 {n} 個玩家，每人玩 200 局（含救援機制）")
    
    print("\n比較前3個玩家的結果：")
    for i in range(min(3, n)):
        avg_no_rescue = np.mean(results_no_rescue[i])
        total_no_rescue = np.sum(results_no_rescue[i])
        avg_with_rescue = np.mean(results_with_rescue[i])
        total_with_rescue = np.sum(results_with_rescue[i])
        diff = total_with_rescue - total_no_rescue
        
        r1, r2 = rescue_stats['rescue_triggered'][i]
        reward1, reward2 = rescue_stats['rescue_rewards'][i]
        round1, round2 = rescue_stats['rescue_rounds'][i]
        
        print(f"\n玩家 {i+1}:")
        print(f"  無救援: 總分 = {total_no_rescue:.2f}")
        print(f"  有救援: 總分 = {total_with_rescue:.2f}")
        print(f"  差異: {diff:+.2f}")
        print(f"  救援組合: ({r1},{r2})")
        print(f"  第1次救援: 第{round1}局, 獲得{reward1:.0f}分")
        print(f"  第2次救援: 第{round2}局, 獲得{reward2:.0f}分")
    
    # 示例3：大量玩家統計分析
    print("\n" + "=" * 50)
    print("示例3：大量玩家統計分析（2000個玩家）")
    print("=" * 50)
    n_large = 2000
    results_no_rescue, results_with_rescue, rescue_stats = simulate_mode1_with_rescue(n_large)
    
    # 分析並打印統計結果
    analysis = analyze_rescue_stats(rescue_stats)
    print_rescue_analysis(analysis)
    
    # 整體RTP比較
    avg_rtp_no_rescue = np.mean(results_no_rescue) / 100
    avg_rtp_with_rescue = np.mean(results_with_rescue) / 100
    print(f"\n整體平均RTP:")
    print(f"  無救援機制: {avg_rtp_no_rescue:.4f}")
    print(f"  有救援機制: {avg_rtp_with_rescue:.4f}")
    print(f"  RTP提升: {(avg_rtp_with_rescue - avg_rtp_no_rescue):.4f}")
    
    # 示例4：計算打平次數
    print("\n" + "=" * 50)
    print("示例4：打平次數分析（從第16局開始）")
    print("=" * 50)
    breakeven_no_rescue = count_breakeven(results_no_rescue)
    breakeven_with_rescue = count_breakeven(results_with_rescue)
    
    print(f"\n打平次數統計（{n_large}個玩家，從第16局開始計算）:")
    print(f"  無救援機制 - 平均打平次數: {np.mean(breakeven_no_rescue):.2f}")
    print(f"  無救援機制 - 最大打平次數: {np.max(breakeven_no_rescue)}")
    print(f"  無救援機制 - 最小打平次數: {np.min(breakeven_no_rescue)}")
    print(f"\n  有救援機制 - 平均打平次數: {np.mean(breakeven_with_rescue):.2f}")
    print(f"  有救援機制 - 最大打平次數: {np.max(breakeven_with_rescue)}")
    print(f"  有救援機制 - 最小打平次數: {np.min(breakeven_with_rescue)}")
    
    # 顯示前5個玩家的詳細打平次數
    print(f"\n前5個玩家的打平次數比較:")
    for i in range(min(5, n_large)):
        print(f"  玩家{i+1}: 無救援={breakeven_no_rescue[i]}, 有救援={breakeven_with_rescue[i]}")

#%%
