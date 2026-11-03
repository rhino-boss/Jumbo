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
import com.jumbogames.sps.entity.client.ExtendFreeGameResult.ExtendInfoForFreeGameResult_JHS101003;
import com.jumbogames.sps.entity.client.ExtendFreeGameSetting.FreeGameExtendSetting_JHS101003;
import com.jumbogames.sps.logic.BaseGame.ExtendDataFromBaseToFeatureGame_JHS101003;
import com.jumbogames.sps.logic.FreeGameHandler;
import com.jumbogames.sps.module.DisplayLogicInfoCalculator;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;



public class FreeGameHandler_JHS101003 extends FreeGameHandler {
    private FreeGameExtendSetting_JHS101003 extendFreeSetting = new FreeGameExtendSetting_JHS101003();
    private ExtendDataFromBaseToFeatureGame_JHS101003 extendBaseGame = new ExtendDataFromBaseToFeatureGame_JHS101003();
    private final int goldenSymbolId = 2;
    private final int wildSymbolId = 0;
    private ArrayList<Integer> highRoundList = new ArrayList<>();
    private int multiplierPosition = 0;
    private boolean randomWildChance = true;
    private int highLow;


    public FreeGameHandler_JHS101003(Common common) {
        super(common);
    }

    public FreeGameResult getSpinResult(SlotSpinRequest slotSpinRequest, EnumHandler.SpecialHitInfo specialHitInfo, DisplayLogicInfo displayLogicInfoOfLastRecord, String json) {
        // 1. 確認是否成功被初始化
        if (!initialFlag) {
            return new FreeGameResult();
        }

        extendFreeSetting = (FreeGameExtendSetting_JHS101003) super.freeGameSetting.getFreeGameExtendSetting();
        this.randomWildChance = true;
        try {
            if (json != null) {
                ObjectMapper objectMapper = new ObjectMapper();
                extendBaseGame = objectMapper.readValue(json, ExtendDataFromBaseToFeatureGame_JHS101003.class);
            }
        } catch (IOException e) {
            e.printStackTrace();
            System.out.println("[Error] getSpinResult objectMapper.readValue exception: " + e);
        }
        if (this.common.getSpinType() == EnumHandler.SpinType.OddsSpin){
            highLow = freeGameSetting.getOddsGroupingIdx()[this.common.getWeightTableIndex()][this.common.getFeatureGameOddsSpinInfo().getOddsLevelIdx()];
            if (this.common.getWeightTableIndex()>1 && extendBaseGame.getAvailableHitJPOption()[this.common.getElementIndex(extendBaseGame.getAvailableBetMultiplier(),slotSpinRequest.getBetRequest().getWaysBet())] == 3){
                this.common.setNoHitGrand(true);
            }
        } else {
            highLow = 0;
        }
        switch (specialHitInfo) {
            case freeGame_01:
                return calculateFreeGameResult(slotSpinRequest, displayLogicInfoOfLastRecord);
            default:
                return new FreeGameResult();
        }

    }

    private FreeGameResult calculateFreeGameResult(SlotSpinRequest slotSpinRequest, DisplayLogicInfo displayLogicInfoOfLastRecord) {
        FreeGameResult freeGameResult = new FreeGameResult();
        ArrayList<FreeGameOneRoundResult> roundResult = new ArrayList<FreeGameOneRoundResult>();

        int initialRounds = extendFreeSetting.getBaseRound();

        freeGameResult.setTotalRound(initialRounds);

        for (int i = 0; i < freeGameResult.getTotalRound(); i++) {
            FreeGameOneRoundResult oneRoundResult = new FreeGameOneRoundResult(super.freeGameSetting);
            // 用RNG產生畫面
            ScreenGeneratorResult screenGeneratorResult = generateScreenLabel(0);

            //將goldenSymbol的地方轉成一般Symbol ID
            int[][] change2NewScreen = changeScreen2NormalSymbol(screenGeneratorResult.screenLabel);
            // 計算畫面
            ScreenCalculatorResult screenCalculatorResult = screenCalculator.CalculateScreenResult(slotSpinRequest, change2NewScreen);

            //  乘上連消倍率
            int firstSpinMultiplier = getCurrentExtraMultiplier(slotSpinRequest.getExtraBetType());
            if (screenCalculatorResult.waysGameResult.getPlayerWin() > 0) {
                reCalculateScreenResult(screenCalculatorResult, firstSpinMultiplier);
            }

            int tableIdx = screenGeneratorResult.tableIdx;
            //  處理消消樂流程
            ExtendInfoForFreeGameResult_JHS101003 extendResult = calculateExtendInfoForFreeGameResult(tableIdx,slotSpinRequest, screenGeneratorResult, screenCalculatorResult);

            //  紀錄連消分數的歷程
            extendResult.setTotalMultiplierList(firstSpinMultiplier, extendResult.getCascadeEliminateResult());

            int[][] lastScreenScreen = getLastScreenLabel(screenGeneratorResult, extendResult);

            // 使用最後的畫面檢查有沒有觸發 re-trigger
            SpecialFeatureCalculatorResult specialFeatureCalculatorResult = specialFeatureHandler.getFeatureResult(lastScreenScreen, slotSpinRequest);

            //用最後的畫面計算畫面上總共有多少FreeGameSymbol
            int lastScreenTotalFreeGameSymbolCount = getFreeGameSymbolCount(lastScreenScreen);
            specialFeatureCalculatorResult = RecalculatespecialFeatureCalculatorResult1(screenGeneratorResult.screenLabel,
                    specialFeatureCalculatorResult,
                    slotSpinRequest);
            //重新計算Special Feature
            specialFeatureCalculatorResult = reCalculatorSpecialFeatureResult(lastScreenScreen,lastScreenTotalFreeGameSymbolCount, specialFeatureCalculatorResult, i);



            recalculateSpecialFeatureCalculatorResult(screenGeneratorResult.screenLabel,
                    specialFeatureCalculatorResult,
                    slotSpinRequest,
                    i);
            //包裝OneRoundResult
            RoundInfo roundInfo = getRoundInfo(specialFeatureCalculatorResult, freeGameResult.getTotalRound(), i, lastScreenTotalFreeGameSymbolCount);

            freeGameResult.setTotalRound(freeGameResult.getTotalRound() + roundInfo.getAddRound());
            //如果有觸發ReTrigger的話，新增高表場次

            int sysScatterCount = getSymbolCount(getLastScreenLabel(screenGeneratorResult, extendResult), EnumHandler.SymbolAttribute.FreeGame);
            extendResult.setSysScatterCount(sysScatterCount);

            DisplayLogicInfo oneRoundDisplayLogicInfo = (new DisplayLogicInfoCalculator()).calculateDisplayLogicInfo(displayLogicInfoOfLastRecord, roundResult, oneRoundResult.calculatePlayWin(screenCalculatorResult, specialFeatureCalculatorResult, extendResult, super.freeGameSetting), super.IsPossibleHitRespin(freeGameResult.getTotalRound()));

            //  依照畫面資訊以及廳談邏輯，計算表演資訊
            DisplayInfo displayInfo = null;

            oneRoundResult.packageOneRoundResult(screenGeneratorResult, screenCalculatorResult, specialFeatureCalculatorResult, extendResult, roundInfo, oneRoundDisplayLogicInfo, displayInfo, super.freeGameSetting);
            roundResult.add(oneRoundResult);
            //重置連消倍率
            resetMultiplierPosition();
        }
        freeGameResult.packageResult(roundResult);

        return freeGameResult;
    }

    private ArrayList<Integer> setRoundList(ArrayList<Integer> roundList,ArrayList<Integer> addRoundList){
        ArrayList<Integer> result = new ArrayList<>();
        result = (ArrayList<Integer>) roundList.clone();
        for (int i = 0; i < addRoundList.size(); i++){
            result.add(addRoundList.get(i));
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

    private boolean isSettingIDWithoutBonus(){
        if(EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.RELIEF_OLD
                || EnumHandler.SettingIDType.fromCode(common.getSettingIdType()) == EnumHandler.SettingIDType.TRIAL)
            return true;

        return false;
    }

    protected void recalculateSpecialFeatureCalculatorResult(int[][] screenLabel, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, SlotSpinRequest slotSpinRequest, int round)
    {
        JackpotResult jackpotResult = new JackpotResult();
        //計算盤面有幾個C1
        int totalC1Count = getSymbolCount(screenLabel, EnumHandler.SymbolAttribute.FreeGame);
        long jackpotWeightMultiplier;
        long truePlayerBet;
        int newbie = this.common.isNoHitGrand()?0:1;
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

        if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame){
            jackpotWeightMultiplier = extendFreeSetting.getScatterComboRate()[scatterComboRateIdx][1];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) extendBaseGame.getBetSpec().getExtraBetPaymentList()[1] / extendBaseGame.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet4050()[newbie][extendBaseGame.getBetIdx()];
            poolInitValue = extendFreeSetting.getPoolInitValueFeatureBuy();
        } else if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02){
            jackpotWeightMultiplier = extendFreeSetting.getScatterComboRate()[scatterComboRateIdx][2];
            truePlayerBet = (long) (slotSpinRequest.getPlayerBet() / ((double) extendBaseGame.getBetSpec().getExtraBetPaymentList()[2] / extendBaseGame.getBetSpec().getBaseBet()));
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet25000()[newbie][extendBaseGame.getBetIdx()];
            poolInitValue = extendFreeSetting.getPoolInitValueSuperBuy();
        }else {
            jackpotWeightMultiplier = extendFreeSetting.getScatterComboRate()[scatterComboRateIdx][0];
            truePlayerBet = slotSpinRequest.getPlayerBet();
            hitPoolWeight = ((JackpotExtendSetting_OPJackpot_jumbo) jackpotHandler.getJackpotSetting().getJackpotPoolData()[jpIdx].getJackpotExtendSetting()).getHitPoolWeight_bet100()[newbie][extendBaseGame.getBetIdx()];
            poolInitValue = extendFreeSetting.getPoolInitValue();
        }

        for (int i = 0; i < specialFeatureCalculatorResult.specialFeatureResult.length; i++) {
            if(specialFeatureCalculatorResult.specialFeatureResult[i].getSpecialHitInfo().compareTo(EnumHandler.SpecialHitInfo.bonusGame_02) == 0)
            {
                jackpotResult = ((JackpotHandler_OPJackpot_jumbo)jackpotHandler).getJackpotGameResult(truePlayerBet, jackpotWeightMultiplier, extendBaseGame.getBaseBet(),hitPoolWeight, poolInitValue);

                //沒中任何pool的處理
                if (jackpotResult.getHitCase() <= 0 || jackpotResult.getHitPool().length == 0){
                    specialFeatureHandler.setNoFeatureResult(specialFeatureCalculatorResult, i);
                }
            }
        }

        ExtendDataFromBaseToFeatureGame_JHS101003 result = new ExtendDataFromBaseToFeatureGame_JHS101003();

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


    private ScreenGeneratorResult generateScreenLabel(int tableIndex) {
        // 在GenerateScreenLabel 只要上限大於0會自動指定輪帶表，所以這裡+1後進入會選擇 (tableIndex- 1) 的表
        ScreenGeneratorResult result = screenGenerator.GenerateScreenLabel(tableIndex, extendFreeSetting.getWheelWeight());
        return result;
    }

    private ExtendInfoForFreeGameResult_JHS101003 calculateExtendInfoForFreeGameResult(int currentTable,SlotSpinRequest slotSpinRequest, ScreenGeneratorResult screenGeneratorResult, ScreenCalculatorResult screenCalculatorResult) {
        ExtendInfoForFreeGameResult_JHS101003 result = new ExtendInfoForFreeGameResult_JHS101003();
        ArrayList<CascadeEliminateResult> cascadeEliminateResult = new ArrayList<CascadeEliminateResult>();

        int tableIdx = screenGeneratorResult.tableIdx;
        int extraMultiplier; //累積倍數
        int[][] randWildScreen = null;
        int[][] afterRandWildScreen = screenGeneratorResult.screenLabel.clone();

        while (screenCalculatorResult.waysGameResult.getPlayerWin() > 0) {

            //紀錄所有金框的位置
            boolean[][] goldenSymbolPosition = recordGoldenSymbolPosition(afterRandWildScreen);

            //計算有連線得分的位置
            int[][] preEliminatePosition = getEliminatePosition(screenCalculatorResult.waysGameResult.getWaysResult());

            //處理未消除的WW2位置
            if(isRandomWildChance())
                screenGeneratorResult.screenLabel = getUneliminateWild2Position(screenGeneratorResult.screenLabel,preEliminatePosition,afterRandWildScreen);

            //處理GoldSymbol變成一般wild，並改變GoldSymbol位置上的消除類型
            int[][] screenSymbol = calculateGoldenSymbol2ChangeWildScreen(screenGeneratorResult.screenLabel, preEliminatePosition, goldenSymbolPosition);

            //回傳倍數
            extraMultiplier = getCurrentExtraMultiplier(slotSpinRequest.getExtraBetType());

            //消除symbol並產生新盤面結果
            screenGeneratorResult = this.screenGenerator.generateEliminateReplacement(tableIdx,screenSymbol,preEliminatePosition, freeGameSetting.getWheelData(), true, getC1SymbolId(), extendFreeSetting.getDropWheelWeight());

            //取得金框消除的idx
            ArrayList<Integer> potentialWild2Idx = getPotentialWild2Idx(preEliminatePosition);

            //判斷是否有機會觸發隨機百搭
            if(isRandomWildChance() && !potentialWild2Idx.isEmpty()) {
                int rnd = common.getArrayIndexByWeight(extendFreeSetting.getRandomWildWeight()[tableIdx]);

                int randomWildCount = extendFreeSetting.getRandomWild()[rnd];

                if(randomWildCount > 0) {
                    //獲得可以分布的位置
                    ArrayList<Integer> randWildPositionIdx = getRandWildPositionIdx(potentialWild2Idx,  screenGeneratorResult.screenLabel, slotSpinRequest);
                    //灑落百搭後的盤面
                    randWildScreen = calculateRandomWildScreen( screenGeneratorResult.screenLabel, randomWildCount, randWildPositionIdx, potentialWild2Idx);
                    //當進化WW2成功時，就不再有機會進化
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
            screenCalculatorResult = this.screenCalculator.CalculateScreenResult(slotSpinRequest, change2NewScreen);

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

    private boolean checkSameSymbol(int symbol,int otherSymbol){
        int noRepeatingCount = extendFreeSetting.getNoRepeatingSymbolCount();
        EnumHandler.SymbolAttribute[] symbolAttributeList = freeGameSetting.getSymbolAttribute();
        if (symbolAttributeList[otherSymbol] == EnumHandler.SymbolAttribute.FreeGame ||
                symbolAttributeList[otherSymbol] == EnumHandler.SymbolAttribute.Wild ) {
            return false;
        }
        return otherSymbol - symbol == 0 || Math.abs(symbol - otherSymbol) == noRepeatingCount;
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
    private int calculateEliminateCount(int[] preEliminatePosition){
        int result = 0;
        for (int j : preEliminatePosition) {
            if (j == EnumHandler.EliminateType.Eliminate.ordinal()) {
                result++;
            }
        }
        return result;
    }
    /**
     * 檢查是否需要改變掉落Symbol，如果需要就回傳不想要掉落的Symbol，不需要則回傳-1
     */
    private int checkScreenIsRepeat(int[] screenRowLabel){
        int noRepeatingCount = extendFreeSetting.getNoRepeatingSymbolCount();
        EnumHandler.SymbolAttribute[] symbolAttributeList = freeGameSetting.getSymbolAttribute();
        Map<Integer,Integer> repeatingSymbolList = new HashMap<>();

        for (int curSymbolId : screenRowLabel) {
            //C1跟Wild、None 不用去計算重複
            if (symbolAttributeList[curSymbolId] == EnumHandler.SymbolAttribute.FreeGame ||
                    symbolAttributeList[curSymbolId] == EnumHandler.SymbolAttribute.Wild ) {
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
    private void reCalculateScreenResult(ScreenCalculatorResult screenCalculatorResult, int firstSpinMultiplier) {
        long totalWin = screenCalculatorResult.waysGameResult.getPlayerWin();

        long newTotalWin = totalWin * firstSpinMultiplier;

        screenCalculatorResult.waysGameResult.setPlayerWin(newTotalWin);
    }

    private int getCurrentExtraMultiplier(EnumHandler.ExtraBetType extraBetType) {
        int[] comboMultiplierList;
        if (extraBetType == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02){
            comboMultiplierList = extendFreeSetting.getComboMultiplierListSuperBuy();
        } else {
            comboMultiplierList = extendFreeSetting.getComboMultiplierList();
        }
        if (multiplierPosition >= comboMultiplierList.length) {
            multiplierPosition = comboMultiplierList.length - 1;
        }
        return comboMultiplierList[multiplierPosition++];
    }

    private void resetMultiplierPosition() {
        multiplierPosition = 0;
    }

    public boolean[][] recordGoldenSymbolPosition(int[][] screen) {
        int noneId = getNoneId();
        boolean[][] goldenSymbol = new boolean[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];
        //重複的一般symbol加上Wild和C1會等於GoldenSymbol起始ID
        int startGoldenID = extendFreeSetting.getNoRepeatingSymbolCount() + 3;

        for (int i = 0; i < freeGameSetting.getScreenColumn(); i++) {
            for (int j = 0; j < freeGameSetting.getScreenRow(); j++) {
                if (screen[i][j] >= startGoldenID && screen[i][j] != noneId) {
                    goldenSymbol[i][j] = true;
                } else {
                    goldenSymbol[i][j] = false;
                }
            }
        }
        return goldenSymbol;
    }

    private int[][] getEliminatePosition(WaysResult[] srcWaysResult) {
        int[][] eliminatePosition = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];
        for (WaysResult waysResult : srcWaysResult) {
            boolean[][] screenHitData = waysResult.getScreenHitData();
            for (int i = 0; i < screenHitData.length; i++) {
                for (int j = 0; j < screenHitData[0].length; j++) {
                    if (screenHitData[i][j] == true) {
                        eliminatePosition[i][j] = EnumHandler.EliminateType.Eliminate.ordinal();
                    }
                }
            }
        }
        return eliminatePosition;
    }

    private int[][] calculateGoldenSymbol2ChangeWildScreen(int[][] screenLabel, int[][] preEliminatePosition, boolean[][] goldenSymbolPosition) {
        int[][] newScreen = new int[screenLabel.length][screenLabel[0].length];
        for (int i = 0; i < screenLabel.length; i++) {
            for (int j = 0; j < screenLabel[0].length; j++) {
                if (preEliminatePosition[i][j] == EnumHandler.EliminateType.Eliminate.ordinal() && goldenSymbolPosition[i][j] == true) {
                    newScreen[i][j] = wildSymbolId;
                    preEliminatePosition[i][j] = goldenSymbolId;
                } else {
                    newScreen[i][j] = screenLabel[i][j];
                }
            }
        }
        return newScreen;
    }

    private SpecialFeatureCalculatorResult reCalculatorSpecialFeatureResult(int[][] lastScreenScreen, int lastScreenTotalFreeGameSymbolCount, SpecialFeatureCalculatorResult specialFeatureCalculatorResult, int roundIdx) {
        SpecialFeatureResult specialFeatureResult = specialFeatureCalculatorResult.specialFeatureResult[0];
        boolean[][] tmpFlagData = new boolean[specialFeatureCalculatorResult.specialFeatureResult[0].getSpecialScreenHitData().length][specialFeatureCalculatorResult.specialFeatureResult[0].getSpecialScreenHitData()[0].length];

        for(int i = 0 ; i < freeGameSetting.getScreenColumn();i++){
            for(int j = 0 ; j < freeGameSetting.getScreenRow();j++){
                if(freeGameSetting.getSymbolAttribute()[lastScreenScreen[i][j]] == EnumHandler.SymbolAttribute.FreeGame){
                    tmpFlagData[i][j] = true;
                }
            }
        }

        if (lastScreenTotalFreeGameSymbolCount >= extendFreeSetting.getMinimumC1Count() && (roundIdx+5) <= extendFreeSetting.getMaxRound()) {
            specialFeatureCalculatorResult.specialFeatureResult[0].setSpecialHitInfo(EnumHandler.SpecialHitInfo.reSpin_01);
            specialFeatureCalculatorResult.specialFeatureResult[0].setSpecialOperations(null);
            specialFeatureCalculatorResult.specialFeatureResult[0].setSpecialScreenHitData(tmpFlagData);
        }
        return specialFeatureCalculatorResult;
    }

    public int[][] changeScreen2NormalSymbol(int[][] originalScreen) {
        EnumHandler.SymbolAttribute[] symbolAttributeList;
        int noRepeatingCount = extendFreeSetting.getNoRepeatingSymbolCount();
        int[][] newScreen = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];
        symbolAttributeList = freeGameSetting.getSymbolAttribute();
        for (int i = 0; i < freeGameSetting.getScreenColumn(); i++) {
            for (int j = 0; j < freeGameSetting.getScreenRow(); j++) {
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

    private int getC1SymbolId() {
        for (int i = 0; i < freeGameSetting.getSymbolAttribute().length; i++) {
            if (freeGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.FreeGame) {
                return i;
            }
        }
        return -1;
    }

    private int getNoneId() {
        for (int i = 0; i < freeGameSetting.getSymbolAttribute().length; i++) {
            if (freeGameSetting.getSymbolAttribute()[i] == EnumHandler.SymbolAttribute.None) {
                return i;
            }
        }
        return -1;
    }

    private int[][] getLastScreenLabel(ScreenGeneratorResult screenGeneratorResult, ExtendInfoForFreeGameResult_JHS101003 extendGameResult) {
        if (extendGameResult.getCascadeEliminateResult().size() == 0) {
            return screenGeneratorResult.screenLabel;
        } else {
            return extendGameResult.getCascadeEliminateResult().get(extendGameResult.getCascadeEliminateResult().size() - 1).getScreenSymbol();
        }
    }

    private int getFreeGameSymbolCount(int[][] screenLabel) {
        int freeGameSymbolCount = 0;
        for (int i = 0; i < freeGameSetting.getScreenColumn(); i++) {
            for (int j = 0; j < freeGameSetting.getScreenRow(); j++) {
                if (freeGameSetting.getSymbolAttribute()[screenLabel[i][j]] == EnumHandler.SymbolAttribute.FreeGame) {
                    freeGameSymbolCount++;
                }
            }
        }
        return freeGameSymbolCount;
    }

    private RoundInfo getRoundInfo(SpecialFeatureCalculatorResult specialFeatureCalculatorResult, int freeGameTotalRound, int roundIdx, int lastScreenTotalFreeGameSymbolCount) {
        RoundInfo roundInfo = new RoundInfo();
        roundInfo.setTotalRound(freeGameTotalRound);
        roundInfo.setRoundNumber(roundIdx + 1);

        int iRemainRounds;
        int reTriggerAddRounds;

        if (specialFeatureCalculatorResult.specialFeatureResult[0].getSpecialHitInfo() == EnumHandler.SpecialHitInfo.reSpin_01){
            reTriggerAddRounds = extendFreeSetting.getIncreaseFreeGameRound();
            iRemainRounds = super.freeGameSetting.getFreeGameExtendSetting().getMaxRound() - freeGameTotalRound;
            if (reTriggerAddRounds > 0 && iRemainRounds > 0) {
                if (iRemainRounds > reTriggerAddRounds) {
                    roundInfo.setAddRound(reTriggerAddRounds);
                } else {
                    roundInfo.setAddRound(iRemainRounds);
                }
            }
        }
        return roundInfo;
    }

    private boolean isRandomWildChance(){ return randomWildChance; }

    private void setRandomWildChance(boolean randomWildChance) { this.randomWildChance = randomWildChance; }

    private ArrayList<Integer> getPotentialWild2Idx(int[][] preEliminatePosition){
        // 蒐集金框消除的位置
        ArrayList<Integer> potentialWild2Idx = new ArrayList<>();

        // 紀錄盤面上的可能變成隨機百搭的wild
        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                if (preEliminatePosition[column][row] == 2)
                    potentialWild2Idx.add(freeGameSetting.getScreenRow()*column+row);
            }
        }

        return potentialWild2Idx;
    }

    private ArrayList<Integer> getRandWildPositionIdx(ArrayList<Integer> potentialWild2Idx, int[][] screenLabel, SlotSpinRequest slotSpinRequest){
        // 2、3、4、5 輪
        ArrayList<Integer> randWildPositionIdx = new ArrayList<>();

        //設定 2~5 輪的 index
        for(int idx = 0; idx < (freeGameSetting.getScreenColumn()-1)*freeGameSetting.getScreenRow(); ++idx)
            randWildPositionIdx.add(idx+freeGameSetting.getScreenRow());

        // 移除 wild1 與 wild2 的 index
        for(int i = 0; i < potentialWild2Idx.size(); ++i)
            randWildPositionIdx.remove(potentialWild2Idx.get(i));

        // 移除 Scatter 的 index
        for (int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                if( freeGameSetting.getSymbolAttribute()[screenLabel[column][row]] == EnumHandler.SymbolAttribute.FreeGame )
                    randWildPositionIdx.remove((Integer) (freeGameSetting.getScreenRow()*column+row));
                if(screenLabel[column][row] == 1 )
                    randWildPositionIdx.remove((Integer) (freeGameSetting.getScreenRow()*column+row));
            }
        }
        if (slotSpinRequest.getExtraBetType() == EnumHandler.ExtraBetType.ExtraBet_BuyFreeGame02){
            ArrayList<Integer> randWildPositionIdxSB = new ArrayList<>(randWildPositionIdx);
            for (int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
                for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                    if( screenLabel[column][row] >= 11 )
                        randWildPositionIdxSB.remove((Integer) (freeGameSetting.getScreenRow()*column+row));
                }
            }
            if (randWildPositionIdxSB.size() >= 4){
                return randWildPositionIdxSB;
            } else {
                return randWildPositionIdx;
            }
        }
        return randWildPositionIdx;
    }

    private int[][] calculateRandomWildScreen(int[][] screenLabel, int randomWildCount, ArrayList<Integer> randWildPositionIdx, ArrayList<Integer> potentialWild2Idx){
        int[][] result = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];
        int wild2Idx = potentialWild2Idx.get(common.getRandomNumber(potentialWild2Idx.size()));
        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                result[column][row] = screenLabel[column][row];
            }
        }
        // wild2
        result[wild2Idx/freeGameSetting.getScreenRow()][wild2Idx%freeGameSetting.getScreenRow()] = 1;

        // 灑落盤面
        for(int i = 0; i < randomWildCount; i++) {
            if (!randWildPositionIdx.isEmpty()) {
                int randIdx = common.getRandomNumber(randWildPositionIdx.size());
                result[randWildPositionIdx.get(randIdx)/freeGameSetting.getScreenRow()][randWildPositionIdx.get(randIdx)%freeGameSetting.getScreenRow()] = 0;
                randWildPositionIdx.remove(randIdx);
            }
        }
        return result;
    }

    private int[][] reCalculateWildScreenSymbol(int[][] randWildScreen){
        int[][] result = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];

        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                if( freeGameSetting.getSymbolAttribute()[randWildScreen[column][row]] == EnumHandler.SymbolAttribute.Wild)
                    result[column][row] = 0;
                else
                    result[column][row] = randWildScreen[column][row];
            }
        }
        return result;
    }

    private int[][] getUneliminateWild2Position(int[][] screenLabel,int[][] preEliminatePosition,int[][] afterRandWildScreen){
        int[][] result = new int[freeGameSetting.getScreenColumn()][freeGameSetting.getScreenRow()];

        for(int column = 0; column < freeGameSetting.getScreenColumn(); ++column){
            for (int row = 0; row < freeGameSetting.getScreenRow(); ++row){
                if( freeGameSetting.getSymbolAttribute()[afterRandWildScreen[column][row]] == EnumHandler.SymbolAttribute.Wild && preEliminatePosition[column][row] == 0 )
                    result[column][row] = 1;
                else
                    result[column][row] = screenLabel[column][row];
            }
        }
        return result;
    }
}

