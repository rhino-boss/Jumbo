from numba import jit

import numpy as np  # math extention
import math
import os
import multiprocessing
import common.DataExport as de
import common.InputSettings as inp
import DefineSymbols as defs

global arr_parsheet #遊戲Parsheet
global arr_pays #遊戲Pays
folder_path = os.path.abspath('.') #此層資料夾位置
global float_estimate_rtp #理論值RTP(用於計算標準差)
global bool_survival_mode #生存模式開關
global triggerLimit # 免費遊戲場次上限
global arr_get_freespins #免費遊戲觸發場次
global bool_show_log #log開關
global int_extrafree_denominator
global int_extrafree_numerator
#------------------輸入參數------------------
getSettings = inp.inputbox() # InputSettings中的inputbox函數
bool_show_log = getSettings[1]
bool_survival_mode = getSettings[2]

arr_parsheet = de.GetFromExcel(folder_path+'/StripTable.xlsx',['Regular','Extra'], False, np.int8) 

arr_pays = de.GetFromExcel(folder_path+'/Pays.xlsx',['Regular','Extra'], True, np.float64) 
# 抓lines檔案
arr_lines = de.GetFromExcel(folder_path+'/common/Lines.xlsx',['5Line'], True, np.int8)


global int_number_of_lines # lines個數
int_number_of_lines = arr_lines.shape[0]

exportfileName = 'FortuneGems_sim' #輸出檔案名稱
float_estimate_rtp = 0.25

Bet = 1

# arr_get_freespins = np.array([[0,8,0,0],[0,8,0,0]],np.int8) #[[base game],[free game]]-->[C1x2,C1x3,C1x4,C1x5]
# 盤面大小
arr_window_reel_settings = np.array([[3,3],[3,3]],np.int8) # reel condition [window, reel] 
int_extrafree_denominator = 100000000
int_extrafree_numerator = 0
#------------------輸入參數------------------
arr_reel_weight = de.GetFromExcel(folder_path+'/Weight.xlsx',['BG_weight', 'BG_weight'], False, np.int64, bool_cumsum=True) 
arr_nudge_num = np.array([2,3,4,5,6,7,8,9,10,20,50], np.int8)
arr_nudge_num_weight = de.GetFromExcel(folder_path+'/Weight.xlsx',['nudge_num'], False, np.int64, bool_cumsum=True) 
arr_nudge_multiplier = np.array([1,2,3,5,10,15,20,25,50,100,500], np.int64)
arr_nudge_multiplier_weight = de.GetFromExcel(folder_path+'/Weight.xlsx',['nudge_multiplier'], False, np.int64, bool_cumsum=True) 
arr_R4_reel = np.array([1,2,3,5,10,15,20,25,50,100,500,0], np.int64) # 0: nudge
arr_R4_reel_weight = de.GetFromExcel(folder_path+'/Weight.xlsx',['R4_reel'], False, np.int64, bool_cumsum=True) 

#------------------自動計算遊戲內所需參數------------------
global int_cpu #cpu數量(用於自動分配執行緒)
global arr_bet_value #生存模式要跑的所有押注
global arr_bet_multiplier #對應不同押注反算出倍率
global arr_start_credit #生存模式的入鈔狀態
int_cpu = multiprocessing.cpu_count()
arr_bet_value = np.array([Bet],np.int16)
arr_bet_multiplier = np.zeros(arr_bet_value.shape[0],np.float64)
for iBet in range(len(arr_bet_value)):
    arr_bet_multiplier[iBet] = arr_bet_value[iBet] / Bet
arr_start_credit = np.array([19526,39589,65944,132630,185951,332105,424757,770084],np.int64)
TotalRound = getSettings[0]

global NeedToCheckSymbol #定義需要算分的Symbol
NeedToCheckSymbol = np.array([defs.WW,defs.M1,defs.M2,defs.M3,defs.A,defs.K,defs.Q,defs.J],np.int8)
int_parsheet_counts = arr_parsheet.shape[0]

# 不要檢查的symbol
global do_not_check_List
do_not_check_List = np.array([defs.C1],np.int8)

global arr_parsheet_length #計算"每個"Parsheet的輪帶長度(base game)
arr_parsheet_length = np.zeros((int_parsheet_counts,arr_window_reel_settings[0][1]),np.int16)
global thresholdMultiple #紀錄的統計區間
thresholdMultiple = np.array([0,0,0.5,1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50,60,70,80,90,100,125,150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,600,700,800,900,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,12000,14000,16000,18000,20000,22000,24000,26000,28000,30000,35000,40000,99999],np.float64)
for sheets in range(int_parsheet_counts):
    for iReel in range(arr_parsheet[sheets].shape[0]):
        arr_parsheet_length[sheets][iReel] = np.count_nonzero(arr_parsheet[sheets][iReel] != -1)
        
#自動分析C1位置
global arr_c1_in_reel
arr_c1_in_reel = np.zeros(arr_window_reel_settings[0][1],np.int16)
total_temp_rng = []

###
for iReel in range(arr_window_reel_settings[0][1]):
    arr_temp_rng = []
    for iSymbol in range(arr_parsheet_length[0][iReel]):
        bool_if_c1_appear = False
        for i in range(arr_window_reel_settings[0][0]):
            if iSymbol + i >= arr_parsheet_length[0][iReel]:
                checking_symbol = arr_parsheet[0][iReel][ iSymbol + i-arr_parsheet_length[0][iReel]]
            else:
                checking_symbol = arr_parsheet[0][iReel][iSymbol + i]
            if checking_symbol == defs.C1:
                bool_if_c1_appear = True
        if bool_if_c1_appear == True:
            arr_temp_rng.append(iSymbol)
    if arr_temp_rng != []:
        arr_c1_in_reel[iReel] = len(arr_temp_rng)
    total_temp_rng.append(arr_temp_rng)
###
    
global arr_force_c1_parsheet
arr_force_c1_parsheet = np.zeros((arr_window_reel_settings[0][1],max(arr_c1_in_reel)),np.int16)
for iReel in range(arr_window_reel_settings[0][1]):
    for iSymbol in range(arr_c1_in_reel[iReel]):
        arr_force_c1_parsheet[iReel][iSymbol] = total_temp_rng[iReel][iSymbol]
global int_c1_status
int_c1_status = np.count_nonzero(arr_c1_in_reel)
#------------------自動計算遊戲內所需參數------------------
# jit decorator tells Numba to compile this function.
# The argument types will be inferred by Numba when function is called.
@jit(['void(float64[:,:],int8,int64,int8)'], nopython=True, nogil=True)
def Main(arr_output_data,int_thread,int_rounds,int_bet_indicator):
    """
    遊戲主結構
    """
    if int_thread == 0:
        if bool_survival_mode == True:
            print('Survival Mode: On')
        else:
            print('Survival Mode: Off')
    #------------------定義遊戲內所需變數------------------
    WinsReport = arr_output_data[0]
        #WinsReport[0] = total spins
        #WinsReport[1] = total free spins
        #WinsReport[2] = mystery free game hits
        #WinsReport[3] = base hits
        #WinsReport[4] = free hits
        #WinsReport[5] = single max payment
        #WinsReport[6] = -
        #WinsReport[7] = -
        #WinsReport[8] = -
        #WinsReport[9] = -
        #WinsReport[10] = Standard deviation ^ 2
    HitsReport_Base = arr_output_data[1] #Base Game Hits報表 #一維陣列
    PayReport_Base = arr_output_data[2] #Base Game Symbol贏分報表
    HitsReport_Extra = arr_output_data[3] #Free Game Hits報表    
    PayReport_Extra = arr_output_data[4] #Free Game Symbol贏分報表
    # arr_output_data[5] R4 輪帶結果
    # arr_output_data[6] nudge數量分布
    # arr_output_data[7~10] nudge 倍數分布

  
   # arr_output_data[17] #Base Game贏分區間表
   # arr_output_data[18] #Free Game贏分區間表

    len_report = HitsReport_Base.shape[0]
    temp_HitsReport = np.zeros(len_report,np.int64)
    temp_PayReport = np.zeros(len_report,np.float64)
    arr_jumbo_rng = np.zeros(arr_window_reel_settings[0][1],np.int16) #RNG
    arr_result_reel = np.full((2,arr_window_reel_settings[1][0],arr_window_reel_settings[1][1]),-1,np.int8) #結果盤面,2*3*3,以-1填滿

    arr_wins = np.zeros(2,np.float64) #[Base Game贏分,Free Game贏分]
    arr_freegame_status = np.zeros(1,np.int8)
    arr_line_wins = np.zeros(2,np.float64)  # 修改為2個元素以支援索引[0]和[1]
    arr_force_reel_status = np.array([1,1,1,0,0],np.bool_) #若有5C1時shuffle過後為強制進入free game的C1位置

    #------------------定義遊戲內所需變數------------------
    def calculate_std(dtWins):
        """
        計算標準差
        """
        net_pay = dtWins - arr_bet_value[int_bet_indicator]
        ev = (float_estimate_rtp - 1) * arr_bet_value[int_bet_indicator]
        distance_to_mean = net_pay - ev
        WinsReport[10] += np.square(distance_to_mean)

    def dice_from_array(arr_parameters):
        """
        從cumsum遞增數列當中擲骰結果
        """
        int_temp_dice = math.ceil(np.random.random() * np.max(arr_parameters))
        for i in range(arr_parameters.shape[0]):
            if int_temp_dice <= arr_parameters[i]:
                return i
        return -1

    def count_1D_array(arr_processing_reel,dtTarget,bool_isequal=True):
        """
        統計一維陣列指定Target的數量
        """
        temp_count = 0
        for i in range(arr_processing_reel.shape[0]):
            if bool_isequal == True:
                if arr_processing_reel[i] == dtTarget:
                    temp_count += 1
            else:
                if arr_processing_reel[i] != dtTarget:
                    temp_count += 1
        return temp_count

    def count_2D_array(arr_processing_reel,dtTarget,bool_isequal=True):
        """
        統計二維陣列指定Target的數量
        """
        temp_count = 0
        for i in range(arr_processing_reel.shape[0]):
            for j in range(arr_processing_reel.shape[1]):
                if bool_isequal == True:
                    if arr_processing_reel[i][j] == dtTarget:
                        temp_count += 1
                else:
                    if arr_processing_reel[i][j] != dtTarget:
                        temp_count += 1
        return temp_count

    def np_isin(np_list,np_target):
        """
        判斷Target是否存在於輸入的List列表內
        """
        w = np_list.shape[0]
        inStatus = False
        for item in range(w):
            if np_list[item] == -1:
                break
            elif np_list[item] == np_target:
                inStatus = True
                break
        return inStatus

    def np_equal(np_list,np_target):
        """
        判斷兩個一維陣列是否完全相等
        """
        inStatus = True
        for item in range(np_list.shape[0]):
            if np_list[item] != np_target[item]:
                inStatus = False
        return inStatus

    def initial_2D_array(arr_arrays,var_value=0):
        """
        初始化二維陣列
        """
        for i in range(arr_arrays.shape[0]):
            for j in range(arr_arrays.shape[1]):
                arr_arrays[i][j] = var_value

    def initial_1D_array(arr_arrays,var_value=0):
        """
        初始化一維陣列
        """
        for i in range(arr_arrays.shape[0]):
            arr_arrays[i] = var_value

    def initial_temp_Report():
        """
        初始化temp_Report
        """
        for item in range(len_report):
            temp_HitsReport[item] = 0
            temp_PayReport[item] = 0

    def Add_temp_report(arr_processing_hitreport,arr_processing_payreport):
        """
        把暫存的hit與pay報表加入正式統計的報表內(因為有些算分狀況可能需要被拋棄，所以必須確認是要計入算分的狀態才合併入正式報表)
        """
        arr_processing_hitreport += temp_HitsReport
        arr_processing_payreport += temp_PayReport
        WinsReport[5] = max(WinsReport[5],np.sum(temp_PayReport))
        initial_temp_Report()

    def go_record(dtValue,dtThreshold,dtRecord):
        """
        紀錄統計區間
        """
        dtLen = len(dtThreshold) - 1
        for iThres in range(dtLen):
            if dtThreshold[iThres] == dtThreshold[iThres+1]:
                if dtThreshold[iThres] == dtValue:
                    dtRecord[iThres] += 1
                    break
            else:
                if dtThreshold[iThres] < dtValue <= dtThreshold[iThres+1]:
                    dtRecord[iThres] += 1
                    break

    def GetReelResult(bool_isfreegame,int_processing_parsheet): # get the whole reel result
        """
        依據arr_jumbo_rng取出盤面
        """
        for iReel in range(arr_window_reel_settings[bool_isfreegame][1]):
            for iSymbol in range(arr_window_reel_settings[bool_isfreegame][0]):
                if arr_jumbo_rng[iReel] + iSymbol >= arr_parsheet_length[bool_isfreegame][iReel]:
                    arr_result_reel[bool_isfreegame][iSymbol][iReel] = arr_parsheet[int_processing_parsheet][iReel][arr_jumbo_rng[iReel] + iSymbol - arr_parsheet_length[int_processing_parsheet][iReel]]
                else:
                    arr_result_reel[bool_isfreegame][iSymbol][iReel] = arr_parsheet[int_processing_parsheet][iReel][arr_jumbo_rng[iReel] + iSymbol]
        if bool_show_log:
            print('-----')
            print(arr_result_reel[bool_isfreegame])
            print('-----')
            
 
    def GetRND(int_processing_parsheet):
        """
        取出RNG
        ex:[1,4,87,78,54]
        """
        for iReel in range(arr_parsheet[int_processing_parsheet].shape[0]):
            # arr_jumbo_rng[iReel] = math.ceil(np.random.random() * arr_parsheet_length[int_processing_parsheet][iReel]) - 1
            arr_jumbo_rng[iReel] = dice_from_array(arr_reel_weight[int_processing_parsheet][iReel])
        if bool_show_log == True:
            print('arr_jumbo_rng:', arr_jumbo_rng)

    def R4_spin():
        R4_ind = dice_from_array(arr_R4_reel_weight)
        R4_result = arr_R4_reel[R4_ind]
        arr_output_data[5][R4_ind] += 1 # 統計R4輪帶結果

        result_multiplier = R4_result  # 預設返回原值
        
        if R4_result == 0:
            # 進行重轉邏輯
            # 1. 決定nudge_num
            nudge_num_ind = dice_from_array(arr_nudge_num_weight)
            nudge_num = arr_nudge_num[nudge_num_ind]
            arr_output_data[6][nudge_num_ind] += 1 # 統計nudge次數
            # 2. 根據次數選擇對應的權重陣列並抽取倍數
            total_multiplier = 0
            
            # 根據次數決定使用哪個權重陣列
            weight_index = 0  # 預設值
            if nudge_num >= 2 and nudge_num <= 4:
                weight_index = 0
            elif nudge_num >= 5 and nudge_num <= 7:
                weight_index = 1
            elif nudge_num >= 8 and nudge_num <= 10:
                weight_index = 2
            else:
                weight_index = 3
            
            # 抽取對應次數的倍數並加總
            for _ in range(nudge_num):
                multiplier_ind = dice_from_array(arr_nudge_multiplier_weight[weight_index])
                arr_output_data[7 + weight_index][multiplier_ind] += 1 # 統計nudge倍數
                total_multiplier += arr_nudge_multiplier[multiplier_ind]
            
            result_multiplier = total_multiplier
        
        return result_multiplier
      
    def CheckWin(bool_isfreegame, R4_mul):
        """
        檢查贏分 - Numba 優化版本
        """
        temp_hit = 0
        
        # 預先計算常用值
        num_reels = arr_window_reel_settings[bool_isfreegame][1]
        
        for iLine in range(int_number_of_lines):
            best_payment = 0.0
            best_symbol = 0
            best_count = 0
            
            # 直接使用索引而不是複製陣列
            main_symbol = arr_result_reel[bool_isfreegame][arr_lines[iLine][0]][0]
            
            # 快速檢查：主要符號是否可以算分
            if main_symbol != defs.C1:  # 使用直接比較而非 np_isin
                
                # 情況1: 純 WW 連線（僅當第一個符號是 WW 時）
                if main_symbol == defs.WW:
                    ww_count = 0
                    for iReel in range(num_reels):
                        symbol = arr_result_reel[bool_isfreegame][arr_lines[iLine][iReel]][iReel]
                        if symbol == defs.WW:
                            ww_count += 1
                        else:
                            break
                    
                    if ww_count >= 2:
                        ww_payment = arr_pays[bool_isfreegame][defs.WW][ww_count-2] * arr_bet_multiplier[int_bet_indicator]
                        if ww_payment > best_payment:
                            best_payment = ww_payment
                            best_symbol = defs.WW
                            best_count = ww_count
                
                # 情況2 & 3: 統一處理所有可能的符號組合
                # 檢查每個可能的目標符號（包括第一個符號）
                for target_reel in range(num_reels):
                    target_symbol = arr_result_reel[bool_isfreegame][arr_lines[iLine][target_reel]][target_reel]
                    
                    # 跳過 WW 和不可算分的符號
                    if target_symbol == defs.WW or target_symbol == defs.C1:
                        continue
                    
                    # 從第一個位置開始檢查連續性
                    match_count = 0
                    for iReel in range(num_reels):
                        current_symbol = arr_result_reel[bool_isfreegame][arr_lines[iLine][iReel]][iReel]
                        
                        # 檢查符號是否匹配（直接比較或 WW）
                        if current_symbol == target_symbol or current_symbol == defs.WW:
                            match_count += 1
                        else:
                            break
                    
                    # 檢查是否達到最低要求且包含目標符號
                    if match_count >= 2 and target_reel < match_count:
                        target_payment = arr_pays[bool_isfreegame][target_symbol][match_count-2] * arr_bet_multiplier[int_bet_indicator]
                        if target_payment > best_payment:
                            best_payment = target_payment
                            best_symbol = target_symbol
                            best_count = match_count
                
                # 額外檢查：非 WW 開頭的傳統連線（使用 WS 相容性）
                if main_symbol != defs.WW:
                    match_count = 1
                    for iReel in range(1, num_reels):
                        checking_symbol = arr_result_reel[bool_isfreegame][arr_lines[iLine][iReel]][iReel]
                        
                        # 使用 WS 相容性檢查
                        is_compatible = False
                        for ws_idx in range(defs.WS[main_symbol].shape[0]):
                            if defs.WS[main_symbol][ws_idx] == checking_symbol:
                                is_compatible = True
                                break
                            elif defs.WS[main_symbol][ws_idx] == -1:
                                break
                        
                        if is_compatible:
                            match_count += 1
                        else:
                            break
                    
                    if match_count >= 2:
                        main_payment = arr_pays[bool_isfreegame][main_symbol][match_count-2] * arr_bet_multiplier[int_bet_indicator]
                        if main_payment > best_payment:
                            best_payment = main_payment
                            best_symbol = main_symbol
                            best_count = match_count
            
            # 記錄最佳結果
            if best_payment > 0.0:
                temp_hit = 1
                record_symbol = 4 * best_symbol + best_count - 2
                temp_HitsReport[record_symbol] += 1
                temp_PayReport[record_symbol] += best_payment * R4_mul
                
                if bool_show_log == True:
                    print(('Line', iLine+1, 'Symbol', best_symbol, 'Count', best_count, 'Payment', best_payment))
        
        WinsReport[3+bool_isfreegame] += temp_hit
    
    
        
    def BaseGame():
        """
        Base Game遊戲流程
        """
        WinsReport[0] += 1 #record total base spins
        #step1. dice rnd
        temp_dice_rnd = math.ceil(np.random.random() * int_extrafree_denominator)
        
        GetRND(0)
        
        GetReelResult(0,0)
        R4_mul = R4_spin()
        #step3. check wins
        CheckWin(0, R4_mul)
        arr_wins[0] = np.sum(temp_PayReport)
        Add_temp_report(HitsReport_Base,PayReport_Base)

    def SpinGame():
        """
        單次Spin流程
        """
        #step1. 玩Base Game
        BaseGame() 
        
        go_record((arr_wins[0] + arr_wins[1])/arr_bet_value[int_bet_indicator], thresholdMultiple, arr_output_data[17])
        return arr_wins[0] + arr_wins[1],  arr_freegame_status[0] #return 總贏分,進入free game(0次/1次)
################################################################################################
    #區分生存模式與單次spin模式與迴圈
    for dr in range(int_rounds):
        checkpoint = int_rounds // 10
        if int_thread == int_cpu-1 and dr % checkpoint == 0: #print進度
            print((dr // checkpoint)*10,'%')
        if bool_show_log == True:
            print('--')
            print('Spin', dr+1)
        if bool_survival_mode == True:
            total_credit = 0
            freeSpinRecord = 0
            total_spin = 0
            max_win_ratio = 0
            start_credit = arr_start_credit[int_bet_indicator]
            while start_credit >= arr_bet_value[int_bet_indicator] and total_spin < 2160:#沒錢或達到每人平均轉數離開
                total_spin += 1
                start_credit -= arr_bet_value[int_bet_indicator]
                total_credit += arr_bet_value[int_bet_indicator]
                totalWins, myFreeSpins = SpinGame() #單次spin game
                calculate_std(totalWins)
                start_credit += totalWins
                freeSpinRecord += myFreeSpins
                max_win_ratio = max(max_win_ratio,totalWins/arr_bet_value[int_bet_indicator])
                #---初始化所有需要初始化的變數---
                initial_1D_array(arr_wins)
                arr_freegame_status[0] = 0
                #---初始化所有需要初始化的變數---
            if start_credit < arr_bet_value[int_bet_indicator]:
                start_credit = 0
            # go_record(total_credit/10000, thresholdMultiple, arr_output_data[7])
            # go_record(freeSpinRecord, thresholdMultiple, arr_output_data[8])
            # go_record(start_credit/10000, thresholdMultiple, arr_output_data[9])
            # go_record(max_win_ratio, thresholdMultiple, arr_output_data[10])
        else:
            totalWins, myFreeSpins = SpinGame()
            calculate_std(totalWins)
            #---初始化所有需要初始化的變數---
            initial_1D_array(arr_wins)
            arr_freegame_status[0] = 0
            #---初始化所有需要初始化的變數---


lenMultiplier = len(arr_bet_multiplier)
arr_combine_report = []
for int_bet_indicator in range(lenMultiplier):
    if bool_survival_mode == True:
        opfileName = folder_path+'/'+exportfileName + ' BET-' + str(arr_bet_value[int_bet_indicator])
        arr_combine_report.append(opfileName+'.xls')
    else:
        opfileName = folder_path+'/'+exportfileName
    print('-------')
    print('BET: %d' % (arr_bet_value[int_bet_indicator]))
    # make multi-thread
    func_nb_mt = de.make_multithread(Main,TotalRound)
    finalReport, finialDuration = de.timefunc("Duration: ",func_nb_mt,int_bet_indicator)
    #export report
    de.DataExport(opfileName + '.xls',finalReport,finialDuration,arr_bet_value[int_bet_indicator],float_estimate_rtp)
    if bool_survival_mode == False:
        break
if bool_survival_mode == True and len(arr_combine_report) > 0:
    de.combine_files(arr_combine_report,'allRawData.csv')