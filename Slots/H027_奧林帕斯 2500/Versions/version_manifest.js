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
        "Keep BF entry scoring and cascade disabled so entry pay remains zero.",
        "Fill the competitor column for all 64 multiplier intervals in NB-BG, NB-FG, and BF-FG.",
        "Repair the 94A Overview layout using the validated 92A cell geometry and merged ranges.",
        "Remove the duplicate right-side Bet Type block from both card workbooks.",
        "Recalibrate 92A and 94A multiplier weights for all three bet modes from the Card-Off natural reports for bet modes 0, 1 and 2.",
        "Set 92A to NB 72.0000/20.0000, EB 42.0000/50.0000 and BF 92.0000; set 94A to NB 74.0000/20.0000, EB 44.0000/50.0000 and BF 92.0000.",
        "Retarget the NB FG cycle to the competitor 1/450.83 and the EB FG cycle to five times that, 1/90.17.",
        "Lock BG Hit Rate to the competitor main 28.193143%, making the per-spin total 28.414956% match the competitor Slot Stats hit rate.",
        "Intersect the configurable intervals with the competitor support: no weight above the competitor actual max multiplier 15,000x, so the top usable interval becomes (9000, 10000].",
        "Lower the natural-occurrence floor from 0.1% to 0.05% while keeping the FG 20x floor and the 15% per-interval cap.",
        "Enable the Extra Bet Card System and fill its weights, replacing the pending_calibration placeholder.",
        "Calibrate the Buy Feature win rate above 100x to 30.0000%."
      ]
    }
  ]
};
