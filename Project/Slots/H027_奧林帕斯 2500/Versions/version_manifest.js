window.H027_VERSION_MANIFEST = {
  current: "1.0.0.0",
  base_version: "1",
  versions: [
    {
      version: "0.0.0.0",
      math_key: "0.0",
      date: "2026-08-21",
      competitor_initial_version: true,
      base_config: "Versions/0.0/final_before_v1_260826_142508/config.js",
      configs: {
        "92A": "Versions/0.0/final_before_v1_260826_142508/config_92A.js",
        "94A": "Versions/0.0/final_before_v1_260826_142508/config_94A.js"
      },
      workbooks: {
        base: "Versions/0.0/final_before_v1_260826_142508/Source/H0271.xlsx",
        92: "Versions/0.0/final_before_v1_260826_142508/Source/H027192A.xlsx",
        94: "Versions/0.0/final_before_v1_260826_142508/Source/H027194A.xlsx"
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
      date: "2026-08-26",
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
        "Keep competitor 63/64-stop cyclic reels, move C1 outside the first/last five RNG rows, and blank inactive XLSX rows."
      ]
    }
  ]
};
