window.H027_VERSION_MANIFEST = {
  current: "5.0.0.0",
  base_version: "5",
  next_version: "6.0.0.0",
  versions: [
    {
      version: "0.0.0.0",
      math_key: "0.0",
      date: "2026-08-21",
      competitor_initial_version: true,
      base_config: "Versions/0.0/config.js",
      configs: {
        "BASE": "Versions/0.0/config.js"
      },
      workbooks: {
        base: "Versions/0.0/Source/H0271.xlsx"
      },
      frozen_base: "Versions/0.0",
      changes: [
        "Freeze competitor-derived H0271 base model at version 0.",
        "Add H016-layout 64-range H027192A and H027194A multiplier workbooks.",
        "Add Card System configs and XLSX/config bidirectional conversion."
      ]
    },
    {
      version: "1.0.0.0",
      math_key: "1.0",
      date: "2026-08-28",
      competitor_initial_version: false,
      base_config: "Versions/1.0/config.js",
      configs: {
        "92A": "Versions/1.0/config_92A.js",
        "94A": "Versions/1.0/config_94A.js"
      },
      workbooks: {
        base: "Versions/1.0/Source/H0271.xlsx",
        92: "Versions/1.0/Source/H027192A.xlsx",
        94: "Versions/1.0/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/1.0",
      changes: [
        "Use competitor reconstructed Reel Set 0-4 with original 63/64 lengths and uniform Symbol Weight 1.",
        "Restore cross-reel weighted-percentile dependence for BG and FG Hit Rate.",
        "Accumulate FG multipliers only on spins with a scoring cascade.",
        "Generate Buy Feature entry with exactly four C1 on R2-R5.",
        "Keep competitor 63/64-stop cyclic reels, move C1 outside the first/last five RNG rows, and blank inactive XLSX rows.",
        "Set the FG C3 5x multiplier probability to 50% for FG_Symbol and FG_Symbol (2).",
        "Redistribute the removed 12.51 percentage points proportionally across the other active sub-100x C3 multipliers.",
        "Keep C3 2x, 3x, 4x and 100x-or-higher probabilities at zero.",
        "Optimize Simulator Card-Off statistics snapshots without changing fixed-seed results."
      ]
    },
    {
      version: "2.0.0.0",
      math_key: "2.0",
      date: "2026-09-01",
      competitor_initial_version: false,
      base_config: "Versions/2.0/config.js",
      configs: {
        "92A": "Versions/2.0/config_92A.js",
        "94A": "Versions/2.0/config_94A.js"
      },
      workbooks: {
        base: "Versions/2.0/Source/H0271.xlsx",
        92: "Versions/2.0/Source/H027192A.xlsx",
        94: "Versions/2.0/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/2.0",
      changes: [
        "Collect FG C2/C3 values only when the spin has a regular-symbol win and a final multiplier ball.",
        "Apply the accumulated FG multiplier only on a scoring spin whose final grid contains C2/C3.",
        "Pay a regular-symbol win at 1x when the final grid has no C2/C3, while retaining the accumulated pool.",
        "Apply the effective multiplier once after all cascades; Scatter pay remains unmultiplied."
      ]
    },
    {
      version: "3.0.0.7",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.7/config.js",
      configs: {
        "92A": "Versions/3.0.0.7/config_92A.js",
        "94A": "Versions/3.0.0.7/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.7/Source/H0271.xlsx",
        92: "Versions/3.0.0.7/Source/H027192A.xlsx",
        94: "Versions/3.0.0.7/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.7",
      changes: [
        "Recalculate NB-BG and NB-FG weights from the restored 1,000,000,000-round Card-Off report H0271_03_2609021651_betmode0_109.xlsx.",
        "Keep NB theoretical RTP at 92.0000%/94.0000%, FG cycle 300, 50-80x FG RTP share 40%, over-200x absolute RTP 2%, and per-interval probability at or below 15%.",
        "Maximize weighted FG Hit Rate to the feasible 42.4163%; reaching competitor 43.5640% is infeasible while all four multiplier constraints remain fixed.",
        "Restore BG_Symbol from the mistakenly assigned FG Reel Set 3 to the v2 Reel Set 0; BG uses Reel Sets 0/1/2 again.",
        "Recalibrate 92A and 94A NB-BG range weights from the restored 10,000,000-round natural report, with all sub-0.1% intervals disabled and BG Cap set to 20x.",
        "Keep theoretical full BG RTP at 72.0000% and 74.0000% without incrementing the candidate version.",
        "Build the BF entry reel from three FG_Symbol-equivalent symbol pools with distinct regular-symbol phase layouts.",
        "Expand valid BF stops to 15/15/15/15/162/162 and distinct positive windows to 15/15/15/15/67/70 by reel.",
        "Guarantee exactly one C1 on R1-R4 and none on R5-R6 for every positive-weight BF entry.",
        "Keep BF entry regular-symbol scoring and cascade disabled (superseded later in this version: the entry now pays Scatter).",
        "Fill the competitor column for all 64 multiplier intervals in NB-BG, NB-FG, and BF-FG.",
        "Repair the 94A Overview layout using the validated 92A cell geometry and merged ranges.",
        "Remove the duplicate right-side Bet Type block from both card workbooks.",
        "Recalibrate 92A and 94A multiplier weights for all three bet modes from the Card-Off natural reports for bet modes 0, 1 and 2.",
        "Put the 92A/94A RTP difference in FG, not BG: the Weight_NB_BG column is identical cell by cell between the two workbooks.",
        "Set 92A Oldhand to NB 72.0000/20.0000 and EB 42.0000/50.0000; set 94A Oldhand to NB 72.0000/22.0000 and EB 39.0000/55.0000.",
        "Add the Newbie player profile (spec 1.4.1 shared 93.00% game RTP): NB 72.0000/21.0000 and EB 40.5000/52.5000, shared by both workbooks, written to the Weight_*_Newbie columns and to card_system.newbie.",
        "Keep Newbie BG identical to Oldhand at 72.0000% cell by cell and let FG absorb the whole difference.",
        "Restrict Newbie multipliers to BG 30x and FG 30x-120x (spec 1.4.4 plus the specified FG floor), leaving 10 configurable FG intervals; the 15% per-interval cap does not apply to Newbie, so its top interval reaches 49.71% and its FG mean is 94.6743x.",
        "Treat the FG floor rule as a minimum multiplier, not as a requirement that every interval above it carry weight; tail intervals may round to zero.",
        "Align the Extra Bet FG x50+ probability with the competitor Slot Stats value 0.27682%; Normal Bet cannot match it because BG tops out at 30x, so its ceiling stays at the trigger rate 0.22181%.",
        "Correct the Overview Hit% and Pulls/Hit columns to the FG trigger probability and cycle; they had been filled with the BG hit rate.",
        "Retarget the NB FG cycle to the competitor 1/450.83 and the EB FG cycle to five times that, 1/90.17.",
        "Lock BG Hit Rate to the competitor main 28.193143%, making the per-spin total 28.414956% match the competitor Slot Stats hit rate.",
        "Give every interval below 20,000x that meets the other conditions a non-zero weight: integerization now reserves one unit per eligible interval and a unit-transfer pass restores the exact RTP target.",
        "Reach a 20,000x multiplier ceiling from the top eligible interval (10000, 20000], above the competitor actual max of 15,000x; (9000, 10000] stays unweighted because its natural occurrence 0.0409% is below the floor.",
        "Lower the natural-occurrence floor from 0.1% to 0.05% while keeping the FG 20x floor and the 15% per-interval cap.",
        "Enable the Extra Bet Card System and fill its weights, replacing the pending_calibration placeholder.",
        "Pay Scatter on the Buy Feature entry board: the entry always shows four C1 and now pays 3 x Bet per the paytable, a fixed 3.00 pp of the 100 x Bet purchase cost. The entry board still skips Pay Anywhere evaluation and cascades.",
        "Keep the Buy Feature total at 92.5000% per the spec by lowering the free-game portion to 89.5000% (entry 3.0000% + FG 89.5000%); the win rate above 100x stays 30.0000%.",
        "Match the Buy Feature card against fg_session_pay instead of total_pay: the entry Scatter is deterministic and outside the interval constraint, and including it made the measured FG RTP fall 3 pp short of the weight target."
      ]
    },
    {
      version: "3.1.0.0",
      math_key: "3.1",
      date: "2026-09-08",
      competitor_initial_version: false,
      base_config: "Versions/3.1.0.0/config.js",
      configs: {
        "92A": "Versions/3.1.0.0/config_92A.js",
        "94A": "Versions/3.1.0.0/config_94A.js",
        "92A_Bet100": "Versions/3.1.0.0/config_92A_Bet100.js"
      },
      workbooks: {
        base: "Versions/3.1.0.0/Source/H0271.xlsx",
        92: "Versions/3.1.0.0/Source/H027192A.xlsx",
        94: "Versions/3.1.0.0/Source/H027194A.xlsx",
        "92_Bet100": "Versions/3.1.0.0/Source/H027192A_Bet100.xlsx"
      },
      frozen_base: "Versions/3.1.0.0",
      changes: [
        "Fix the Extra Bet card denominator to comply with math-model spec 2.5: the Card System multiplier is judged against the Normal Bet base cost for every bet mode, not against the mode's actual charge. Extra Bet had been dividing by its own 2x charge, so a card interval of 10-15x paid only 10-15x the base bet against a 2x stake - half the intended value.",
        "Apply the same denominator to the Multiplier Line buckets, the X statistic and max_win_x, as required by simulator spec L146 (the report's X denominator must match the card judging denominator). RTP keeps the mode's actual cost as its denominator per spec 1.4.1.",
        "Re-run the Extra Bet Card-Off natural report at 1,000,000,000 rounds on the corrected denominator; the bucket-scale diagnostic (interval mean divided by bucket midpoint) moves from 1.99 to 1.00, matching Normal Bet 0.995 and Buy Feature 0.981.",
        "Re-solve every Extra Bet weight column on the corrected scale: the Extra Bet FG interval mean rises from 45.162 to 90.1660, equal to Normal Bet, and the x50+ share still lands exactly on the competitor Slot Stats value 0.276820%.",
        "Split the Oldhand weights by bet tier as required by spec 1.1 and 1.4.4: small bet under $2 uses the 94x family, medium bet $2-$100 and big bet over $100 use the 92x family, and each tier carries its own independent weight set with no runtime scaling or fallback.",
        "Add H027192A_Bet100.xlsx and config_92A_Bet100.js for the big-bet tier, whose FG Max Multiplier is 2000x per spec 1.4.4 rather than 20000x. The 2000x ceiling leaves 33 usable FG intervals instead of 41 and raises the minimum weight from 13,647 to 307,424, so the line shape stays non-degenerate. The _Bet100 filename suffix follows H026 practice; spec 1.2 does not codify it.",
        "Tag each config with bet_tier_scope (small_bet / medium_bet / big_bet) so the tier a config serves is traceable from the file itself.",
        "Bump to 3.1.0.0 per spec 1.3.1: a Card System interval or weight change increments the second digit and zeroes the third and fourth. Config excel_version is synced to match.",
        "Link and Bonus Game RTP are out of scope for this revision by request; the JP module carries them. Only Game RTP is modelled here."
      ]
    },
    {
      version: "4.0.0.1",
      math_key: "4.0",
      date: "2026-09-24",
      competitor_initial_version: false,
      configs: {
        "92A": "Versions/4.0.0.1/config_92A.js",
        "94A": "Versions/4.0.0.1/config_94A.js",
        "92A_Bet100": "Versions/4.0.0.1/config_92A_Bet100.js"
      },
      workbooks: {
        base: "Versions/4.0.0.1/Source/H0271.xlsx",
        92: "Versions/4.0.0.1/Source/H027192A.xlsx",
        94: "Versions/4.0.0.1/Source/H027194A.xlsx",
        "92_Bet100": "Versions/4.0.0.1/Source/H027192A_Bet100.xlsx"
      },
      frozen_base: "Versions/4.0.0.1",
      changes: [
        "Make a regular-symbol win structurally impossible on the Buy Feature entry screen. The entry reel had been expanded to 15/15/15/15/162/162 positive stops, which let seven of the nine regular symbols reach eight or more cells board-wide (K and TE could reach 14), so an Any-8 win was possible. SPS confirmed it: its Buy Feature report shows BaseGameRtp 0.6936% because SPS evaluates the entry screen while our simulator merely skipped scoring.",
        "Re-select the BF_Symbol stop weights to 9/12/9/9/71/28 positive stops, chosen so that every regular symbol can occupy at most 7 of the 30 cells across every reachable stop combination. The board still carries exactly four C1 (one per R1-R4, none on R5-R6) and never a C2 or C3, and 17,391,024 distinct RNG combinations remain - far more variety than the 58-stop configuration that last satisfied the constraint.",
        "Verified two ways: an exhaustive per-reel maximum (M1 4, M2 6, M3 7, M4 6, A 7, K 7, Q 7, J 7, TE 7) and a 300,000-board Monte Carlo that found a largest same-symbol count of 7, zero Any-8 boards and zero boards with a C1 count other than four.",
        "Rename the game to Zeus 2500 / 宙斯 2500 per the updated Game List, and rename the project folder to H027_宙斯 2500 to match.",
        "Bump to 4.0.0.0 per spec 1.3: the BF entry reel is base-math reel data, so the first digit increments and the remaining three reset. H0271.xlsx moves to version 4, every RTP/Variant workbook to 4.0.0.0, config.js excel_version to 4 and each variant config to 4.0.0.0.",
        "Card weights are unchanged from 3.1.0.0: the entry screen contributes no cascade, no multiplier ball and no regular-symbol pay, so the Buy Feature free-game distribution the cards constrain is unaffected. Card-On re-validation gives total RTP 92.4933% against the 92.5000% target (entry 3.0000% + FG 89.4933%) with zero Retry Limit Exceeded.",
        "Fix a live Demogame defect: every variant config carried its own copy of the reel strips, and that copy had never received the v3.0.0.7 correction that moved the Base Game off FG Reel Set 3. config_92A/94A/92A_Bet100 all still described BG_Symbol as source_reel_set 3 with a 64-stop strip, and reel_set_usage.BG.sets as [3,1,2]. Simulator.py read the strips from config.js so its results were always correct, but index.html reads the variant config directly - so the Demo had been running the Base Game on an FG reel since 3.0.0.7. The stale copies are now replaced with the Reel Set 0 data (63 stops).",
        "This is exactly the drift that spec section 9's Config/Simulator/Demogame three-way reconciliation exists to catch; that reconciliation had never been run, which is why a duplicated field could disagree for three versions without anyone noticing.",
        "Retire config.js. Each RTP/Variant config is now self-contained and the simulator loads exactly one config file, so the same data can no longer exist in two places and drift. The variant configs already carried a full superset of config.js (61 keys vs 55), so no values needed to move.",
        "Replace the base-versus-variant config pair validation with a single-config check. The spec 1.3 rule that a variant's first version digit must equal the base math version is preserved by a new base_excel_version field on each config, so removing config.js does not remove the check.",
        "Verified behaviour-preserving: a fixed-seed 300,000-round Normal Bet run on 92A returns byte-identical figures before and after (RTP 87.6700%, BG hit 28.0523%, FG cycle 485.44, max win 985.75x, and six more fields).",
        "Card weights, reels, paytable and all math values are unchanged; this revision only removes duplicated configuration and repairs the Demo's reel selection, hence the fourth digit."
      ]
    },
    {
      version: "5.0.0.0",
      math_key: "5.0",
      date: "2026-09-24",
      competitor_initial_version: false,
      configs: {
        "92A": "Versions/5.0.0.0/config_92A.js",
        "94A": "Versions/5.0.0.0/config_94A.js",
        "92A_Bet100": "Versions/5.0.0.0/config_92A_Bet100.js"
      },
      workbooks: {
        base_a: "Versions/5.0.0.0/Source/H0271A.xlsx",
        base_b: "Versions/5.0.0.0/Source/H0271B.xlsx",
        92: "Versions/5.0.0.0/Source/H027192A.xlsx",
        94: "Versions/5.0.0.0/Source/H027194A.xlsx",
        "92_Bet100": "Versions/5.0.0.0/Source/H027192A_Bet100.xlsx"
      },
      frozen_base: "Versions/5.0.0.0",
      changes: [
        "Split the base math workbook into an A and a B family: H0271.xlsx becomes H0271A.xlsx (unchanged content) and H0271B.xlsx. Reels are byte-identical between the two; the whole A/B difference is 84 cells on the Parameter sheet plus the model name.",
        "B raises the multiplier-ball frequency to one spin in ten without touching a single reel symbol. The ball only ever comes from BG_Symbol (3) - the other two base tables carry no C2 at all - so re-weighting the three table-selection weights from 9698/19298/2344 to 162386/619916/217698 moves the rate from 3.4492% to 9.9282% while BG hit rate stays at 28.31% against A's 28.38%. Solving for both targets at once is possible because three weights give two degrees of freedom and there are exactly two constraints.",
        "B re-shapes the C3 multiplier distribution so its mean is half of C2's, as requested: 0.5014 on base game and 0.4993 on free game. C3 now carries every value from 2x to 1000x (sixteen of them, up from nine) with 2500x deliberately left at zero. The shape is C2's own distribution minus 2500x, tilted by a single exponent (BG -0.2057, FG -0.1962) to hit the target mean, which weakens the high end exactly as intended.",
        "Retire config.js in favour of self-contained variant configs, and fix the Demo defect where every variant config still described BG_Symbol as FG Reel Set 3 - a stale copy that had survived since 3.0.0.7 because only config.js received the correction and only the Demo reads the variant copy.",
        "Version 5 because the Parameter sheet of the base math workbook changed, which spec 1.3 assigns to the first digit.",
        "B's card weights are not yet calibrated: config_92B/94B/92B_Bet100 currently carry A's weights and are therefore not registered in this version's config list. B's natural-probability reports are still running, and the weights will follow in 5.1.0.0."
      ]
    }
  ]
};
