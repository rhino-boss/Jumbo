window.H027_VERSION_MANIFEST = {
  "current": "7.4.0.0",
  "base_version": "7",
  "next_version": "8.0.0.0",
  "versions": [
    {
      "version": "3.1.0.0",
      "math_key": "3.1",
      "date": "2026-09-08",
      "competitor_initial_version": false,
      "base_config": "Versions/3.1.0.0/config.js",
      "configs": {
        "92A": "Versions/3.1.0.0/config_92A.js",
        "94A": "Versions/3.1.0.0/config_94A.js",
        "92A_Bet100": "Versions/3.1.0.0/config_92A_Bet100.js"
      },
      "workbooks": {
        "92": "Versions/3.1.0.0/Source/H027192A.xlsx",
        "94": "Versions/3.1.0.0/Source/H027194A.xlsx",
        "base": "Versions/3.1.0.0/Source/H0271.xlsx",
        "92_Bet100": "Versions/3.1.0.0/Source/H027192A_Bet100.xlsx"
      },
      "frozen_base": "Versions/3.1.0.0",
      "changes": [
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
      "version": "4.0.0.1",
      "math_key": "4.0",
      "date": "2026-09-24",
      "competitor_initial_version": false,
      "configs": {
        "92A": "Versions/4.0.0.1/config_92A.js",
        "94A": "Versions/4.0.0.1/config_94A.js",
        "92A_Bet100": "Versions/4.0.0.1/config_92A_Bet100.js"
      },
      "workbooks": {
        "92": "Versions/4.0.0.1/Source/H027192A.xlsx",
        "94": "Versions/4.0.0.1/Source/H027194A.xlsx",
        "base": "Versions/4.0.0.1/Source/H0271.xlsx",
        "92_Bet100": "Versions/4.0.0.1/Source/H027192A_Bet100.xlsx"
      },
      "frozen_base": "Versions/4.0.0.1",
      "changes": [
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
      "version": "5.1.1.2",
      "math_key": "5.1",
      "date": "2026-09-30",
      "competitor_initial_version": false,
      "configs": {
        "92A": "Versions/5.1.1.2/config_92A.js",
        "94A": "Versions/5.1.1.2/config_94A.js",
        "92A_Bet100": "Versions/5.1.1.2/config_92A_Bet100.js",
        "92B": "Versions/5.1.1.2/config_92B.js",
        "94B": "Versions/5.1.1.2/config_94B.js",
        "92B_Bet100": "Versions/5.1.1.2/config_92B_Bet100.js"
      },
      "workbooks": {
        "92": "Versions/5.1.1.2/Source/H027192A.xlsx",
        "94": "Versions/5.1.1.2/Source/H027194A.xlsx",
        "base_a": "Versions/5.1.1.2/Source/H0271A.xlsx",
        "base_b": "Versions/5.1.1.2/Source/H0271B.xlsx",
        "92_Bet100": "Versions/5.1.1.2/Source/H027192A_Bet100.xlsx",
        "92B": "Versions/5.1.1.2/Source/H027192B.xlsx",
        "94B": "Versions/5.1.1.2/Source/H027194B.xlsx",
        "92B_Bet100": "Versions/5.1.1.2/Source/H027192B_Bet100.xlsx"
      },
      "frozen_base": "Versions/5.1.0.0",
      "changes": [
        "Calibrate the B family card weights from the B natural-probability reports (NB/EB 1,000,000,000 rounds, BF 100,000,000) with the same minimum-distortion projection used for A. Targets are identical to A: Oldhand 92/94, Newbie 93, Buy Feature 92.5, BG hit 28.193143%, FG cycle 1/450.83 (EB 1/90.17), FG mean 90.1660x/99.1826x, BF win rate 30%.",
        "B's BG card covers 22 intervals up to 80x (A: 15 up to 30x) because the ten-spin multiplier ball widens the natural BG distribution. Newbie columns are identical across the three B workbooks; the BF column is shared by 92B/94B with Bet100 carrying its own 2000x-capped set.",
        "Exclude the FG-trigger spin from the BG interval means used by the solver. The natural report counts the trigger spin (four Scatters paying 3x) inside the (2,3] bucket, but a range card rejects trigger spins on retry, so the realised bucket mean was slightly lower than the natural one. Every 100,000,000-round validation had BG RTP at 71.92-71.97% for a 72% target; after the fix BG lands at 71.93-72.05% with deviations in both directions.",
        "Re-solve the A family (BG, FG and BF columns) from the v5 natural reports H0271A_05_*. The previous EB solve relied on a 9/8 report that no longer exists; the original weights evaluated against the new reports differ by at most 0.01 pp, so this is a reproducibility change, not a retune.",
        "Fix a simulator defect where every batch child shared the parent's NUMBA_CACHE_DIR (set with setdefault and inherited through the environment). Numba freezes module-level arrays such as the card weights into the compiled kernel, so the first child's cards were reused by every later child: Newbie validation ran with Oldhand weights and a Buy Feature Card-On run reported the Card-Off 232%. The cache directory is now always overridden per process and keyed by bet mode, base bet, card enabled and profile.",
        "Bring report file names in line with simulator spec 3.1.4: Card-Off reports use the base workbook name (H0271A/H0271B), Card-On reports use oldhand/newbie followed by the bet tier for Oldhand, and the card suffix is gone. The spec gains a row for games with several base-math families.",
        "Add a Range_Avg_Multi sheet to all six weight workbooks: same layout as Multiplier_Weight, Avg_Multi_* headers, natural per-interval mean multiplier in Normal Bet base-cost units (BG excluding trigger spins), formatted 0.0000.",
        "Set card_multiplier_denominator to normal_bet_base_cost for all three bet modes per spec 2.5 (informational field). Fix the Demo config-code parser so 92B/94B/_Bet100 codes are no longer suffixed with A.",
        "Fill the OP Jackpot sheet of all six weight workbooks with SCR measured from the Card-On reports, one representative per group (NB, EB, BF; within-group spread under 0.6%): A 5,110,370,100 / 5,347,849,900 / 30,085,360,000 and B 4,437,685,400 / 4,688,244,300 / 30,190,367,000, each row citing its source report. SCR content increments the third digit per spec 1.3, so 5.1.0.0 becomes 5.1.1.0 and the 5.1.0.0 snapshot is replaced (one snapshot per major version).",
        "Rename the Range_Avg_Multi sheet to Avg_Multi and add a Nature_Prob sheet to all six weight workbooks: same layout as Multiplier_Weight, Nature_Prob_* headers, the natural probability of each interval (BG per non-trigger spin with the Free Game row holding the trigger probability; FG/BF per free-game session), formatted 0.0000%. Document-only change, so the fourth digit increments to 5.1.1.1 and the 5.1.1.0 snapshot is replaced.",
        "Update game_rule.md 6.1 to describe the C3 multiplier distribution and BG table-selection weights of both base-math families (A and B); the previous text described A only.",
        "Validation (spec 3.2.2 rounds, identical weight sets run once, no Newbie BF): 20 Card-On runs, all within 2 sigma of target with Retry Limit Exceeded at most 486 per 100,000,000 rounds. Bump to 5.1.0.0 per spec 1.3.1 (card weight change)."
      ]
    },
    {
      "version": "7.4.0.0",
      "math_key": "7.4",
      "date": "2026-10-14",
      "competitor_initial_version": false,
      "base_configs": {
        "A": "Versions/7.4.0.0/config_A.js",
        "B": "Versions/7.4.0.0/config_B.js"
      },
      "configs": {
        "92A": "Versions/7.4.0.0/config_92A.js",
        "94A": "Versions/7.4.0.0/config_94A.js",
        "92A_Bet100": "Versions/7.4.0.0/config_92A_Bet100.js",
        "92B": "Versions/7.4.0.0/config_92B.js",
        "94B": "Versions/7.4.0.0/config_94B.js",
        "92B_Bet100": "Versions/7.4.0.0/config_92B_Bet100.js"
      },
      "workbooks": {
        "92": "Versions/7.4.0.0/Source/H027192A.xlsx",
        "94": "Versions/7.4.0.0/Source/H027194A.xlsx",
        "base_a": "Versions/7.4.0.0/Source/H0271A.xlsx",
        "base_b": "Versions/7.4.0.0/Source/H0271B.xlsx",
        "92_Bet100": "Versions/7.4.0.0/Source/H027192A_Bet100.xlsx",
        "92B": "Versions/7.4.0.0/Source/H027192B.xlsx",
        "94B": "Versions/7.4.0.0/Source/H027194B.xlsx",
        "92B_Bet100": "Versions/7.4.0.0/Source/H027192B_Bet100.xlsx"
      },
      "frozen_base": "Versions/7.1.1.0",
      "changes": [
        "Card-On BG ran 0.15-0.4pp low in every 7.x version because a BG range card retries at most 10,000 times; intervals whose natural rate is near the 0.02% threshold miss about 13% of the time and the last (mostly low) natural spin is kept.",
        "Oldhand BG columns (NB/EB) of all six workbooks re-solved with the effective mean e'_i = s_i*e_i + (1-s_i)*F, s_i = 1-(1-p_i)^10000; shape and trigger weight unchanged; FG/BF/Newbie unchanged; SCR unchanged.",
        "Validation: oldhand NB/EB 12 runs at 10^8, BG within +/-0.08pp of target; Newbie/BF 10 runs at 10^7 all within 2 sigma."
      ]
    }
  ]
};
