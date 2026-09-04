window.H027_VERSION_MANIFEST = {
  current: "3.0.0.7",
  base_version: "3",
  next_version: "4.0.0.0",
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
    }
  ]
};
