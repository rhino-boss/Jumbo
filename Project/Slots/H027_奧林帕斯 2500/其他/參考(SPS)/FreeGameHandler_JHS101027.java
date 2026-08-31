package com.jumbogames.sps.logic.FreeGame;

import com.JH5.jps.ExtendJackpotSetting.JackpotExtendSetting_OPJackpot_jumbo;
import com.JH5.jps.JackpotHandler_OPJackpot_jumbo;
import com.base.jps.Jackpot.JackpotResult;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.base.sps.common.Common;
import com.base.sps.entity.client.*;
import com.base.sps.entity.system.ScreenCalculatorResult;
import com.base.sps.entity.system.SpecialFeatureCalculatorResult;
import com.base.sps.logic.ScreenGeneratorResult;
import com.jumbogames.sps.entity.client.ExtendFreeGameResult.ExtendInfoForFreeGameResult_JHS101027;
import com.jumbogames.sps.entity.client.ExtendFreeGameSetting.FreeGameExtendSetting_JHS101027;
import com.jumbogames.sps.logic.BaseGame.ExtendDataFromBaseToFeatureGame_JHS101027;
import com.jumbogames.sps.logic.FreeGameHandler;
import com.jumbogames.sps.module.DisplayLogicInfoCalculator;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * 101027（奧林帕斯2500）FreeGame：架構沿用101006，
 * 差異僅在 mergeSpecialScreen 存活C2/C3的升級規則：C2、C3皆提供乘倍值，但只有C3每次消除後往上升一級，
 * C2維持原值不變（§3.2，見 getUpgradedMultiplierValue，對應§7.2跨局累積乘倍）。
 */
public class FreeGameHandler_JHS101027 extends FreeGameHandler {
    private FreeGameExtendSetting_JHS101027 extendFreeSetting = new FreeGameExtendSetting_JHS101027();
    private ExtendDataFromBaseToFeatureGame_JHS101027 extendBaseGame = new ExtendDataFromBaseToFeatureGame_JHS101027();
    private int highLow;
    public FreeGameHandler_JHS101027(Common common) {
        super(common);
    }

    public FreeGameResult getSpinResult(SlotSpinRequest slotSpinRequest, EnumHandler.SpecialHitInfo specialHitInfo, DisplayLogicInfo displayLogicInfoOfLastRecord, String json) {
        // 1. 確認是否成功被初始化。
        if (initialFlag != true)
            return new FreeGameResult();
        highLow = 0;

        extendFreeSetting = (FreeGameExtendSetting_JHS101027) super.freeGameSetting.getFreeGameExtendSetting();

        try {
            if (json != null){
                ObjectMapper objectMapper = new ObjectMapper();
                extendBaseGame = objectMapper.readValue(json, ExtendDataFromBaseToFeatureGame_JHS101027.class);
            }
        } catch (IOException e) {
            e.printStackTrace();
            System.out.println("[Error] getSpinResult objectMapper.readValue exception: " + e);
        }
        if (this.common.getSpinType() == EnumHandler.SpinType.OddsSpin){
            if (this.common.getWeightTableIndex()>1 && extendBaseGame.getAvailableHitJPOption()[this.common.getElementIndex(extendBaseGame.getAvailableBetMultiplier(),slotSpinRequest.getBetRequest().getWaysBet())] == 3){
                this.common.setNoHitGrand(true);
            }
            switch (slotSpinRequest.getExtraBetType()){
                case ExtraBet_BuyFreeGame:
                case ExtraBet_FreeGameCard:
                    highLow = freeGameSetting.getBuyFeatureOddsGroupingIdx()[0][this.common.getFeatureGameOddsSpinInfo().getOddsLevelIdx()];
                    break;
                case ExtraBet_BuyFreeGame02:
                    highLow = freeGameSetting.getBuyFeatureOddsGroupingIdx()[1][this.common.getFeatureGameOddsSpinInfo().getOddsLevelIdx()];
                    break;
                default:
                    highLow = freeGameSetting.getOddsGroupingIdx()[this.common.getWeightTableIndex()][this.common.getFeatureGameOddsSpinInfo().getOddsLevelIdx()];
            }
        }
        switch (specialHitInfo) {
            case freeGame_01:
            case freeGame_02:
            case freeGame_03:
                return calculateFreeGameResult(slotSpinRequest, displayLogicInfoOfLastRecord, getDefaultFreeGameRounds(specialHitInfo));
            default :
                return new FreeGameResult();
        }
    }

    private FreeGameResult calculateFreeGameResult(SlotSpinRequest slotSpinRequest, DisplayLogicInfo displayLogicInfoOfLastRecord, int initialRounds) {
        FreeGameResult freeGameResult = new FreeGameResult();
        ArrayList<FreeGameOneRoundResult> roundResult = new ArrayList<FreeGameOneRoundResult>();
        // Extra Bet / Buy Feature 專用盤面邏輯待下個階段補上，目前一律使用一般FG輪帶起始位置
        int startTable = extendFreeSetting.getTableStart()[0];

        //設定起始場次
        freeGameResult.setTotalRound(initialRounds);

        ArrayList<Integer> roundTableList = new ArrayList<>();
        // 目前都只有一種RoundList排序
        roundTableList = getRoundList(extendFreeSetting.getRoundTableList());
        shuffleArray(roundTableList);// 打亂

        for (int i = 0; i < freeGameResult.getTotalRound(); i = i + 1) {
            int currentTable = getRoundTable(roundTableList,i) + startTable;

            FreeGameOneRoundResult oneRoundResult = new FreeGameOneRoundResult(super.freeGameSetting);

            // 用RNG產生畫面
            ScreenGeneratorResult screenGeneratorResult = GenerateScreenLabel(currentTable);

            // C2起始倍數、C2→C3轉換的權重取決於這次用哪套FG輪帶(tableIdx，對應FG_Symbol/(2)/(3))
            int selectC2Table = screenGeneratorResult.tableIdx;

            // 滾停初始盤面若出現C2，依目前C2顆數各自獨立骰一次轉C3（§3.2 weight_C2_to_C3_by_initial_count）
            int[] multiplierSymbolIds = getMultiplierSymbolIds();
            applyInitialC2ToC3Conversion(screenGeneratorResult.screenLabel, selectC2Table, multiplierSymbolIds);

            // 計算畫面。
            ScreenCalculatorResult screenCalculatorResult = screenCalculator.CalculateCrushCountScreenResult(slotSpinRequest, screenGeneratorResult.screenLabel, extendFreeSetting.getHitCrushCount());

            int[][] specialScreen = getSpecialScreenMultiplier(screenGeneratorResult.screenLabel, selectC2Table);

            // 處理消消樂流程
            ExtendInfoForFreeGameResult_JHS101027 extendResult = calculateExtendInfoForFreeGameResult(slotSpinRequest, screenGeneratorResult, screenCalculatorResult, specialScreen, selectC2Table);

            // 使用最後的畫面判斷是否中了reSpin。(re-trigger)
            SpecialFeatureCalculatorResult specialFeatureCalculatorResult = specialFeatureHandler.getFeatureResult(getLastScreenLabel(screenGeneratorResult, extendResult), slotSpinRequest);

            specialFeatureCalculatorResult = RecalculatespecialFeatureCalculatorResult1(screenGeneratorResult.screenLabel,
                    specialFeatureCalculatorResult,
                    slotSpinRequest);
            // 依據數學權重判斷非盤面bonus是否真的中了特殊feature。(by game)
            ExtendDataFromBaseToFeatureGame_JHS101027 tmpExtend = RecalculatespecialFeatureCalculatorResult(screenGeneratorResult.screenLabel,
                    specialFeatureCalculatorResult,
                    slotSpinRequest,
                    i);

            long initialScreenWin = getInitialScreenWin(screenCalculatorResult);

            // 累計
            int accumulateMultiplier = extendResult.getAccumulateMultiplier();
            if(i > 0) {
                accumulateMultiplier = extendResult.updateAccumulateMultiplier(((ExtendInfoForFreeGameResult_JHS101027) roundResult.get(i - 1).getExtendInfoForFreeGameResult()).getAccumulateMultiplier());
            }else
                accumulateMultiplier = extendResult.updateAccumulateMultiplier(0);

            extendResult.setAccumulateMultiplier(accumulateMultiplier);

            //計算盤面有幾個C1
            int sysScatterCount = getSymbolCount(getLastScreenLabel(screenGeneratorResult, extendResult), EnumHandler.SymbolAttribute.FreeGame);
            extendResult.setSysScatterCount(sysScatterCount);

            // 計算FG贏分乘倍（Scatter/reSpin賠付不乘倍，見ExtendInfoForFreeGameResult_JHS101027.calculateExtendTotalWin註解）
            extendResult.calculateExtendTotalWin(initialScreenWin);

            // 包裝OneRoundRoundResult
            RoundInfo roundInfo = getRoundInfo(specialFeatureCalculatorResult, freeGameResult.getTotalRound(), i);

            freeGameResult.setTotalRound(freeGameResult.getTotalRound() + roundInfo.getAddRound());
            //如果有觸發ReTrigger的話，新增高表場次
            if (roundInfo.getAddRound() > 0){
                ArrayList<Integer> addRoundList = getRoundList(extendFreeSetting.getAddRoundTableList());
                shuffleArray(addRoundList);
                roundTableList = setRoundList(roundTableList,addRoundList);
            }

            DisplayLogicInfo oneRoundDisplayLogicInfo = (new DisplayLogicInfoCalculator()).calculateDisplayLogicInfo(displayLogicInfoOfLastRecord, roundResult, oneRoundResult.calculatePlayWin(screenCalculatorResult, specialFeatureCalculatorResult, extendResult, super.freeGameSetting), super.IsPossibleHitRespin(freeGameResult.getTotalRound()));

            // 依照畫面資訊以及聽牌邏輯，計算表演資訊。
            DisplayInfo displayInfo = null;

            oneRoundResult.packageOneRoundResult(screenGeneratorResult, screenCalculatorResult, specialFeatureCalculatorResult, extendResult, roundInfo, oneRoundDisplayLogicInfo, displayInfo, super.freeGameSetting);
            roundResult.add(oneRoundResult);
        }

        freeGameResult.packageResult(roundResult);

        return freeGameResult;
    }

    protected ExtendDataFromBaseToFeatureGame_JHS101027 RecalculatespecialFeatureCalculatorResult(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest, int round)
    {
        JackpotResult jackpotResult = new JackpotResult();
        //計算盤面有幾個C1
        long jackpotWeightMultiplier;
        long truePlayerBet;
        int newbie = this.common.isNoHitGrand() ? 0 : 1;
        if (extendBaseGame.getAvailableHitJPOption()[this.common.getElementIndex(extendBaseGame.getAvailableBetMultiplier(),slotSpinRequest.getBetRequest().getWaysBet())] == 3 && common.getWeightTableIndex() >= 2){
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
            jackpotWeightMultiplier = extendFreeSetting.getScatterComboRate()[abtest][scatterComboRateIdx][1];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) this.extendBaseGame.getBetSpec().getExtraBetPaymentList()[1] / this.extendBaseGame.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet10000()[newbie][extendBaseGame.getBetIdx()];
            poolInitValue = extendFreeSetting.getPoolInitValueFeatureBuy();
        } else if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02){
            jackpotWeightMultiplier = extendFreeSetting.getScatterComboRate()[abtest][scatterComboRateIdx][2];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) this.extendBaseGame.getBetSpec().getExtraBetPaymentList()[2] / this.extendBaseGame.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet50000()[newbie][extendBaseGame.getBetIdx()];
            poolInitValue = extendFreeSetting.getPoolInitValueSuperBuy();
        } else {
            jackpotWeightMultiplier = extendFreeSetting.getScatterComboRate()[abtest][scatterComboRateIdx][0];
            truePlayerBet = slotSpinRequest.getPlayerBet();
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet100()[newbie][extendBaseGame.getBetIdx()];
            poolInitValue = extendFreeSetting.getPoolInitValue();
        }

        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(EnumHandler.SpecialHitInfo.bonusGame_02) == 0)
            {
                jackpotResult = ((JackpotHandler_OPJackpot_jumbo)jackpotHandler).getJackpotGameResult(truePlayerBet, jackpotWeightMultiplier, extendBaseGame.getBetSpec().getBaseBet(),hitPoolWeight, poolInitValue);

                //沒中任何pool的處理
                if (jackpotResult.getHitCase() <= 0 || jackpotResult.getHitPool().length == 0){
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i);
                }
            }
        }

        ExtendDataFromBaseToFeatureGame_JHS101027 result = new ExtendDataFromBaseToFeatureGame_JHS101027();

        result.setBonusHitPool(jackpotResult.getHitCase());
        result.setBonusHitCase(jackpotResult.getHitCase());
        result.setJackpotResult(jackpotResult);
        result.setAvailableBetMultiplier(extendBaseGame.getAvailableBetMultiplier());
        result.setAvailableHitJPOption(extendBaseGame.getAvailableHitJPOption());
        // 當有Scatter出現則可以骰MiniGame
        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(EnumHandler.SpecialHitInfo.bonusGame_02) == 0)
            {
                String json = common.prinToJson(result);
                specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(json);
            }
            else
                specialFeatureCalculatorResult.specialFeatureResult[i].setJsonExtendData(null);
        }

        return result;
    }


    protected SpecialFeatureCalculatorResult RecalculatespecialFeatureCalculatorResult1(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest) {

        if(common.isNoHitGrand()) {
            //新手不拉Grand
            for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; ++i) {
                if (specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo() == EnumHandler.SpecialHitInfo.bonusGame_02 && isSettingIDWithoutBonus())
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i); // 新手救援+新手體驗 不提供MiniGame
            }
        }
        return specialFeatureCalculatorResult;
    }

    private int getSymbolCount(int[][] screenLabel, EnumHandler.SymbolAttribute symbolAttribute){
        int symbolCount = 0;
        for (int column = 0; column < freeGameSetting.getScreenColumn(); column++) {
            for (int row = 0; row < freeGameSetting.getScreenRow(); row++) {
                if (freeGameSetting.getSymbolAttribute()[screenLabel[column][row]] == symbolAttribute) {
                    symbolCount = symbolCount + 1;
                }
            }
        }
        return symbolCount;
    }

    private RoundInfo getRoundInfo(SpecialFeatureCalculatorResult specialFeatureCalculatorResult, int freeGameTotalRound, int roundIdx) {
        RoundInfo roundInfo = new RoundInfo();
        roundInfo.setTotalRound(freeGameTotalRound);
        roundInfo.setRoundNumber(roundIdx + 1);

        int iRemainRounds = 0;
        int reTriggerAddRounds = 0;
        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            reTriggerAddRounds = getReTriggerAddRounds(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo());
            iRemainRounds = super.freeGameSetting.getFreeGameExtendSetting().getMaxRound()-freeGameTotalRound;
            if( reTriggerAddRounds > 0 && iRemainRounds > 0){
                iRemainRounds = super.freeGameSetting.getFreeGameExtendSetting().getMaxRound()-freeGameTotalRound;
                if (iRemainRounds > reTriggerAddRounds)
                    roundInfo.setAddRound(reTriggerAddRounds);
                else
                    roundInfo.setAddRound(iRemainRounds);
            }
        }

        return roundInfo;
    }

    private int getReTriggerAddRounds(EnumHandler.SpecialHitInfo specialHitInfo) {
        try {
            if (specialHitInfo == null)
                return 0;

            if (specialHitInfo.ordinal() < EnumHandler.SpecialHitInfo.reSpin_01.ordinal() ||
                    specialHitInfo.ordinal() > EnumHandler.SpecialHitInfo.reSpin_04.ordinal())
                return 0;

            int index = specialHitInfo.ordinal() - EnumHandler.SpecialHitInfo.reSpin_01.ordinal();
            return extendFreeSetting.getAddRoundPerHit()[index];
        } catch (Exception e) {
            System.out.println("[Error] getReTriggerAddRounds = " + specialHitInfo);
            e.printStackTrace();
            return 0;
        }
    }

    private ScreenGeneratorResult GenerateScreenLabel(int tableIndex) {
        ScreenGeneratorResult result = screenGenerator.GenerateScreenLabel(tableIndex,extendFreeSetting.getWheelWeight());
        return result;
    }

    private int getDefaultFreeGameRounds(EnumHandler.SpecialHitInfo specialHitInfo){
        try {
            int index = specialHitInfo.ordinal() - EnumHandler.SpecialHitInfo.freeGame_01.ordinal();
            return extendFreeSetting.getDefaultRound()[index];
        } catch (Exception e) {
            System.out.println("[Error] getDefaultFreeGameRounds = " + specialHitInfo);
            e.printStackTrace();
            return 0;
        }
    }

    private ExtendInfoForFreeGameResult_JHS101027 calculateExtendInfoForFreeGameResult(SlotSpinRequest slotSpinRequest, ScreenGeneratorResult screenGeneratorResult, ScreenCalculatorResult screenCalculatorResult, int[][] specialScreen,int selectC2Table) {
        ExtendInfoForFreeGameResult_JHS101027 result = new ExtendInfoForFreeGameResult_JHS101027();

        ArrayList<CascadeEliminateResult> cascadeEliminateResult = new ArrayList<CascadeEliminateResult>(); // 紀錄每一次消除結果。

        int tableIdx = screenGeneratorResult.tableIdx;
        int extraMultiplier = 1;
        int[][] roundRngInfo = screenGeneratorResult.getRngInfo();
        int[][] roundSpecialScreen = specialScreen.clone();
        int[] cantRepeatSymbolId = getCantRepeatSymbolId();
        int[] multiplierSymbolIds = getMultiplierSymbolIds();
        int comboCount = 0; // 第幾次消除，供weight_C2_to_C3_by_drop_combo查表用

        //有贏分再計算消除掉落使用哪個輪帶表
        while (screenCalculatorResult.waysGameResult.getPlayerWin() > 0){
            comboCount++;

            //計算有連線得分的位置
            int[][] preEliminatePosition = getEliminatePosition(screenCalculatorResult.waysGameResult.getWaysResult());

            //消除symbol並產生新盤面結果
            screenGeneratorResult = this.screenGenerator.generateCrushEliminateFallDownScreen(tableIdx, screenGeneratorResult.screenLabel, preEliminatePosition, freeGameSetting.getWheelData(), false, cantRepeatSymbolId,roundRngInfo, multiplierSymbolIds);

            //Eliminate後未被消除的位置
            int[][] afterEliminatePosition = getAfterEliminatePosition(preEliminatePosition);

            //消除掉落後新補進來的C2，依combo數各自獨立骰一次轉C3（§3.2 weight_C2_to_C3_by_drop_combo）
            applyDropComboC2ToC3Conversion(screenGeneratorResult.screenLabel, afterEliminatePosition, selectC2Table, comboCount, multiplierSymbolIds);

            roundRngInfo = getMergeRNGInfo(roundRngInfo,screenGeneratorResult.rngInfo);

            // 重新排列specialScreen（存活的C3在此往上升一級，C2維持原值，見§3.2）
            int[][] cascadeSpecialScreen = mergeSpecialScreen(roundSpecialScreen,screenGeneratorResult, selectC2Table, afterEliminatePosition);
            roundSpecialScreen = cascadeSpecialScreen.clone();

            //計算累計乘倍
            extraMultiplier = getMultiplier(roundSpecialScreen);

            //計算新盤面得分
            screenCalculatorResult = this.screenCalculator.CalculateCrushCountScreenResult(slotSpinRequest, screenGeneratorResult.screenLabel,extendFreeSetting.getHitCrushCount());

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

        return result;
    }

    private int[][] getEliminatePosition(WaysResult[] srcWaysResult){
        int[][] eliminatePosition = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];

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
        for (int i = 0; i < freeGameSetting.getSymbolAttribute().length; i++) {
            if (freeGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.FreeGame)
                result[0] = i;
        }
        return result;
    }

    // 找出C2、C3的symbol id，兩者都需要在cascade掉落時被framework用rngInfo==-2追蹤延續（見generateCrushEliminateFallDownScreen）。
    private int[] getMultiplierSymbolIds(){
        int c2Id = -1;
        int c3Id = -1;
        for (int i = 0; i < freeGameSetting.getSymbolAttribute().length; i++) {
            if (freeGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.ballC2)
                c2Id = i;
            if (freeGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.ballC3)
                c3Id = i;
        }
        return new int[]{c2Id, c3Id};
    }

    private int[][] getLastScreenLabel(ScreenGeneratorResult screenGeneratorResult, ExtendInfoForFreeGameResult_JHS101027 extendGameResult){
        if (extendGameResult.getCascadeEliminateResult().size() == 0)
            return screenGeneratorResult.screenLabel;
        else
            return extendGameResult.getCascadeEliminateResult().get(extendGameResult.getCascadeEliminateResult().size()-1).getScreenSymbol();
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
        for (int column = 0; column < freeGameSetting.getScreenColumn(); ++column)
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row)
                if(screenLabel[column][row] == c2Id)
                    c2Count++;

        if(c2Count == 0)
            return;

        int c3Id = multiplierSymbolIds[1];
        int countIdx = Math.min(c2Count, 6) - 1; // count=1~5對應index0~4，6+對應index5
        int weight = extendFreeSetting.getWeightC2ToC3ByInitialCount()[selectC2Table][countIdx];

        for (int column = 0; column < freeGameSetting.getScreenColumn(); ++column) {
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row) {
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
        int weight = extendFreeSetting.getWeightC2ToC3ByDropCombo()[selectC2Table][comboIdx];

        for (int column = 0; column < freeGameSetting.getScreenColumn(); ++column) {
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row) {
                boolean isFreshlyDropped = afterEliminatePosition[column][row] != 0;
                if(isFreshlyDropped && screenLabel[column][row] == c2Id && common.getRandomNumber(10000) < weight)
                    screenLabel[column][row] = c3Id;
            }
        }
    }

    // C2、C3各自有獨立的權重表（multiplierWeightC2／multiplierWeightC3），倍數池(multiplier)則共用同一份。
    private int[] getMultiplierWeightRow(EnumHandler.SymbolAttribute symbolAttribute, int selectC2Table){
        return (symbolAttribute == EnumHandler.SymbolAttribute.ballC3)
                ? extendFreeSetting.getMultiplierWeightC3()[selectC2Table]
                : extendFreeSetting.getMultiplierWeightC2()[selectC2Table];
    }

    private int[][] getSpecialScreenMultiplier(int[][] screenLabel, int selectC2Table){
        int[][] result = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];

        for (int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                EnumHandler.SymbolAttribute symbolAttribute = freeGameSetting.getSymbolAttribute()[screenLabel[column][row]];
                if(isMultiplierSymbol(symbolAttribute)) {
                    result[column][row] = extendFreeSetting.getMultiplier()[common.getArrayIndexByWeight(getMultiplierWeightRow(symbolAttribute, selectC2Table))];
                }
            }
        }
        return result;
    }

    private int[][] mergeSpecialScreen(int[][] specialScreen, ScreenGeneratorResult screenGeneratorResult, int selectC2Table,int[][] afterEliminatePosition){
        int[][] result = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];
        ArrayList<Integer> multiplierList = new ArrayList<>();

        // 先調整舊specialScreen位置
        for(int i = 0; i < freeGameSetting.getScreenColumn(); ++i)
            Arrays.fill(result[i],0);

        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for(int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                if(specialScreen[column][row] > 0)
                    multiplierList.add(specialScreen[column][row]);
            }
        }

        // 合併補牌的specialScreen(先取值再處理位置)
        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for(int row = 0; row < freeGameSetting.getScreenRow(); ++row) {
                if(afterEliminatePosition[column][row] == 0 && screenGeneratorResult.rngInfo[column][row] == -2 &&  multiplierList.size() > 0) {
                    // 初始盤面已存在的C2/C3存活下來：C3每發生一次消除就往上升一級，C2維持原值不變（§3.2）
                    int carriedValue = multiplierList.get(0);
                    EnumHandler.SymbolAttribute survivedAttribute = freeGameSetting.getSymbolAttribute()[screenGeneratorResult.screenLabel[column][row]];
                    result[column][row] = (survivedAttribute == EnumHandler.SymbolAttribute.ballC3)
                            ? getUpgradedMultiplierValue(carriedValue)
                            : carriedValue;
                    multiplierList.remove(0);
                }else if( screenGeneratorResult.rngInfo[column][row] != -2){
                    EnumHandler.SymbolAttribute newAttribute = freeGameSetting.getSymbolAttribute()[screenGeneratorResult.screenLabel[column][row]];
                    if(isMultiplierSymbol(newAttribute)) {
                        // 補牌新出現的 C2/C3，起始倍數一律重新依「各自」的權重表抽值
                        int idx = common.getArrayIndexByWeight(getMultiplierWeightRow(newAttribute, selectC2Table));
                        result[column][row] = extendFreeSetting.getMultiplier()[idx];
                    }
                }
            }
        }

        return result;
    }

    private int getUpgradedMultiplierValue(int currentValue) {
        int[] pool = extendFreeSetting.getMultiplier();
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

        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for(int row = 0; row < freeGameSetting.getScreenRow(); ++row) {
                result += specialScreen[column][row];
            }
        }

        return result;
    }

    private ArrayList<Integer> getRoundList(int[] input) {
        ArrayList<Integer> result = new ArrayList<>();

        for (int i = 0; i < input.length; i++) {
            int repeat = input[i];
            for (int j = 0; j < repeat; j++) {
                result.add(i);
            }
        }

        return result;
    }

    public void shuffleArray(ArrayList<Integer> data) {
        int length;
        length = data.size(); // 避免越界


        for (int i = length - 1; i > 0; i--) {
            int j = common.getRandomNumber(i + 1); // 產生 0~i
            int tmp = data.get(i);
            data.set(i, data.get(j));
            data.set(j, tmp);
        }
    }

    private Integer getRoundTable(ArrayList<Integer> tableList,int round){
        return tableList.get(round);
    }

    private ArrayList<Integer> setRoundList(ArrayList<Integer> roundList,ArrayList<Integer> addRoundList){
        ArrayList<Integer> result = new ArrayList<>();
        result = (ArrayList<Integer>) roundList.clone();
        for (int i = 0; i < addRoundList.size(); i++){
            result.add(addRoundList.get(i));
        }
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

    // 本局初始盤面（cascade開始前）的一般符號贏分，餵給calculateExtendTotalWin做乘倍計算。
    // 101006對應方法會把Scatter/reSpin賠付一併加總進來，101027 §4規定「Scatter獎金不乘C2」，所以這裡不比照辦理。
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

    private boolean isSettingIDWithoutBonus(){
        if(EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF_OLD
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL_D)
            return true;

        return false;
    }
}
