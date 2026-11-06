# Sugar Rush Reel Cracker

抓 PP 免費試玩的 gameService 封包（不需登入）：

| 編號 | 遊戲 | gameSymbol |
|---|---|---|
| 1 | Sugar Rush 1000 | `vs20sugarrushx` |
| 2 | Sugar Rush Super Scatter | `vs20sugrushss` |

輸出在 `data/<遊戲名>/game_responses_<遊戲名>_<時間>[_tag].jsonl／.xlsx`。
`.jsonl` 每筆即時寫入，`.xlsx` 定期保存（工作表 `game_data`）。

## 兩種模式

**手動模式**（有畫面，點擊座標要校正）：直接執行 `ReelCracker_SugarRush.exe` 或 `.py`，照提示操作。

**自動模式**（無介面，可 SSH 遠端跑）：

```
ReelCracker_SugarRush.exe --auto --game 1 --spins 5000
```

| 參數 | 預設 | 說明 |
|---|---|---|
| `--game` | 1 | 1＝Sugar Rush 1000，2＝Super Scatter |
| `--spins` | 5000 | 付費轉數（以餘額被扣款的 doSpin 計） |
| `--save-every` | 200 | 每幾局保存一次 xlsx 並印進度 |
| `--tag` | 空 | 檔名後綴，同時開多個程式時區分輸出 |
| `--show` | 關 | 顯示 Chrome 視窗（本機觀察用） |
| `--no-turbo` | 關 | 改用點 Spin，不按住空白鍵（較慢） |

- 預設按住空白鍵（遊戲內建 Turbo Spin），單一程式約 1,200 局／小時（本機實測，兩個同時跑各約 1,200）。
- 只抓預設押注（底注 2.00、一般模式）；Ante／購買要用手動模式設定。
- 卡在 FG 彈窗會自動點掉；120 秒沒回應或試玩餘額低於 1,000 會重新載入。
- 同時開多個程式可倍增速度（每個都是獨立試玩 Session），每個約吃 1 核 CPU。

## 在另一台 Windows 桌機用 SSH 跑

那台桌機需要：Windows、Chrome、能連外網、已開 OpenSSH Server 並設好金鑰登入（由使用者自己設定）。

1. 複製 `portable/ReelCracker_SugarRush` 整個資料夾過去：
   ```
   scp -r portable/ReelCracker_SugarRush <帳號>@<IP>:C:/ReelCracker_SugarRush
   ```
2. 用 WMI 啟動（SSH 斷線不會把程式關掉）：
   ```
   ssh <帳號>@<IP> "powershell -c \"([wmiclass]'Win32_Process').Create('cmd /c cd /d C:\ReelCracker_SugarRush && ReelCracker_SugarRush.exe --auto --game 1 --spins 5000 --tag a > run_a.log 2>&1')\""
   ```
3. 看進度：`ssh <帳號>@<IP> "type C:\ReelCracker_SugarRush\run_a.log"`
4. 提前結束：`ssh <帳號>@<IP> "type nul > C:\ReelCracker_SugarRush\STOP"`，所有自動模式程式會保存後關閉 Chrome 結束；下次啟動前刪掉 `STOP`（`del C:\ReelCracker_SugarRush\STOP`）。
5. 取回資料：`scp -r <帳號>@<IP>:C:/ReelCracker_SugarRush/data ./data_remote`

## 封包判讀注意

- 試玩封包沒有 `rid`；付費轉數＝`req_action=doSpin` 且 `balance` 比上一筆少的列。
- `balance` 有千分位逗號。
- 連消每一步都是一筆 `doSpin`（餘額不變），回合結束有一筆 `doCollect`。
