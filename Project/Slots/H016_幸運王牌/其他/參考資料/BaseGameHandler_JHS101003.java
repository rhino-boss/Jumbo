package com.jumbogames.sps.logic.BaseGame;

import com.JH5.jps.ExtendJackpotSetting.JackpotExtendSetting_OPJackpot_jumbo;
import com.JH5.jps.JackpotHandler_OPJackpot_jumbo;
import com.base.jps.Jackpot.JackpotResult;
import com.base.sps.common.Common;
import com.base.sps.common.MiniGameWaterLevelUtil;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;
import com.jumbogames.sps.entity.client.ExtendBaseGameResult.ExtendInfoForBaseGameResult_JHS101003;
import com.jumbogames.sps.entity.client.ExtendBaseGameSetting.BaseGameExtendSetting_JHS101003;
import com.jumbogames.sps.entity.client.GameStatusCaches.SeatStatusCache_101001;
import com.jumbogames.sps.entity.client.GameStatusCaches.SeatStatusCache_110001;
import com.jumbogames.sps.logic.BaseGame.ExtendDataFromBaseToFeatureGame_JHS101003;
import com.base.sps.entity.system.ScreenCalculatorResult;
import com.base.sps.entity.system.SpecialFeatureCalculatorResult;
import com.base.sps.entity.client.*;
import com.base.sps.entity.client.EnumHandler.SpecialHitInfo;
import com.base.sps.logic.ScreenGeneratorResult;
import com.jumbogames.sps.logic.BaseGameHandler;

import java.util.ArrayList;
import java.util.*;

public class BaseGameHandler_JHS101003 extends BaseGameHandler {
    private BaseGameExtendSetting_JHS101003 extendBaseSetting = new BaseGameExtendSetting_JHS101003();

    private int multiplierPosition = 0;
    private boolean randomWildChance = true;
    private int betIdx;
    private final int statusMaxAccum = 350;
    private SeatStatusCache_101001 seatStatusCache;
    private SeatInfo seatInfo;
    private MiniGameWaterLevelUtil miniGameWater;


    //    private int C2Idx = -1;
    public BaseGameHandler_JHS101003(Common common) {
        super(common);
        seatStatusCache = new SeatStatusCache_101001();
        seatInfo = new SeatInfo();
        miniGameWater = new MiniGameWaterLevelUtil();
    }

    public EnumHandler.ErrorCode initialGameStatusCache(int denom, String gameStatusCache){
        extendBaseSetting = (BaseGameExtendSetting_JHS101003) super.baseGameSetting.getBaseGameExtendSetting();
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
        if(invalidSpinRequest(slotSpinRequest))
            return new BaseGameResult();
        this.betIdx = getBetIndex(slotSpinRequest);

        extendBaseSetting = (BaseGameExtendSetting_JHS101003) super.baseGameSetting.getBaseGameExtendSetting();
        if (this.common.getSpinType() == EnumHandler.SpinType.OddsSpin){
            if (this.common.getSettingIdType() == 2 || this.common.getSettingIdType() == 3 || availableHitJPOption[this.common.getElementIndex(availableBetMultiplier,slotSpinRequest.getBetRequest().getWaysBet())] == 3){
                this.common.setNoHitGrand(true);
            }
        }
        //選擇要用哪個輪帶並產生畫面
        int tableIdx = getWheelTableIndex(slotSpinRequest.getExtraBetType());
        ScreenGeneratorResult screenGeneratorResult = screenGenerator.GenerateScreenLabel(0, extendBaseSetting.getWheelWeight());

        //將畫面左下與右下設定為NoneSymbol，更改為45554版面
//        changeScreenCorners2NoneSymbol(screenGeneratorResult.screenLabel);

        //將goldenSymbol的地方轉成一般Symbol ID
        int[][] change2NewScreen = changeScreen2NormalSymbol(screenGeneratorResult.screenLabel);

        //計算畫面結果，並將結果紀錄於spinResult中
        ScreenCalculatorResult screenCalculatorResult = screenCalculator.CalculateScreenResult(slotSpinRequest,change2NewScreen);
        //乘與連消倍率
        int firstSpinMultiplier = getCurrentExtraMultiplier();
        if (screenCalculatorResult.waysGameResult.getPlayerWin() > 0) {
            reCalculateScreenResult(screenCalculatorResult,firstSpinMultiplier);
        }

        //透過Mystery改變掉落消除權重
//        WheelData[][] exchangeEliminateWeightData = exchangeEliminateWeightData(extendBaseSetting.getEliminateWheelData(),extendBaseSetting.getMysteryWheelWeightData(),extendBaseSetting.getIncreaseMysteryWheelWeight());

        //計算 by game 資訊 - 消消樂流程處理
        ExtendInfoForBaseGameResult_JHS101003 extendInfoForBaseGameResult = calculateExtendInfoForBaseGameResult(slotSpinRequest,screenGeneratorResult,screenCalculatorResult);

        //  紀錄連消分數的歷程
        extendInfoForBaseGameResult.setTotalMultiplierList(firstSpinMultiplier,extendInfoForBaseGameResult.getCascadeEliminateResult());

        //使用最後畫面判斷是否中了特殊feature
        SpecialFeatureCalculatorResult specialFeatureCalculatorResult = specialFeatureHandler.getFeatureResult(getLastScreenLabel(screenGeneratorResult,extendInfoForBaseGameResult),slotSpinRequest);

        specialFeatureCalculatorResult = RecalculatespecialFeatureCalculatorResult1(screenGeneratorResult.screenLabel,
                specialFeatureCalculatorResult,
                slotSpinRequest);

        extendInfoForBaseGameResult = calculateMiniWaterLvl(extendInfoForBaseGameResult,screenGeneratorResult,specialFeatureCalculatorResult);

        int sysScatterCount = getSymbolCount(getLastScreenLabel(screenGeneratorResult, extendInfoForBaseGameResult), EnumHandler.SymbolAttribute.FreeGame);
        extendInfoForBaseGameResult.setSysScatterCount(sysScatterCount);

        JackpotResult jackpotResult = calculateMiniGameResult(screenGeneratorResult.screenLabel,
                specialFeatureCalculatorResult,
                slotSpinRequest);

        ExtendDataFromBaseToFeatureGame_JHS101003 extendDataFromBaseToFeatureGame = new ExtendDataFromBaseToFeatureGame_JHS101003();

        //重新計算特殊feature 的結果，並將C1數量結果包裝起來傳送至FreeGameHandler
        reCalculatorSpecialFeatureResult(getLastScreenLabel(screenGeneratorResult,extendInfoForBaseGameResult),specialFeatureCalculatorResult,extendDataFromBaseToFeatureGame);

        calculateExtendDataFromBaseToFeatureGame(extendInfoForBaseGameResult, specialFeatureCalculatorResult,jackpotResult,getPlayerBetLevel(slotSpinRequest));

        BaseGameResult result = packageRoundResult_JHS101003(screenGeneratorResult,screenCalculatorResult,specialFeatureCalculatorResult,extendInfoForBaseGameResult,null, slotSpinRequest);

        // 重置MultiplierPosition
        resetMultiplierPosition();

        // 重製randomWildChance
        resetRandomWildChance();

        return result;
    }

    private int getPlayerBetLevel(SlotSpinRequest slotSpinRequest){
        for (int i = 0; i < this.baseGameSetting.getBetSpec().getWaysBetList().length; i++) {
            if (slotSpinRequest.getPlayerBet() == this.baseGameSetting.getBetSpec().getWaysBetList()[i]*this.baseGameSetting.getBetSpec().getBaseBet()){
                return i;
            }
        }
        return -1;
    }

    protected SpecialFeatureCalculatorResult RecalculatespecialFeatureCalculatorResult1(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest) {

        if(common.isNoHitGrand()) {
            //新手不拉Grand
            for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; ++i) {
                if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo() == SpecialHitInfo.bonusGame_02) {
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i);
                } else if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo() == SpecialHitInfo.bonusGame_01   && isSettingIDWithoutBonus())
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i); // 新手救援+新手體驗 不提供MiniGame
            }
        }

        return specialFeatureCalculatorResult;
    }

    private boolean isSettingIDWithoutBonus(){
        if(EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF_OLD
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL)
            return true;

        return false;
    }


    protected void calculateExtendDataFromBaseToFeatureGame(ExtendInfoForBaseGameResult_JHS101003 extendInfoForBaseGameResult, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, JackpotResult jackpotResult, int playerBetLevel)
    {
        ExtendDataFromBaseToFeatureGame_JHS101003 result = new ExtendDataFromBaseToFeatureGame_JHS101003();
        result.setBonusHitPool(jackpotResult.getHitCase());
        result.setBonusHitCase(jackpotResult.getHitCase());
        result.setBetSpec(baseGameSetting.getBetSpec());
        result.setPlayerBetLevel(playerBetLevel);
        result.setJackpotResult(jackpotResult);
        result.setAvailableBetMultiplier(availableBetMultiplier);
        result.setAvailableHitJPOption(availableHitJPOption);
        result.setBaseBet(baseGameSetting.getBetSpec().getBaseBet());
        result.setBetIdx(this.betIdx);
        for(int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++)
        {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.noSpecialHit) != 0)
            {
                String json = common.prinToJson(result);
                specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(json);
            } else
                specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(null);
        }
    }

    protected BaseGameResult packageRoundResult_JHS101003(
            ScreenGeneratorResult screenGeneratorResult,
            ScreenCalculatorResult screenCalculatorResult,
            SpecialFeatureCalculatorResult specialFeatureCalculatorResult,
            ExtendInfoForBaseGameResult_JHS101003 extendResult,
            DisplayInfo displayInfo, SlotSpinRequest slotSpinRequest) {

        BaseGameResult result = new BaseGameResult();
        result.setBaseGameTotalWin(calculateBaseGameTotalWin_JHS101003(screenCalculatorResult,specialFeatureCalculatorResult,extendResult));
        result.setDisplayInfo(displayInfo);

        if(screenGeneratorResult != null){
            result.setScreenSymbol(screenGeneratorResult.screenLabel);
            result.setUsedTableIndex(screenGeneratorResult.tableIdx);

            if(displayInfo != null){
                result.getDisplayInfo().setDampInfo(screenGeneratorResult.dampInfo);
            }else{
                result.setRngInfo(screenGeneratorResult.getRngInfo());
            }
        }

        if (!extendResult.getCascadeEliminateResult().isEmpty()){
            result.setCrashLastSymbol(extendResult.getCascadeEliminateResult().get(extendResult.getCascadeEliminateResult().size()-1).getScreenSymbol());
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

    protected JackpotResult calculateMiniGameResult(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest)
    {
        JackpotResult jackpotResult = new JackpotResult();
        //計算盤面有幾個C1
        int totalC1Count = getSymbolCount(screenLabel, EnumHandler.SymbolAttribute.FreeGame);
        long jackpotWeightMultiplier;
        long truePlayerBet;
        int newbie = this.common.isNoHitGrand()?0:1;
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

        if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame){
            jackpotWeightMultiplier = extendBaseSetting.getScatterComboRate()[scatterComboRateIdx][1];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) this.baseGameSetting.getBetSpec().getExtraBetPaymentList()[1] / this.baseGameSetting.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet4050()[newbie][betIdx];
            poolInitValue = extendBaseSetting.getPoolInitValueFeatureBuy();
        }else if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02){
            jackpotWeightMultiplier = extendBaseSetting.getScatterComboRate()[scatterComboRateIdx][2];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) this.baseGameSetting.getBetSpec().getExtraBetPaymentList()[2] / this.baseGameSetting.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet25000()[newbie][betIdx];
            poolInitValue = extendBaseSetting.getPoolInitValueSuperBuy();
        }else {
            jackpotWeightMultiplier = extendBaseSetting.getScatterComboRate()[scatterComboRateIdx][0];
            truePlayerBet = slotSpinRequest.getPlayerBet();
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet100()[newbie][betIdx];
            poolInitValue = extendBaseSetting.getPoolInitValue();
        }

        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.bonusGame_01) == 0)
            {
                jackpotResult = ((JackpotHandler_OPJackpot_jumbo)jackpotHandler).getJackpotGameResult(truePlayerBet, jackpotWeightMultiplier, this.baseGameSetting.getBetSpec().getBaseBet(), hitPoolWeight, poolInitValue);

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

    protected ExtendInfoForBaseGameResult_JHS101003 calculateExtendInfoForBaseGameResult(SlotSpinRequest slotSpinRequest,ScreenGeneratorResult screenGeneratorResult,ScreenCalculatorResult screenCalculatorResult){
        ExtendInfoForBaseGameResult_JHS101003 result = new ExtendInfoForBaseGameResult_JHS101003();
        ArrayList<CascadeEliminateResult> cascadeEliminateResult = new ArrayList<CascadeEliminateResult>();
        int tableIdx = screenGeneratorResult.tableIdx;
        int extraMultiplier; //累積倍數
        int[][] randWildScreen = null;
        int[][] afterRandWildScreen = screenGeneratorResult.screenLabel.clone();

        while(screenCalculatorResult.waysGameResult.getPlayerWin() > 0){

            //紀錄所有金框的位置
            boolean[][] goldenSymbolPosition = recordGoldenSymbolPosition(afterRandWildScreen);

            //計算有連線得分的位置
            int[][] preEliminatePosition = getEliminatePosition(screenCalculatorResult.waysGameResult.getWaysResult());

            //處理未消除的WW2位置
            if(!isRandomWildChance())
                screenGeneratorResult.screenLabel = getUneliminateWild2Position(screenGeneratorResult.screenLabel,preEliminatePosition,afterRandWildScreen);

            //處理GoldSymbol變成一般wild，並改變GoldSymbol位置上的消除類型
            int[][] screenSymbol = calculateGoldenSymbol2ChangeWildScreen(screenGeneratorResult.screenLabel,preEliminatePosition,goldenSymbolPosition);

            //回傳倍數
            extraMultiplier = getCurrentExtraMultiplier();

            //消除Symbol並產生新盤面結果
            screenGeneratorResult = this.screenGenerator.generateEliminateReplacement(tableIdx,screenSymbol,preEliminatePosition, baseGameSetting.getWheelData(), true, getC1SymbolId());

            //取得金框消除的idx
            ArrayList<Integer> potentialWild2Idx = getPotentialWild2Idx(preEliminatePosition);

            //判斷是否有機會觸發隨機百搭
            if(isRandomWildChance() && !potentialWild2Idx.isEmpty()) {
                int rnd = common.getArrayIndexByWeight(extendBaseSetting.getRandomWildWeight()[tableIdx]);
                int randomWildCount = extendBaseSetting.getRandomWild()[rnd];

                if(randomWildCount > 0) {
                    //獲得可以分布的位置
                    ArrayList<Integer> randWildPositionIdx = getRandWildPositionIdx(potentialWild2Idx, screenGeneratorResult.screenLabel);
                    //灑落百搭後的盤面
                    randWildScreen = calculateRandomWildScreen(screenGeneratorResult.screenLabel, randomWildCount, randWildPositionIdx, potentialWild2Idx);
                    //當進化WW2成功時，就不再有機會進化
                    setRandomWildChance(false);
                }
            }

            int[][] wildScreenSymbol;//將WW系列都轉成SymbolID = 0 做盤面計算
            int[][] change2NewScreen;//將goldenSymbol的地方轉成一般Symbol ID
            if(randWildScreen != null)
                wildScreenSymbol = reCalculateWildScreenSymbol(randWildScreen);
            else
                wildScreenSymbol = reCalculateWildScreenSymbol(screenGeneratorResult.screenLabel);

            change2NewScreen = changeScreen2NormalSymbol(wildScreenSymbol);

            //計算新盤面得分
            screenCalculatorResult = this.screenCalculator.CalculateScreenResult(slotSpinRequest,change2NewScreen);

            CascadeEliminateResult eliminateResult = new CascadeEliminateResult();
            eliminateResult.setExtraMultiplier(extraMultiplier);
            eliminateResult.setPreEliminatePosition(preEliminatePosition);
            eliminateResult.setScreenSymbol(screenGeneratorResult.screenLabel);
            eliminateResult.setWaysGameResult(screenCalculatorResult.waysGameResult);
            eliminateResult.calculateEliminateWinWin();
            eliminateResult.setSpecialScreen(randWildScreen);
            cascadeEliminateResult.add(eliminateResult);

            //記錄前一把消除位置
            if(randWildScreen != null)
                afterRandWildScreen = randWildScreen.clone();
            else
                afterRandWildScreen = screenGeneratorResult.screenLabel.clone();

            //重置randWildScreen
            randWildScreen = null;
        }
        result.setCascadeEliminateResult(cascadeEliminateResult);
        result.calculateExtendTotalWin();

        return result;
    }

    private long calculateBaseGameTotalWin_JHS101003(
            ScreenCalculatorResult screenCalculatorResult,
            SpecialFeatureCalculatorResult specialFeatureCalculatorResult,
            ExtendInfoForBaseGameResult_JHS101003 extendResult) {
        long totalWin = 0;

        if (Objects.requireNonNull(this.baseGameSetting.getGameHitPattern()) == EnumHandler.GameHitPattern.WaysGame) {
            totalWin = totalWin + screenCalculatorResult.waysGameResult.getPlayerWin();
        }
        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            totalWin = totalWin + specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialScreenWin();
        }

        totalWin = totalWin + extendResult.getExtendPlayerWin();

        return totalWin;
    }

    private void reCalculateScreenResult(ScreenCalculatorResult screenCalculatorResult,int firstSpinMultiplier){
        long totalWin = screenCalculatorResult.waysGameResult.getPlayerWin();

        long newTotalWin = totalWin * firstSpinMultiplier;

        screenCalculatorResult.waysGameResult.setPlayerWin(newTotalWin);
    }
    private void reCalculatorSpecialFeatureResult(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, ExtendDataFromBaseToFeatureGame_JHS101003 extendDataFromBaseToFeatureGame){
        int freeGameSymbolCount = 0;
        SpecialFeatureResult specialFeatureResult = specialFeatureCalculatorResult.specialFeatureResult[0];
        boolean[][] tmpFlagData = new boolean[specialFeatureResult.getSpecialScreenHitData().length][specialFeatureResult.getSpecialScreenHitData()[0].length];
        for(int i = 0 ; i < baseGameSetting.getScreenColumn();i++){
            for(int j = 0 ; j < baseGameSetting.getScreenRow();j++){
                if(baseGameSetting.getSymbolAttribute()[screenLabel[i][j]] == EnumHandler.SymbolAttribute.FreeGame){
                    freeGameSymbolCount++;
                    tmpFlagData[i][j] = true;
                }
            }
        }

        if (freeGameSymbolCount >= extendBaseSetting.getMinimumFreeGameCount()) {
            specialFeatureResult.setSpecialHitInfo(EnumHandler.SpecialHitInfo.freeGame_01);
            specialFeatureResult.setSpecialOperations(null);
            specialFeatureResult.setSpecialScreenHitData(tmpFlagData);
            extendDataFromBaseToFeatureGame.setFreeGameSymbolCount(freeGameSymbolCount);

            String json = common.prinToJson(extendDataFromBaseToFeatureGame);

            for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
                if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(SpecialHitInfo.freeGame_01) == 0)
                    specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(json);
            }
        }
    }

    private void changeScreenCorners2NoneSymbol(int[][] screenLabel){
        int lastColumnPosition = baseGameSetting.getScreenColumn() - 1;
        int lastRowPosition = baseGameSetting.getScreenRow() - 1;
        int noneId = getNoneId();

        screenLabel[0][lastRowPosition] = noneId;
        screenLabel[lastColumnPosition][lastRowPosition] = noneId;
    }
    private void changeScreenInSpecialRule(int tableIdx,int[][] preEliminatePosition,int[][] curScreenLabel,WheelData[][] exchangeEliminateWeightData){
        for(int row = 0 ; row < curScreenLabel.length;row++){
            //找到該列重複3次以上的Symbol為何，沒有的話回傳-1
            int repeatSymbol = checkScreenIsRepeat(curScreenLabel[row]);
            if(repeatSymbol != -1){
                int changeCount = 1;
                //計算重複的Symbol有幾顆
                int repeatCount = calculateSymbolCount(repeatSymbol,curScreenLabel[row]);
                //計算該行是幾顆掉落
                int eliminateCount = calculateEliminateCount(preEliminatePosition[row]);
                //全消的情況要移除兩顆
                if(repeatCount == 5){
                    changeCount = 2;
                }
                int changeSymbolPosition = eliminateCount - 1;
                while(changeCount > 0){
                    if(changeSymbolPosition == -1){
                        //這裡只會出現初始輪帶就存在數量4以上的情況，有這種情況就不替換
                        break;
                    }
                    if(!checkSameSymbol(curScreenLabel[row][changeSymbolPosition],repeatSymbol)){
                        //如果該位置不是重複的Symbol就往上一個位置
                        changeSymbolPosition--;
                        continue;
                    }
                    int newSymbol;
                    do{
                        newSymbol = common.getArrayIndexByWeight(exchangeEliminateWeightData[tableIdx][row].getWheelData());
                    }while(checkSameSymbol(newSymbol,repeatSymbol));

                    //將該行掉落最底層的Symbol替換成新的Symbol
                    curScreenLabel[row][changeSymbolPosition] = newSymbol;
                    changeCount--;
                    changeSymbolPosition--;
                }
            }
        }
    }
    /**
     * 檢查是否需要改變掉落Symbol，如果需要就回傳不想要掉落的Symbol，不需要則回傳-1
     */
    private int checkScreenIsRepeat(int[] screenRowLabel){
        int noRepeatingCount = extendBaseSetting.getNoRepeatingSymbolCount();
        EnumHandler.SymbolAttribute[] symbolAttributeList = baseGameSetting.getSymbolAttribute();
        Map<Integer,Integer> repeatingSymbolList = new HashMap<>();

        for (int curSymbolId : screenRowLabel) {
            //C1跟Wild、None 不用去計算重複
            if (symbolAttributeList[curSymbolId] == EnumHandler.SymbolAttribute.FreeGame ||
                    symbolAttributeList[curSymbolId] == EnumHandler.SymbolAttribute.Wild) {
                continue;
            }
            if (curSymbolId - noRepeatingCount > 0) {
                //要把金框轉成一般SymbolID
                switch (symbolAttributeList[curSymbolId - noRepeatingCount]) {
                    case M1:
                    case M2:
                    case M3:
                    case Base:
                        curSymbolId = curSymbolId - noRepeatingCount;
                        break;
                    default:
                }
            }
            repeatingSymbolList.put(curSymbolId, repeatingSymbolList.getOrDefault(curSymbolId, 0) + 1);
        }

        for(int symbolId : repeatingSymbolList.keySet()){
            if(repeatingSymbolList.get(symbolId) > 3){
                return symbolId;
            }
        }

        return -1;
    }

    private int calculateSymbolCount(int repeatSymbol, int[] screenRowLabel){
        int repeatCount = 0;
        for(int curSymbol : screenRowLabel){
            if(checkSameSymbol(repeatSymbol,curSymbol)){
                repeatCount++;
            }
        }
        return repeatCount;
    }
    private boolean checkSameSymbol(int symbol,int otherSymbol){
        int noRepeatingCount = extendBaseSetting.getNoRepeatingSymbolCount();
        EnumHandler.SymbolAttribute[] symbolAttributeList = baseGameSetting.getSymbolAttribute();
        if (symbolAttributeList[otherSymbol] == EnumHandler.SymbolAttribute.FreeGame ||
                symbolAttributeList[otherSymbol] == EnumHandler.SymbolAttribute.Wild) {
            return false;
        }
        return otherSymbol - symbol == 0 || Math.abs(symbol - otherSymbol) == noRepeatingCount;
    }
    private int calculateEliminateCount(int[] preEliminatePosition){
        int result = 0;
        for (int j : preEliminatePosition) {
            if (j == EnumHandler.EliminateType.Eliminate.ordinal()) {
                result++;
            }
        }
        return result;
    }
    private WheelData[][] exchangeEliminateWeightData(WheelData[][] eliminateWheelData,WheelData[][] mysteryWheelWeightData,int[][] increaseMysteryWheelWeight) {
        WheelData[][] newWeightDataResult = new WheelData[eliminateWheelData.length][eliminateWheelData[0].length];
        int[] rng = getMysteryWheelWeight(mysteryWheelWeightData);

        for (int index = 0; index < eliminateWheelData.length; index++) {
            for (int wheelIndex = 0; wheelIndex < eliminateWheelData[index].length; wheelIndex++) {
                newWeightDataResult[index][wheelIndex] = eliminateWheelData[index][wheelIndex].Copy();
                if (increaseMysteryWheelWeight[index][wheelIndex] == 0) {    //判斷此輪帶有需要增加掉落權重
                    continue;
                }
                int[] weightData = newWeightDataResult[index][wheelIndex].getWheelData();
                weightData[rng[wheelIndex]] += increaseMysteryWheelWeight[index][wheelIndex];
                newWeightDataResult[index][wheelIndex].setWheelData(weightData);
            }
        }

        return newWeightDataResult;
    }

    private void rearrangeScreen(int[][] preEliminatePosition,int[][] screenLabel) {
        for (int column = 0; column < screenLabel.length; column++) {
            int eliminateCount = calculateEliminateCount(preEliminatePosition[column]);
            if (eliminateCount >= 3) {
                int targetRow = -1;
                for (int row = 0; row < screenLabel[column].length - 2; row++) {
                    if (checkSameSymbol(screenLabel[column][row], screenLabel[column][row + 1]) &&
                            checkSameSymbol(screenLabel[column][row + 1], screenLabel[column][row + 2])) {
                        if (eliminateCount == 3 && (row == 1 || row == 2)) {
                            targetRow = 0;
                            break;
                        } else if (eliminateCount > 3) {
                            if (row == 0) {
                                targetRow = 3;
                                break;
                            } else if (row == 1 || row == 2) {
                                targetRow = 0;
                                break;
                            }
                        }
                    }
                }

                if (targetRow != -1) {
                    swapScreenPosition(screenLabel, column, 2, targetRow);
                }
            }
        }
    }
    public void swapScreenPosition(int[][] screen,int column,int row1,int row2){
        int temp = screen[column][row1];
        screen[column][row1] = screen[column][row2];
        screen[column][row2] = temp;
    }
    private int[] getMysteryWheelWeight(WheelData[][] mysteryWheelWeightData){
        int[] mysteryRNGWheelData = new int[mysteryWheelWeightData[0].length];
        for (int wheelIndex = 0; wheelIndex < mysteryWheelWeightData[0].length; wheelIndex++) {
            mysteryRNGWheelData[wheelIndex] = common.getArrayIndexByWeight(mysteryWheelWeightData[0][wheelIndex].getWheelData());
        }

        return mysteryRNGWheelData;
    }

    private int[][] getLastScreenLabel(ScreenGeneratorResult screenGeneratorResult,ExtendInfoForBaseGameResult_JHS101003 extendGameResult){
        if(extendGameResult.getCascadeEliminateResult().isEmpty()){
            return  screenGeneratorResult.screenLabel;
        }else{
            return extendGameResult.getCascadeEliminateResult().get(extendGameResult.getCascadeEliminateResult().size() - 1).getScreenSymbol();
        }
    }
    private int[][] getEliminatePosition(WaysResult[] srcWaysResult){
        int[][] eliminatePosition = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];

        for(WaysResult wayResult:srcWaysResult){
            boolean[][] screenHitData = wayResult.getScreenHitData();
            for(int i = 0 ; i < screenHitData.length ; i++){
                for(int j = 0 ; j < screenHitData[0].length;j++){
                    if(screenHitData[i][j] == true){
                        eliminatePosition[i][j] = EnumHandler.EliminateType.Eliminate.ordinal();
                    }
                }
            }
        }
        return eliminatePosition;
    }

    private int[][] calculateGoldenSymbol2ChangeWildScreen(int[][] screenLabel,int[][] preEliminatePosition,boolean[][] goldenSymbolPosition){
        final int wildSymbolId = 0;
        final int goldenSymbolId = 2;
        int[][] newScreen = new int[screenLabel.length][screenLabel[0].length];
        for(int i = 0; i < screenLabel.length;i++){
            for(int j =0 ; j < screenLabel[0].length;j++){
                if(preEliminatePosition[i][j] == EnumHandler.EliminateType.Eliminate.ordinal() && goldenSymbolPosition[i][j] == true){
                    newScreen[i][j] = wildSymbolId;
                    preEliminatePosition[i][j] = goldenSymbolId;
                }else{
                    newScreen[i][j] = screenLabel[i][j];
                }
            }
        }
        return newScreen;
    }

    public boolean[][] recordGoldenSymbolPosition(int[][] screen) {
        int noneId = getNoneId();
        boolean[][] goldenSymbol = new boolean[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];
        //重複的一般symbol加上Wild和C1會等於GoldenSymbol起始ID
        int startGoldenID = extendBaseSetting.getNoRepeatingSymbolCount() + 3;

        for (int i = 0; i < baseGameSetting.getScreenColumn(); i++) {
            for (int j = 0; j < baseGameSetting.getScreenRow(); j++) {
                if (screen[i][j] >= startGoldenID && screen[i][j] != noneId) {
                    goldenSymbol[i][j] = true;
                } else {
                    goldenSymbol[i][j] = false;
                }
            }
        }
        return goldenSymbol;
    }

    public int[][] changeScreen2NormalSymbol(int[][] originalScreen) {
        EnumHandler.SymbolAttribute[] symbolAttributeList;
        int noRepeatingCount = extendBaseSetting.getNoRepeatingSymbolCount();
        int[][] newScreen = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];
        symbolAttributeList = baseGameSetting.getSymbolAttribute();
        for (int i = 0; i < baseGameSetting.getScreenColumn(); i++) {
            for (int j = 0; j < baseGameSetting.getScreenRow(); j++) {
                int symbolID = originalScreen[i][j];
                if (symbolAttributeList[symbolID] == EnumHandler.SymbolAttribute.FreeGame ||
                        symbolAttributeList[symbolID] == EnumHandler.SymbolAttribute.Wild ||
                        originalScreen[i][j] - noRepeatingCount <= 0 ||
                        symbolAttributeList[originalScreen[i][j] - noRepeatingCount] == EnumHandler.SymbolAttribute.Wild ||
                        symbolAttributeList[originalScreen[i][j] - noRepeatingCount] == EnumHandler.SymbolAttribute.FreeGame
                ) {
                    newScreen[i][j] = originalScreen[i][j];
                } else {
                    newScreen[i][j] = originalScreen[i][j] - noRepeatingCount;
                }
            }
        }
        return newScreen;
    }

    private int getC1SymbolId(){
        for(int i = 0 ;i < baseGameSetting.getSymbolAttribute().length;i++){
            if(baseGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.FreeGame){
                return i ;
            }
        }
        return -1;
    }

    private int getNoneId(){
        for(int i = 0 ;i < baseGameSetting.getSymbolAttribute().length;i++){
            if(baseGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.None){
                return i ;
            }
        }
        return -1;
    }

    //    private int getWheelTableIndex(int comboCount){
//        int[] eliminateWheelComboThreshold = extendBaseSetting.getEliminateWheelComboThreshold();
//        for(int i = 0 ; i < eliminateWheelComboThreshold.length;i++){
//            if(comboCount < eliminateWheelComboThreshold[i]){
//                return i ;
//            }
//        }
//        return extendBaseSetting.getEliminateWheelData().length - 1;
//    }
    private int getCurrentExtraMultiplier() {
        int[] comboMultiplierList = extendBaseSetting.getComboMultiplierList();

        if(multiplierPosition >= comboMultiplierList.length){
            multiplierPosition = comboMultiplierList.length - 1;
        }
        return comboMultiplierList[multiplierPosition++];
    }

    private void resetMultiplierPosition(){
        multiplierPosition = 0;
    }
    private int getWheelTableIndex(EnumHandler.ExtraBetType extraBetType){
        if (this.common.getSettingIdType() == 2){
            return 1;
        }
        if(extraBetType == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame
                || extraBetType == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF_OLD
                ||  EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL){
            return 3;
        }
        return 0;
    }

    private boolean isRandomWildChance(){ return randomWildChance; }

    private void setRandomWildChance(boolean randomWildChance) { this.randomWildChance = randomWildChance; }

    private void resetRandomWildChance(){ randomWildChance = true; }

    private ArrayList<Integer> getPotentialWild2Idx(int[][] preEliminatePosition){
        // 蒐集金框消除的位置
        ArrayList<Integer> potentialWild2Idx = new ArrayList<>();

        // 紀錄盤面上的可能變成隨機百搭的wild
        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                if (preEliminatePosition[column][row] == 2)
                    potentialWild2Idx.add(baseGameSetting.getScreenRow()*column+row);
            }
        }

        return potentialWild2Idx;
    }

    private ArrayList<Integer> getRandWildPositionIdx(ArrayList<Integer> potentialWild2Idx, int[][] screenLabel){
        // 2、3、4、5 輪
        ArrayList<Integer> randWildPositionIdx = new ArrayList<>();

        //設定 2~5 輪的 index
        for(int idx = 0; idx < (baseGameSetting.getScreenColumn()-1)*baseGameSetting.getScreenRow(); ++idx)
            randWildPositionIdx.add(idx+baseGameSetting.getScreenRow());

        // 移除 wild1 與 wild2 的 index
        for(int i = 0; i < potentialWild2Idx.size(); ++i)
            randWildPositionIdx.remove(potentialWild2Idx.get(i));

        // 移除 Scatter 的 index
        for (int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                if( baseGameSetting.getSymbolAttribute()[screenLabel[column][row]] == EnumHandler.SymbolAttribute.FreeGame )
                    randWildPositionIdx.remove((Integer) (baseGameSetting.getScreenRow()*column+row));

            }
        }

        return randWildPositionIdx;
    }

    private int[][] calculateRandomWildScreen(int[][] screenLabel, int randomWildCount, ArrayList<Integer> randWildPositionIdx, ArrayList<Integer> potentialWild2Idx){
        int[][] result = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];
        int wild2Idx = potentialWild2Idx.get(common.getRandomNumber(potentialWild2Idx.size()));

        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                result[column][row] = screenLabel[column][row];
            }
        }

        // wild2
        result[wild2Idx/baseGameSetting.getScreenRow()][wild2Idx%baseGameSetting.getScreenRow()] = 1;

        // 灑落盤面
        for(int i = 0; i < randomWildCount; i++) {
            int randIdx = common.getRandomNumber(randWildPositionIdx.size());
            result[randWildPositionIdx.get(randIdx)/baseGameSetting.getScreenRow()][randWildPositionIdx.get(randIdx)%baseGameSetting.getScreenRow()] = 0;
            randWildPositionIdx.remove(randIdx);
        }
        return result;
    }

    private int[][] reCalculateWildScreenSymbol(int[][] randWildScreen){
        int[][] result = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];

        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                if( baseGameSetting.getSymbolAttribute()[randWildScreen[column][row]] == EnumHandler.SymbolAttribute.Wild)
                    result[column][row] = 0;
                else
                    result[column][row] = randWildScreen[column][row];
            }
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

    private int[][] getUneliminateWild2Position(int[][] screenLabel,int[][] preEliminatePosition,int[][] afterRandWildScreen){
        int[][] result = new int[baseGameSetting.getScreenColumn()][baseGameSetting.getScreenRow()];

        for(int column = 0; column < baseGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < baseGameSetting.getScreenRow(); ++row){
                if( baseGameSetting.getSymbolAttribute()[afterRandWildScreen[column][row]] == EnumHandler.SymbolAttribute.Wild && preEliminatePosition[column][row] == 0 )
                    result[column][row] = 1;
                else
                    result[column][row] = screenLabel[column][row];
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

    private boolean isOddSpin() {
        return common.getSpinType() == EnumHandler.SpinType.OddsSpin
                || common.getSettingIdType() == 2;
    }

    public int getMiniGameWaterLevel(int accumulateData){
        double gap = (extendBaseSetting.getScatterComboRate()[1][0] / 10000000000.0) * 35;
        int rounded = (int) Math.round(gap);
        int curLevel = accumulateData / rounded + 1;
        if (curLevel > 9) {
            return 10;
        }
        return curLevel;
    }

    private int[] getNewBieAccumulation(int ballCount,SeatInfo seatInfo,SpecialFeatureCalculatorResult specialFeatureCalculatorResult){
        int accumulateData = seatInfo.getStatusAccumulation() == null ? 0 : seatInfo.getStatusAccumulation()[0];
        int addData = 1;
        if(addData + accumulateData < this.statusMaxAccum && ballCount > 0) {
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
    protected ExtendInfoForBaseGameResult_JHS101003 calculateMiniWaterLvl(ExtendInfoForBaseGameResult_JHS101003 extendInfo , ScreenGeneratorResult screenGeneratorResult, SpecialFeatureCalculatorResult specialFeatureCalculatorResult) {
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

}
