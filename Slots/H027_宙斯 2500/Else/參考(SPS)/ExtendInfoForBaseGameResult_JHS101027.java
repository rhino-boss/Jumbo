package com.jumbogames.sps.entity.client.ExtendBaseGameResult;

import java.util.ArrayList;
import com.base.sps.entity.client.*;

public class ExtendInfoForBaseGameResult_JHS101027 extends ExtendInfoForBaseGameResult {
    private ArrayList<CascadeEliminateResult> cascadeEliminateResult; // 紀錄每一次消除結果。
    private int extraMultiplier;			// 記錄此次消除的額外乘倍
    private int[][] specialScreen;  		// byGame的特殊盤面紀錄。

    public ExtendInfoForBaseGameResult_JHS101027 Copy() {
        ExtendInfoForBaseGameResult_JHS101027 result = new ExtendInfoForBaseGameResult_JHS101027();
        super.clone(result);
        if(this.cascadeEliminateResult != null){
            result.cascadeEliminateResult = new ArrayList<CascadeEliminateResult>();
            for(int i = 0; i < this.cascadeEliminateResult.size(); i = i + 1)
                result.cascadeEliminateResult.add(this.cascadeEliminateResult.get(i).copy());
        }

        result.extraMultiplier = this.extraMultiplier;

        if(this.specialScreen != null)
            result.specialScreen = this.specialScreen.clone();

        return result;
    }

    public void setCascadeEliminateResult(ArrayList<CascadeEliminateResult> cascadeEliminateResult) {
        this.cascadeEliminateResult = cascadeEliminateResult;
    }

    public ArrayList<CascadeEliminateResult> getCascadeEliminateResult() {
        return cascadeEliminateResult;
    }

    /**
     * 計算BG最終贏分乘倍（§6.1：一般符號贏分乘倍，Scatter獎金不乘倍）。
     * @param initialScreenWin 初始盤面（cascade開始前）的一般符號贏分。呼叫端(calculateBaseGameTotalWin_JHS101027)
     *                         已經把這個值原始加總過一次（未乘倍），這裡用(multiplier-1)而非multiplier，
     *                         兩處相加後淨效果就是initialScreenWin恰好被乘了一次multiplier倍：
     *                         initialScreenWin + initialScreenWin×(multiplier-1) = initialScreenWin×multiplier。
     */
    public void calculateExtendTotalWin(long initialScreenWin){
        long extendTotalWin = 0;
        long cascadeTotalWin = getCascadeTotalWin();
        int multiplier = getFinalMultiplier();

        if(multiplier > 0)
            extendTotalWin = cascadeTotalWin * multiplier + initialScreenWin * (multiplier-1);
        else
            extendTotalWin = cascadeTotalWin;

        super.setExtendPlayerWin(extendTotalWin);
    }

    // 最終倍數＝最後一次cascade結束時盤面上所有C2的加總；若整場spin沒有發生cascade，退回初始盤面的C2加總。
    private int getFinalMultiplier() {
        return (this.cascadeEliminateResult.size() > 0)
                ? this.cascadeEliminateResult.get(this.cascadeEliminateResult.size() - 1).getExtraMultiplier()
                : this.extraMultiplier;
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
}
