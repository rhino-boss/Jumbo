window.C027_VERSION_MANIFEST = {
  current: "0.0.0.0",
  base_version: "0",
  versions: [
    {
      version: "0.0.0.0",
      math_key: "0.0",
      date: "2026-08-25",
      competitor_initial_version: true,
      base_config: "../config.js",
      configs: {
        "92A": "../config_92A.js",
        "94A": "../config_94A.js"
      },
      workbooks: {
        base: "../Source/C0271.xlsx",
        92: "../Source/C027192A.xlsx",
        94: "../Source/C027194A.xlsx"
      },
      frozen_base: "Versions/0.0",
      changes: [
        "Fork the C027 math line from the H027 competitor-derived model; base math stays at version 0 because the initial source is still the Gates of Olympus 1000 capture report.",
        "Replace the four single-scene reel tables with seven tables: a dedicated BF_Symbol entry strip plus a two-table Scene Mixture for BG, natural FG and Buy Feature FG.",
        "Route every multiplier value of 10x and above through the C3 / Super Multiplier path, as game_rule.md section 5.1 requires; the C2 pool keeps 2x-8x only.",
        "Add the ball dimension to the Card System range cards so the Card-On multiplier-ball rate lands on target instead of being inflated by interval oversampling.",
        "Split BG:FG RTP by the competitor's measured ratio scaled to the variant label, so the FG entry cycle and the FG average multiplier can both be aligned."
      ]
    }
  ]
};
