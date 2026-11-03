package com.jumbogames.sps.entity.client.ExtendFreeGameResult;

import java.util.ArrayList;
import com.base.sps.entity.client.*;

/*
 * 說明：此物件紀錄各款不同遊戲的freeGame之特殊結果。
 */
public class ExtendInfoForFreeGameResult_JHS101027 extends ExtendInfoForFreeGameResult {
    private int extraMultiplier;			// 記錄此次消除的額外乘倍
    private int[][] specialScreen;  		// byGame的特殊盤面紀錄。
    private ArrayList<CascadeEliminateResult> cascadeEliminateResult; // 紀錄每一次消除結果。
    private int accumulateMultiplier; // 累計的額外乘倍。

    public ExtendInfoForFreeGameResult_JHS101027 Copy() {
        ExtendInfoForFreeGameResult_JHS101027 result = new ExtendInfoForFreeGameResult_JHS101027();
        super.clone(result);

        result.extraMultiplier = this.extraMultiplier;

        if(this.cascadeEliminateResult != null){
            result.cascadeEliminateResult = new ArrayList<CascadeEliminateResult>();
            for(int i = 0; i < this.cascadeEliminateResult.size(); i = i + 1)
                result.cascadeEliminateResult.add(this.cascadeEliminateResult.get(i).copy());
        }

        if(this.specialScreen != null){
            result.specialScreen = new int[this.specialScreen.length][this.specialScreen[0].length];
            for(int i = 0; i < this.specialScreen.length; ++i)
                result.specialScreen[i] = this.specialScreen[i].clone();
        }

        result.accumulateMultiplier = this.accumulateMultiplier;

        return result;
    }

    public ArrayList<CascadeEliminateResult> getCascadeEliminateResult() {
        return cascadeEliminateResult;
    }

    public void setCascadeEliminateResult(ArrayList<CascadeEliminateResult> cascadeEliminateResult) {
        this.cascadeEliminateResult = cascadeEliminateResult;
    }

    /**
     * @param initialScreenWin 已經把這個值原始加總過一次（未乘倍），這裡用(accumulateMultiplier-1)而非accumulateMultiplier，
     *                         兩處相加後淨效果就是initialScreenWin恰好被乘了一次accumulateMultiplier倍。
     */
    public void calculateExtendTotalWin(long initialScreenWin){
        long extendTotalWin = 0;
        long cascadeTotalWin = getCascadeTotalWin();

        if(this.accumulateMultiplier > 0) {
            extendTotalWin = cascadeTotalWin * this.accumulateMultiplier + initialScreenWin * (this.accumulateMultiplier - 1);
        }else
            extendTotalWin = cascadeTotalWin;

        super.setExtendPlayerWin(extendTotalWin);
    }

    public int[][] getSpecialScreen() {
        return specialScreen;
    }

    public void setSpecialScreen(int[][] specialScreen) {
        this.specialScreen = specialScreen;
    }

    public int getExtraMultiplier() {
        return extraMultiplier;
    }

    public void setExtraMultiplier(int extraMultiplier) {
        this.extraMultiplier = extraMultiplier;
    }

    public long getCascadeTotalWin() {
        long result = 0;

        if (this.cascadeEliminateResult.size() > 0) {
            for (int i = 0; i < cascadeEliminateResult.size(); i = i + 1) {
                result += cascadeEliminateResult.get(i).getEliminateWin();
            }
        }

        return result;
    }

    public int getAccumulateMultiplier() {
        return accumulateMultiplier;
    }

    public void setAccumulateMultiplier(int accumulateMultiplier) {
        this.accumulateMultiplier = accumulateMultiplier;
    }

    public int updateAccumulateMultiplier(int accumulateMultiplier){
        int multiplier = 0;

        if(this.cascadeEliminateResult.size() > 0) {
            multiplier = multiplier + this.cascadeEliminateResult.get(this.cascadeEliminateResult.size() - 1).getExtraMultiplier();
        }

        return accumulateMultiplier += multiplier;
    }
}
