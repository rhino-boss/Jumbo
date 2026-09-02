package com.jumbogames.sps.logic.BaseGame;

import com.JH5.jps.ExtendJackpotSetting.JackpotExtendSetting_OPJackpot_jumbo;
import com.JH5.jps.JackpotHandler_OPJackpot_jumbo;
import com.base.jps.Jackpot.JackpotResult;
import com.base.sps.common.Common;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;
import com.jumbogames.sps.entity.client.ExtendBaseGameResult.ExtendInfoForBaseGameResult_JHS101027;
import com.jumbogames.sps.entity.client.ExtendBaseGameSetting.BaseGameExtendSetting_JHS101027;
import com.jumbogames.sps.entity.client.GameStatusCaches.SeatStatusCache_101001;
import com.jumbogames.sps.logic.BaseGame.ExtendDataFromBaseToFeatureGame_JHS101027;
import com.base.sps.entity.system.ScreenCalculatorResult;
import com.base.sps.entity.system.SpecialFeatureCalculatorResult;
import com.base.sps.entity.client.*;
import com.base.sps.entity.client.EnumHandler.SpecialHitInfo;
import com.base.sps.logic.ScreenGeneratorResult;
import com.jumbogames.sps.logic.BaseGameHandler;

import java.util.*;

/**
 * 描述：此物件負責產生本局的基本盤面，並計算其結果。
 * 101027（奧林帕斯2500）：Any-8 count-anywhere + Cascade 消除架構沿用101006；
 * OP Jackpot 架構沿用101006；本作無Wild（§9.1），輪帶不出現WW、不參與Any-8替代、也沒有WW→C2。
 * 與101006的差異：C2、C3皆提供乘倍值，但只有C3每次消除後往上升一級，C2維持原值不變（§3.2，見 mergeSpecialScreen 內 getUpgradedMultiplierValue）。
 * Extra Bet / Buy Feature 的專用盤面邏輯待下個階段補上，目前兩者皆走一般輪帶。
 * @author AI
 * 日期：
 */
public class BaseGameHandler_JHS101027 extends BaseGameHandler {
    private int highLow = 0;
    private int betIdx;
    private final int statusMaxAccum = 350;
    private SeatStatusCache_101001 seatStatusCache;
    private SeatInfo seatInfo;

    private BaseGameExtendSetting_JHS101027 extendBaseSetting = new BaseGameExtendSetting_JHS101027();

    public BaseGameHandler_JHS101027(Common common) {
        super(common);
        seatStatusCache = new SeatStatusCache_101001();
        seatInfo = new SeatInfo();
    }


    public EnumHandler.ErrorCode initialGameStatusCache(int denom, String gameStatusCache){
        extendBaseSetting = (BaseGameExtendSetting_JHS101027) super.baseGameSetting.getBaseGameExtendSetting();
        this.common.setDenom(denom);

        // 建立 gameStatusCache
        if ( gameStatusCache == null ){
            gameStatusCache = new Gson().toJson(new SeatStatusCache_101001());
        }

        GsonBuilder gsonBuilder = new GsonBuilder();
        gsonBuilder.setLenient();
        Gson gson = gsonBuilder.create();
        SeatStatusCache_101001 gameStatusCacheObj = null;

        try {
            gameStatusCacheObj = gson.fromJson(gameStatusCache, SeatStatusCache_101001.class);
        }
        catch (JsonSyntaxException e){
            if (e.getMessage().equals("IllegalStateException"))
                gameStatusCacheObj = new SeatStatusCache_101001();
        } catch (Exception e) {
            e.printStackTrace();
        }
        System.out.println( "initialGameStatusCache gameStatusCacheObj = " + gameStatusCacheObj);

        if (gameStatusCacheObj == null
                || gameStatusCacheObj.getSeatInfo() == null
                || denom != gameStatusCacheObj.getDenom()
                || !isSeatInfo(gameStatusCacheObj.getSeatInfo())) {
            initialSeatStatusCache();
        }
        else {
            this.seatInfo = gameStatusCacheObj.getSeatInfo().Copy();
            setRedisAccumulateData(this.seatInfo.getStatusAccumulation()[0]);
            setRedisGameWaterLevel(this.seatInfo.getMiniGameWaterLevel());
            this.seatStatusCache.setSeatInfo(this.seatInfo);
            this.seatStatusCache.setGameType(gameStatusCacheObj.getGameType());
            this.seatStatusCache.setDenom(gameStatusCacheObj.getDenom());
        }

        return EnumHandler.ErrorCode.Correct;
    }

    // 初始化 seatStatusCache 資料
    public Object initialGameData(){
        Object initialGameData = this.seatStatusCache;
        Map<String, Object> map = new HashMap<>();
        map.put("seatStatusCache", initialGameData);

        return map;
    }

    public String getGameStatusCache(){
        SeatStatusCache_101001 gameStatusCache = new SeatStatusCache_101001();
        gameStatusCache.setGameType(this.common.getGameType());
        gameStatusCache.setDenom(this.common.getDenom());
        if (this.seatInfo != null)
            gameStatusCache.setSeatInfo(this.seatInfo);
        return new Gson().toJson(gameStatusCache);
    }

    public BaseGameResult getSpinResult(SlotSpinRequest slotSpinRequest) {

        // 確認是否成功被初始化。
        if(invalidSpinRequest(slotSpinRequest))
            return new BaseGameResult();
        this.betIdx = getBetIndex(slotSpinRequest);
        if (this.common.getSpinType() == EnumHandler.SpinType.OddsSpin){
            if (this.common.getSettingIdType() == 2 || this.common.getSettingIdType() == 3 || availableHitJPOption[this.common.getElementIndex(availableBetMultiplier,slotSpinRequest.getBetRequest().getWaysBet())] == 3){
                this.common.setNoHitGrand(true);
            }
            highLow = baseGameSetting.getOddsGroupingIdx()[this.common.getWeightTableIndex()][this.common.getBaseGameOddsSpinInfo().getOddsLevelIdx()];
        }
        extendBaseSetting = (BaseGameExtendSetting_JHS101027) super.baseGameSetting.getBaseGameExtendSetting();

        // 產生一個畫面。
        ScreenGeneratorResult screenGeneratorResult = GenerateScreenLabel(slotSpinRequest.getExtraBetType());

        // C2起始/升級倍數、C2→C3轉換的權重列直接對應這次用哪套輪帶(tableIdx)
        int selectC2Table = getC2WeightRow(screenGeneratorResult.tableIdx);

        // 滾停初始盤面若出現C2，依目前C2顆數各自獨立骰一次轉C3（§3.2 weight_C2_to_C3_by_initial_count）
        int[] multiplierSymbolIds = getMultiplierSymbolIds();
        applyInitialC2ToC3Conversion(screenGeneratorResult.screenLabel, selectC2Table, multiplierSymbolIds);

        // 計算產生的畫面結果，並且將結果紀錄於spinResult中。
        ScreenCalculatorResult screenCalculatorResult = screenCalculator.CalculateCrushCountScreenResult(slotSpinRequest, screenGeneratorResult.screenLabel, extendBaseSetting.getHitCrushCount());

        //C2 乘倍位置與數字
        int[][] specialScreen = getSpecialScreenMultiplier(screenGeneratorResult.screenLabel, selectC2Table);

        // 計算by game 資訊 - 消消樂流程處理
        ExtendInfoForBaseGameResult_JHS101027 extendInfoForBaseGameResult = calculateExtendInfoForBaseGameResult(slotSpinRequest, screenGeneratorResult, screenCalculatorResult,specialScreen,selectC2Table);

        // 使用最後的畫面判斷是否中了特殊feature。
        SpecialFeatureCalculatorResult specialFeatureCalculatorResult = specialFeatureHandler.getFeatureResult(getLastScreenLabel(screenGeneratorResult, extendInfoForBaseGameResult), slotSpinRequest);

        specialFeatureCalculatorResult = RecalculatespecialFeatureCalculatorResult1(screenGeneratorResult.screenLabel,
                specialFeatureCalculatorResult,
                slotSpinRequest);

        extendInfoForBaseGameResult = calculateMiniWaterLvl(extendInfoForBaseGameResult,screenGeneratorResult,specialFeatureCalculatorResult);

        //計算盤面有幾個C1
        int sysScatterCount = getSymbolCount(getLastScreenLabel(screenGeneratorResult, extendInfoForBaseGameResult), EnumHandler.SymbolAttribute.FreeGame);
        extendInfoForBaseGameResult.setSysScatterCount(sysScatterCount);

        JackpotResult jackpotResult = calculateMiniGameResult(screenGeneratorResult.screenLabel,
                specialFeatureCalculatorResult,
                slotSpinRequest);


        ExtendDataFromBaseToFeatureGame_JHS101027 extendDataFromBaseToFeatureGame = calculateExtendDataFromBaseToFeatureGame(extendInfoForBaseGameResult, specialFeatureCalculatorResult, jackpotResult, getPlayerBetLevel(slotSpinRequest));
        long initialScreenWin = getInitialScreenWin(screenCalculatorResult);

        // 計算BG贏分乘倍（Scatter贏分不乘倍，維持在calculateBaseGameTotalWin_JHS101027裡原樣加總，見該method註解）
        extendInfoForBaseGameResult.calculateExtendTotalWin(initialScreenWin);

        // 依照畫面資訊以及聽牌邏輯，計算表演資訊。
        DisplayInfo displayInfo = null;

        // 包裝spinResult
        BaseGameResult result = packageRoundResult_JHS101027(screenGeneratorResult, screenCalculatorResult, specialFeatureCalculatorResult, extendInfoForBaseGameResult, null,slotSpinRequest);

        return result;
    }

    // C2/C3乘倍、C2→C3轉換的權重列直接對應「這次用哪套輪帶」；multiplierWeightC2現在跟tableCount一樣有4列(BG_Symbol/(2)/(3)+BF)，不用再clamp
    private int getC2WeightRow(int tableIdx) {
        return tableIdx;
    }

    protected SpecialFeatureCalculatorResult RecalculatespecialFeatureCalculatorResult1(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest) {

        if(common.isNoHitGrand()) {
            //新手不拉Grand
            for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; ++i) {
                if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo() == SpecialHitInfo.bonusGame_02) {
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i);
                } else if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo() == SpecialHitInfo.bonusGame_01 && isSettingIDWithoutBonus())
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i); // 新老手救援+新手體驗 不提供MiniGame
            }
        }
        return specialFeatureCalculatorResult;
    }

    private int[][] getEliminatePosition(WaysResult[] srcWaysResult){
        int[][] eliminatePosition = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];

        for (WaysResult wayResult:srcWaysResult) {
            boolean[][] screenHitData = wayResult.getScreenHitData();
            for (int i = 0; i < screenHitData.length; i++) {
                for (int j = 0; j < screenHitData[0].length; j++) {
                    if (screenHitData[i][j] == true)
                        eliminatePosition[i][j] = EnumHandler.EliminateType.Eliminate.ordinal();
                }
            }
        }
        return eliminatePosition;
    }

    private int[] getCantRepeatSymbolId(){
        int[] result = new int[]{-1,-1};
        for (int i = 0; i < baseGameSetting.getSymbolAttribute().length; i++) {
            if (baseGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.FreeGame)
                result[0] = i;
        }
        return result;
    }

    // 找出C2、C3的symbol id，兩者都需要在cascade掉落時被framework用rngInfo==-2追蹤延續（見generateCrushEliminateFallDownScreen）。
    private int[] getMultiplierSymbolIds(){
        int c2Id = -1;
        int c3Id = -1;
        for (int i = 0; i < baseGameSetting.getSymbolAttribute().length; i++) {
            if (baseGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.ballC2)
                c2Id = i;
            if (baseGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.ballC3)
                c3Id = i;
        }
        return new int[]{c2Id, c3Id};
    }

    protected ExtendInfoForBaseGameResult_JHS101027 calculateExtendInfoForBaseGameResult(SlotSpinRequest slotSpinRequest, ScreenGeneratorResult screenGeneratorResult, ScreenCalculatorResult screenCalculatorResult, int[][] specialScreen,int selectC2Table) {
        ExtendInfoForBaseGameResult_JHS101027 result = new ExtendInfoForBaseGameResult_JHS101027();
        ArrayList<CascadeEliminateResult> cascadeEliminateResult = new ArrayList<CascadeEliminateResult>(); // 紀錄每一次消除結果。

        int tableIdx = screenGeneratorResult.tableIdx;
        //計算使用哪個輪帶表
        int extraMultiplier = 1;
        int [][] roundRngInfo = screenGeneratorResult.getRngInfo();
        int[][] roundSpecialScreen = specialScreen.clone();
        int[] cantRepeatSymbolId = getCantRepeatSymbolId();
        int[] multiplierSymbolIds = getMultiplierSymbolIds();
        int comboCount = 0; // 第幾次消除，供weight_C2_to_C3_by_drop_combo查表用

        while (screenCalculatorResult.waysGameResult.getPlayerWin() > 0){
            comboCount++;

            //計算有連線得分的位置
            int[][] preEliminatePosition = getEliminatePosition(screenCalculatorResult.waysGameResult.getWaysResult());

            //消除symbol並產生新盤面結果
            screenGeneratorResult = this.screenGenerator.generateCrushEliminateFallDownScreen(tableIdx, screenGeneratorResult.screenLabel, preEliminatePosition, baseGameSetting.getWheelData(), false, cantRepeatSymbolId,roundRngInfo, multiplierSymbolIds);

            //Eliminate後未被消除的位置
            int[][] afterEliminatePosition = getAfterEliminatePosition(preEliminatePosition);

            //消除掉落後新補進來的C2，依combo數各自獨立骰一次轉C3（§3.2 weight_C2_to_C3_by_drop_combo）
            applyDropComboC2ToC3Conversion(screenGeneratorResult.screenLabel, afterEliminatePosition, selectC2Table, comboCount, multiplierSymbolIds);

            roundRngInfo = getMergeRNGInfo(roundRngInfo,screenGeneratorResult.rngInfo);

            //重新排列specialScreen（存活的C3在此往上升一級，C2維持原值，見§3.2）
            int[][] cascadeSpecialScreen = mergeSpecialScreen(roundSpecialScreen,screenGeneratorResult, selectC2Table,afterEliminatePosition);
            roundSpecialScreen = cascadeSpecialScreen.clone();

            //計算累計乘倍
            extraMultiplier = getMultiplier(roundSpecialScreen);

            //計算新盤面得分
            screenCalculatorResult = this.screenCalculator.CalculateCrushCountScreenResult(slotSpinRequest, screenGeneratorResult.screenLabel, extendBaseSetting.getHitCrushCount());

            //封裝結果
            CascadeEliminateResult eliminateResult = new CascadeEliminateResult();
            eliminateResult.setExtraMultiplier(extraMultiplier);
            eliminateResult.setPreEliminatePosition(preEliminatePosition);
            eliminateResult.setScreenSymbol(screenGeneratorResult.screenLabel);
            eliminateResult.setWaysGameResult(screenCalculatorResult.waysGameResult);
            eliminateResult.setSpecialScreen(cascadeSpecialScreen);
            eliminateResult.calculateEliminateWinWin();

            cascadeEliminateResult.add(eliminateResult);
        }
        result.setCascadeEliminateResult(cascadeEliminateResult);
        result.setSpecialScreen(specialScreen);
        result.setExtraMultiplier(getMultiplier(specialScreen));
        result.calculateExtendTotalWin(getMultiplier(specialScreen));

        return result;
    }

    protected ExtendDataFromBaseToFeatureGame_JHS101027 calculateExtendDataFromBaseToFeatureGame(ExtendInfoForBaseGameResult_JHS101027 extendInfoForBaseGameResult, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, JackpotResult jackpotResult, int playerBetLevel)
    {
        ExtendDataFromBaseToFeatureGame_JHS101027 result = new ExtendDataFromBaseToFeatureGame_JHS101027();
        result.setBonusHitPool(jackpotResult.getHitCase());
        result.setBonusHitCase(jackpotResult.getHitCase());
        result.setPlayerBetLevel(playerBetLevel);
        result.setJackpotResult(jackpotResult);
        result.setAvailableBetMultiplier(availableBetMultiplier);
        result.setAvailableHitJPOption(availableHitJPOption);
        result.setBaseBet(baseGameSetting.getBetSpec().getBaseBet());
        result.setBetIdx(this.betIdx);
        result.setBetSpec(baseGameSetting.getBetSpec());
        for(int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++)
        {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.noSpecialHit) != 0)
            {
                String json = common.prinToJson(result);
                specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(json);

            }
            else
                specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(null);
        }
        return result;
    }

    protected JackpotResult calculateMiniGameResult(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest)
    {
        JackpotResult jackpotResult = new JackpotResult();
        //計算盤面有幾個C1
        long jackpotWeightMultiplier;
        long truePlayerBet;
        int newbie = this.common.isNoHitGrand() ? 0 : 1;
        if (availableHitJPOption[this.common.getElementIndex(availableBetMultiplier,slotSpinRequest.getBetRequest().getWaysBet())] == 3 && common.getWeightTableIndex() >= 2){
            newbie = 2;
        }
        int scatterComboRateIdx = this.common.getWeightTableIndex() <2?0:1;
        long[] poolInitValue;
        long[] hitPoolWeight;
        int jpIdx = 0;
        for (int i = 0; i < jackpotHandler.getJackpotSetting().getJackpotPoolData().length; i++) {
            if (jackpotHandler.getJackpotSetting().getJackpotPoolData()[i].getOption() == jackpotHandler.getJPOption()) {
                jpIdx = i;
                break;
            }
        }

        int abtest = this.common.getWeightTableIndex() % 2 == 0 ? 0:1;// mod 0 A版, mod 1 B版

        if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame){
            jackpotWeightMultiplier = extendBaseSetting.getScatterComboRate()[abtest][scatterComboRateIdx][1];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) this.baseGameSetting.getBetSpec().getExtraBetPaymentList()[1] / this.baseGameSetting.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet10000()[newbie][betIdx];
            poolInitValue = extendBaseSetting.getPoolInitValueFeatureBuy();
        } else if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02){
            jackpotWeightMultiplier = extendBaseSetting.getScatterComboRate()[abtest][scatterComboRateIdx][2];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) this.baseGameSetting.getBetSpec().getExtraBetPaymentList()[2] / this.baseGameSetting.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet50000()[newbie][betIdx];
            poolInitValue = extendBaseSetting.getPoolInitValueSuperBuy();
        } else {
            jackpotWeightMultiplier = extendBaseSetting.getScatterComboRate()[abtest][scatterComboRateIdx][0];
            truePlayerBet = slotSpinRequest.getPlayerBet();
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet100()[newbie][betIdx];
            poolInitValue = extendBaseSetting.getPoolInitValue();
        }

        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.bonusGame_01) == 0)
            {
                jackpotResult = ((JackpotHandler_OPJackpot_jumbo)jackpotHandler).getJackpotGameResult(truePlayerBet, jackpotWeightMultiplier, this.baseGameSetting.getBetSpec().getBaseBet(), hitPoolWeight,poolInitValue);

                //沒中任何pool的處理
                if (jackpotResult.getHitCase() <= 0 || jackpotResult.getHitPool().length == 0){
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i);
                }
            }
        }

        return jackpotResult;
    }

    private int getSymbolCount(int[][] screenLabel, EnumHandler.SymbolAttribute symbolAttribute){
        int symbolCount = 0;
        for (int column = 0; column < baseGameSetting.getScreenColumn(); column++) {
            for (int row = 0; row < baseGameSetting.getScreenRow(); row++) {
                if (baseGameSetting.getSymbolAttribute()[screenLabel[column][row]] == symbolAttribute) {
                    symbolCount = symbolCount + 1;
                }
            }
        }
        return symbolCount;
    }

    protected BaseGameResult packageRoundResult_JHS101027(
            ScreenGeneratorResult screenGeneratorResult,
            ScreenCalculatorResult screenCalculatorResult,
            SpecialFeatureCalculatorResult specialFeatureCalculatorResult,
            ExtendInfoForBaseGameResult_JHS101027 extendResult,
            DisplayInfo displayInfo,
            SlotSpinRequest slotSpinRequest) {

        BaseGameResult result = new BaseGameResult();

        result.setBaseGameTotalWin(calculateBaseGameTotalWin_JHS101027(screenCalculatorResult, specialFeatureCalculatorResult, extendResult));

        result.setDisplayInfo(displayInfo);

        if(screenGeneratorResult != null){
            result.setScreenSymbol(screenGeneratorResult.screenLabel);
            result.setUsedTableIndex(screenGeneratorResult.tableIdx);

            if(displayInfo != null)
                result.getDisplayInfo().setDampInfo(screenGeneratorResult.dampInfo);
            else
                result.setRngInfo(screenGeneratorResult.getRngInfo());
        }

        if(screenCalculatorResult != null){
            result.setLineGameResult(screenCalculatorResult.lineGameResult);
            result.setWaysGameResult(screenCalculatorResult.waysGameResult);
        }

        if(specialFeatureCalculatorResult != null){
            result.setSpecialFeatureResult(specialFeatureCalculatorResult.specialFeatureResult);
        }
        extendResult.setExtraBetMulti((double) (slotSpinRequest.getBetRequest().getWaysBet() * slotSpinRequest.getDenom() / 10));

        result.setExtendInfoForbaseGameResult(extendResult);

        return result;
    }

    private long calculateBaseGameTotalWin_JHS101027(
            ScreenCalculatorResult screenCalculatorResult,
            SpecialFeatureCalculatorResult specialFeatureCalculatorResult,
            ExtendInfoForBaseGameResult_JHS101027 extendResult) {

        long totalWin = 0;

        switch (this.baseGameSetting.getGameHitPattern()) {
            case WaysGame :
                totalWin = totalWin + screenCalculatorResult.waysGameResult.getPlayerWin();
                break;
            default :
                break;
        }
        for(int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++)
            totalWin = totalWin + specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialScreenWin();

        totalWin = totalWin + extendResult.getExtendPlayerWin();

        return totalWin;
    }

    private int[][] getLastScreenLabel(ScreenGeneratorResult screenGeneratorResult, ExtendInfoForBaseGameResult_JHS101027 extendGameResult){
        if (extendGameResult.getCascadeEliminateResult().size() == 0)
            return screenGeneratorResult.screenLabel;
        else
            return extendGameResult.getCascadeEliminateResult().get(extendGameResult.getCascadeEliminateResult().size()-1).getScreenSymbol();
    }

    private ScreenGeneratorResult GenerateScreenLabel(EnumHandler.ExtraBetType extraBetType){
        // tableIdx=0 交由框架依 baseGameSetting.tableHitProbability 權重隨機選一般輪帶(BG_Symbol/(2)/(3))
        // TODO: Extra Bet / Buy Feature 專用盤面邏輯，待下個階段補上
        int tableIdx = 0;
        try
        {
            if(EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF
                    || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF_OLD
                    ||  EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL){
                tableIdx = baseGameSetting.getTableCount();
            }

        }catch (Exception e) {
            System.out.println("[Error] 101027 GenerateScreenLabel Fail!");
            e.printStackTrace();
        }

        ScreenGeneratorResult result = screenGenerator.GenerateScreenLabel(tableIdx,extendBaseSetting.getWheelWeight());
        return result;
    }

    private int[][] getMergeRNGInfo(int[][] roundRngInfo,int [][] eliminateRngInfo){
        int[][] result = new int[roundRngInfo.length][roundRngInfo[0].length];

        for(int i = 0; i < eliminateRngInfo.length; i++){
            if(eliminateRngInfo[i][0] == -1 || eliminateRngInfo[i][0] == -2)
                result[0][i] = roundRngInfo[0][i];
            else
                result[0][i] = eliminateRngInfo[i][0];
        }

        return result;
    }

    private int getBetIndex(SlotSpinRequest slotSpinRequest){

        for(int i = 0; i < baseGameSetting.getBetSpec().getWaysBetList().length; ++i){
            if(slotSpinRequest.getBetRequest().getWaysBet() == baseGameSetting.getBetSpec().getWaysBetList()[i])
                return i;
        }

        return -1;
    }

    private int getPlayerBetLevel(SlotSpinRequest slotSpinRequest){
        for (int i = 0; i < this.baseGameSetting.getBetSpec().getWaysBetList().length; i++) {
            if (slotSpinRequest.getPlayerBet() == this.baseGameSetting.getBetSpec().getWaysBetList()[i]*this.baseGameSetting.getBetSpec().getBaseBet()){
                return i;
            }
        }
        return -1;
    }

    private boolean isMultiplierSymbol(EnumHandler.SymbolAttribute symbolAttribute){
        return symbolAttribute == EnumHandler.SymbolAttribute.ballC2 || symbolAttribute == EnumHandler.SymbolAttribute.ballC3;
    }

    // 滾停初始盤面：C2輪帶權重雖然存在，但C3輪帶權重恆為0（不會被直接抽到）。
    // 依「目前畫面C2總顆數」查表(1~5,6+共6欄)取得同一個萬分位門檻，畫面上每顆C2各自獨立骰一次(0~9999)，骰到小於門檻就轉成C3。
    private void applyInitialC2ToC3Conversion(int[][] screenLabel, int selectC2Table, int[] multiplierSymbolIds){
        int c2Id = multiplierSymbolIds[0];
        if(c2Id < 0)
            return;

        int c2Count = 0;
        for (int column = 0; column < baseGameSetting.getScreenColumn(); ++column)
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row)
                if(screenLabel[column][row] == c2Id)
                    c2Count++;

        if(c2Count == 0)
            return;

        int c3Id = multiplierSymbolIds[1];
        int countIdx = Math.min(c2Count, 6) - 1; // count=1~5對應index0~4，6+對應index5
        int weight = extendBaseSetting.getWeightC2ToC3ByInitialCount()[selectC2Table][countIdx];

        for (int column = 0; column < baseGameSetting.getScreenColumn(); ++column) {
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row) {
                if(screenLabel[column][row] == c2Id && common.getRandomNumber(10000) < weight)
                    screenLabel[column][row] = c3Id;
            }
        }
    }

    // 消除掉落後新補進來的C2：依「第幾次消除(combo)」查表(1~4,5+共5欄)取得萬分位門檻，
    // 新補進來的每顆C2各自獨立骰一次(0~9999)，骰到小於門檻就轉成C3。只處理「非存活」(afterEliminatePosition!=0)的新補位置。
    private void applyDropComboC2ToC3Conversion(int[][] screenLabel, int[][] afterEliminatePosition, int selectC2Table, int comboCount, int[] multiplierSymbolIds){
        int c2Id = multiplierSymbolIds[0];
        if(c2Id < 0)
            return;

        int c3Id = multiplierSymbolIds[1];
        int comboIdx = Math.min(comboCount, 5) - 1; // combo=1~4對應index0~3，5+對應index4
        int weight = extendBaseSetting.getWeightC2ToC3ByDropCombo()[selectC2Table][comboIdx];

        for (int column = 0; column < baseGameSetting.getScreenColumn(); ++column) {
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row) {
                boolean isFreshlyDropped = afterEliminatePosition[column][row] != 0;
                if(isFreshlyDropped && screenLabel[column][row] == c2Id && common.getRandomNumber(10000) < weight)
                    screenLabel[column][row] = c3Id;
            }
        }
    }

    // C2、C3各自有獨立的權重表（multiplierWeightC2／multiplierWeightC3），倍數池(multiplier)則共用同一份。
    private int[] getMultiplierWeightRow(EnumHandler.SymbolAttribute symbolAttribute, int selectC2Table){
        return (symbolAttribute == EnumHandler.SymbolAttribute.ballC3)
                ? extendBaseSetting.getMultiplierWeightC3()[selectC2Table]
                : extendBaseSetting.getMultiplierWeightC2()[selectC2Table];
    }

    private int[][] getSpecialScreenMultiplier(int[][] screenLabel, int selectC2Table){
        int[][] result = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];

        for (int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                EnumHandler.SymbolAttribute symbolAttribute = baseGameSetting.getSymbolAttribute()[screenLabel[column][row]];
                if(isMultiplierSymbol(symbolAttribute)) {
                    result[column][row] = extendBaseSetting.getMultiplier()[common.getArrayIndexByWeight(getMultiplierWeightRow(symbolAttribute, selectC2Table))];
                }
            }
        }

        return result;
    }

    private int[][] mergeSpecialScreen(int[][] specialScreen, ScreenGeneratorResult screenGeneratorResult, int selectC2Table,int[][] afterEliminatePosition){
        int[][] result = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];
        ArrayList<Integer> multiplierList = new ArrayList<>();

        // 先調整舊specialScreen位置
        for(int i = 0; i < baseGameSetting.getScreenColumn(); ++i)
            Arrays.fill(result[i],0);

        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for(int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                if(specialScreen[column][row] > 0)
                    multiplierList.add(specialScreen[column][row]);
            }
        }

        // 合併補牌的specialScreen(先取值再處理位置)
        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for(int row = 0; row < baseGameSetting.getScreenRow(); ++row) {
                if(afterEliminatePosition[column][row] == 0 && screenGeneratorResult.rngInfo[column][row] == -2 &&  multiplierList.size() > 0) {
                    // 初始盤面已存在的C2/C3存活下來：C3每發生一次消除就往上升一級，C2維持原值不變（§3.2）
                    int carriedValue = multiplierList.get(0);
                    EnumHandler.SymbolAttribute survivedAttribute = baseGameSetting.getSymbolAttribute()[screenGeneratorResult.screenLabel[column][row]];
                    result[column][row] = (survivedAttribute == EnumHandler.SymbolAttribute.ballC3)
                            ? getUpgradedMultiplierValue(carriedValue)
                            : carriedValue;
                    multiplierList.remove(0);
                }else if( screenGeneratorResult.rngInfo[column][row] != -2){
                    EnumHandler.SymbolAttribute newAttribute = baseGameSetting.getSymbolAttribute()[screenGeneratorResult.screenLabel[column][row]];
                    if(isMultiplierSymbol(newAttribute)) {
                        // 補牌新出現的 C2/C3，起始倍數一律重新依「各自」的權重表抽值
                        int idx = common.getArrayIndexByWeight(getMultiplierWeightRow(newAttribute, selectC2Table));
                        result[column][row] = extendBaseSetting.getMultiplier()[idx];
                    }
                }
            }
        }

        return result;
    }

    private int getUpgradedMultiplierValue(int currentValue) {
        int[] pool = extendBaseSetting.getMultiplier();
        int idx = -1;
        for (int i = 0; i < pool.length; i++) {
            if (pool[i] == currentValue) {
                idx = i;
                break;
            }
        }
        if (idx < 0)
            return currentValue;

        return pool[Math.min(idx + 1, pool.length - 1)];
    }

    private int getMultiplier(int[][] specialScreen){
        int result = 0;

        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for(int row = 0; row < baseGameSetting.getScreenRow(); ++row) {
                result += specialScreen[column][row];
            }
        }

        return result;
    }
    // 初始盤面（cascade開始前）的一般符號贏分，餵給calculateExtendTotalWin做乘倍計算。
    // 101006對應方法會把Scatter賠付一併加總進來，101027 §4規定「Scatter獎金不乘C2」，所以這裡不比照辦理。
    private long getInitialScreenWin(ScreenCalculatorResult screenCalculatorResult){
        return screenCalculatorResult.waysGameResult.getPlayerWin();
    }

    private int[][] getAfterEliminatePosition(int[][] screen) {
        int cols = screen.length;        // 外層是 column
        int rows = screen[0].length;     // 內層是 row
        int[][] result = new int[cols][rows];

        for (int col = 0; col < cols; col++) {
            Arrays.fill(result[col], -1); // 先補 -1
            int writeIndex = rows - 1;    // 從下往上寫（右側對齊）

            for (int row = rows - 1; row >= 0; row--) {
                if (screen[col][row] != 1) {
                    result[col][writeIndex] = screen[col][row];
                    writeIndex--;
                }
            }
        }

        return result;
    }

    private boolean isSeatInfo(SeatInfo seatInfo){
        if(seatInfo.getStatusAccumulation() == null || seatInfo.getScreenRngInfo() == null || seatInfo.getMiniGameWaterLevel() == 0)
            return false;

        if(seatInfo.getUsedTableIndex() >= baseGameSetting.getTableCount() || seatInfo.getUsedTableIndex() < 0)
            return false;

        for (int i = 0; i < seatInfo.getStatusAccumulation().length; ++i)
            if(seatInfo.getStatusAccumulation()[i] < 0)
                return false;

        for (int row = 0; row < seatInfo.getScreenRngInfo().length; ++row)
            for (int col = 0; col < seatInfo.getScreenRngInfo()[0].length; ++col)
                if(seatInfo.getScreenRngInfo()[row][col] < 0)
                    return false;

        return true;
    }

    private void initialSeatStatusCache(){
        this.seatInfo.setStatusAccumulation(new int[]{0});
        setRedisAccumulateData(0);
        this.seatInfo.setMiniGameWaterLevel(1);
        setRedisGameWaterLevel(1);
        this.seatInfo.setUsedTableIndex(0);
        this.seatInfo.setBetMultiplierIndex(0);
        int[][] screenRngInfo = new int[1][baseGameSetting.getScreenColumn()];
        this.seatInfo.setScreenRngInfo(screenRngInfo);
        this.seatStatusCache.setSeatInfo(this.seatInfo);
        this.seatStatusCache.setGameType(common.getGameType());
        this.seatStatusCache.setDenom(common.getDenom());
    }

    public int getMiniGameWaterLevel(int accumulateData){
        double gap = (extendBaseSetting.getScatterComboRate()[0][1][0] / 10000000000.0) * 35;
        int rounded = (int) Math.round(gap);
        int curLevel = accumulateData / rounded + 1;
        if (curLevel > 9) {
            return 10;
        }
        return curLevel;
    }

    private int[] getNewBieAccumulation(int symbolCount,SeatInfo seatInfo,SpecialFeatureCalculatorResult specialFeatureCalculatorResult){
        int accumulateData = seatInfo.getStatusAccumulation() == null ? 0 : seatInfo.getStatusAccumulation()[0];
        int addData = 1;
        if(addData + accumulateData < this.statusMaxAccum && symbolCount > 0) {
            accumulateData += addData;
        }
        else if(addData + accumulateData >= this.statusMaxAccum)
            accumulateData = this.statusMaxAccum;

        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.bonusGame_01) == 0 ||
                    specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.bonusGame_02) == 0)
                accumulateData = 0;
        }
        return new int[]{accumulateData};
    }

    protected ExtendInfoForBaseGameResult_JHS101027 calculateMiniWaterLvl(ExtendInfoForBaseGameResult_JHS101027 extendInfo , ScreenGeneratorResult screenGeneratorResult, SpecialFeatureCalculatorResult specialFeatureCalculatorResult) {
        //更新狀態機座位資訊
        int symbolCount = getSymbolCount(getLastScreenLabel(screenGeneratorResult,extendInfo),EnumHandler.SymbolAttribute.FreeGame);
        int[] accumulation = new int[]{ this.redisAccumulateData };

        int waterLevel = this.redisGameWaterLevel;

        // 新手體驗 RNG 水位計算
        if(common.getSettingIdType() == 2 || common.getSettingIdType() == 4) {
            accumulation = getNewBieAccumulation(symbolCount, this.seatInfo, specialFeatureCalculatorResult);
            waterLevel = getMiniGameWaterLevel(accumulation[0]);
        }

        this.seatInfo.setUsedTableIndex(screenGeneratorResult.tableIdx);
        this.seatInfo.setScreenRngInfo(screenGeneratorResult.rngInfo);
        this.seatInfo.setStatusAccumulation(accumulation);
        this.seatInfo.setMiniGameWaterLevel(waterLevel);
        this.seatInfo.setBetMultiplierIndex(this.betIdx);

        extendInfo.setSeatInfo(this.seatInfo);

        return extendInfo;
    }

    private boolean isSettingIDWithoutBonus(){
        if(EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF_OLD
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL_D)
            return true;

        return false;
    }
}
