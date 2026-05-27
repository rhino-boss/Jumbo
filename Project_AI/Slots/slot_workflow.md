# Slot 新專案流程

## 目的

這份文件用來整理：如果要開一個新的 slot 專案，參考 `Project_AI` 底下既有 `.md` 與 `H026_彩罐熱舞` 範例時，應該先看什麼、再確認什麼資料、以及每個階段資料到位後才建立哪些資料夾與檔案。

---

## 一、先看哪些參考文件

### 1. 共用規範

1. `Project_AI/slot_demogame_standards.md`
   - 用途：定義 `Demogame` 應有哪些 UI 區塊、互動、資料綁定、RNG 顯示、最低驗收標準。
   - 影響輸出：`index.html`、部分 `config.js` 欄位需求。

2. `Project_AI/slot_simulator_standards.md`
   - 用途：定義 `Simulator.py` 的程式結構、前段設定區、Numba 核心、console 顯示、xlsx 報表輸出格式。
   - 影響輸出：`Simulator.py`、`Record/*.xlsx`。

### 2. 專案規格文件

3. `Project_AI/<專案資料夾>/game_rule.md`
   - 用途：定義玩法規則。
   - 內容至少包含：盤面、symbol、paytable、核心流程、feature、FG、Buy Feature、edge cases。
   - 影響輸出：`config.js` 欄位設計、`Simulator.py` 邏輯、`index.html` 顯示內容。

4. `Project_AI/<專案資料夾>/Tool/xlsx_config_usage_mapping.md`
   - 用途：說明 `xlsx -> config.js -> simulator/index.html` 的資料流。
   - 若該專案暫時不走 `xlsx` generator 流程，可延後建立。

---

## 二、流程操作原則

### 1. 先確認資料，再建立檔案

新專案流程中，不應一開始就把整套資料夾與檔案全部建出來。

原則如下：

1. 先確認該步驟所需資料是否已提供
2. 該步驟可以成立後，才建立對應資料夾或空檔案
3. 若資料尚未提供齊全，停在當前步驟，不提前建立下一步檔案

### 2. 模擬流程時的確認方式

如果是在模擬開案流程，不一定要真的提供檔案內容，可以只確認「是否已提供」。

例如：

1. `提案文件：有`
2. `Help 截圖：有`
3. `主來源：提案文件`

只要流程判定資料已到位，就可以進下一步並建立對應空檔案。

### 3. 允許兩種主流程

新專案可依情況選擇下列其中一條主流程：

1. `xlsx generator 流程`
   - 有數學 `xlsx`
   - 要做 `xlsx_to_config.py`
   - `config.js` 由 generator 產生

2. `手工 config 流程`
   - 先根據 `game_rule.md` 討論需要哪些權重與設定表
   - 不先做 `xlsx_to_config.py`
   - 直接手工建立 `config.js`
   - 再由 `config.js` 延伸出 `Simulator.py` 與 `index.html`

---

## 三、標準建立順序

### Step 1. 確認玩法來源並建立專案起始檔

先確認下列資料是否已提供：

1. 遊戲提案文件
2. Help 截圖 / 競品說明
3. 主來源

規則：

1. 若提案與 Help / 競品可能衝突，必須先決定主來源
2. 在主來源未確認前，`Step 1` 不算完成

這一步完成後才建立：

1. 專案資料夾 `Project_AI/<專案名稱>`
2. `game_rule.md`

輸出：

1. `game_rule.md`

### Step 2. 確認 config 需要的資料來源

這一步依專案選的主流程分成兩種。

#### Step 2A. 若走 xlsx generator 流程

先確認數學 `xlsx` 是否能支撐 runtime 需要的欄位。

至少要確認：

1. `overview`
2. `pay_table`
3. `paylines`
4. `value`
5. `weight`
6. 各場景 strip sheet
7. 是否有足夠資料支援 feature 規則

這一步完成後才建立：

1. `Source`
2. `Tool`
3. `Tool/xlsx_config_usage_mapping.md`
4. `Tool/xlsx_to_config.py`
5. `update_config.bat`

輸出：

1. 新專案的數學 `xlsx`
2. `Tool/xlsx_config_usage_mapping.md`
3. `Tool/xlsx_to_config.py`
4. `update_config.bat`

#### Step 2B. 若走手工 config 流程

先根據 `game_rule.md` 討論這款遊戲需要哪些權重與設定表。

常見會確認的項目：

1. 基本下注設定
2. bet mode 設定
3. paytable
4. paylines / ways 規則
5. symbol 定義
6. reel strips
7. reel stop weights
8. table selection weights
9. drop weights
10. wild / scatter 權重
11. feature trigger 權重
12. multiplier 權重
13. free game 進場設定
14. retrigger 權重
15. buy feature 設定
16. 特殊機制權重

這一步完成後才建立：

1. `config.js`
2. 視需要建立 `Source`、`Tool`、`Record`

輸出：

1. 權重 / 設定表需求清單
2. 空的 `config.js`

### Step 3. 生成或建立 config.js

#### 若走 xlsx generator 流程

流程為：

1. 提供 `xlsx`
2. 用 `update_config.bat`
3. `update_config.bat` 呼叫 `Tool/xlsx_to_config.py`
4. 生成或更新 `config.js`

#### 若走手工 config 流程

流程為：

1. 根據 `game_rule.md` 與已確認的權重表
2. 直接建立或補齊 `config.js`

重點：

1. `config.js` 應成為 simulator 與 demogame 的共同資料來源
2. 若目前只是跑流程模擬，也可以只先建立空的 `config.js`

輸出：

1. `config.js`

### Step 4. 建立 Simulator.py

參考來源：

1. `slot_simulator_standards.md`
2. `game_rule.md`
3. `config.js`

這一步完成後才建立：

1. `Simulator.py`
2. `Record`

若目前只是跑流程模擬，也可以只先建立空的 `Simulator.py`。

輸出：

1. `Simulator.py`
2. `Record/*.xlsx`

### Step 5. 建立 index.html

參考來源：

1. `slot_demogame_standards.md`
2. `game_rule.md`
3. `config.js`

這一步完成後才建立：

1. `index.html`
2. 若缺素材則建立 `Source/Image`

若目前只是跑流程模擬，也可以只先建立空的 `index.html`。

輸出：

1. `index.html`

### Step 6. 驗證資料流一致

若走 `xlsx generator 流程`，要確認：

1. `xlsx` 的主要欄位都有正確進 `config.js`
2. `Simulator.py` 與 `index.html` 讀的是同一份欄位定義
3. 規則文件、數學資料、runtime 行為三者一致

若走 `手工 config 流程`，要確認：

1. `game_rule.md` 定義的玩法都有對應到 `config.js`
2. `Simulator.py` 與 `index.html` 讀的是同一份 `config.js`
3. 若未來要接 `xlsx`，需再補 generator 流程

輸出：

1. 更新版 `xlsx_config_usage_mapping.md` 或手工欄位說明
2. 修正後的 `config.js` / `Simulator.py` / `index.html`

---

## 四、最推薦的實作依賴順序

### 1. 完整正式版

1. `game_rule.md`
2. 數學 `xlsx`
3. `Tool/xlsx_to_config.py`
4. `config.js`
5. `Simulator.py`
6. `index.html`
7. `Tool/xlsx_config_usage_mapping.md`
8. `Record/*.xlsx`

### 2. 快速模擬版

1. 確認提案 / Help / 主來源
2. 建立專案資料夾與 `game_rule.md`
3. 根據 `game_rule.md` 討論需要哪些權重與設定表
4. 建立空的 `config.js`
5. 建立空的 `Simulator.py`
6. 建立空的 `index.html`

---

## 五、H026 可作為哪些參考

### 主要參考

1. `slot_demogame_standards.md`
2. `slot_simulator_standards.md`
3. `H026_彩罐熱舞/game_rule.md`
4. `H026_彩罐熱舞/Tool/xlsx_config_usage_mapping.md`
5. `H026_彩罐熱舞/Source` 內數學 `xlsx` 與素材

### 主要手工產出

1. `game_rule.md`
2. `Tool/xlsx_to_config.py`
3. `update_config.bat`
4. `Simulator.py`
5. `index.html`
6. `Tool/xlsx_config_usage_mapping.md`

### 主要生成產出

1. `config.js`
2. `Record/*.xlsx`
3. `__pycache__` 可忽略

---

## 六、最短版本流程

如果只看這次模擬過的最短執行順序，就是：

1. 先確認 `提案文件`、`Help 截圖`、`主來源`
2. `Step 1` 完成後，建立專案資料夾與 `game_rule.md`
3. 根據 `game_rule.md` 討論需要哪些權重與設定表
4. 建立空的 `config.js`
5. 建立空的 `Simulator.py`
6. 建立空的 `index.html`

這個版本適合：

1. 先演練流程
2. 先開專案骨架
3. 之後再補正式內容
