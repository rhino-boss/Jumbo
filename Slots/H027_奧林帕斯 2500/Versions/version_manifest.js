window.H027_VERSION_MANIFEST = {
  current: "3.0.0.6",
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
      version: "3.0.0.0",
      math_key: "3.0",
      date: "2026-09-01",
      competitor_initial_version: false,
      base_config: "Versions/3.0/config.js",
      configs: {
        "92A": "Versions/3.0/config_92A.js",
        "94A": "Versions/3.0/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0/Source/H0271.xlsx",
        92: "Versions/3.0/Source/H027192A.xlsx",
        94: "Versions/3.0/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0",
      changes: [
        "Keep the v2 FG reel symbols, ordering, and 63/64-stop lengths.",
        "Tune only FG_Symbol and FG_Symbol (2) integer stop weights within 1-10; actual v3 weights use 1-5.",
        "Reach 43.9809% FG Hit Rate in a 100,000,000-round Card-Off validation report."
      ]
    },
    {
      version: "3.0.0.1",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.1/config.js",
      configs: {
        "92A": "Versions/3.0.0.1/config_92A.js",
        "94A": "Versions/3.0.0.1/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.1/Source/H0271.xlsx",
        92: "Versions/3.0.0.1/Source/H027192A.xlsx",
        94: "Versions/3.0.0.1/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.1",
      changes: [
        "Calibrate 92A and 94A multiplier ranges from the Gates of Olympus 1000 competitor line.",
        "Target NB RTP splits of 72:20 and 74:20 with a 300-spin FG cycle.",
        "Reserve 40% of FG RTP for 50-80x and 2% absolute RTP for Oldhand FG above 200x.",
        "Apply the natural-rate, 20,000x cap, FG minimum-range, and 15% FG interval-share constraints.",
        "Calibrate Buy Feature win rate to 30%; use competitor 15.415% and 3.953% for the 1.5x and 3x benchmarks."
      ]
    },
    {
      version: "3.0.0.2",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.2/config.js",
      configs: {
        "92A": "Versions/3.0.0.2/config_92A.js",
        "94A": "Versions/3.0.0.2/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.2/Source/H0271.xlsx",
        92: "Versions/3.0.0.2/Source/H027192A.xlsx",
        94: "Versions/3.0.0.2/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.2",
      changes: [
        "Make BG_Symbol use the FG_Symbol reel symbols and stop weights.",
        "Generate Buy Feature entry directly from BF_Symbol stop weights with no board override.",
        "Guarantee exactly one C1 on R1-R4 and none on R5-R6.",
        "Make the Buy Feature entry screen pay zero and produce no cascade."
      ]
    },
    {
      version: "3.0.0.3",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.3/config.js",
      configs: {
        "92A": "Versions/3.0.0.3/config_92A.js",
        "94A": "Versions/3.0.0.3/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.3/Source/H0271.xlsx",
        92: "Versions/3.0.0.3/Source/H027192A.xlsx",
        94: "Versions/3.0.0.3/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.3",
      changes: [
        "Expand BF_Symbol to 63-stop reels with 61 valid stops on R1-R4 and 63 on R5-R6.",
        "Guarantee exactly four C1 across every valid independent RNG combination.",
        "Use one distinct regular symbol per reel so the maximum regular-symbol count is five.",
        "Keep Buy Feature entry pay and cascades fixed at zero."
      ]
    },
    {
      version: "3.0.0.4",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.4/config.js",
      configs: {
        "92A": "Versions/3.0.0.4/config_92A.js",
        "94A": "Versions/3.0.0.4/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.4/Source/H0271.xlsx",
        92: "Versions/3.0.0.4/Source/H027192A.xlsx",
        94: "Versions/3.0.0.4/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.4",
      changes: [
        "Copy the complete FG_Symbol reel symbols and lengths into BF_Symbol.",
        "Optimize BF stop weights for 58 positive stops: 3/3/3/3/15/31 by reel.",
        "Exclude C2/C3 and guarantee exactly four C1 across every valid RNG combination.",
        "Prove every regular symbol remains below the Any-8 scoring threshold."
      ]
    },
    {
      version: "3.0.0.5",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.5/config.js",
      configs: {
        "92A": "Versions/3.0.0.5/config_92A.js",
        "94A": "Versions/3.0.0.5/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.5/Source/H0271.xlsx",
        92: "Versions/3.0.0.5/Source/H027192A.xlsx",
        94: "Versions/3.0.0.5/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.5",
      changes: [
        "Enable every FG_Symbol stop valid for the BF four-C1 trigger screen.",
        "Use 128 positive stops: 5/5/5/5/54/54 by reel.",
        "Exclude C2/C3 and guarantee exactly one C1 on R1-R4 and none on R5-R6.",
        "Skip Pay Anywhere and Cascade processing on BF entry so entry pay is always zero."
      ]
    },
    {
      version: "3.0.0.6",
      math_key: "3.0",
      date: "2026-09-02",
      competitor_initial_version: false,
      base_config: "Versions/3.0.0.6/config.js",
      configs: {
        "92A": "Versions/3.0.0.6/config_92A.js",
        "94A": "Versions/3.0.0.6/config_94A.js"
      },
      workbooks: {
        base: "Versions/3.0.0.6/Source/H0271.xlsx",
        92: "Versions/3.0.0.6/Source/H027192A.xlsx",
        94: "Versions/3.0.0.6/Source/H027194A.xlsx"
      },
      frozen_base: "Versions/3.0.0.6",
      changes: [
        "Build the BF entry reel from three FG_Symbol-equivalent symbol pools with distinct regular-symbol phase layouts.",
        "Expand valid BF stops to 15/15/15/15/162/162 and distinct positive windows to 15/15/15/15/67/70 by reel.",
        "Guarantee exactly one C1 on R1-R4 and none on R5-R6 for every positive-weight BF entry.",
        "Keep BF entry scoring and cascade disabled so entry pay remains zero."
      ]
    }
  ]
};
