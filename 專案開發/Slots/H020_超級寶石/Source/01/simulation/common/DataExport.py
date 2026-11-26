from numpy.core.fromnumeric import std
import xlwt
import pandas as pd
import numpy as np
import time
import math
import multiprocessing
import threading

def GetFromExcel(str_fileName,arr_sheetName,bool_transpose,str_datatype,int_default_value=-1,bool_cumsum=False):
    '''
    str_fileName=檔案名稱 ex:'Parsheet.xlsx'\n
    arr_sheetName=[頁籤名稱1,頁籤名稱2...] ex:['base','free']\n
    bool_transpode=是否要矩陣轉置\n
    str_datatype=資料的格式 ex:np.int8, np.float64, np.bool_\n
    int_default_value=資料的預設值，預設為-1\n
    bool_cumsum=資料是否要累加，若累加則[1,1,1,1]會變成[1,2,3,4]
    '''
    arr_dataframe = []
    arr_max_shape = [0,0]
    int_file_counts = len(arr_sheetName)
    for sheets in range(int_file_counts):
        arr_temp_dataframe = pd.read_excel(str_fileName,sheet_name=arr_sheetName[sheets],engine='openpyxl')
        arr_max_shape[0] = max(arr_max_shape[0],arr_temp_dataframe.shape[0])
        arr_max_shape[1] = max(arr_max_shape[1],arr_temp_dataframe.shape[1])
        arr_dataframe.append(arr_temp_dataframe)
    if bool_transpose == False:
        arr_main = np.full(shape=(int_file_counts,arr_max_shape[1],arr_max_shape[0]),fill_value=int_default_value,dtype=str_datatype)
        for sheets in range(int_file_counts):
            for i, arrayName in enumerate(arr_dataframe[sheets]):
                temp_element = 0
                for j, element in enumerate(arr_dataframe[sheets][arrayName]):
                    if np.isnan(element) == False:
                        if bool_cumsum == True:
                            temp_element += element
                            arr_main[sheets][i][j] = temp_element
                        else:
                            arr_main[sheets][i][j] = element
    else:
        arr_main = np.full(shape=(int_file_counts,arr_max_shape[0],arr_max_shape[1]),fill_value=int_default_value,dtype=str_datatype)
        for sheets in range(int_file_counts):
            for i, arrayName in enumerate(arr_dataframe[sheets]):
                temp_element = 0
                for j, element in enumerate(arr_dataframe[sheets][arrayName]):
                    if np.isnan(element) == False:
                        if bool_cumsum == True:
                            temp_element += element
                            arr_main[sheets][j][i] = temp_element
                        else:
                            arr_main[sheets][j][i] = element
    if int_file_counts == 1:
        if arr_main[0].shape[0] == 1:
            return arr_main[0][0]
        else:
            return arr_main[0]
    else:
        return arr_main

def timefunc(s, func, *args, **kwargs):
    """
    Benchmark *func* and print out its runtime.
    """
    print('---start at--- %s' % (time.ctime()))
    time1 = time.time()
    res = func(*args, **kwargs)
    time2 = time.time()
    minutes, seconds = divmod(time2 - time1, 60)
    hours, minutes = divmod(minutes, 60)
    print(s + '%s hours, %s minutes, %s seconds' %
          (math.floor(hours), math.floor(minutes), math.floor(seconds)))
    return res, time2 - time1

def make_multithread(inner_func,dtTotalRound):
    """
    Run the given function inside *numthreads* threads, splitting its
    arguments into equal-sized chunks.
    """
    multithread_bc = 10000
    def func_mt(*args):
        if dtTotalRound > multithread_bc:
            #print multithread status
            numthreads = multiprocessing.cpu_count()
            print('Multi-Thread Mode: On (%d Thread)' % (numthreads))
        else:
            numthreads = 1
            print('Multi-Thread Mode: Off')
        threadSpins = dtTotalRound // numthreads #總次數/thread數的商
        result = np.zeros((numthreads,40,68), np.float64) #array for return
        chunks = []
        if numthreads == 1:
            chunks.append((result[0],0,threadSpins,) + args)
        else:
            for int_thread in range(numthreads-1):
                chunks.append((result[int_thread],int_thread,threadSpins,) + args)
            chunks.append((result[numthreads-1],numthreads-1,dtTotalRound - threadSpins * (numthreads-1),) + args)
        
        # threading.Thread 可以創建新的線程并在其上運行函数。target放目標函數.在創建線程對象后，可以調用其start()方法来啟動線程
        threads = [threading.Thread(target=inner_func, args=chunks[t]) for t in range(len(chunks))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        #processing max data
        if numthreads > 1:
            int_single_max_win = result[0][0][5]
            for int_thread in range(numthreads-1):
                int_single_max_win = max(int_single_max_win,result[int_thread+1][0][5])
                result[0] += result[int_thread+1]
            result[0][0][5] = int_single_max_win
        return result[0]
    return func_mt

def DataExport(opfileName,finalReport,finialDuration,GameBet,float_estimate_rtp,bool_force_export=False):

    # thresholdMultiple = [0,0,0.5,1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50,60,70,80,90,100,125,150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,600,700,800,900,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,12000,14000,16000,18000,20000,22000,24000,26000,28000,30000,35000,40000,99999]
    thresholdMultiple = np.array([
         0,     0,     1,     2,      3,      4,      5,       6,      7,      8,
         9,    10,    15,    20,     25,     30,     35,      40,     45,     50,
        60,    70,    80,    90,    100,    120,    140,     160,    180,    200,
       250,   300,   350,   400,    450,    500,    550,     600,    650,    700,
       750,   800,   850,   900,    950,   1000,   2000,    3000,   4000,   5000,
      6000,  7000,  8000,  9000,  10000,  20000,  30000,  100000,
    999999
], np.float64)
    # print result
    print('Total Spins: %s' % (format(int(finalReport[0][0]),',')))
    if GameBet >= 250:
        Costs = GameBet * finalReport[0][0]/10
    else:
        Costs = GameBet * finalReport[0][0]  
    baseRTP = np.sum(finalReport[2]) / Costs
    # freeRTP = (np.sum(finalReport[4]) + np.sum(finalReport[6]) + np.sum(finalReport[8]) + np.sum(finalReport[10]) + np.sum(finalReport[12]) + np.sum(finalReport[14]) + np.sum(finalReport[16])) / Costs
    gameSTD = np.sqrt(finalReport[0][10]/finalReport[0][0]) / GameBet
    std_threshold = np.array([0,7,9,11,13],np.int8)
    str_std_level = 'Lv' + str(std_threshold.shape[0])
    for i in range(std_threshold.shape[0]-1):
        if std_threshold[i] <= gameSTD < std_threshold[i+1]:
            str_std_level = 'Lv' + str(i + 1)
            break
    targetErr = 0.02
    EstimateSpins_99 = np.square((2.576 * gameSTD) / targetErr)
    EstimateSpins_95 = np.square((1.96 * gameSTD) / targetErr)
    TotalRTP = baseRTP
    ErrRRP = TotalRTP - float_estimate_rtp

    print('baseRTP:%.2f%%\n (Err:%.4f%%)' % (baseRTP*100,ErrRRP*100))
    print('變異係數(%s):%.2f -> 收斂至正負2%%Spin次數 99%%信心:%s  95%%信心:%s' % (str_std_level,gameSTD,format(int(EstimateSpins_99),','),format(int(EstimateSpins_95),',')))
    float_max_parameter = 0.00000005
    int_sum_diagram = np.sum(finalReport[5])
    if int_sum_diagram > 0:
        arr_max_diagram = np.zeros(finalReport[0].shape[0],np.float64)
        for i in range(arr_max_diagram.shape[0]):
            arr_max_diagram[i] = finalReport[18][i] / int_sum_diagram
        arr_max_diagram = np.flipud(arr_max_diagram)
        arr_max_diagram = np.cumsum(arr_max_diagram)
        arr_max_diagram = np.flipud(arr_max_diagram)
        int_max_result = 0
        for i in range(arr_max_diagram.shape[0]):
            if arr_max_diagram[i] < float_max_parameter:
                int_max_result = i - 1
                break
        print('最大倍數(機率大於億分之5):%d' % (thresholdMultiple[int_max_result + 1]))
    hitspin = 0
    # original_hitspin = 0
    # guarantee_hitspin = 0
    retriggerhit = 0
    freegamehits = 0
    retriggerhits = 0
    BaseHitRate = 0
    FreeHitRate = 0
    for i in range(4):
        freegamehits += finalReport[1][4+i]
        retriggerhits += finalReport[2][4+i]
    if freegamehits != 0:
        hitspin = round(finalReport[0][0]/freegamehits, 0)
        # original_hitspin = round(finalReport[0][0]/(freegamehits - finalReport[0][2]), 0)
        # if finalReport[0][2] != 0:
        #     guarantee_hitspin = round(finalReport[0][0]/finalReport[0][2], 0)
    if retriggerhits != 0:
        retriggerhit = round(finalReport[0][1]/retriggerhits, 0)
    print('freegame pull-hit:%d, retrigger pull-hit:%d' % (hitspin,retriggerhit))
    BaseHitRate = finalReport[0][3]/finalReport[0][0]
    if finalReport[0][1] > 0:
        FreeHitRate = finalReport[0][4]/finalReport[0][1]
    print('base hit%%:%.2f%%, free hit%%:%.2f%%' % (BaseHitRate*100,FreeHitRate*100))
    spin_per_second = (finalReport[0][0]+finalReport[0][1]) // finialDuration
    print('Average Speed: %d spins per second' % (spin_per_second))
    # =================================================
    # print(f're-spin used freq.: {finalReport[0][7]/finalReport[0][0]*100:.2f}%')
    print(f're-spin used prob.: {finalReport[0][7]/finalReport[0][0]*100:.2f}%')
    print(f're-spin avg. times: {finalReport[0][8]/finalReport[0][7]:.2f}')
    R4_mul = np.array([1,2,3,5,10,15,20,25,50,100,500,0],np.int32)
    for i in range(R4_mul.shape[0]):
        print(f'R4 multi {R4_mul[i]:>3d} prob.: {finalReport[0][11+i]/finalReport[0][0]*100:.2f}%')
    # =================================================
    #Base+Free總次數大於百萬次才輸出報表
    if (finalReport[0][0] + finalReport[0][1] >= 1000000 and bool_force_export == False) or (bool_force_export == True):
        file = xlwt.Workbook()  # Work的W是大寫
        table = file.add_sheet('Data Export', cell_overwrite_ok=True)  # 對同個儲存格可複寫的sheet
        RawData = file.add_sheet('Raw Data', cell_overwrite_ok=True)  # 對同個儲存格可複寫的sheet
        table.write(0, 0, 'Total Spins')
        table.write(0, 1, int(finalReport[0][0]))
        table.write(0, 2, 'Duration')
        table.write(0, 3, str('%s seconds' % (int(finialDuration))))
        table.write(0, 4, 'Base RTP')
        table.write(0, 5, float(baseRTP))
        
        table.write(0, 10, 'Base Hit%')
        table.write(0, 11, float(BaseHitRate))
        
        # table.write(1, 6, '99% CI Spins(Error=2%)')
        # table.write(1, 7, float(EstimateSpins_99))
        # table.write(1, 8, '95% CI Spins(Error=2%)')
        # table.write(1, 9, float(EstimateSpins_95))
        table.write(3, 0, 'Hit Report')
        table.write(3, 1, 'Base Game hit%')
        table.write(3, 2, 'Base Game pay')
        table.write(3, 3, 'R4_Reel Result')
        table.write(3, 4, 'nudge number')
        table.write(3, 5, 'nudge倍數2~4')
        table.write(3, 6, 'nudge倍數5~7')
        table.write(3, 7, 'nudge倍數8~10')
        table.write(3, 8, 'nudge倍數20/50')
        table.write(3, 9, 'Win Multiple Range')
        table.write(3, 10, 'Base Game Hit Count')
        table.write(3, 11, 'Hit Probability')
        
        SymbolDefination = ['WW','C1','C2','C3','M1','M2','M3','M4','M5','M6',
                            'MY','A','K','Q','J','TE','NI']
        # fill in symbol defination
        x = 0
        for item in SymbolDefination:
            table.write(4 * x + 4, 0, str(item+'x2'))
            table.write(4 * x + 5, 0, str(item+'x3'))
            table.write(4 * x + 6, 0, str(item+'x4'))
            table.write(4 * x + 7, 0, str(item+'x5'))
            x += 1
        
        try:
            #fill in HitsReport_Base
            x = 4
            y = 1
            for item in finalReport[1]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1
            #fill in PayReport_Base
            x = 4
            y = 2
            for item in finalReport[2]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1
            
            x = 4
            y = 3
            for item in finalReport[5]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1

            x = 4
            y = 4
            for item in finalReport[6]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1

            x = 4
            y = 5
            for item in finalReport[7]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1
            
            x = 4
            y = 6
            for item in finalReport[10]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1

            x = 4
            y = 7
            for item in finalReport[13]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1

            x = 4
            y = 8
            for item in finalReport[16]:
                if 'int' in str(type(item)):
                    table.write(x, y, int(item))  # 對某個儲存格寫入資料
                elif 'str' in str(type(item)):
                    table.write(x, y, str(item))  # 對某個儲存格寫入資料
                else:
                    table.write(x, y, item)
                x += 1
            x = 4
            y = 9
            win_thresholds = thresholdMultiple
            max_threshold_index = min(len(finalReport[18]), len(win_thresholds) - 1)
            total_base_spins = float(finalReport[0][0]) if finalReport[0][0] != 0 else 0.0
            for idx in range(max_threshold_index):
                lower = win_thresholds[idx]
                upper = win_thresholds[idx + 1]
                if lower == upper:
                    label = f'x = {lower:g}'
                else:
                    label = f'{lower:g} < x <= {upper:g}'
                table.write(x, y, label)
                raw_count = finalReport[18][idx]
                count_output = raw_count
                try:
                    numeric_count = float(raw_count)
                except (TypeError, ValueError):
                    numeric_count = 0.0
                if total_base_spins > 0.0:
                    prob_value = numeric_count / total_base_spins
                else:
                    prob_value = 0.0
                try:
                    count_output = int(raw_count)
                except (TypeError, ValueError):
                    count_output = raw_count
                table.write(x, y + 1, count_output)
                table.write(x, y + 2, prob_value)
                x += 1
            # #fill in win threhold
            # #--------------------
            # #--------------------
            # x = 4
            # y = 6
            # for i in range(len(thresholdMultiple)-1):
            #     table.write(x, y, str('%.1f< x <=%.1f' % (thresholdMultiple[i],thresholdMultiple[i+1])))  # 對某個儲存格寫入資料
            #     x += 1
            # #fill in BaseThreholdReport
            # x = 4
            # y = 7
            # for item in finalReport[5]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # #fill in FreeThreholdReport
            # x = 4
            # y = 8
            # for item in finalReport[6]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # #fill in SurvivalCreditReport
            # x = 4
            # y = 9
            # for item in finalReport[7]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # #fill in SurvivalFreeGameReport
            # x = 4
            # y = 10
            # for item in finalReport[8]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # #fill in NetWinReport
            # x = 4
            # y = 11
            # for item in finalReport[9]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # y = 0
            # #fill in MaxWinReport
            # x = 4
            # y = 12
            # for item in finalReport[10]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # #fill in Respin hit
            # x = 4
            # y = 14
            # for item in finalReport[11]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
            # #fill in Respin pay
            # x = 4
            # y = 15
            # for item in finalReport[12]:
            #     if 'int' in str(type(item)):
            #         table.write(x, y, int(item))  # 對某個儲存格寫入資料
            #     elif 'str' in str(type(item)):
            #         table.write(x, y, str(item))  # 對某個儲存格寫入資料
            #     else:
            #         table.write(x, y, item)
            #     x += 1
                
        except Exception as e:
            print(f'你遇到了還沒定義要如何處理的錯誤: {e}')
        finally:
            y = 0
            for items in finalReport:
                x = 0
                for item in items:
                    if 'int' in str(type(item)):
                        RawData.write(x, y, int(item))  # 對某個儲存格寫入資料
                    elif 'str' in str(type(item)):
                        RawData.write(x, y, str(item))  # 對某個儲存格寫入資料
                    else:
                        RawData.write(x, y, item)
                    x += 1
                y += 1
            file_error = 1
            export_success = False
            while export_success == False:
                try:
                    file.save(opfileName)  # 儲存為excel
                    export_success = True
                except:
                    opfileName = opfileName.replace('.xls', '') + '_' + str(file_error) + '.xls'
                    file_error += 1
            print('data exported to %s.' % (opfileName))
            print('---end at--- %s' % (time.ctime()))

def combine_files(arr_input,str_output):
    if len(arr_input) == 0:
        return
    arr_main_data = pd.read_excel(arr_input[0],'Raw Data',header=None,dtype=np.int64)
    for int_input in range(1, len(arr_input)):
        arr_other_data = pd.read_excel(arr_input[int_input],'Raw Data',header=None,dtype=np.int64)
        arr_main_data = pd.concat([arr_main_data,arr_other_data])
    arr_main_data.to_csv(str_output,header=False,index=False)

def sum_array_parameters(arr_input):
    arr_output = np.zeros((arr_input.shape[0],arr_input.shape[1]),np.int64)
    for sheets in range(arr_input.shape[0]):
        for iReel in range(arr_input.shape[1]):
            arr_output[sheets][iReel] = np.sum(arr_input[sheets][iReel])
    return arr_output

if __name__ == '__main__':
    arr_parameters = GetFromExcel('Parameters.xlsx',['Regular','Free'], False, np.int32)
    print(sum_array_parameters(arr_parameters))
