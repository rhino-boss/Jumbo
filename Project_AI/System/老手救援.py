#%%
import numpy as np
import random
from numba import njit

# 倍率權重 (Multiplier Weights)
weights = np.array([
885913313,
11764624,
16365756,
11623926,
12367038,
10095520,
8063906,
1960044,
8419726,
3082035,
6201756,
9885740,
5874476,
2464217,
2137165,
408530,
953627,
221560,
1108012,
432204,
44452,
190628,
73375,
138440,
87332,
21172,
14257,
12709,
5645,
6007,
707,
355,
0,
0,
0,
68,
0,
0,
0,
0,
0,
0,
0,
0,
0,
222
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
3258,
3828,
4352,
4812,
5677,
6551,
7616,
8629,
9616,
11175,
13098,
15114,
17151,
19208,
22424,
27525,
32461,
37619,
42528,
47730,
52473,
57610,
62584,
67529,
72491,
78153,
82694,
87446,
92469,
98281,
140954
], dtype=np.float64)
JP1 = 0.01/10
JP2 = 0.01/50
JP3 = 0.01/1000
JP4 = 0.01/(5000/0.65)
# JP 權重和獎金
JP_weights = np.array([(1-JP1-JP2-JP3-JP4), JP1, JP2, JP3, JP4], dtype=np.float64)
JP_values = np.array([0, 1000, 5000, 100000, 769230], dtype=np.float64)

# 將權重歸一化為概率
weights_prob = weights / weights.sum()
JP_prob = JP_weights / JP_weights.sum()

# 老手救援獎勵和閾值
loyal_raise1 = np.array([3500, 1000, 0], dtype=np.float64)  # 第150轉救援的獎勵
loyal_raise2 = np.array([3500, 1000, 0], dtype=np.float64)  # 第300轉救援的獎勵
loyal_raise3 = np.array([3500, 2000, 0], dtype=np.float64)  # 第450,600,750...轉救援的獎勵（正常情況）
loyal_raise3mini = np.array([3500, 0, 0], dtype=np.float64)  # 第3階段當前500轉RTP>100時使用的獎勵

loyal_tet1 = np.array([35, 55, 90], dtype=np.float64)  # 第150轉的RTP閾值
loyal_tet2 = np.array([35, 55, 90], dtype=np.float64)  # 第300轉的RTP閾值
loyal_tet3 = np.array([40, 46, 90], dtype=np.float64)  # 第450,600,750...轉的RTP閾值（正常情況）
loyal_tet3mini = np.array([40, 46, 90], dtype=np.float64)  # 第3階段當前500轉RTP>100時使用的閾值 
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

def simulate_mode1(n_players, n_rounds=3000):
    """
    模擬模式1: n個玩家各玩n_rounds局（無機制）
    
    Parameters:
    -----------
    n_players : int
        玩家數量
    n_rounds : int
        每個玩家的局數 (預設3000)
    
    Returns:
    --------
    results : numpy.ndarray
        shape (n_players, n_rounds)，包含每個玩家每局的總分數
    """
    return simulate_mode1_core(n_players, n_rounds, multipliers, weights_prob, JP_values, JP_prob)

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

def simulate_loyal_rescue(n_players, n_rounds=3000):
    """
    模擬老手救援機制
    
    三個階段的救援機制：
    - 第1階段：第150轉
      檢查第1-150轉的RTP，使用 loyal_tet1 閾值和 loyal_raise1 獎勵
    - 第2階段：第300轉
      檢查第151-300轉的RTP，使用 loyal_tet2 閾值和 loyal_raise2 獎勵  
    - 第3階段：第450, 600, 750...轉（每隔150轉）
      檢查該區間150轉的RTP（例如第450轉檢查301-450轉）
      正常情況：使用 loyal_tet3 閾值和 loyal_raise3 獎勵
      特殊條件：如果前500轉（不足500則以實際轉數）RTP>100%，
      則改用 loyal_tet3mini 閾值和 loyal_raise3mini 獎勵（更嚴格的條件和較低的獎勵）
    
    每個階段都有3個RTP區間：
      * RTP% < tet[0] → raise[0]
      * tet[0] ≤ RTP% < tet[1] → raise[1]
      * tet[1] ≤ RTP% < tet[2] → raise[2]
      * RTP% ≥ tet[2] → 不觸發
    
    Parameters:
    -----------
    n_players : int
        玩家數量
    n_rounds : int
        每個玩家的局數 (預設3000，以涵蓋多次第3階段救援)
    
    Returns:
    --------
    results_no_rescue : numpy.ndarray
        無救援機制的結果，shape (n_players, n_rounds)
    results_with_rescue : numpy.ndarray
        有救援機制的結果，shape (n_players, n_rounds)
    rescue_stats : dict
        救援統計信息，包含：
        - 'rescue_count': (n_players,) 每個玩家觸發的救援總次數
        - 'rescue_details': list of lists，每個玩家的救援詳情
          每條記錄為 (round_num, stage, rtp, reward)
    """
    # 先生成無機制的模擬結果
    results_no_rescue = simulate_mode1_core(n_players, n_rounds, multipliers, weights_prob, JP_values, JP_prob)
    
    # 複製一份用於有機制的結果
    results_with_rescue = results_no_rescue.copy()
    
    # 初始化統計數據
    rescue_count = np.zeros(n_players, dtype=np.int32)
    rescue_details = [[] for _ in range(n_players)]
    
    # 對每個玩家應用救援機制
    for player in range(n_players):
        # 第1階段：第150轉（索引149）
        # 檢查第1-150轉的RTP
        if n_rounds > 150:
            round_idx = 149
            # 計算第1-150轉（索引0-149）的總分和RTP
            total_score_interval = np.sum(results_with_rescue[player, 0:round_idx+1])
            rtp = total_score_interval / 150 / 100
            rtp_percent = rtp * 100
            
            triggered = False
            reward = 0
            if rtp_percent < loyal_tet1[0]:
                reward = loyal_raise1[0]
                triggered = True
            elif rtp_percent < loyal_tet1[1]:
                reward = loyal_raise1[1]
                triggered = True
            elif rtp_percent < loyal_tet1[2]:
                reward = loyal_raise1[2]
                triggered = True
            
            if triggered:
                results_with_rescue[player, round_idx] = reward
                rescue_count[player] += 1
                rescue_details[player].append((150, 1, rtp_percent, reward))
        
        # 第2階段：第300轉（索引299）
        # 檢查第151-300轉的RTP
        if n_rounds > 300:
            round_idx = 299
            # 計算第151-300轉（索引150-299）的總分和RTP
            total_score_interval = np.sum(results_with_rescue[player, 150:round_idx+1])
            rtp = total_score_interval / 150 / 100
            rtp_percent = rtp * 100
            
            triggered = False
            reward = 0
            if rtp_percent < loyal_tet2[0]:
                reward = loyal_raise2[0]
                triggered = True
            elif rtp_percent < loyal_tet2[1]:
                reward = loyal_raise2[1]
                triggered = True
            elif rtp_percent < loyal_tet2[2]:
                reward = loyal_raise2[2]
                triggered = True
            
            if triggered:
                results_with_rescue[player, round_idx] = reward
                rescue_count[player] += 1
                rescue_details[player].append((300, 2, rtp_percent, reward))
        
        # 第3階段：第450, 600, 750...轉（每隔150轉）
        # 自動生成所有第3階段的救援輪數
        round_num = 450
        while round_num <= n_rounds:
            round_idx = round_num - 1
            
            # 計算該區間150轉的RTP
            # 第450轉：檢查301-450轉（索引300-449）
            # 第600轉：檢查451-600轉（索引450-599）
            # 第750轉：檢查601-750轉（索引600-749）
            interval_start = round_num - 150
            total_score_interval = np.sum(results_with_rescue[player, interval_start:round_idx+1])
            rtp = total_score_interval / 150 / 100
            rtp_percent = rtp * 100
            
            # 檢查前500轉（或實際轉數）的RTP來決定使用哪個閾值和獎勵
            check_rounds = min(500, round_idx)  # 不足500則用實際轉數
            start_idx = round_idx - check_rounds
            total_score_last_500 = np.sum(results_with_rescue[player, start_idx:round_idx])
            rtp_last_500_percent = (total_score_last_500 / check_rounds) / 100 * 100
            
            # 根據前500轉RTP選擇使用哪個閾值和獎勵
            if rtp_last_500_percent > 100:
                current_tet3 = loyal_tet3mini
                current_raise3 = loyal_raise3mini
            else:
                current_tet3 = loyal_tet3
                current_raise3 = loyal_raise3
            
            triggered = False
            reward = 0
            if rtp_percent < current_tet3[0]:
                reward = current_raise3[0]
                triggered = True
            elif rtp_percent < current_tet3[1]:
                reward = current_raise3[1]
                triggered = True
            elif rtp_percent < current_tet3[2]:
                reward = current_raise3[2]
                triggered = True
            
            if triggered:
                results_with_rescue[player, round_idx] = reward
                rescue_count[player] += 1
                rescue_details[player].append((round_num, 3, rtp_percent, reward))
            
            round_num += 150  # 每隔150轉
    
    rescue_stats = {
        'rescue_count': rescue_count,
        'rescue_details': rescue_details
    }
    
    return results_no_rescue, results_with_rescue, rescue_stats

def analyze_loyal_rescue_stats(rescue_stats, n_rounds):
    """
    分析老手救援統計數據
    
    Parameters:
    -----------
    rescue_stats : dict
        從 simulate_loyal_rescue 返回的救援統計數據
    n_rounds : int
        模擬的總局數
    
    Returns:
    --------
    analysis : dict
        包含各種統計信息
    """
    rescue_count = rescue_stats['rescue_count']
    rescue_details = rescue_stats['rescue_details']
    n_players = len(rescue_count)
    
    # 統計各階段的觸發情況
    stage_stats = {
        1: {'total': 0, 'triggered': 0, 'rewards': {}},
        2: {'total': 0, 'triggered': 0, 'rewards': {}},
        3: {'total': 0, 'triggered': 0, 'rewards': {}}
    }
    
    # 初始化獎勵計數
    for reward in loyal_raise1:
        stage_stats[1]['rewards'][reward] = 0
    for reward in loyal_raise2:
        stage_stats[2]['rewards'][reward] = 0
    for reward in loyal_raise3:
        stage_stats[3]['rewards'][reward] = 0
    for reward in loyal_raise3mini:
        stage_stats[3]['rewards'][reward] = 0
    
    # 統計每個階段
    for player_details in rescue_details:
        for round_num, stage, rtp_percent, reward in player_details:
            stage_stats[stage]['triggered'] += 1
            if reward in stage_stats[stage]['rewards']:
                stage_stats[stage]['rewards'][reward] += 1
    
    # 計算每個階段有多少玩家經歷過
    if n_rounds > 150:
        stage_stats[1]['total'] = n_players
    if n_rounds > 300:
        stage_stats[2]['total'] = n_players
    if n_rounds > 450:
        # 計算第3階段的總次數（450, 600, 750...）
        stage3_count = (n_rounds - 300) // 150
        stage_stats[3]['total'] = n_players * stage3_count
    
    analysis = {
        'stage_stats': stage_stats,
        'total_rescues': np.sum(rescue_count),
        'avg_rescues_per_player': np.mean(rescue_count),
        'max_rescues': np.max(rescue_count),
        'min_rescues': np.min(rescue_count),
        'total_players': n_players
    }
    
    return analysis

def print_loyal_rescue_analysis(analysis):
    """
    打印老手救援分析結果
    """
    print("\n" + "=" * 60)
    print("老手救援機制統計分析")
    print("=" * 60)
    
    print(f"\n總玩家數: {analysis['total_players']}")
    print(f"總救援觸發次數: {analysis['total_rescues']}")
    print(f"平均每位玩家救援次數: {analysis['avg_rescues_per_player']:.2f}")
    print(f"最大救援次數: {analysis['max_rescues']}")
    print(f"最小救援次數: {analysis['min_rescues']}")
    
    stage_stats = analysis['stage_stats']
    
    for stage in [1, 2, 3]:
        stats = stage_stats[stage]
        if stats['total'] > 0:
            if stage == 1:
                stage_name = "第1階段（第150轉）"
            elif stage == 2:
                stage_name = "第2階段（第300轉）"
            else:
                stage_name = "第3階段（第450,600,750...轉）"
            
            print(f"\n【{stage_name}】")
            print(f"  可觸發總次數: {stats['total']}")
            print(f"  實際觸發次數: {stats['triggered']}")
            trigger_rate = stats['triggered'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  觸發率: {trigger_rate:.2f}%")
            
            print(f"  獎勵分布:")
            for reward, count in sorted(stats['rewards'].items()):
                if stats['triggered'] > 0:
                    percentage = count / stats['triggered'] * 100
                    print(f"    {reward:5.0f}分: {count:6d} 次 ({percentage:5.2f}%)")
    
    print("=" * 60)

#%%
# 範例使用 - 老手救援機制
if __name__ == "__main__":
    print("=" * 60)
    print("老手救援機制模擬（3000轉）")
    print("=" * 60)
    
    # 示例1：無救援機制的基礎模擬
    print("\n" + "=" * 50)
    print("示例1：無救援機制（10個玩家，3000轉）")
    print("=" * 50)
    n = 10
    n_rounds = 3000
    results_no_rescue = simulate_mode1(n, n_rounds)
    print(f"模擬 {n} 個玩家，每人玩 {n_rounds} 局")
    print(f"結果形狀: {results_no_rescue.shape}")
    for i in range(min(3, n)):
        avg_score = np.mean(results_no_rescue[i])
        total_score = np.sum(results_no_rescue[i])
        rtp = avg_score / 100
        print(f"玩家 {i+1}: 平均分數 = {avg_score:.2f}, 總分 = {total_score:.2f}, RTP = {rtp:.4f}")
    
    # 示例2：老手救援機制（少量玩家）
    print("\n" + "=" * 50)
    print("示例2：老手救援機制（10個玩家，3000轉）")
    print("=" * 50)
    results_no_rescue, results_with_rescue, rescue_stats = simulate_loyal_rescue(n, n_rounds)
    print(f"模擬 {n} 個玩家，每人玩 {n_rounds} 局（含老手救援機制）")
    
    print("\n比較前3個玩家的結果：")
    for i in range(min(3, n)):
        total_no_rescue = np.sum(results_no_rescue[i])
        total_with_rescue = np.sum(results_with_rescue[i])
        diff = total_with_rescue - total_no_rescue
        rtp_no_rescue = (total_no_rescue / n_rounds) / 100
        rtp_with_rescue = (total_with_rescue / n_rounds) / 100
        
        details = rescue_stats['rescue_details'][i]
        
        print(f"\n玩家 {i+1}:")
        print(f"  無救援: 總分 = {total_no_rescue:.2f}, RTP = {rtp_no_rescue:.4f}")
        print(f"  有救援: 總分 = {total_with_rescue:.2f}, RTP = {rtp_with_rescue:.4f}")
        print(f"  差異: {diff:+.2f}")
        print(f"  救援次數: {len(details)}")
        
        if details and len(details) <= 5:  # 只顯示前5次救援
            print(f"  救援詳情:")
            for round_num, stage, rtp_percent, reward in details[:5]:
                stage_name = {1: "階段1", 2: "階段2", 3: "階段3"}[stage]
                print(f"    第{round_num}局 [{stage_name}] RTP={rtp_percent:.1f}% → 獲得{reward:.0f}分")
    
    # 示例3：大量玩家統計分析
    print("\n" + "=" * 50)
    print("示例3：大量玩家統計分析（2000個玩家，3000轉）")
    print("=" * 50)
    n_large = 2000
    results_no_rescue, results_with_rescue, rescue_stats = simulate_loyal_rescue(n_large, n_rounds)
    
    # 分析並打印統計結果
    analysis = analyze_loyal_rescue_stats(rescue_stats, n_rounds)
    print_loyal_rescue_analysis(analysis)
    
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
    
    # 示例5：救援分數統計
    print("\n" + "=" * 50)
    print("示例5：救援總分數貢獻分析")
    print("=" * 50)
    total_rescue_contribution = np.sum(results_with_rescue - results_no_rescue)
    avg_rescue_contribution = total_rescue_contribution / n_large
    print(f"總救援貢獻: {total_rescue_contribution:.2f} 分")
    print(f"平均每位玩家救援貢獻: {avg_rescue_contribution:.2f} 分")
    print(f"平均每位玩家救援次數: {analysis['avg_rescues_per_player']:.2f} 次")
    if analysis['avg_rescues_per_player'] > 0:
        avg_per_rescue = avg_rescue_contribution / analysis['avg_rescues_per_player']
        print(f"平均每次救援貢獻: {avg_per_rescue:.2f} 分")

#%%
