// Generated from Source/H027194A.xlsx by Source/rtp_xlsx_config.py.
const data = {
  "game_id": "101027",
  "parsheet_id": "H027194",
  "config_type": "rtp_variant",
  "config_code": "94A",
  "is_competitor_model": true,
  "initial_version_rule": "competitor_model_starts_at_0",
  "display_name": "Olympus 2500",
  "game_name_zh": "奧林帕斯 2500",
  "mode_normalbet": 0,
  "mode_extrabet": 1,
  "mode_featurebuy": 2,
  "supported_bet_modes": [
    0,
    1,
    2
  ],
  "extra_bet_multiplier": 2,
  "extra_fg_probability_multiplier": 5,
  "has_super_feature": false,
  "has_wild": false,
  "has_jackpot": true,
  "max_free_spins": 50,
  "fg_trigger_count": 4,
  "fg_retrigger_count": 3,
  "cascade_limit": 100,
  "denom": 0.002,
  "bet_options": [
    1,
    2,
    3,
    4,
    5,
    6,
    8,
    10,
    12,
    16,
    20,
    30,
    40,
    60,
    100,
    200,
    300,
    600,
    1000,
    1500
  ],
  "initial_balance": 10000,
  "drop_mode": "cascade_drop",
  "bet_tier_thresholds": {
    "small_bet_lt": 2,
    "medium_bet_lte": 100
  },
  "link": {
    "enabled": false
  },
  "rtp_accounting": {
    "link": "none",
    "bonus_game": "free_game",
    "game": "base_game",
    "target_status": "pending"
  },
  "reference_presentation": "參考資料/260630_Olympus 2500.pptx",
  "rule_document": "game_rule.md",
  "model_status": "rules_confirmed_math_draft",
  "pending_math_items": [
    "Extra Bet dedicated reel and card weights",
    "Formal RTP target confirmation and final calibration",
    "C3 multiplier pool and appearance weights"
  ],
  "multiplier_max_value": 2500,
  "model": "H027194",
  "excel_version": "0.0.0.0",
  "default_coin_in": 100,
  "reel_num": 6,
  "window_size": 5,
  "symbol_codes": [
    "C1",
    "C2",
    "C3",
    "M1",
    "M2",
    "M3",
    "M4",
    "A",
    "K",
    "Q",
    "J",
    "TE"
  ],
  "symbol_ids": [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12
  ],
  "pay_table": [
    [
      300,
      500,
      10000,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      0,
      0,
      0
    ],
    [
      0,
      0,
      0,
      1000,
      2500,
      5000
    ],
    [
      0,
      0,
      0,
      250,
      1000,
      2500
    ],
    [
      0,
      0,
      0,
      200,
      500,
      1500
    ],
    [
      0,
      0,
      0,
      150,
      200,
      1200
    ],
    [
      0,
      0,
      0,
      100,
      150,
      1000
    ],
    [
      0,
      0,
      0,
      80,
      120,
      800
    ],
    [
      0,
      0,
      0,
      50,
      100,
      500
    ],
    [
      0,
      0,
      0,
      40,
      90,
      400
    ],
    [
      0,
      0,
      0,
      25,
      75,
      200
    ]
  ],
  "pay_count_bounds": [
    8,
    10,
    12
  ],
  "scatter_pay_counts": [
    4,
    5,
    6
  ],
  "normalbet": 1,
  "extrabet": 2,
  "featurebuy": 100,
  "source_model": "H0271",
  "multiplier_levels": [
    2,
    3,
    4,
    5,
    6,
    8,
    10,
    12,
    15,
    20,
    25,
    50,
    100,
    250,
    500,
    1000,
    2500,
    2500,
    2500,
    2500,
    2500,
    2500,
    2500,
    2500,
    2500
  ],
  "parameter": {
    "multiplier_levels": [
      2,
      3,
      4,
      5,
      6,
      8,
      10,
      12,
      15,
      20,
      25,
      50,
      100,
      250,
      500,
      1000,
      2500,
      2500,
      2500,
      2500,
      2500,
      2500,
      2500,
      2500,
      2500
    ],
    "super_multiplier": {
      "multipliers": [
        2,
        3,
        4,
        5,
        6,
        8,
        10,
        12,
        15,
        20,
        25,
        50,
        100,
        250,
        500,
        1000,
        2500,
        2500,
        2500,
        2500,
        2500,
        2500,
        2500,
        2500,
        2500
      ],
      "table_names": [
        "Super Ball"
      ],
      "weights": {
        "Super Ball": [
          0,
          0,
          0,
          0,
          0,
          0,
          6079,
          969,
          751,
          1533,
          0,
          299,
          310,
          0,
          59,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0,
          0
        ]
      },
      "weights_cum": {
        "Super Ball": [
          0,
          0,
          0,
          0,
          0,
          0,
          6079,
          7048,
          7799,
          9332,
          9332,
          9631,
          9941,
          9941,
          10000,
          10000,
          10000,
          10000,
          10000,
          10000,
          10000,
          10000,
          10000,
          10000,
          10000
        ]
      }
    },
    "normal": {
      "base_reel_names": [
        "BG_Symbol",
        "BG_Symbol (2)"
      ],
      "base_reel_weights": [
        1,
        0
      ],
      "base_reel_weights_cum": [
        1,
        1
      ],
      "free_table": {
        "names": [
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "initial": [
          15,
          0
        ],
        "retrigger": [
          5,
          0
        ]
      },
      "use_super_multiplier": {
        "table_names": [
          "BG_Symbol",
          "BG_Symbol (2)",
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "initial_ball_counts": [
          1,
          2,
          3,
          4,
          5,
          6
        ],
        "weights_by_initial_ball_count": {
          "BG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0
          ]
        },
        "denominator": 10000
      },
      "c2": {
        "multipliers": [
          2,
          3,
          4,
          5,
          6,
          8,
          10,
          12,
          15,
          20,
          25,
          50,
          100,
          250,
          500,
          1000,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500
        ],
        "table_names": [
          "BG_Symbol",
          "BG_Symbol (2)",
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "weights": {
          "BG_Symbol": [
            920,
            896,
            778,
            2028,
            2098,
            1439,
            849,
            330,
            189,
            236,
            24,
            47,
            118,
            24,
            24,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            4631,
            2486,
            1166,
            1017,
            320,
            143,
            70,
            52,
            42,
            21,
            17,
            28,
            7,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            4543,
            2218,
            1338,
            986,
            458,
            317,
            35,
            35,
            70,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            4631,
            2486,
            1166,
            1017,
            320,
            143,
            70,
            52,
            42,
            21,
            17,
            28,
            7,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        },
        "weights_cum": {
          "BG_Symbol": [
            920,
            1816,
            2594,
            4622,
            6720,
            8159,
            9008,
            9338,
            9527,
            9763,
            9787,
            9834,
            9952,
            9976,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ],
          "BG_Symbol (2)": [
            4631,
            7117,
            8283,
            9300,
            9620,
            9763,
            9833,
            9885,
            9927,
            9948,
            9965,
            9993,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ],
          "FG_Symbol": [
            4543,
            6761,
            8099,
            9085,
            9543,
            9860,
            9895,
            9930,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ],
          "FG_Symbol (2)": [
            4631,
            7117,
            8283,
            9300,
            9620,
            9763,
            9833,
            9885,
            9927,
            9948,
            9965,
            9993,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ]
        }
      },
      "c3": {
        "multipliers": [
          2,
          3,
          4,
          5,
          6,
          8,
          10,
          12,
          15,
          20,
          25,
          50,
          100,
          250,
          500,
          1000,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500
        ],
        "table_names": [
          "BG_Symbol",
          "BG_Symbol (2)",
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "weights": {
          "BG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        },
        "weights_cum": {
          "BG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        }
      }
    },
    "featurebuy": {
      "base_reel_names": [
        "BG_Symbol"
      ],
      "base_reel_weights": [
        0,
        1
      ],
      "base_reel_weights_cum": [
        0,
        1
      ],
      "free_table": {
        "names": [
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "initial": [
          0,
          15
        ],
        "retrigger": [
          0,
          5
        ]
      },
      "use_super_multiplier": {
        "table_names": [
          "BG_Symbol",
          "BG_Symbol (2)",
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "initial_ball_counts": [
          1,
          2,
          3,
          4,
          5,
          6
        ],
        "weights_by_initial_ball_count": {
          "BG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0
          ]
        },
        "denominator": 10000
      },
      "c2": {
        "multipliers": [
          2,
          3,
          4,
          5,
          6,
          8,
          10,
          12,
          15,
          20,
          25,
          50,
          100,
          250,
          500,
          1000,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500
        ],
        "table_names": [
          "BG_Symbol",
          "BG_Symbol (2)",
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "weights": {
          "BG_Symbol": [
            920,
            896,
            778,
            2028,
            2098,
            1439,
            849,
            330,
            189,
            236,
            24,
            47,
            118,
            24,
            24,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            4631,
            2486,
            1166,
            1017,
            320,
            143,
            70,
            52,
            42,
            21,
            17,
            28,
            7,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            4543,
            2218,
            1338,
            986,
            458,
            317,
            35,
            35,
            70,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            4631,
            2486,
            1166,
            1017,
            320,
            143,
            70,
            52,
            42,
            21,
            17,
            28,
            7,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        },
        "weights_cum": {
          "BG_Symbol": [
            920,
            1816,
            2594,
            4622,
            6720,
            8159,
            9008,
            9338,
            9527,
            9763,
            9787,
            9834,
            9952,
            9976,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ],
          "BG_Symbol (2)": [
            4631,
            7117,
            8283,
            9300,
            9620,
            9763,
            9833,
            9885,
            9927,
            9948,
            9965,
            9993,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ],
          "FG_Symbol": [
            4543,
            6761,
            8099,
            9085,
            9543,
            9860,
            9895,
            9930,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ],
          "FG_Symbol (2)": [
            4631,
            7117,
            8283,
            9300,
            9620,
            9763,
            9833,
            9885,
            9927,
            9948,
            9965,
            9993,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000,
            10000
          ]
        }
      },
      "c3": {
        "multipliers": [
          2,
          3,
          4,
          5,
          6,
          8,
          10,
          12,
          15,
          20,
          25,
          50,
          100,
          250,
          500,
          1000,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500,
          2500
        ],
        "table_names": [
          "BG_Symbol",
          "BG_Symbol (2)",
          "FG_Symbol",
          "FG_Symbol (2)"
        ],
        "weights": {
          "BG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        },
        "weights_cum": {
          "BG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "BG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "FG_Symbol (2)": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ]
        }
      }
    }
  },
  "card_system": {
    "enabled": true,
    "retry_limit": 10000,
    "weight_threshold": 1000000000,
    "card_multiplier_denominator": "normal_bet_base_cost",
    "fg_entry_cycle_target": 5000.0,
    "newbie": {
      "normal_bet": {
        "weight_bg": [
          {
            "type": "range",
            "min": -1,
            "max": 0,
            "weight": 694112196
          },
          {
            "type": "range",
            "min": 0,
            "max": 1,
            "weight": 154179940
          },
          {
            "type": "range",
            "min": 1,
            "max": 2,
            "weight": 52969308
          },
          {
            "type": "range",
            "min": 2,
            "max": 3,
            "weight": 25304058
          },
          {
            "type": "range",
            "min": 3,
            "max": 4,
            "weight": 16909959
          },
          {
            "type": "range",
            "min": 4,
            "max": 5,
            "weight": 10604147
          },
          {
            "type": "range",
            "min": 5,
            "max": 6,
            "weight": 6991786
          },
          {
            "type": "range",
            "min": 6,
            "max": 7,
            "weight": 4663978
          },
          {
            "type": "range",
            "min": 7,
            "max": 8,
            "weight": 3128355
          },
          {
            "type": "range",
            "min": 8,
            "max": 9,
            "weight": 2617719
          },
          {
            "type": "range",
            "min": 9,
            "max": 10,
            "weight": 3068713
          },
          {
            "type": "range",
            "min": 10,
            "max": 15,
            "weight": 10040517
          },
          {
            "type": "range",
            "min": 15,
            "max": 20,
            "weight": 6133908
          },
          {
            "type": "range",
            "min": 20,
            "max": 25,
            "weight": 4753847
          },
          {
            "type": "range",
            "min": 25,
            "max": 30,
            "weight": 4521569
          },
          {
            "type": "range",
            "min": 30,
            "max": 35,
            "weight": 0
          },
          {
            "type": "range",
            "min": 35,
            "max": 40,
            "weight": 0
          },
          {
            "type": "range",
            "min": 40,
            "max": 45,
            "weight": 0
          },
          {
            "type": "range",
            "min": 45,
            "max": 50,
            "weight": 0
          },
          {
            "type": "range",
            "min": 50,
            "max": 60,
            "weight": 0
          },
          {
            "type": "range",
            "min": 60,
            "max": 70,
            "weight": 0
          },
          {
            "type": "range",
            "min": 70,
            "max": 80,
            "weight": 0
          },
          {
            "type": "range",
            "min": 80,
            "max": 90,
            "weight": 0
          },
          {
            "type": "range",
            "min": 90,
            "max": 100,
            "weight": 0
          },
          {
            "type": "range",
            "min": 100,
            "max": 120,
            "weight": 0
          },
          {
            "type": "range",
            "min": 120,
            "max": 140,
            "weight": 0
          },
          {
            "type": "range",
            "min": 140,
            "max": 160,
            "weight": 0
          },
          {
            "type": "range",
            "min": 160,
            "max": 180,
            "weight": 0
          },
          {
            "type": "range",
            "min": 180,
            "max": 200,
            "weight": 0
          },
          {
            "type": "range",
            "min": 200,
            "max": 250,
            "weight": 0
          },
          {
            "type": "range",
            "min": 250,
            "max": 300,
            "weight": 0
          },
          {
            "type": "range",
            "min": 300,
            "max": 350,
            "weight": 0
          },
          {
            "type": "range",
            "min": 350,
            "max": 400,
            "weight": 0
          },
          {
            "type": "range",
            "min": 400,
            "max": 450,
            "weight": 0
          },
          {
            "type": "range",
            "min": 450,
            "max": 500,
            "weight": 0
          },
          {
            "type": "range",
            "min": 500,
            "max": 550,
            "weight": 0
          },
          {
            "type": "range",
            "min": 550,
            "max": 600,
            "weight": 0
          },
          {
            "type": "range",
            "min": 600,
            "max": 650,
            "weight": 0
          },
          {
            "type": "range",
            "min": 650,
            "max": 700,
            "weight": 0
          },
          {
            "type": "range",
            "min": 700,
            "max": 750,
            "weight": 0
          },
          {
            "type": "range",
            "min": 750,
            "max": 800,
            "weight": 0
          },
          {
            "type": "range",
            "min": 800,
            "max": 850,
            "weight": 0
          },
          {
            "type": "range",
            "min": 850,
            "max": 900,
            "weight": 0
          },
          {
            "type": "range",
            "min": 900,
            "max": 950,
            "weight": 0
          },
          {
            "type": "range",
            "min": 950,
            "max": 1000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 1000,
            "max": 2000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 2000,
            "max": 3000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 3000,
            "max": 4000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 4000,
            "max": 5000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 5000,
            "max": 6000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 6000,
            "max": 7000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 7000,
            "max": 8000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 8000,
            "max": 9000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 9000,
            "max": 10000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 10000,
            "max": 20000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 20000,
            "max": 30000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 30000,
            "max": 40000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 40000,
            "max": 50000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 50000,
            "max": 60000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 60000,
            "max": 70000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 70000,
            "max": 80000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 80000,
            "max": 90000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 90000,
            "max": 100000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 100000,
            "max": 9999999,
            "weight": 0
          },
          {
            "type": "free_game",
            "weight": 200040
          }
        ],
        "weight_fg": [
          {
            "type": "range",
            "min": -1,
            "max": 0,
            "weight": 16217
          },
          {
            "type": "range",
            "min": 0,
            "max": 1,
            "weight": 11228
          },
          {
            "type": "range",
            "min": 1,
            "max": 2,
            "weight": 8790
          },
          {
            "type": "range",
            "min": 2,
            "max": 3,
            "weight": 15407
          },
          {
            "type": "range",
            "min": 3,
            "max": 4,
            "weight": 12971
          },
          {
            "type": "range",
            "min": 4,
            "max": 5,
            "weight": 23747
          },
          {
            "type": "range",
            "min": 5,
            "max": 6,
            "weight": 39494
          },
          {
            "type": "range",
            "min": 6,
            "max": 7,
            "weight": 22658
          },
          {
            "type": "range",
            "min": 7,
            "max": 8,
            "weight": 59644
          },
          {
            "type": "range",
            "min": 8,
            "max": 9,
            "weight": 28907
          },
          {
            "type": "range",
            "min": 9,
            "max": 10,
            "weight": 43878
          },
          {
            "type": "range",
            "min": 10,
            "max": 15,
            "weight": 420522
          },
          {
            "type": "range",
            "min": 15,
            "max": 20,
            "weight": 522819
          },
          {
            "type": "range",
            "min": 20,
            "max": 25,
            "weight": 883893
          },
          {
            "type": "range",
            "min": 25,
            "max": 30,
            "weight": 1372118
          },
          {
            "type": "range",
            "min": 30,
            "max": 35,
            "weight": 2089279
          },
          {
            "type": "range",
            "min": 35,
            "max": 40,
            "weight": 3091774
          },
          {
            "type": "range",
            "min": 40,
            "max": 45,
            "weight": 3597897
          },
          {
            "type": "range",
            "min": 45,
            "max": 50,
            "weight": 4657727
          },
          {
            "type": "range",
            "min": 50,
            "max": 60,
            "weight": 17767174
          },
          {
            "type": "range",
            "min": 60,
            "max": 70,
            "weight": 31716923
          },
          {
            "type": "range",
            "min": 70,
            "max": 80,
            "weight": 53338083
          },
          {
            "type": "range",
            "min": 80,
            "max": 90,
            "weight": 85581112
          },
          {
            "type": "range",
            "min": 90,
            "max": 100,
            "weight": 143176099
          },
          {
            "type": "range",
            "min": 100,
            "max": 120,
            "weight": 651501639
          },
          {
            "type": "range",
            "min": 120,
            "max": 140,
            "weight": 0
          },
          {
            "type": "range",
            "min": 140,
            "max": 160,
            "weight": 0
          },
          {
            "type": "range",
            "min": 160,
            "max": 180,
            "weight": 0
          },
          {
            "type": "range",
            "min": 180,
            "max": 200,
            "weight": 0
          },
          {
            "type": "range",
            "min": 200,
            "max": 250,
            "weight": 0
          },
          {
            "type": "range",
            "min": 250,
            "max": 300,
            "weight": 0
          },
          {
            "type": "range",
            "min": 300,
            "max": 350,
            "weight": 0
          },
          {
            "type": "range",
            "min": 350,
            "max": 400,
            "weight": 0
          },
          {
            "type": "range",
            "min": 400,
            "max": 450,
            "weight": 0
          },
          {
            "type": "range",
            "min": 450,
            "max": 500,
            "weight": 0
          },
          {
            "type": "range",
            "min": 500,
            "max": 550,
            "weight": 0
          },
          {
            "type": "range",
            "min": 550,
            "max": 600,
            "weight": 0
          },
          {
            "type": "range",
            "min": 600,
            "max": 650,
            "weight": 0
          },
          {
            "type": "range",
            "min": 650,
            "max": 700,
            "weight": 0
          },
          {
            "type": "range",
            "min": 700,
            "max": 750,
            "weight": 0
          },
          {
            "type": "range",
            "min": 750,
            "max": 800,
            "weight": 0
          },
          {
            "type": "range",
            "min": 800,
            "max": 850,
            "weight": 0
          },
          {
            "type": "range",
            "min": 850,
            "max": 900,
            "weight": 0
          },
          {
            "type": "range",
            "min": 900,
            "max": 950,
            "weight": 0
          },
          {
            "type": "range",
            "min": 950,
            "max": 1000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 1000,
            "max": 2000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 2000,
            "max": 3000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 3000,
            "max": 4000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 4000,
            "max": 5000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 5000,
            "max": 6000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 6000,
            "max": 7000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 7000,
            "max": 8000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 8000,
            "max": 9000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 9000,
            "max": 10000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 10000,
            "max": 20000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 20000,
            "max": 30000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 30000,
            "max": 40000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 40000,
            "max": 50000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 50000,
            "max": 60000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 60000,
            "max": 70000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 70000,
            "max": 80000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 80000,
            "max": 90000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 90000,
            "max": 100000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 100000,
            "max": 9999999,
            "weight": 0
          }
        ]
      },
      "buy_feature": {
        "weight_fg": [
          {
            "type": "range",
            "min": -1,
            "max": 0,
            "weight": 0
          },
          {
            "type": "range",
            "min": 0,
            "max": 1,
            "weight": 0
          },
          {
            "type": "range",
            "min": 1,
            "max": 2,
            "weight": 0
          },
          {
            "type": "range",
            "min": 2,
            "max": 3,
            "weight": 28562
          },
          {
            "type": "range",
            "min": 3,
            "max": 4,
            "weight": 26090
          },
          {
            "type": "range",
            "min": 4,
            "max": 5,
            "weight": 39665
          },
          {
            "type": "range",
            "min": 5,
            "max": 6,
            "weight": 48205
          },
          {
            "type": "range",
            "min": 6,
            "max": 7,
            "weight": 66589
          },
          {
            "type": "range",
            "min": 7,
            "max": 8,
            "weight": 78123
          },
          {
            "type": "range",
            "min": 8,
            "max": 9,
            "weight": 96053
          },
          {
            "type": "range",
            "min": 9,
            "max": 10,
            "weight": 112205
          },
          {
            "type": "range",
            "min": 10,
            "max": 15,
            "weight": 863568
          },
          {
            "type": "range",
            "min": 15,
            "max": 20,
            "weight": 1449251
          },
          {
            "type": "range",
            "min": 20,
            "max": 25,
            "weight": 2212457
          },
          {
            "type": "range",
            "min": 25,
            "max": 30,
            "weight": 3128345
          },
          {
            "type": "range",
            "min": 30,
            "max": 35,
            "weight": 4352684
          },
          {
            "type": "range",
            "min": 35,
            "max": 40,
            "weight": 5846792
          },
          {
            "type": "range",
            "min": 40,
            "max": 45,
            "weight": 7641034
          },
          {
            "type": "range",
            "min": 45,
            "max": 50,
            "weight": 9857532
          },
          {
            "type": "range",
            "min": 50,
            "max": 60,
            "weight": 28397923
          },
          {
            "type": "range",
            "min": 60,
            "max": 70,
            "weight": 44726944
          },
          {
            "type": "range",
            "min": 70,
            "max": 80,
            "weight": 68800809
          },
          {
            "type": "range",
            "min": 80,
            "max": 90,
            "weight": 104364313
          },
          {
            "type": "range",
            "min": 90,
            "max": 100,
            "weight": 156240608
          },
          {
            "type": "range",
            "min": 100,
            "max": 120,
            "weight": 561622248
          },
          {
            "type": "range",
            "min": 120,
            "max": 140,
            "weight": 0
          },
          {
            "type": "range",
            "min": 140,
            "max": 160,
            "weight": 0
          },
          {
            "type": "range",
            "min": 160,
            "max": 180,
            "weight": 0
          },
          {
            "type": "range",
            "min": 180,
            "max": 200,
            "weight": 0
          },
          {
            "type": "range",
            "min": 200,
            "max": 250,
            "weight": 0
          },
          {
            "type": "range",
            "min": 250,
            "max": 300,
            "weight": 0
          },
          {
            "type": "range",
            "min": 300,
            "max": 350,
            "weight": 0
          },
          {
            "type": "range",
            "min": 350,
            "max": 400,
            "weight": 0
          },
          {
            "type": "range",
            "min": 400,
            "max": 450,
            "weight": 0
          },
          {
            "type": "range",
            "min": 450,
            "max": 500,
            "weight": 0
          },
          {
            "type": "range",
            "min": 500,
            "max": 550,
            "weight": 0
          },
          {
            "type": "range",
            "min": 550,
            "max": 600,
            "weight": 0
          },
          {
            "type": "range",
            "min": 600,
            "max": 650,
            "weight": 0
          },
          {
            "type": "range",
            "min": 650,
            "max": 700,
            "weight": 0
          },
          {
            "type": "range",
            "min": 700,
            "max": 750,
            "weight": 0
          },
          {
            "type": "range",
            "min": 750,
            "max": 800,
            "weight": 0
          },
          {
            "type": "range",
            "min": 800,
            "max": 850,
            "weight": 0
          },
          {
            "type": "range",
            "min": 850,
            "max": 900,
            "weight": 0
          },
          {
            "type": "range",
            "min": 900,
            "max": 950,
            "weight": 0
          },
          {
            "type": "range",
            "min": 950,
            "max": 1000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 1000,
            "max": 2000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 2000,
            "max": 3000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 3000,
            "max": 4000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 4000,
            "max": 5000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 5000,
            "max": 6000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 6000,
            "max": 7000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 7000,
            "max": 8000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 8000,
            "max": 9000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 9000,
            "max": 10000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 10000,
            "max": 20000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 20000,
            "max": 30000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 30000,
            "max": 40000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 40000,
            "max": 50000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 50000,
            "max": 60000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 60000,
            "max": 70000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 70000,
            "max": 80000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 80000,
            "max": 90000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 90000,
            "max": 100000,
            "weight": 0
          },
          {
            "type": "range",
            "min": 100000,
            "max": 9999999,
            "weight": 0
          }
        ]
      }
    },
    "oldhand": {
      "normal_bet": {
        "small_bet": {
          "weight_bg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 693473066
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 154113757
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 52998656
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 25343868
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 16953005
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 10641538
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 7023229
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 4689260
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 3148673
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 2637421
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 3095317
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 10151360
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 6233172
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 4856237
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 4641441
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 0
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 0
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 0
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 0
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 0
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 0
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 0
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 0
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 0
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 0
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 0
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 0
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 0
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 0
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 0
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 0
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 0
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 0
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 0
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 0
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 0
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 0
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            },
            {
              "type": "free_game",
              "weight": 200040
            }
          ],
          "weight_fg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 2143577
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 1416535
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 1051862
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 1732660
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 1369763
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 2372063
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 3678676
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 1983117
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 4898638
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 2265996
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 3191785
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 25620053
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 23274151
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 28800167
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 33189112
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 36294419
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 39544654
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 33845601
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 31872625
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 75891239
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 73025955
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 67078410
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 57317958
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 51861382
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 94348715
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 72874992
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 58890411
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 39862712
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 32205840
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 50357847
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 24756557
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 11826471
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 5845440
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 2772494
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 1321158
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 650610
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 292176
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 133634
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 75655
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 32682
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 16487
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 8644
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 4043
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 1942
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 989
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 103
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            }
          ]
        },
        "medium_bet": {
          "weight_bg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 693473066
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 154113757
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 52998656
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 25343868
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 16953005
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 10641538
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 7023229
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 4689260
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 3148673
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 2637421
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 3095317
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 10151360
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 6233172
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 4856237
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 4641441
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 0
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 0
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 0
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 0
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 0
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 0
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 0
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 0
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 0
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 0
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 0
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 0
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 0
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 0
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 0
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 0
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 0
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 0
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 0
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 0
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 0
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 0
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            },
            {
              "type": "free_game",
              "weight": 200040
            }
          ],
          "weight_fg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 2143577
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 1416535
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 1051862
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 1732660
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 1369763
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 2372063
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 3678676
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 1983117
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 4898638
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 2265996
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 3191785
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 25620053
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 23274151
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 28800167
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 33189112
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 36294419
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 39544654
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 33845601
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 31872625
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 75891239
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 73025955
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 67078410
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 57317958
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 51861382
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 94348715
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 72874992
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 58890411
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 39862712
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 32205840
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 50357847
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 24756557
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 11826471
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 5845440
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 2772494
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 1321158
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 650610
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 292176
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 133634
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 75655
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 32682
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 16487
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 8644
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 4043
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 1942
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 989
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 103
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            }
          ]
        },
        "big_bet": {
          "weight_bg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 693473066
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 154113757
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 52998656
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 25343868
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 16953005
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 10641538
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 7023229
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 4689260
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 3148673
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 2637421
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 3095317
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 10151360
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 6233172
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 4856237
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 4641441
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 0
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 0
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 0
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 0
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 0
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 0
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 0
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 0
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 0
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 0
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 0
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 0
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 0
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 0
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 0
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 0
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 0
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 0
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 0
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 0
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 0
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 0
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            },
            {
              "type": "free_game",
              "weight": 200040
            }
          ],
          "weight_fg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 2143577
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 1416535
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 1051862
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 1732660
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 1369763
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 2372063
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 3678676
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 1983117
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 4898638
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 2265996
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 3191785
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 25620053
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 23274151
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 28800167
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 33189112
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 36294419
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 39544654
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 33845601
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 31872625
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 75891239
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 73025955
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 67078410
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 57317958
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 51861382
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 94348715
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 72874992
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 58890411
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 39862712
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 32205840
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 50357847
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 24756557
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 11826471
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 5845440
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 2772494
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 1321158
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 650610
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 292176
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 133634
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 75655
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 32682
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 16487
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 8644
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 4043
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 1942
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 989
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 103
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            }
          ]
        }
      },
      "buy_feature": {
        "small_bet": {
          "weight_fg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 0
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 28562
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 26090
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 39665
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 48205
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 66589
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 78123
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 96053
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 112205
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 863568
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 1449251
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 2212457
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 3128345
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 4352684
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 5846792
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 7641034
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 9857532
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 28397923
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 44726944
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 68800809
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 104364313
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 156240608
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 561622248
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 0
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 0
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 0
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 0
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 0
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 0
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 0
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 0
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 0
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 0
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 0
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 0
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 0
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 0
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 0
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 0
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 0
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 0
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 0
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            }
          ]
        },
        "medium_bet": {
          "weight_fg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 0
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 28562
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 26090
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 39665
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 48205
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 66589
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 78123
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 96053
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 112205
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 863568
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 1449251
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 2212457
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 3128345
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 4352684
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 5846792
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 7641034
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 9857532
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 28397923
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 44726944
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 68800809
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 104364313
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 156240608
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 561622248
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 0
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 0
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 0
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 0
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 0
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 0
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 0
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 0
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 0
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 0
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 0
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 0
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 0
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 0
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 0
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 0
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 0
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 0
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 0
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            }
          ]
        },
        "big_bet": {
          "weight_fg": [
            {
              "type": "range",
              "min": -1,
              "max": 0,
              "weight": 0
            },
            {
              "type": "range",
              "min": 0,
              "max": 1,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1,
              "max": 2,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2,
              "max": 3,
              "weight": 28562
            },
            {
              "type": "range",
              "min": 3,
              "max": 4,
              "weight": 26090
            },
            {
              "type": "range",
              "min": 4,
              "max": 5,
              "weight": 39665
            },
            {
              "type": "range",
              "min": 5,
              "max": 6,
              "weight": 48205
            },
            {
              "type": "range",
              "min": 6,
              "max": 7,
              "weight": 66589
            },
            {
              "type": "range",
              "min": 7,
              "max": 8,
              "weight": 78123
            },
            {
              "type": "range",
              "min": 8,
              "max": 9,
              "weight": 96053
            },
            {
              "type": "range",
              "min": 9,
              "max": 10,
              "weight": 112205
            },
            {
              "type": "range",
              "min": 10,
              "max": 15,
              "weight": 863568
            },
            {
              "type": "range",
              "min": 15,
              "max": 20,
              "weight": 1449251
            },
            {
              "type": "range",
              "min": 20,
              "max": 25,
              "weight": 2212457
            },
            {
              "type": "range",
              "min": 25,
              "max": 30,
              "weight": 3128345
            },
            {
              "type": "range",
              "min": 30,
              "max": 35,
              "weight": 4352684
            },
            {
              "type": "range",
              "min": 35,
              "max": 40,
              "weight": 5846792
            },
            {
              "type": "range",
              "min": 40,
              "max": 45,
              "weight": 7641034
            },
            {
              "type": "range",
              "min": 45,
              "max": 50,
              "weight": 9857532
            },
            {
              "type": "range",
              "min": 50,
              "max": 60,
              "weight": 28397923
            },
            {
              "type": "range",
              "min": 60,
              "max": 70,
              "weight": 44726944
            },
            {
              "type": "range",
              "min": 70,
              "max": 80,
              "weight": 68800809
            },
            {
              "type": "range",
              "min": 80,
              "max": 90,
              "weight": 104364313
            },
            {
              "type": "range",
              "min": 90,
              "max": 100,
              "weight": 156240608
            },
            {
              "type": "range",
              "min": 100,
              "max": 120,
              "weight": 561622248
            },
            {
              "type": "range",
              "min": 120,
              "max": 140,
              "weight": 0
            },
            {
              "type": "range",
              "min": 140,
              "max": 160,
              "weight": 0
            },
            {
              "type": "range",
              "min": 160,
              "max": 180,
              "weight": 0
            },
            {
              "type": "range",
              "min": 180,
              "max": 200,
              "weight": 0
            },
            {
              "type": "range",
              "min": 200,
              "max": 250,
              "weight": 0
            },
            {
              "type": "range",
              "min": 250,
              "max": 300,
              "weight": 0
            },
            {
              "type": "range",
              "min": 300,
              "max": 350,
              "weight": 0
            },
            {
              "type": "range",
              "min": 350,
              "max": 400,
              "weight": 0
            },
            {
              "type": "range",
              "min": 400,
              "max": 450,
              "weight": 0
            },
            {
              "type": "range",
              "min": 450,
              "max": 500,
              "weight": 0
            },
            {
              "type": "range",
              "min": 500,
              "max": 550,
              "weight": 0
            },
            {
              "type": "range",
              "min": 550,
              "max": 600,
              "weight": 0
            },
            {
              "type": "range",
              "min": 600,
              "max": 650,
              "weight": 0
            },
            {
              "type": "range",
              "min": 650,
              "max": 700,
              "weight": 0
            },
            {
              "type": "range",
              "min": 700,
              "max": 750,
              "weight": 0
            },
            {
              "type": "range",
              "min": 750,
              "max": 800,
              "weight": 0
            },
            {
              "type": "range",
              "min": 800,
              "max": 850,
              "weight": 0
            },
            {
              "type": "range",
              "min": 850,
              "max": 900,
              "weight": 0
            },
            {
              "type": "range",
              "min": 900,
              "max": 950,
              "weight": 0
            },
            {
              "type": "range",
              "min": 950,
              "max": 1000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 1000,
              "max": 2000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 2000,
              "max": 3000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 3000,
              "max": 4000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 4000,
              "max": 5000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 5000,
              "max": 6000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 6000,
              "max": 7000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 7000,
              "max": 8000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 8000,
              "max": 9000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 9000,
              "max": 10000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 10000,
              "max": 20000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 20000,
              "max": 30000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 30000,
              "max": 40000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 40000,
              "max": 50000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 50000,
              "max": 60000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 60000,
              "max": 70000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 70000,
              "max": 80000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 80000,
              "max": 90000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 90000,
              "max": 100000,
              "weight": 0
            },
            {
              "type": "range",
              "min": 100000,
              "max": 9999999,
              "weight": 0
            }
          ]
        }
      }
    },
    "calibration": {
      "rtp_family": 94,
      "newbie_bg_mean": 0.9300000143841866,
      "oldhand_bg_mean": 0.9400000039464846,
      "fg_package_mean": 100.00000019476835,
      "fg_entry_probability": 0.0001999999920016,
      "buy_package_mean": 96.49999999554723,
      "normal_report": "H0271_00_2608211639_betmode0_107.xlsx",
      "buy_report": "H0271_00_2608211708_betmode2_107.xlsx"
    }
  },
  "strip_names": [
    "BG_Symbol",
    "BG_Symbol (2)",
    "FG_Symbol",
    "FG_Symbol (2)"
  ],
  "strips": [
    {
      "symbols": [
        [
          12,
          12,
          12,
          12,
          12,
          12
        ],
        [
          11,
          12,
          10,
          11,
          11,
          10
        ],
        [
          10,
          11,
          11,
          10,
          11,
          10
        ],
        [
          8,
          10,
          9,
          9,
          10,
          11
        ],
        [
          9,
          8,
          9,
          7,
          8,
          11
        ],
        [
          7,
          9,
          8,
          7,
          8,
          8
        ],
        [
          12,
          7,
          12,
          12,
          12,
          8
        ],
        [
          12,
          12,
          10,
          11,
          9,
          12
        ],
        [
          11,
          11,
          11,
          10,
          11,
          10
        ],
        [
          10,
          11,
          7,
          10,
          10,
          9
        ],
        [
          8,
          10,
          9,
          9,
          10,
          11
        ],
        [
          8,
          8,
          8,
          8,
          8,
          5
        ],
        [
          9,
          9,
          8,
          8,
          12,
          8
        ],
        [
          12,
          12,
          12,
          12,
          12,
          8
        ],
        [
          11,
          7,
          12,
          12,
          11,
          12
        ],
        [
          10,
          11,
          10,
          11,
          11,
          10
        ],
        [
          7,
          10,
          11,
          10,
          10,
          10
        ],
        [
          8,
          8,
          9,
          9,
          9,
          11
        ],
        [
          9,
          9,
          9,
          7,
          8,
          9
        ],
        [
          9,
          9,
          8,
          7,
          12,
          9
        ],
        [
          12,
          12,
          8,
          12,
          12,
          12
        ],
        [
          11,
          11,
          12,
          11,
          12,
          12
        ],
        [
          10,
          10,
          11,
          11,
          11,
          10
        ],
        [
          8,
          8,
          10,
          10,
          10,
          11
        ],
        [
          7,
          7,
          9,
          10,
          9,
          11
        ],
        [
          9,
          9,
          7,
          9,
          9,
          8
        ],
        [
          9,
          12,
          8,
          12,
          8,
          9
        ],
        [
          12,
          11,
          8,
          8,
          12,
          9
        ],
        [
          11,
          10,
          12,
          11,
          12,
          12
        ],
        [
          11,
          10,
          12,
          7,
          11,
          10
        ],
        [
          10,
          8,
          10,
          10,
          10,
          11
        ],
        [
          10,
          9,
          10,
          9,
          9,
          8
        ],
        [
          8,
          12,
          11,
          12,
          8,
          8
        ],
        [
          12,
          11,
          9,
          12,
          7,
          9
        ],
        [
          9,
          11,
          8,
          11,
          12,
          12
        ],
        [
          11,
          10,
          12,
          11,
          11,
          10
        ],
        [
          7,
          8,
          7,
          11,
          10,
          11
        ],
        [
          7,
          9,
          10,
          10,
          9,
          6
        ],
        [
          10,
          12,
          11,
          9,
          8,
          6
        ],
        [
          12,
          6,
          11,
          12,
          6,
          8
        ],
        [
          8,
          11,
          9,
          8,
          12,
          12
        ],
        [
          8,
          10,
          12,
          7,
          12,
          10
        ],
        [
          11,
          8,
          8,
          11,
          11,
          10
        ],
        [
          9,
          8,
          10,
          10,
          10,
          11
        ],
        [
          10,
          12,
          7,
          9,
          10,
          9
        ],
        [
          12,
          12,
          11,
          12,
          10,
          8
        ],
        [
          6,
          11,
          11,
          8,
          9,
          12
        ],
        [
          8,
          10,
          12,
          7,
          9,
          7
        ],
        [
          11,
          9,
          9,
          11,
          12,
          7
        ],
        [
          11,
          8,
          10,
          11,
          11,
          10
        ],
        [
          10,
          7,
          8,
          10,
          8,
          10
        ],
        [
          12,
          7,
          6,
          12,
          8,
          11
        ],
        [
          9,
          12,
          11,
          9,
          10,
          12
        ],
        [
          8,
          12,
          11,
          9,
          9,
          8
        ],
        [
          8,
          11,
          12,
          8,
          12,
          9
        ],
        [
          11,
          10,
          10,
          11,
          12,
          5
        ],
        [
          10,
          8,
          9,
          10,
          11,
          10
        ],
        [
          12,
          9,
          9,
          12,
          8,
          11
        ],
        [
          9,
          9,
          7,
          7,
          10,
          11
        ],
        [
          5,
          12,
          7,
          9,
          9,
          12
        ],
        [
          8,
          11,
          12,
          8,
          9,
          8
        ],
        [
          8,
          11,
          10,
          8,
          12,
          9
        ],
        [
          11,
          10,
          11,
          10,
          11,
          10
        ],
        [
          12,
          8,
          9,
          12,
          8,
          5
        ],
        [
          12,
          6,
          9,
          11,
          10,
          11
        ],
        [
          10,
          12,
          8,
          6,
          7,
          12
        ],
        [
          10,
          12,
          8,
          9,
          9,
          8
        ],
        [
          9,
          12,
          12,
          7,
          12,
          9
        ],
        [
          11,
          11,
          10,
          10,
          12,
          10
        ],
        [
          11,
          10,
          11,
          12,
          11,
          7
        ],
        [
          12,
          8,
          9,
          11,
          11,
          11
        ],
        [
          8,
          9,
          6,
          6,
          10,
          11
        ],
        [
          10,
          6,
          6,
          9,
          8,
          11
        ],
        [
          10,
          12,
          12,
          8,
          8,
          12
        ],
        [
          9,
          12,
          10,
          10,
          12,
          12
        ],
        [
          9,
          11,
          11,
          12,
          5,
          10
        ],
        [
          12,
          10,
          11,
          11,
          11,
          10
        ],
        [
          12,
          8,
          9,
          11,
          11,
          10
        ],
        [
          11,
          5,
          8,
          7,
          10,
          11
        ],
        [
          10,
          9,
          12,
          5,
          7,
          8
        ],
        [
          5,
          12,
          12,
          5,
          12,
          12
        ],
        [
          7,
          11,
          10,
          12,
          6,
          9
        ],
        [
          6,
          10,
          10,
          10,
          6,
          6
        ],
        [
          12,
          6,
          11,
          10,
          11,
          10
        ],
        [
          11,
          8,
          11,
          11,
          11,
          11
        ],
        [
          10,
          5,
          11,
          11,
          11,
          8
        ],
        [
          10,
          12,
          12,
          9,
          12,
          12
        ],
        [
          8,
          11,
          9,
          12,
          10,
          12
        ],
        [
          5,
          10,
          10,
          6,
          8,
          9
        ],
        [
          12,
          10,
          7,
          10,
          9,
          9
        ],
        [
          11,
          9,
          7,
          10,
          7,
          10
        ],
        [
          11,
          9,
          11,
          11,
          11,
          11
        ],
        [
          10,
          12,
          11,
          9,
          12,
          8
        ],
        [
          9,
          12,
          12,
          9,
          10,
          12
        ],
        [
          7,
          11,
          10,
          12,
          5,
          5
        ],
        [
          12,
          11,
          9,
          12,
          6,
          7
        ],
        [
          6,
          10,
          6,
          10,
          7,
          10
        ],
        [
          6,
          10,
          8,
          11,
          7,
          11
        ],
        [
          11,
          7,
          11,
          8,
          12,
          11
        ],
        [
          10,
          12,
          12,
          7,
          12,
          12
        ],
        [
          5,
          12,
          10,
          6,
          10,
          8
        ],
        [
          12,
          11,
          9,
          12,
          11,
          6
        ],
        [
          7,
          11,
          5,
          10,
          11,
          10
        ],
        [
          9,
          11,
          5,
          10,
          8,
          10
        ],
        [
          11,
          10,
          11,
          11,
          8,
          11
        ],
        [
          11,
          7,
          11,
          5,
          12,
          12
        ],
        [
          10,
          12,
          12,
          7,
          10,
          8
        ],
        [
          10,
          8,
          10,
          12,
          5,
          6
        ],
        [
          12,
          5,
          9,
          6,
          5,
          5
        ],
        [
          8,
          11,
          7,
          10,
          11,
          10
        ],
        [
          9,
          10,
          6,
          11,
          9,
          11
        ],
        [
          11,
          10,
          11,
          8,
          9,
          12
        ],
        [
          6,
          12,
          12,
          7,
          12,
          12
        ],
        [
          5,
          6,
          12,
          12,
          12,
          12
        ],
        [
          12,
          5,
          10,
          12,
          10,
          9
        ],
        [
          7,
          5,
          8,
          12,
          11,
          10
        ],
        [
          8,
          11,
          7,
          10,
          6,
          8
        ],
        [
          11,
          10,
          7,
          11,
          8,
          7
        ],
        [
          10,
          12,
          6,
          6,
          7,
          11
        ],
        [
          9,
          9,
          12,
          6,
          12,
          11
        ],
        [
          12,
          6,
          10,
          5,
          10,
          12
        ],
        [
          6,
          7,
          9,
          12,
          11,
          10
        ],
        [
          8,
          11,
          8,
          10,
          6,
          9
        ],
        [
          11,
          10,
          11,
          11,
          5,
          9
        ],
        [
          5,
          10,
          6,
          9,
          9,
          8
        ],
        [
          7,
          12,
          12,
          8,
          9,
          8
        ],
        [
          12,
          8,
          10,
          5,
          12,
          12
        ],
        [
          9,
          7,
          5,
          12,
          10,
          10
        ],
        [
          10,
          11,
          8,
          12,
          11,
          5
        ],
        [
          11,
          9,
          11,
          10,
          8,
          5
        ],
        [
          6,
          6,
          9,
          11,
          8,
          7
        ],
        [
          5,
          12,
          12,
          11,
          7,
          6
        ],
        [
          5,
          10,
          10,
          7,
          7,
          6
        ],
        [
          12,
          8,
          7,
          8,
          12,
          12
        ],
        [
          12,
          11,
          8,
          12,
          10,
          12
        ],
        [
          11,
          7,
          6,
          12,
          10,
          11
        ],
        [
          8,
          5,
          11,
          10,
          6,
          7
        ],
        [
          7,
          12,
          12,
          10,
          6,
          10
        ],
        [
          10,
          9,
          10,
          11,
          5,
          10
        ],
        [
          9,
          6,
          10,
          9,
          12,
          6
        ],
        [
          12,
          11,
          9,
          7,
          11,
          12
        ],
        [
          12,
          8,
          5,
          12,
          10,
          11
        ],
        [
          11,
          10,
          5,
          8,
          10,
          9
        ],
        [
          11,
          12,
          12,
          8,
          9,
          8
        ],
        [
          7,
          12,
          12,
          10,
          5,
          8
        ],
        [
          6,
          5,
          10,
          11,
          12,
          7
        ],
        [
          8,
          11,
          10,
          6,
          11,
          12
        ],
        [
          12,
          7,
          10,
          12,
          7,
          5
        ],
        [
          10,
          10,
          9,
          9,
          8,
          9
        ],
        [
          11,
          10,
          7,
          5,
          8,
          6
        ],
        [
          5,
          12,
          12,
          10,
          6,
          6
        ],
        [
          5,
          4,
          11,
          11,
          12,
          10
        ],
        [
          8,
          11,
          11,
          4,
          9,
          12
        ],
        [
          12,
          6,
          6,
          12,
          5,
          11
        ],
        [
          12,
          6,
          8,
          9,
          11,
          5
        ],
        [
          11,
          9,
          9,
          9,
          10,
          5
        ],
        [
          7,
          12,
          12,
          10,
          6,
          7
        ],
        [
          9,
          8,
          5,
          11,
          6,
          7
        ],
        [
          6,
          11,
          7,
          5,
          12,
          12
        ],
        [
          6,
          5,
          6,
          12,
          4,
          12
        ],
        [
          12,
          4,
          10,
          12,
          4,
          10
        ],
        [
          11,
          7,
          8,
          7,
          10,
          9
        ],
        [
          10,
          12,
          12,
          7,
          10,
          8
        ],
        [
          4,
          8,
          12,
          6,
          9,
          4
        ],
        [
          8,
          9,
          11,
          10,
          12,
          11
        ],
        [
          9,
          9,
          9,
          11,
          7,
          11
        ],
        [
          12,
          11,
          6,
          12,
          5,
          12
        ],
        [
          11,
          7,
          10,
          5,
          11,
          12
        ],
        [
          7,
          7,
          7,
          4,
          8,
          10
        ],
        [
          4,
          12,
          12,
          4,
          9,
          10
        ],
        [
          5,
          8,
          5,
          10,
          12,
          6
        ],
        [
          8,
          8,
          8,
          8,
          12,
          5
        ],
        [
          12,
          10,
          11,
          12,
          7,
          8
        ],
        [
          11,
          5,
          6,
          11,
          7,
          12
        ],
        [
          6,
          4,
          10,
          11,
          5,
          9
        ],
        [
          7,
          12,
          10,
          6,
          11,
          4
        ],
        [
          9,
          11,
          12,
          5,
          11,
          4
        ],
        [
          10,
          6,
          12,
          10,
          12,
          7
        ],
        [
          12,
          9,
          5,
          10,
          8,
          8
        ],
        [
          11,
          10,
          9,
          12,
          10,
          12
        ],
        [
          11,
          10,
          9,
          12,
          5,
          9
        ],
        [
          5,
          12,
          4,
          6,
          6,
          5
        ],
        [
          7,
          5,
          7,
          7,
          9,
          5
        ],
        [
          7,
          5,
          12,
          7,
          4,
          7
        ],
        [
          12,
          6,
          8,
          9,
          12,
          11
        ],
        [
          9,
          4,
          5,
          9,
          7,
          6
        ],
        [
          9,
          4,
          11,
          12,
          10,
          12
        ],
        [
          4,
          12,
          6,
          12,
          10,
          4
        ],
        [
          4,
          11,
          7,
          8,
          5,
          10
        ],
        [
          8,
          9,
          7,
          5,
          5,
          10
        ],
        [
          12,
          9,
          12,
          5,
          11,
          11
        ],
        [
          10,
          6,
          8,
          6,
          4,
          7
        ],
        [
          6,
          7,
          4,
          6,
          8,
          9
        ],
        [
          6,
          12,
          5,
          11,
          6,
          8
        ],
        [
          5,
          8,
          5,
          4,
          12,
          6
        ],
        [
          11,
          11,
          11,
          8,
          9,
          12
        ],
        [
          12,
          5,
          12,
          10,
          11,
          12
        ],
        [
          10,
          4,
          8,
          10,
          7,
          5
        ],
        [
          8,
          10,
          10,
          10,
          8,
          11
        ],
        [
          4,
          6,
          4,
          9,
          4,
          9
        ],
        [
          6,
          6,
          9,
          9,
          4,
          7
        ],
        [
          6,
          7,
          6,
          7,
          6,
          8
        ],
        [
          12,
          7,
          12,
          11,
          12,
          8
        ],
        [
          10,
          11,
          7,
          4,
          9,
          6
        ],
        [
          8,
          8,
          11,
          4,
          7,
          4
        ],
        [
          5,
          12,
          8,
          8,
          7,
          11
        ],
        [
          7,
          10,
          10,
          12,
          10,
          9
        ],
        [
          7,
          4,
          9,
          5,
          11,
          5
        ],
        [
          12,
          9,
          12,
          5,
          11,
          10
        ],
        [
          9,
          11,
          6,
          6,
          5,
          6
        ],
        [
          9,
          5,
          4,
          6,
          5,
          6
        ],
        [
          11,
          12,
          4,
          7,
          9,
          4
        ],
        [
          10,
          8,
          10,
          8,
          8,
          4
        ],
        [
          8,
          8,
          10,
          11,
          12,
          7
        ],
        [
          8,
          10,
          12,
          12,
          6,
          9
        ],
        [
          8,
          4,
          6,
          9,
          4,
          9
        ],
        [
          12,
          9,
          9,
          4,
          10,
          8
        ],
        [
          12,
          7,
          8,
          7,
          9,
          8
        ],
        [
          11,
          5,
          11,
          8,
          8,
          12
        ],
        [
          11,
          12,
          7,
          11,
          12,
          5
        ],
        [
          5,
          12,
          5,
          12,
          6,
          11
        ],
        [
          5,
          6,
          12,
          10,
          11,
          7
        ],
        [
          4,
          6,
          12,
          10,
          7,
          10
        ],
        [
          12,
          11,
          4,
          9,
          9,
          6
        ],
        [
          6,
          11,
          6,
          4,
          8,
          12
        ],
        [
          9,
          9,
          6,
          5,
          10,
          4
        ],
        [
          7,
          10,
          9,
          7,
          10,
          11
        ],
        [
          10,
          5,
          9,
          11,
          5,
          7
        ],
        [
          10,
          5,
          8,
          6,
          5,
          7
        ],
        [
          12,
          7,
          8,
          6,
          4,
          10
        ],
        [
          4,
          4,
          11,
          12,
          12,
          5
        ],
        [
          5,
          4,
          5,
          8,
          6,
          4
        ],
        [
          6,
          8,
          7,
          4,
          8,
          11
        ],
        [
          7,
          8,
          7,
          5,
          9,
          6
        ],
        [
          7,
          9,
          1,
          11,
          11,
          8
        ],
        [
          12,
          11,
          12,
          11,
          4,
          10
        ],
        [
          12,
          11,
          12,
          7,
          4,
          9
        ],
        [
          9,
          6,
          4,
          7,
          7,
          1
        ],
        [
          11,
          12,
          4,
          8,
          12,
          12
        ],
        [
          4,
          10,
          10,
          8,
          6,
          5
        ],
        [
          6,
          7,
          10,
          12,
          10,
          11
        ],
        [
          1,
          7,
          11,
          9,
          8,
          11
        ],
        [
          12,
          9,
          5,
          1,
          5,
          6
        ],
        [
          12,
          1,
          7,
          5,
          11,
          1
        ],
        [
          8,
          4,
          1,
          5,
          7,
          7
        ],
        [
          9,
          12,
          6,
          10,
          7,
          8
        ],
        [
          9,
          8,
          6,
          4,
          6,
          5
        ],
        [
          10,
          6,
          8,
          12,
          12,
          5
        ],
        [
          11,
          10,
          11,
          6,
          1,
          4
        ],
        [
          4,
          5,
          9,
          9,
          9,
          10
        ],
        [
          5,
          1,
          5,
          9,
          5,
          12
        ],
        [
          6,
          7,
          12,
          7,
          11,
          9
        ],
        [
          8,
          12,
          1,
          4,
          4,
          6
        ],
        [
          8,
          9,
          8,
          1,
          10,
          1
        ],
        [
          7,
          8,
          7,
          11,
          6,
          4
        ],
        [
          4,
          11,
          10,
          6,
          8,
          4
        ],
        [
          4,
          10,
          5,
          10,
          8,
          7
        ],
        [
          10,
          6,
          11,
          12,
          8,
          12
        ],
        [
          11,
          4,
          4,
          8,
          1,
          10
        ],
        [
          5,
          4,
          9,
          5,
          12,
          9
        ],
        [
          5,
          5,
          9,
          11,
          9,
          8
        ],
        [
          1,
          1,
          6,
          6,
          5,
          6
        ],
        [
          12,
          10,
          1,
          10,
          7,
          1
        ],
        [
          9,
          6,
          5,
          12,
          6,
          11
        ],
        [
          11,
          7,
          8,
          9,
          6,
          12
        ],
        [
          11,
          7,
          12,
          1,
          1,
          10
        ],
        [
          11,
          8,
          12,
          8,
          9,
          5
        ],
        [
          10,
          8,
          12,
          7,
          4,
          8
        ],
        [
          12,
          12,
          11,
          4,
          11,
          9
        ],
        [
          7,
          5,
          4,
          4,
          10,
          7
        ],
        [
          6,
          9,
          7,
          5,
          10,
          1
        ],
        [
          1,
          11,
          10,
          9,
          12,
          11
        ],
        [
          4,
          11,
          10,
          12,
          12,
          6
        ],
        [
          10,
          1,
          1,
          11,
          9,
          5
        ],
        [
          5,
          12,
          5,
          1,
          5,
          12
        ],
        [
          9,
          12,
          9,
          7,
          11,
          8
        ],
        [
          8,
          5,
          8,
          6,
          4,
          4
        ],
        [
          8,
          10,
          4,
          10,
          7,
          10
        ],
        [
          6,
          10,
          11,
          8,
          1,
          9
        ],
        [
          1,
          10,
          7,
          8,
          6,
          7
        ],
        [
          12,
          9,
          6,
          1,
          12,
          5
        ],
        [
          12,
          9,
          10,
          11,
          5,
          6
        ],
        [
          12,
          6,
          9,
          11,
          11,
          11
        ],
        [
          7,
          6,
          5,
          5,
          4,
          10
        ],
        [
          7,
          4,
          5,
          6,
          1,
          1
        ],
        [
          9,
          1,
          1,
          9,
          8,
          7
        ],
        [
          5,
          8,
          11,
          10,
          10,
          7
        ],
        [
          1,
          8,
          4,
          7,
          7,
          9
        ],
        [
          6,
          7,
          7,
          7,
          9,
          9
        ],
        [
          10,
          5,
          8,
          4,
          9,
          8
        ],
        [
          10,
          5,
          8,
          12,
          4,
          12
        ],
        [
          4,
          11,
          6,
          12,
          2,
          12
        ],
        [
          4,
          11,
          6,
          1,
          6,
          4
        ],
        [
          7,
          4,
          11,
          10,
          1,
          6
        ],
        [
          8,
          12,
          12,
          5,
          8,
          10
        ],
        [
          5,
          9,
          1,
          8,
          5,
          1
        ],
        [
          1,
          6,
          4,
          6,
          10,
          11
        ],
        [
          6,
          1,
          9,
          4,
          11,
          5
        ],
        [
          11,
          7,
          10,
          2,
          7,
          4
        ],
        [
          9,
          4,
          7,
          9,
          12,
          8
        ]
      ],
      "weights": [
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ]
      ],
      "drop_weights": [
        [
          16400,
          12501,
          16700,
          18098,
          13701,
          20700
        ],
        [
          3100,
          1400,
          2600,
          4000,
          3000,
          4400
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          42800,
          46505,
          42200,
          43696,
          60906,
          68000
        ],
        [
          86200,
          86709,
          74600,
          83792,
          96110,
          103900
        ],
        [
          73600,
          83608,
          83900,
          95490,
          109911,
          99500
        ],
        [
          80700,
          84609,
          94400,
          128287,
          96210,
          97000
        ],
        [
          103900,
          108611,
          114400,
          108589,
          131013,
          123600
        ],
        [
          129400,
          132513,
          150100,
          115788,
          125013,
          118900
        ],
        [
          129400,
          138214,
          138200,
          136786,
          113511,
          128700
        ],
        [
          156300,
          143414,
          129700,
          130987,
          121212,
          124200
        ],
        [
          178200,
          161916,
          153200,
          134487,
          129413,
          111100
        ]
      ],
      "reel_lengths": [
        300,
        300,
        300,
        300,
        300,
        300
      ]
    },
    {
      "symbols": [
        [
          12,
          12,
          12,
          12,
          12,
          12
        ],
        [
          12,
          11,
          12,
          11,
          11,
          10
        ],
        [
          11,
          10,
          11,
          10,
          10,
          11
        ],
        [
          11,
          9,
          10,
          10,
          9,
          9
        ],
        [
          10,
          9,
          10,
          9,
          8,
          8
        ],
        [
          10,
          8,
          9,
          7,
          6,
          6
        ],
        [
          9,
          12,
          9,
          12,
          12,
          12
        ],
        [
          12,
          12,
          12,
          12,
          12,
          10
        ],
        [
          8,
          11,
          11,
          11,
          11,
          10
        ],
        [
          11,
          10,
          8,
          11,
          10,
          11
        ],
        [
          6,
          9,
          10,
          10,
          9,
          9
        ],
        [
          6,
          6,
          7,
          9,
          9,
          8
        ],
        [
          10,
          8,
          9,
          7,
          8,
          12
        ],
        [
          10,
          12,
          9,
          7,
          12,
          6
        ],
        [
          12,
          11,
          12,
          12,
          11,
          10
        ],
        [
          11,
          10,
          11,
          12,
          10,
          11
        ],
        [
          11,
          9,
          10,
          11,
          6,
          9
        ],
        [
          9,
          6,
          6,
          11,
          9,
          8
        ],
        [
          8,
          8,
          6,
          10,
          8,
          12
        ],
        [
          10,
          12,
          9,
          9,
          12,
          6
        ],
        [
          10,
          11,
          9,
          8,
          11,
          10
        ],
        [
          12,
          10,
          12,
          12,
          11,
          11
        ],
        [
          12,
          9,
          11,
          7,
          10,
          11
        ],
        [
          11,
          6,
          11,
          11,
          9,
          11
        ],
        [
          9,
          7,
          10,
          10,
          8,
          12
        ],
        [
          8,
          12,
          8,
          9,
          12,
          9
        ],
        [
          10,
          11,
          9,
          8,
          6,
          9
        ],
        [
          7,
          10,
          12,
          12,
          11,
          10
        ],
        [
          7,
          9,
          7,
          5,
          10,
          8
        ],
        [
          12,
          8,
          7,
          11,
          10,
          8
        ],
        [
          12,
          5,
          11,
          10,
          9,
          12
        ],
        [
          12,
          12,
          10,
          9,
          12,
          12
        ],
        [
          11,
          11,
          9,
          9,
          12,
          11
        ],
        [
          10,
          10,
          12,
          12,
          11,
          11
        ],
        [
          10,
          9,
          8,
          7,
          11,
          10
        ],
        [
          9,
          6,
          6,
          11,
          10,
          9
        ],
        [
          8,
          8,
          11,
          10,
          9,
          9
        ],
        [
          12,
          8,
          10,
          6,
          9,
          12
        ],
        [
          11,
          12,
          9,
          9,
          12,
          7
        ],
        [
          6,
          12,
          12,
          12,
          8,
          11
        ],
        [
          10,
          12,
          8,
          12,
          8,
          10
        ],
        [
          9,
          11,
          8,
          11,
          11,
          8
        ],
        [
          8,
          10,
          11,
          10,
          10,
          8
        ],
        [
          12,
          10,
          10,
          10,
          5,
          12
        ],
        [
          11,
          9,
          9,
          9,
          12,
          12
        ],
        [
          5,
          7,
          9,
          7,
          12,
          11
        ],
        [
          10,
          12,
          12,
          12,
          8,
          10
        ],
        [
          10,
          11,
          6,
          11,
          11,
          5
        ],
        [
          9,
          6,
          11,
          6,
          10,
          9
        ],
        [
          12,
          10,
          11,
          10,
          9,
          6
        ],
        [
          11,
          9,
          10,
          9,
          7,
          6
        ],
        [
          8,
          9,
          10,
          8,
          12,
          12
        ],
        [
          8,
          12,
          10,
          8,
          12,
          12
        ],
        [
          10,
          12,
          12,
          12,
          11,
          10
        ],
        [
          9,
          11,
          9,
          11,
          10,
          10
        ],
        [
          12,
          11,
          11,
          10,
          10,
          11
        ],
        [
          11,
          10,
          5,
          9,
          6,
          11
        ],
        [
          6,
          5,
          7,
          9,
          8,
          9
        ],
        [
          5,
          5,
          10,
          5,
          8,
          9
        ],
        [
          10,
          12,
          10,
          12,
          12,
          12
        ],
        [
          9,
          7,
          12,
          11,
          11,
          10
        ],
        [
          12,
          11,
          11,
          10,
          10,
          7
        ],
        [
          11,
          10,
          9,
          10,
          7,
          7
        ],
        [
          7,
          9,
          9,
          7,
          9,
          11
        ],
        [
          6,
          6,
          5,
          5,
          5,
          5
        ],
        [
          10,
          12,
          10,
          12,
          12,
          12
        ],
        [
          9,
          7,
          12,
          11,
          11,
          10
        ],
        [
          12,
          11,
          11,
          9,
          10,
          8
        ],
        [
          11,
          10,
          7,
          10,
          6,
          7
        ],
        [
          5,
          8,
          9,
          6,
          6,
          11
        ],
        [
          8,
          8,
          8,
          7,
          9,
          5
        ],
        [
          10,
          12,
          10,
          12,
          12,
          12
        ],
        [
          9,
          12,
          12,
          11,
          11,
          10
        ],
        [
          9,
          11,
          11,
          11,
          10,
          10
        ],
        [
          12,
          10,
          6,
          10,
          5,
          6
        ],
        [
          11,
          10,
          6,
          10,
          7,
          11
        ],
        [
          7,
          6,
          9,
          9,
          8,
          5
        ],
        [
          10,
          6,
          10,
          9,
          12,
          12
        ],
        [
          6,
          12,
          10,
          12,
          11,
          9
        ],
        [
          8,
          11,
          12,
          11,
          10,
          10
        ],
        [
          12,
          9,
          11,
          6,
          9,
          8
        ],
        [
          11,
          9,
          11,
          10,
          9,
          11
        ],
        [
          7,
          10,
          8,
          8,
          7,
          6
        ],
        [
          10,
          5,
          8,
          5,
          7,
          12
        ],
        [
          9,
          12,
          10,
          12,
          12,
          5
        ],
        [
          5,
          11,
          12,
          11,
          11,
          5
        ],
        [
          5,
          7,
          9,
          6,
          10,
          10
        ],
        [
          12,
          9,
          9,
          6,
          5,
          11
        ],
        [
          11,
          10,
          11,
          10,
          5,
          7
        ],
        [
          10,
          5,
          5,
          10,
          8,
          12
        ],
        [
          6,
          12,
          5,
          12,
          12,
          8
        ],
        [
          9,
          11,
          12,
          12,
          11,
          9
        ],
        [
          8,
          11,
          10,
          11,
          6,
          10
        ],
        [
          12,
          6,
          7,
          7,
          6,
          11
        ],
        [
          11,
          10,
          7,
          8,
          10,
          7
        ],
        [
          11,
          8,
          11,
          8,
          9,
          12
        ],
        [
          6,
          8,
          11,
          10,
          12,
          12
        ],
        [
          10,
          12,
          12,
          12,
          12,
          6
        ],
        [
          10,
          11,
          12,
          11,
          11,
          10
        ],
        [
          12,
          7,
          10,
          5,
          8,
          11
        ],
        [
          7,
          10,
          10,
          7,
          7,
          9
        ],
        [
          11,
          5,
          6,
          7,
          5,
          8
        ],
        [
          5,
          4,
          11,
          10,
          10,
          8
        ],
        [
          8,
          12,
          8,
          12,
          12,
          12
        ],
        [
          8,
          11,
          12,
          11,
          11,
          10
        ],
        [
          12,
          9,
          5,
          9,
          9,
          11
        ],
        [
          12,
          10,
          10,
          5,
          6,
          5
        ],
        [
          11,
          6,
          10,
          5,
          8,
          7
        ],
        [
          11,
          6,
          11,
          10,
          8,
          6
        ],
        [
          11,
          12,
          9,
          12,
          12,
          12
        ],
        [
          6,
          11,
          9,
          11,
          11,
          10
        ],
        [
          6,
          11,
          12,
          9,
          11,
          11
        ],
        [
          12,
          10,
          6,
          6,
          7,
          11
        ],
        [
          7,
          7,
          7,
          8,
          10,
          9
        ],
        [
          9,
          5,
          11,
          10,
          5,
          9
        ],
        [
          11,
          12,
          11,
          12,
          5,
          12
        ],
        [
          10,
          12,
          10,
          11,
          12,
          10
        ],
        [
          5,
          11,
          12,
          7,
          11,
          10
        ],
        [
          12,
          10,
          12,
          9,
          7,
          11
        ],
        [
          7,
          7,
          5,
          4,
          10,
          5
        ],
        [
          9,
          7,
          6,
          10,
          10,
          4
        ],
        [
          11,
          5,
          11,
          12,
          6,
          12
        ],
        [
          11,
          5,
          8,
          11,
          12,
          8
        ],
        [
          8,
          11,
          7,
          11,
          9,
          8
        ],
        [
          12,
          12,
          12,
          8,
          9,
          7
        ],
        [
          12,
          10,
          10,
          6,
          11,
          7
        ],
        [
          6,
          9,
          9,
          6,
          11,
          10
        ],
        [
          6,
          4,
          11,
          12,
          5,
          12
        ],
        [
          11,
          8,
          5,
          10,
          12,
          12
        ],
        [
          9,
          11,
          6,
          10,
          8,
          11
        ],
        [
          4,
          12,
          12,
          11,
          6,
          11
        ],
        [
          12,
          12,
          12,
          5,
          7,
          6
        ],
        [
          10,
          10,
          8,
          8,
          11,
          9
        ],
        [
          5,
          10,
          7,
          12,
          10,
          4
        ],
        [
          5,
          6,
          11,
          12,
          10,
          5
        ],
        [
          11,
          6,
          9,
          10,
          12,
          5
        ],
        [
          7,
          11,
          5,
          11,
          12,
          10
        ],
        [
          12,
          12,
          12,
          11,
          12,
          6
        ],
        [
          10,
          12,
          8,
          4,
          5,
          6
        ],
        [
          9,
          9,
          10,
          7,
          9,
          12
        ],
        [
          4,
          8,
          6,
          7,
          4,
          11
        ],
        [
          4,
          4,
          11,
          12,
          4,
          11
        ],
        [
          11,
          4,
          7,
          12,
          8,
          4
        ],
        [
          12,
          11,
          7,
          11,
          12,
          9
        ],
        [
          8,
          12,
          12,
          9,
          7,
          10
        ],
        [
          7,
          10,
          9,
          5,
          6,
          10
        ],
        [
          7,
          10,
          10,
          10,
          5,
          7
        ],
        [
          9,
          5,
          5,
          4,
          5,
          8
        ],
        [
          11,
          5,
          5,
          4,
          9,
          12
        ],
        [
          12,
          11,
          6,
          12,
          12,
          4
        ],
        [
          8,
          9,
          12,
          11,
          7,
          4
        ],
        [
          10,
          8,
          12,
          11,
          11,
          6
        ],
        [
          6,
          12,
          11,
          10,
          8,
          6
        ],
        [
          5,
          12,
          8,
          6,
          8,
          5
        ],
        [
          11,
          7,
          10,
          5,
          6,
          8
        ],
        [
          11,
          7,
          4,
          12,
          12,
          12
        ],
        [
          12,
          11,
          7,
          9,
          10,
          7
        ],
        [
          12,
          11,
          12,
          11,
          11,
          9
        ],
        [
          10,
          6,
          11,
          8,
          11,
          9
        ],
        [
          6,
          6,
          6,
          10,
          4,
          11
        ],
        [
          6,
          4,
          6,
          7,
          4,
          8
        ],
        [
          11,
          8,
          9,
          12,
          12,
          12
        ],
        [
          11,
          9,
          8,
          5,
          6,
          10
        ],
        [
          12,
          11,
          8,
          11,
          6,
          5
        ],
        [
          5,
          7,
          12,
          6,
          9,
          5
        ],
        [
          4,
          12,
          12,
          8,
          7,
          7
        ],
        [
          8,
          4,
          10,
          8,
          5,
          7
        ],
        [
          7,
          10,
          11,
          12,
          12,
          9
        ],
        [
          11,
          10,
          11,
          9,
          10,
          9
        ],
        [
          12,
          11,
          5,
          11,
          10,
          8
        ],
        [
          9,
          11,
          5,
          5,
          8,
          11
        ],
        [
          9,
          11,
          9,
          5,
          9,
          12
        ],
        [
          5,
          5,
          7,
          6,
          7,
          4
        ],
        [
          8,
          8,
          12,
          12,
          7,
          6
        ],
        [
          4,
          9,
          4,
          4,
          12,
          10
        ],
        [
          12,
          7,
          10,
          11,
          12,
          10
        ],
        [
          12,
          4,
          8,
          7,
          6,
          5
        ],
        [
          11,
          12,
          6,
          9,
          5,
          11
        ],
        [
          11,
          12,
          7,
          10,
          4,
          4
        ],
        [
          7,
          5,
          9,
          12,
          8,
          6
        ],
        [
          7,
          8,
          12,
          12,
          9,
          12
        ],
        [
          10,
          9,
          4,
          11,
          12,
          12
        ],
        [
          12,
          6,
          4,
          11,
          11,
          7
        ],
        [
          9,
          11,
          10,
          4,
          11,
          8
        ],
        [
          9,
          10,
          6,
          8,
          11,
          4
        ],
        [
          4,
          5,
          6,
          10,
          4,
          11
        ],
        [
          5,
          4,
          11,
          12,
          9,
          11
        ],
        [
          8,
          4,
          9,
          9,
          6,
          5
        ],
        [
          12,
          6,
          7,
          6,
          5,
          10
        ],
        [
          10,
          11,
          5,
          7,
          10,
          9
        ],
        [
          6,
          11,
          12,
          8,
          12,
          8
        ],
        [
          11,
          8,
          12,
          8,
          7,
          7
        ],
        [
          4,
          8,
          12,
          12,
          8,
          6
        ],
        [
          8,
          7,
          8,
          11,
          9,
          4
        ],
        [
          12,
          9,
          4,
          11,
          5,
          10
        ],
        [
          12,
          9,
          7,
          11,
          4,
          9
        ],
        [
          7,
          10,
          10,
          5,
          12,
          5
        ],
        [
          5,
          5,
          11,
          5,
          10,
          12
        ],
        [
          10,
          12,
          5,
          12,
          6,
          7
        ],
        [
          6,
          7,
          8,
          7,
          7,
          8
        ],
        [
          8,
          6,
          9,
          6,
          7,
          8
        ],
        [
          8,
          9,
          6,
          10,
          8,
          6
        ],
        [
          9,
          4,
          7,
          4,
          8,
          6
        ],
        [
          7,
          10,
          7,
          9,
          4,
          11
        ],
        [
          4,
          11,
          11,
          12,
          10,
          5
        ],
        [
          4,
          11,
          8,
          7,
          10,
          5
        ],
        [
          5,
          6,
          9,
          6,
          9,
          4
        ],
        [
          10,
          12,
          10,
          6,
          5,
          12
        ],
        [
          10,
          7,
          5,
          10,
          6,
          9
        ],
        [
          6,
          7,
          4,
          9,
          12,
          7
        ],
        [
          11,
          5,
          4,
          4,
          11,
          7
        ],
        [
          12,
          5,
          6,
          12,
          11,
          10
        ],
        [
          5,
          8,
          12,
          7,
          8,
          11
        ],
        [
          7,
          12,
          11,
          8,
          5,
          12
        ],
        [
          7,
          9,
          10,
          5,
          4,
          9
        ],
        [
          9,
          9,
          9,
          10,
          6,
          8
        ],
        [
          9,
          6,
          5,
          9,
          9,
          4
        ],
        [
          11,
          4,
          8,
          12,
          7,
          10
        ],
        [
          12,
          4,
          4,
          12,
          12,
          10
        ],
        [
          6,
          10,
          6,
          12,
          10,
          6
        ],
        [
          10,
          10,
          11,
          4,
          4,
          12
        ],
        [
          8,
          8,
          10,
          10,
          5,
          9
        ],
        [
          5,
          7,
          10,
          10,
          11,
          5
        ],
        [
          11,
          6,
          9,
          5,
          8,
          4
        ],
        [
          4,
          12,
          12,
          11,
          6,
          7
        ],
        [
          6,
          5,
          8,
          9,
          6,
          6
        ],
        [
          12,
          5,
          8,
          9,
          7,
          11
        ],
        [
          7,
          8,
          7,
          7,
          9,
          8
        ],
        [
          8,
          8,
          5,
          7,
          12,
          12
        ],
        [
          9,
          11,
          6,
          8,
          8,
          12
        ],
        [
          9,
          10,
          6,
          4,
          4,
          4
        ],
        [
          10,
          7,
          11,
          6,
          4,
          4
        ],
        [
          12,
          4,
          11,
          11,
          10,
          5
        ],
        [
          11,
          6,
          11,
          5,
          7,
          11
        ],
        [
          4,
          9,
          9,
          12,
          7,
          6
        ],
        [
          6,
          12,
          5,
          8,
          9,
          8
        ],
        [
          5,
          11,
          5,
          4,
          11,
          9
        ],
        [
          10,
          11,
          12,
          6,
          12,
          7
        ],
        [
          7,
          7,
          4,
          10,
          12,
          7
        ],
        [
          12,
          8,
          7,
          10,
          5,
          10
        ],
        [
          12,
          10,
          7,
          10,
          5,
          6
        ],
        [
          4,
          6,
          9,
          11,
          10,
          5
        ],
        [
          8,
          6,
          10,
          7,
          8,
          8
        ],
        [
          5,
          9,
          12,
          5,
          9,
          11
        ],
        [
          5,
          9,
          4,
          4,
          9,
          9
        ],
        [
          6,
          4,
          4,
          8,
          11,
          10
        ],
        [
          11,
          12,
          2,
          6,
          6,
          10
        ],
        [
          1,
          5,
          8,
          6,
          7,
          10
        ],
        [
          2,
          2,
          5,
          2,
          7,
          7
        ],
        [
          10,
          8,
          6,
          9,
          10,
          6
        ],
        [
          4,
          11,
          10,
          9,
          10,
          12
        ],
        [
          7,
          4,
          9,
          12,
          12,
          4
        ],
        [
          7,
          10,
          2,
          5,
          8,
          4
        ],
        [
          8,
          7,
          7,
          11,
          2,
          5
        ],
        [
          8,
          12,
          12,
          4,
          4,
          2
        ],
        [
          6,
          5,
          12,
          4,
          11,
          11
        ],
        [
          11,
          11,
          8,
          8,
          6,
          8
        ],
        [
          9,
          2,
          10,
          7,
          5,
          9
        ],
        [
          9,
          8,
          2,
          2,
          1,
          12
        ],
        [
          2,
          10,
          7,
          5,
          2,
          1
        ],
        [
          4,
          7,
          1,
          11,
          8,
          5
        ],
        [
          6,
          7,
          11,
          6,
          9,
          6
        ],
        [
          11,
          9,
          9,
          9,
          9,
          7
        ],
        [
          1,
          6,
          5,
          9,
          4,
          2
        ],
        [
          10,
          12,
          8,
          12,
          5,
          11
        ],
        [
          5,
          1,
          4,
          12,
          12,
          9
        ],
        [
          5,
          4,
          6,
          8,
          11,
          8
        ],
        [
          12,
          5,
          12,
          8,
          11,
          10
        ],
        [
          2,
          2,
          12,
          2,
          6,
          1
        ],
        [
          9,
          9,
          11,
          7,
          6,
          7
        ],
        [
          7,
          10,
          11,
          10,
          7,
          11
        ],
        [
          10,
          10,
          10,
          1,
          8,
          4
        ],
        [
          6,
          8,
          10,
          4,
          4,
          2
        ],
        [
          12,
          5,
          1,
          4,
          10,
          8
        ],
        [
          4,
          1,
          9,
          5,
          1,
          5
        ],
        [
          4,
          6,
          4,
          5,
          12,
          5
        ],
        [
          11,
          12,
          7,
          2,
          2,
          9
        ],
        [
          11,
          11,
          2,
          6,
          5,
          12
        ],
        [
          1,
          4,
          5,
          7,
          7,
          6
        ],
        [
          8,
          8,
          6,
          7,
          4,
          6
        ],
        [
          8,
          1,
          8,
          11,
          10,
          10
        ],
        [
          7,
          5,
          8,
          11,
          1,
          7
        ],
        [
          9,
          7,
          7,
          10,
          12,
          1
        ],
        [
          6,
          7,
          2,
          2,
          12,
          8
        ],
        [
          6,
          6,
          4,
          6,
          9,
          8
        ],
        [
          10,
          12,
          1,
          9,
          5,
          2
        ],
        [
          2,
          11,
          5,
          12,
          5,
          12
        ],
        [
          1,
          11,
          6,
          1,
          6,
          12
        ],
        [
          5,
          4,
          9,
          8,
          11,
          11
        ],
        [
          12,
          2,
          11,
          5,
          2,
          11
        ],
        [
          4,
          9,
          4,
          2,
          8,
          4
        ],
        [
          9,
          5,
          10,
          6,
          8,
          9
        ],
        [
          11,
          1,
          5,
          4,
          9,
          7
        ],
        [
          1,
          8,
          1,
          7,
          4,
          5
        ],
        [
          5,
          12,
          12,
          9,
          1,
          1
        ],
        [
          2,
          6,
          6,
          12,
          10,
          10
        ],
        [
          8,
          2,
          7,
          8,
          7,
          6
        ],
        [
          10,
          9,
          2,
          1,
          2,
          9
        ],
        [
          7,
          10,
          9,
          10,
          6,
          4
        ],
        [
          12,
          4,
          8,
          11,
          11,
          2
        ]
      ],
      "weights": [
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ]
      ],
      "drop_weights": [
        [
          7101,
          5000,
          6199,
          7800,
          7799,
          11900
        ],
        [
          16902,
          14599,
          20598,
          19800,
          16398,
          27300
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          33003,
          45995,
          43596,
          51000,
          70093,
          80000
        ],
        [
          91209,
          85291,
          77692,
          80200,
          102490,
          111900
        ],
        [
          78608,
          81592,
          86391,
          100000,
          110989,
          104800
        ],
        [
          95810,
          95490,
          101590,
          135200,
          111489,
          91800
        ],
        [
          99210,
          101690,
          96590,
          94400,
          119788,
          99700
        ],
        [
          114111,
          113989,
          147285,
          133200,
          129487,
          118000
        ],
        [
          134413,
          147285,
          139786,
          142300,
          110489,
          141400
        ],
        [
          155216,
          143386,
          136087,
          113000,
          104690,
          108500
        ],
        [
          174417,
          165683,
          144186,
          123100,
          116288,
          104700
        ]
      ],
      "reel_lengths": [
        300,
        300,
        300,
        300,
        300,
        300
      ]
    },
    {
      "symbols": [
        [
          12,
          12,
          12,
          12,
          11,
          11
        ],
        [
          12,
          11,
          12,
          11,
          12,
          12
        ],
        [
          11,
          11,
          10,
          10,
          10,
          10
        ],
        [
          10,
          10,
          10,
          9,
          10,
          10
        ],
        [
          9,
          10,
          11,
          9,
          9,
          8
        ],
        [
          9,
          8,
          9,
          6,
          6,
          9
        ],
        [
          8,
          12,
          8,
          12,
          11,
          11
        ],
        [
          12,
          12,
          8,
          11,
          12,
          12
        ],
        [
          11,
          11,
          12,
          10,
          12,
          12
        ],
        [
          10,
          9,
          10,
          7,
          10,
          10
        ],
        [
          5,
          10,
          11,
          9,
          9,
          8
        ],
        [
          9,
          8,
          9,
          6,
          8,
          8
        ],
        [
          8,
          6,
          9,
          12,
          11,
          11
        ],
        [
          8,
          12,
          8,
          11,
          6,
          11
        ],
        [
          12,
          11,
          12,
          10,
          12,
          12
        ],
        [
          11,
          11,
          10,
          7,
          10,
          10
        ],
        [
          10,
          11,
          11,
          7,
          9,
          9
        ],
        [
          9,
          10,
          11,
          9,
          8,
          8
        ],
        [
          7,
          9,
          9,
          12,
          8,
          6
        ],
        [
          8,
          12,
          9,
          11,
          11,
          6
        ],
        [
          12,
          8,
          12,
          10,
          12,
          11
        ],
        [
          12,
          6,
          12,
          6,
          10,
          11
        ],
        [
          11,
          11,
          10,
          7,
          9,
          12
        ],
        [
          10,
          10,
          11,
          9,
          6,
          10
        ],
        [
          9,
          9,
          8,
          12,
          6,
          8
        ],
        [
          8,
          12,
          8,
          11,
          11,
          9
        ],
        [
          5,
          8,
          9,
          10,
          12,
          6
        ],
        [
          12,
          6,
          12,
          6,
          10,
          11
        ],
        [
          12,
          11,
          10,
          6,
          9,
          12
        ],
        [
          11,
          11,
          11,
          9,
          8,
          12
        ],
        [
          11,
          10,
          7,
          12,
          8,
          10
        ],
        [
          10,
          12,
          6,
          11,
          11,
          8
        ],
        [
          9,
          8,
          9,
          10,
          12,
          8
        ],
        [
          8,
          8,
          12,
          5,
          12,
          11
        ],
        [
          8,
          9,
          12,
          6,
          10,
          11
        ],
        [
          12,
          11,
          12,
          6,
          9,
          12
        ],
        [
          11,
          10,
          10,
          12,
          6,
          10
        ],
        [
          10,
          10,
          10,
          12,
          6,
          9
        ],
        [
          9,
          12,
          11,
          11,
          11,
          9
        ],
        [
          7,
          6,
          9,
          10,
          12,
          8
        ],
        [
          6,
          6,
          6,
          9,
          10,
          11
        ],
        [
          12,
          11,
          12,
          7,
          9,
          12
        ],
        [
          12,
          9,
          7,
          5,
          9,
          10
        ],
        [
          11,
          10,
          10,
          12,
          8,
          10
        ],
        [
          10,
          12,
          11,
          12,
          11,
          6
        ],
        [
          9,
          8,
          9,
          11,
          11,
          8
        ],
        [
          8,
          7,
          8,
          10,
          12,
          11
        ],
        [
          7,
          11,
          12,
          10,
          10,
          12
        ],
        [
          12,
          11,
          6,
          9,
          9,
          9
        ],
        [
          11,
          10,
          10,
          9,
          9,
          10
        ],
        [
          11,
          10,
          11,
          12,
          6,
          10
        ],
        [
          10,
          12,
          9,
          12,
          11,
          6
        ],
        [
          9,
          12,
          8,
          11,
          12,
          11
        ],
        [
          9,
          9,
          8,
          10,
          10,
          11
        ],
        [
          12,
          11,
          12,
          10,
          7,
          12
        ],
        [
          6,
          8,
          12,
          9,
          8,
          5
        ],
        [
          11,
          10,
          10,
          6,
          5,
          5
        ],
        [
          10,
          5,
          10,
          12,
          11,
          10
        ],
        [
          10,
          5,
          11,
          11,
          11,
          6
        ],
        [
          8,
          12,
          9,
          11,
          12,
          11
        ],
        [
          12,
          12,
          5,
          10,
          12,
          12
        ],
        [
          12,
          11,
          5,
          9,
          10,
          8
        ],
        [
          11,
          10,
          12,
          7,
          10,
          9
        ],
        [
          5,
          9,
          10,
          12,
          8,
          10
        ],
        [
          10,
          9,
          11,
          6,
          8,
          6
        ],
        [
          8,
          6,
          9,
          6,
          11,
          11
        ],
        [
          8,
          12,
          9,
          11,
          11,
          12
        ],
        [
          12,
          11,
          7,
          10,
          12,
          8
        ],
        [
          11,
          10,
          7,
          5,
          10,
          9
        ],
        [
          6,
          7,
          12,
          12,
          7,
          10
        ],
        [
          10,
          8,
          11,
          9,
          6,
          7
        ],
        [
          9,
          5,
          11,
          8,
          6,
          11
        ],
        [
          7,
          12,
          10,
          11,
          11,
          11
        ],
        [
          12,
          12,
          9,
          10,
          12,
          12
        ],
        [
          11,
          10,
          9,
          7,
          10,
          9
        ],
        [
          5,
          11,
          9,
          12,
          7,
          10
        ],
        [
          10,
          8,
          12,
          12,
          9,
          5
        ],
        [
          10,
          8,
          11,
          8,
          5,
          6
        ],
        [
          6,
          9,
          10,
          11,
          11,
          6
        ],
        [
          12,
          9,
          10,
          10,
          12,
          12
        ],
        [
          11,
          12,
          6,
          5,
          10,
          12
        ],
        [
          11,
          10,
          6,
          9,
          7,
          12
        ],
        [
          9,
          10,
          12,
          12,
          7,
          11
        ],
        [
          10,
          11,
          11,
          7,
          9,
          10
        ],
        [
          5,
          7,
          5,
          11,
          11,
          8
        ],
        [
          12,
          6,
          10,
          10,
          12,
          8
        ],
        [
          7,
          12,
          8,
          10,
          10,
          7
        ],
        [
          7,
          5,
          7,
          5,
          5,
          12
        ],
        [
          11,
          5,
          12,
          5,
          6,
          12
        ],
        [
          10,
          11,
          11,
          12,
          8,
          11
        ],
        [
          9,
          10,
          11,
          11,
          11,
          10
        ],
        [
          12,
          10,
          10,
          11,
          11,
          5
        ],
        [
          5,
          12,
          6,
          10,
          11,
          9
        ],
        [
          6,
          7,
          6,
          9,
          12,
          8
        ],
        [
          6,
          7,
          12,
          9,
          10,
          8
        ],
        [
          11,
          11,
          5,
          12,
          9,
          11
        ],
        [
          10,
          6,
          5,
          6,
          9,
          12
        ],
        [
          12,
          10,
          10,
          11,
          5,
          10
        ],
        [
          8,
          12,
          11,
          10,
          11,
          9
        ],
        [
          9,
          8,
          8,
          8,
          11,
          6
        ],
        [
          5,
          9,
          12,
          7,
          12,
          5
        ],
        [
          5,
          11,
          7,
          12,
          10,
          11
        ],
        [
          11,
          6,
          9,
          12,
          6,
          12
        ],
        [
          12,
          10,
          10,
          12,
          8,
          10
        ],
        [
          10,
          12,
          11,
          11,
          7,
          7
        ],
        [
          7,
          5,
          8,
          10,
          11,
          9
        ],
        [
          8,
          9,
          12,
          6,
          12,
          5
        ],
        [
          6,
          11,
          7,
          6,
          10,
          11
        ],
        [
          11,
          6,
          5,
          8,
          6,
          12
        ],
        [
          11,
          6,
          10,
          12,
          8,
          10
        ],
        [
          12,
          12,
          11,
          11,
          5,
          6
        ],
        [
          10,
          10,
          6,
          10,
          5,
          4
        ],
        [
          8,
          8,
          12,
          10,
          12,
          7
        ],
        [
          7,
          11,
          12,
          9,
          11,
          11
        ],
        [
          9,
          11,
          8,
          7,
          10,
          11
        ],
        [
          11,
          7,
          10,
          12,
          8,
          12
        ],
        [
          12,
          12,
          11,
          11,
          8,
          10
        ],
        [
          10,
          12,
          9,
          8,
          7,
          5
        ],
        [
          4,
          10,
          7,
          10,
          12,
          7
        ],
        [
          8,
          8,
          12,
          5,
          11,
          8
        ],
        [
          6,
          8,
          8,
          6,
          11,
          8
        ],
        [
          11,
          11,
          10,
          12,
          10,
          11
        ],
        [
          12,
          5,
          11,
          11,
          10,
          11
        ],
        [
          10,
          12,
          9,
          9,
          6,
          12
        ],
        [
          10,
          12,
          7,
          9,
          12,
          10
        ],
        [
          4,
          10,
          12,
          10,
          9,
          4
        ],
        [
          5,
          7,
          12,
          7,
          11,
          6
        ],
        [
          5,
          7,
          10,
          7,
          5,
          9
        ],
        [
          12,
          11,
          11,
          11,
          10,
          9
        ],
        [
          11,
          9,
          6,
          11,
          7,
          11
        ],
        [
          11,
          12,
          5,
          12,
          12,
          12
        ],
        [
          10,
          6,
          9,
          12,
          12,
          10
        ],
        [
          7,
          5,
          12,
          10,
          11,
          4
        ],
        [
          9,
          10,
          10,
          8,
          4,
          7
        ],
        [
          12,
          11,
          11,
          5,
          10,
          5
        ],
        [
          6,
          9,
          6,
          5,
          9,
          11
        ],
        [
          11,
          9,
          7,
          11,
          6,
          12
        ],
        [
          11,
          12,
          5,
          11,
          12,
          10
        ],
        [
          11,
          5,
          12,
          11,
          11,
          6
        ],
        [
          7,
          5,
          10,
          12,
          5,
          6
        ],
        [
          12,
          8,
          10,
          10,
          10,
          7
        ],
        [
          4,
          7,
          11,
          6,
          8,
          7
        ],
        [
          8,
          11,
          11,
          4,
          7,
          11
        ],
        [
          9,
          12,
          11,
          8,
          12,
          12
        ],
        [
          11,
          6,
          12,
          11,
          11,
          10
        ],
        [
          10,
          10,
          12,
          12,
          6,
          10
        ],
        [
          12,
          8,
          8,
          12,
          6,
          4
        ],
        [
          7,
          9,
          10,
          10,
          10,
          5
        ],
        [
          4,
          7,
          6,
          10,
          10,
          11
        ],
        [
          9,
          7,
          5,
          5,
          12,
          11
        ],
        [
          11,
          12,
          7,
          11,
          11,
          11
        ],
        [
          10,
          6,
          7,
          11,
          4,
          12
        ],
        [
          12,
          6,
          12,
          12,
          4,
          12
        ],
        [
          8,
          10,
          8,
          4,
          9,
          9
        ],
        [
          5,
          11,
          9,
          8,
          10,
          8
        ],
        [
          5,
          9,
          4,
          8,
          12,
          5
        ],
        [
          11,
          12,
          10,
          6,
          11,
          11
        ],
        [
          6,
          8,
          11,
          11,
          7,
          6
        ],
        [
          12,
          8,
          12,
          11,
          8,
          6
        ],
        [
          7,
          4,
          5,
          12,
          9,
          12
        ],
        [
          7,
          4,
          5,
          9,
          5,
          10
        ],
        [
          4,
          5,
          8,
          7,
          12,
          9
        ],
        [
          11,
          12,
          9,
          5,
          12,
          9
        ],
        [
          9,
          11,
          6,
          10,
          12,
          8
        ],
        [
          12,
          10,
          6,
          11,
          11,
          4
        ],
        [
          12,
          9,
          12,
          11,
          10,
          12
        ],
        [
          6,
          7,
          10,
          12,
          5,
          10
        ],
        [
          8,
          5,
          11,
          4,
          9,
          5
        ],
        [
          8,
          12,
          9,
          4,
          9,
          11
        ],
        [
          10,
          11,
          7,
          9,
          6,
          7
        ],
        [
          11,
          10,
          4,
          6,
          7,
          4
        ],
        [
          12,
          6,
          4,
          6,
          11,
          12
        ],
        [
          12,
          9,
          12,
          12,
          8,
          8
        ],
        [
          12,
          9,
          8,
          11,
          10,
          6
        ],
        [
          4,
          12,
          6,
          7,
          10,
          6
        ],
        [
          4,
          12,
          7,
          10,
          4,
          9
        ],
        [
          5,
          7,
          9,
          8,
          12,
          11
        ],
        [
          6,
          6,
          9,
          9,
          7,
          4
        ],
        [
          6,
          8,
          12,
          12,
          6,
          10
        ],
        [
          12,
          11,
          5,
          12,
          8,
          10
        ],
        [
          11,
          5,
          11,
          11,
          8,
          8
        ],
        [
          11,
          12,
          11,
          7,
          4,
          8
        ],
        [
          9,
          12,
          8,
          5,
          5,
          12
        ],
        [
          10,
          4,
          10,
          6,
          11,
          5
        ],
        [
          7,
          10,
          12,
          8,
          10,
          7
        ],
        [
          12,
          8,
          6,
          12,
          7,
          7
        ],
        [
          5,
          6,
          6,
          11,
          9,
          4
        ],
        [
          5,
          6,
          5,
          10,
          6,
          4
        ],
        [
          9,
          12,
          7,
          4,
          4,
          11
        ],
        [
          9,
          11,
          8,
          9,
          4,
          9
        ],
        [
          8,
          11,
          8,
          5,
          5,
          9
        ],
        [
          8,
          10,
          12,
          12,
          12,
          5
        ],
        [
          12,
          7,
          12,
          12,
          11,
          12
        ],
        [
          10,
          4,
          4,
          11,
          10,
          7
        ],
        [
          10,
          4,
          4,
          11,
          7,
          7
        ],
        [
          7,
          12,
          10,
          7,
          7,
          6
        ],
        [
          11,
          5,
          11,
          6,
          6,
          8
        ],
        [
          4,
          10,
          11,
          4,
          8,
          11
        ],
        [
          4,
          9,
          5,
          4,
          11,
          10
        ],
        [
          12,
          7,
          9,
          12,
          12,
          5
        ],
        [
          6,
          8,
          12,
          11,
          9,
          5
        ],
        [
          6,
          8,
          7,
          11,
          5,
          12
        ],
        [
          9,
          12,
          10,
          5,
          6,
          4
        ],
        [
          8,
          5,
          10,
          7,
          8,
          6
        ],
        [
          10,
          6,
          4,
          9,
          10,
          9
        ],
        [
          12,
          6,
          4,
          12,
          10,
          8
        ],
        [
          7,
          10,
          6,
          10,
          4,
          10
        ],
        [
          5,
          11,
          12,
          10,
          5,
          10
        ],
        [
          11,
          12,
          9,
          10,
          12,
          11
        ],
        [
          9,
          12,
          5,
          11,
          11,
          12
        ],
        [
          9,
          7,
          7,
          8,
          9,
          12
        ],
        [
          12,
          4,
          7,
          8,
          9,
          6
        ],
        [
          7,
          9,
          8,
          12,
          7,
          7
        ],
        [
          4,
          5,
          12,
          6,
          8,
          9
        ],
        [
          10,
          11,
          6,
          5,
          6,
          11
        ],
        [
          6,
          11,
          5,
          11,
          5,
          11
        ],
        [
          8,
          12,
          9,
          9,
          5,
          8
        ],
        [
          12,
          4,
          11,
          7,
          12,
          5
        ],
        [
          12,
          8,
          11,
          12,
          11,
          4
        ],
        [
          5,
          10,
          8,
          6,
          4,
          4
        ],
        [
          11,
          10,
          10,
          8,
          6,
          10
        ],
        [
          7,
          5,
          5,
          11,
          9,
          6
        ],
        [
          6,
          12,
          6,
          4,
          7,
          7
        ],
        [
          6,
          7,
          4,
          5,
          7,
          7
        ],
        [
          8,
          7,
          12,
          12,
          12,
          9
        ],
        [
          4,
          9,
          9,
          7,
          4,
          8
        ],
        [
          5,
          6,
          9,
          9,
          10,
          5
        ],
        [
          12,
          8,
          8,
          9,
          10,
          12
        ],
        [
          10,
          12,
          7,
          11,
          8,
          12
        ],
        [
          10,
          5,
          7,
          6,
          11,
          10
        ],
        [
          11,
          4,
          10,
          5,
          9,
          10
        ],
        [
          8,
          4,
          12,
          12,
          9,
          9
        ],
        [
          8,
          9,
          6,
          8,
          4,
          11
        ],
        [
          7,
          9,
          8,
          4,
          12,
          8
        ],
        [
          9,
          12,
          4,
          11,
          12,
          6
        ],
        [
          9,
          12,
          11,
          11,
          8,
          4
        ],
        [
          5,
          12,
          10,
          7,
          6,
          5
        ],
        [
          12,
          10,
          5,
          7,
          6,
          5
        ],
        [
          4,
          10,
          9,
          10,
          5,
          11
        ],
        [
          4,
          2,
          8,
          9,
          11,
          8
        ],
        [
          11,
          11,
          4,
          6,
          11,
          9
        ],
        [
          6,
          11,
          11,
          12,
          8,
          6
        ],
        [
          10,
          12,
          6,
          4,
          2,
          12
        ],
        [
          10,
          7,
          6,
          5,
          4,
          4
        ],
        [
          10,
          8,
          12,
          5,
          10,
          7
        ],
        [
          5,
          8,
          7,
          10,
          7,
          2
        ],
        [
          7,
          6,
          5,
          10,
          5,
          10
        ],
        [
          7,
          5,
          10,
          8,
          5,
          8
        ],
        [
          11,
          12,
          9,
          7,
          6,
          6
        ],
        [
          12,
          9,
          8,
          11,
          9,
          9
        ],
        [
          12,
          7,
          2,
          6,
          4,
          12
        ],
        [
          4,
          2,
          7,
          2,
          4,
          11
        ],
        [
          6,
          4,
          11,
          4,
          11,
          7
        ],
        [
          5,
          6,
          4,
          4,
          11,
          5
        ],
        [
          2,
          12,
          12,
          8,
          8,
          5
        ],
        [
          11,
          5,
          10,
          8,
          12,
          2
        ],
        [
          8,
          7,
          10,
          9,
          12,
          4
        ],
        [
          9,
          2,
          10,
          12,
          7,
          4
        ],
        [
          6,
          11,
          5,
          5,
          2,
          1
        ],
        [
          12,
          9,
          11,
          5,
          10,
          7
        ],
        [
          5,
          12,
          6,
          2,
          8,
          9
        ],
        [
          11,
          4,
          4,
          1,
          6,
          2
        ],
        [
          11,
          8,
          8,
          7,
          9,
          11
        ],
        [
          4,
          6,
          12,
          7,
          7,
          6
        ],
        [
          2,
          10,
          7,
          9,
          5,
          12
        ],
        [
          7,
          5,
          5,
          12,
          2,
          8
        ],
        [
          7,
          12,
          2,
          11,
          10,
          10
        ],
        [
          8,
          4,
          9,
          10,
          10,
          9
        ],
        [
          9,
          8,
          11,
          10,
          10,
          9
        ],
        [
          1,
          11,
          11,
          6,
          6,
          5
        ],
        [
          12,
          9,
          7,
          8,
          8,
          2
        ],
        [
          10,
          1,
          5,
          12,
          9,
          4
        ],
        [
          4,
          5,
          5,
          12,
          2,
          7
        ],
        [
          2,
          6,
          2,
          11,
          1,
          6
        ],
        [
          5,
          12,
          1,
          2,
          7,
          1
        ],
        [
          6,
          10,
          12,
          9,
          4,
          12
        ],
        [
          8,
          10,
          12,
          1,
          12,
          8
        ],
        [
          9,
          10,
          4,
          6,
          12,
          10
        ],
        [
          10,
          2,
          8,
          4,
          5,
          10
        ],
        [
          10,
          7,
          8,
          5,
          5,
          10
        ],
        [
          12,
          12,
          9,
          11,
          11,
          11
        ],
        [
          12,
          8,
          6,
          10,
          6,
          12
        ],
        [
          1,
          6,
          2,
          7,
          2,
          12
        ],
        [
          9,
          5,
          7,
          7,
          4,
          7
        ],
        [
          9,
          5,
          7,
          9,
          1,
          6
        ],
        [
          2,
          9,
          10,
          9,
          9,
          4
        ],
        [
          7,
          4,
          10,
          8,
          7,
          8
        ],
        [
          11,
          11,
          4,
          8,
          7,
          5
        ],
        [
          4,
          1,
          6,
          2,
          8,
          2
        ],
        [
          8,
          2,
          1,
          4,
          11,
          1
        ],
        [
          6,
          7,
          9,
          6,
          11,
          11
        ],
        [
          5,
          12,
          9,
          1,
          5,
          4
        ],
        [
          1,
          4,
          11,
          10,
          12,
          6
        ],
        [
          2,
          9,
          2,
          5,
          9,
          5
        ],
        [
          4,
          8,
          4,
          2,
          2,
          8
        ],
        [
          11,
          1,
          1,
          4,
          8,
          9
        ],
        [
          7,
          2,
          6,
          6,
          10,
          11
        ],
        [
          8,
          11,
          12,
          1,
          4,
          1
        ],
        [
          5,
          6,
          5,
          12,
          1,
          2
        ],
        [
          6,
          7,
          8,
          11,
          6,
          7
        ]
      ],
      "weights": [
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ]
      ],
      "drop_weights": [
        [
          1500,
          6101,
          4600,
          1500,
          7600,
          12198
        ],
        [
          30500,
          29006,
          25997,
          29003,
          7600,
          33593
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          55000,
          51910,
          45795,
          47305,
          65600,
          91582
        ],
        [
          91600,
          99220,
          68693,
          84008,
          94700,
          102280
        ],
        [
          71800,
          87017,
          73293,
          93109,
          113000,
          100780
        ],
        [
          84000,
          82417,
          86991,
          102310,
          87000,
          62587
        ],
        [
          103800,
          65613,
          125188,
          82408,
          137400,
          123675
        ],
        [
          113000,
          128226,
          163384,
          135914,
          117600,
          123675
        ],
        [
          128200,
          177136,
          151085,
          166417,
          113000,
          111478
        ],
        [
          146600,
          111522,
          119088,
          131313,
          143500,
          134373
        ],
        [
          174000,
          161832,
          135886,
          126713,
          113000,
          103779
        ]
      ],
      "reel_lengths": [
        300,
        300,
        300,
        300,
        300,
        300
      ]
    },
    {
      "symbols": [
        [
          12,
          12,
          12,
          12,
          12,
          12
        ],
        [
          11,
          11,
          11,
          11,
          11,
          10
        ],
        [
          10,
          10,
          10,
          10,
          11,
          11
        ],
        [
          9,
          10,
          9,
          10,
          10,
          9
        ],
        [
          9,
          9,
          9,
          9,
          9,
          8
        ],
        [
          8,
          8,
          8,
          7,
          8,
          6
        ],
        [
          12,
          12,
          12,
          12,
          12,
          12
        ],
        [
          12,
          11,
          11,
          11,
          6,
          10
        ],
        [
          11,
          6,
          10,
          8,
          11,
          11
        ],
        [
          10,
          10,
          7,
          10,
          10,
          9
        ],
        [
          9,
          9,
          9,
          9,
          10,
          8
        ],
        [
          8,
          9,
          8,
          9,
          9,
          6
        ],
        [
          6,
          12,
          12,
          12,
          12,
          12
        ],
        [
          12,
          11,
          11,
          11,
          8,
          10
        ],
        [
          11,
          11,
          10,
          7,
          11,
          11
        ],
        [
          10,
          10,
          10,
          10,
          11,
          9
        ],
        [
          9,
          10,
          9,
          5,
          11,
          8
        ],
        [
          8,
          9,
          6,
          9,
          10,
          8
        ],
        [
          8,
          12,
          12,
          12,
          12,
          12
        ],
        [
          12,
          12,
          12,
          11,
          9,
          10
        ],
        [
          12,
          12,
          11,
          7,
          8,
          11
        ],
        [
          11,
          11,
          11,
          10,
          6,
          9
        ],
        [
          10,
          10,
          11,
          6,
          6,
          6
        ],
        [
          9,
          9,
          10,
          9,
          11,
          6
        ],
        [
          6,
          8,
          10,
          12,
          11,
          12
        ],
        [
          8,
          6,
          12,
          11,
          12,
          12
        ],
        [
          12,
          12,
          12,
          7,
          10,
          11
        ],
        [
          11,
          11,
          9,
          10,
          10,
          10
        ],
        [
          10,
          10,
          11,
          10,
          9,
          10
        ],
        [
          9,
          9,
          6,
          9,
          8,
          10
        ],
        [
          7,
          9,
          10,
          12,
          11,
          9
        ],
        [
          6,
          8,
          10,
          11,
          12,
          9
        ],
        [
          6,
          12,
          10,
          7,
          7,
          12
        ],
        [
          12,
          12,
          12,
          8,
          10,
          11
        ],
        [
          11,
          11,
          11,
          10,
          9,
          8
        ],
        [
          10,
          10,
          9,
          9,
          8,
          10
        ],
        [
          9,
          6,
          8,
          12,
          11,
          5
        ],
        [
          7,
          9,
          8,
          11,
          12,
          9
        ],
        [
          5,
          5,
          10,
          5,
          12,
          12
        ],
        [
          12,
          12,
          12,
          7,
          10,
          11
        ],
        [
          11,
          11,
          12,
          7,
          10,
          8
        ],
        [
          11,
          10,
          11,
          10,
          9,
          10
        ],
        [
          11,
          7,
          9,
          12,
          11,
          7
        ],
        [
          10,
          8,
          7,
          12,
          8,
          9
        ],
        [
          9,
          8,
          10,
          11,
          12,
          9
        ],
        [
          12,
          12,
          6,
          9,
          5,
          12
        ],
        [
          8,
          11,
          12,
          6,
          10,
          11
        ],
        [
          8,
          10,
          11,
          10,
          9,
          10
        ],
        [
          11,
          9,
          11,
          8,
          11,
          5
        ],
        [
          10,
          6,
          9,
          8,
          8,
          8
        ],
        [
          9,
          6,
          9,
          12,
          12,
          7
        ],
        [
          12,
          12,
          10,
          11,
          5,
          12
        ],
        [
          5,
          11,
          10,
          11,
          5,
          11
        ],
        [
          5,
          10,
          12,
          10,
          10,
          10
        ],
        [
          11,
          9,
          11,
          9,
          11,
          5
        ],
        [
          10,
          5,
          7,
          6,
          9,
          5
        ],
        [
          10,
          7,
          9,
          6,
          12,
          7
        ],
        [
          12,
          12,
          8,
          12,
          12,
          7
        ],
        [
          7,
          11,
          10,
          12,
          7,
          12
        ],
        [
          6,
          10,
          12,
          11,
          10,
          12
        ],
        [
          11,
          8,
          11,
          10,
          11,
          11
        ],
        [
          11,
          5,
          6,
          9,
          9,
          10
        ],
        [
          10,
          9,
          9,
          9,
          9,
          9
        ],
        [
          12,
          12,
          9,
          5,
          12,
          9
        ],
        [
          9,
          11,
          10,
          12,
          8,
          8
        ],
        [
          8,
          10,
          12,
          11,
          10,
          8
        ],
        [
          6,
          10,
          11,
          10,
          11,
          12
        ],
        [
          11,
          6,
          11,
          8,
          6,
          11
        ],
        [
          10,
          7,
          5,
          9,
          6,
          11
        ],
        [
          12,
          12,
          9,
          5,
          12,
          11
        ],
        [
          7,
          11,
          10,
          12,
          12,
          10
        ],
        [
          9,
          5,
          12,
          11,
          10,
          6
        ],
        [
          6,
          5,
          12,
          11,
          11,
          12
        ],
        [
          11,
          10,
          11,
          10,
          8,
          9
        ],
        [
          10,
          6,
          11,
          7,
          7,
          5
        ],
        [
          12,
          12,
          9,
          9,
          7,
          5
        ],
        [
          5,
          11,
          10,
          9,
          12,
          10
        ],
        [
          8,
          11,
          7,
          12,
          12,
          11
        ],
        [
          7,
          7,
          12,
          11,
          11,
          12
        ],
        [
          11,
          10,
          8,
          11,
          9,
          6
        ],
        [
          10,
          8,
          11,
          11,
          10,
          7
        ],
        [
          12,
          12,
          9,
          10,
          10,
          8
        ],
        [
          9,
          9,
          9,
          10,
          5,
          10
        ],
        [
          9,
          11,
          10,
          12,
          5,
          11
        ],
        [
          7,
          6,
          12,
          6,
          12,
          11
        ],
        [
          7,
          10,
          6,
          8,
          12,
          12
        ],
        [
          11,
          10,
          11,
          11,
          11,
          6
        ],
        [
          11,
          12,
          11,
          11,
          9,
          7
        ],
        [
          12,
          9,
          5,
          10,
          6,
          7
        ],
        [
          10,
          11,
          10,
          12,
          8,
          10
        ],
        [
          8,
          7,
          10,
          5,
          10,
          11
        ],
        [
          5,
          8,
          12,
          7,
          10,
          12
        ],
        [
          5,
          8,
          7,
          6,
          12,
          12
        ],
        [
          11,
          12,
          11,
          11,
          11,
          9
        ],
        [
          12,
          10,
          9,
          11,
          6,
          6
        ],
        [
          10,
          11,
          8,
          12,
          7,
          6
        ],
        [
          10,
          7,
          5,
          10,
          9,
          10
        ],
        [
          6,
          5,
          12,
          7,
          8,
          11
        ],
        [
          9,
          9,
          10,
          5,
          12,
          12
        ],
        [
          9,
          12,
          10,
          8,
          12,
          8
        ],
        [
          12,
          12,
          6,
          11,
          11,
          9
        ],
        [
          11,
          11,
          6,
          12,
          7,
          5
        ],
        [
          11,
          11,
          11,
          10,
          9,
          5
        ],
        [
          10,
          10,
          12,
          9,
          5,
          10
        ],
        [
          8,
          6,
          7,
          7,
          8,
          12
        ],
        [
          6,
          6,
          5,
          8,
          8,
          11
        ],
        [
          12,
          12,
          9,
          11,
          12,
          11
        ],
        [
          7,
          12,
          8,
          12,
          12,
          8
        ],
        [
          11,
          11,
          11,
          10,
          11,
          8
        ],
        [
          10,
          10,
          12,
          6,
          11,
          10
        ],
        [
          10,
          5,
          7,
          9,
          6,
          10
        ],
        [
          5,
          4,
          6,
          5,
          6,
          12
        ],
        [
          12,
          9,
          5,
          11,
          10,
          12
        ],
        [
          6,
          12,
          10,
          12,
          12,
          11
        ],
        [
          11,
          11,
          8,
          10,
          9,
          6
        ],
        [
          8,
          8,
          12,
          10,
          7,
          7
        ],
        [
          10,
          7,
          7,
          6,
          5,
          10
        ],
        [
          9,
          10,
          9,
          9,
          11,
          9
        ],
        [
          12,
          5,
          11,
          11,
          11,
          12
        ],
        [
          7,
          5,
          6,
          12,
          12,
          11
        ],
        [
          11,
          11,
          10,
          7,
          8,
          4
        ],
        [
          5,
          12,
          12,
          10,
          8,
          4
        ],
        [
          10,
          12,
          12,
          8,
          9,
          10
        ],
        [
          4,
          8,
          5,
          5,
          10,
          6
        ],
        [
          12,
          8,
          9,
          11,
          7,
          12
        ],
        [
          8,
          6,
          8,
          12,
          12,
          11
        ],
        [
          11,
          11,
          11,
          12,
          6,
          5
        ],
        [
          6,
          10,
          7,
          10,
          5,
          9
        ],
        [
          10,
          12,
          12,
          4,
          5,
          10
        ],
        [
          10,
          4,
          10,
          7,
          10,
          10
        ],
        [
          12,
          4,
          10,
          7,
          9,
          12
        ],
        [
          12,
          7,
          9,
          11,
          12,
          11
        ],
        [
          11,
          11,
          5,
          12,
          7,
          7
        ],
        [
          11,
          11,
          6,
          10,
          6,
          8
        ],
        [
          7,
          12,
          12,
          5,
          8,
          9
        ],
        [
          7,
          9,
          12,
          6,
          10,
          10
        ],
        [
          5,
          10,
          11,
          8,
          9,
          12
        ],
        [
          12,
          7,
          7,
          11,
          12,
          11
        ],
        [
          4,
          6,
          7,
          12,
          11,
          4
        ],
        [
          11,
          11,
          8,
          10,
          7,
          7
        ],
        [
          11,
          12,
          6,
          9,
          5,
          5
        ],
        [
          9,
          9,
          12,
          4,
          6,
          6
        ],
        [
          6,
          5,
          11,
          8,
          4,
          12
        ],
        [
          12,
          10,
          5,
          8,
          4,
          10
        ],
        [
          12,
          4,
          5,
          12,
          12,
          10
        ],
        [
          8,
          11,
          8,
          12,
          12,
          11
        ],
        [
          11,
          12,
          8,
          12,
          10,
          8
        ],
        [
          11,
          8,
          12,
          11,
          5,
          5
        ],
        [
          9,
          6,
          9,
          11,
          11,
          12
        ],
        [
          4,
          7,
          10,
          10,
          7,
          12
        ],
        [
          4,
          9,
          7,
          6,
          9,
          6
        ],
        [
          12,
          11,
          11,
          4,
          12,
          4
        ],
        [
          5,
          12,
          6,
          12,
          8,
          7
        ],
        [
          11,
          12,
          6,
          9,
          6,
          8
        ],
        [
          11,
          4,
          9,
          11,
          11,
          11
        ],
        [
          6,
          4,
          12,
          10,
          11,
          11
        ],
        [
          10,
          8,
          4,
          10,
          7,
          9
        ],
        [
          10,
          11,
          10,
          5,
          12,
          9
        ],
        [
          12,
          11,
          5,
          5,
          9,
          4
        ],
        [
          12,
          5,
          8,
          12,
          9,
          7
        ],
        [
          8,
          6,
          7,
          11,
          10,
          8
        ],
        [
          11,
          7,
          7,
          9,
          6,
          8
        ],
        [
          6,
          12,
          11,
          4,
          5,
          5
        ],
        [
          9,
          10,
          9,
          4,
          12,
          12
        ],
        [
          5,
          11,
          12,
          7,
          8,
          6
        ],
        [
          12,
          9,
          4,
          7,
          8,
          10
        ],
        [
          7,
          9,
          10,
          12,
          4,
          10
        ],
        [
          8,
          8,
          5,
          11,
          6,
          11
        ],
        [
          4,
          12,
          6,
          11,
          5,
          7
        ],
        [
          11,
          5,
          6,
          10,
          12,
          5
        ],
        [
          5,
          10,
          8,
          6,
          10,
          6
        ],
        [
          12,
          7,
          8,
          6,
          10,
          6
        ],
        [
          9,
          7,
          11,
          12,
          7,
          9
        ],
        [
          7,
          11,
          12,
          9,
          7,
          12
        ],
        [
          6,
          6,
          9,
          5,
          4,
          4
        ],
        [
          10,
          4,
          4,
          11,
          12,
          7
        ],
        [
          8,
          8,
          5,
          10,
          8,
          5
        ],
        [
          8,
          9,
          10,
          8,
          9,
          8
        ],
        [
          12,
          9,
          11,
          8,
          6,
          9
        ],
        [
          12,
          5,
          12,
          12,
          6,
          10
        ],
        [
          12,
          5,
          7,
          6,
          4,
          4
        ],
        [
          6,
          10,
          9,
          7,
          11,
          4
        ],
        [
          5,
          10,
          4,
          11,
          5,
          12
        ],
        [
          9,
          6,
          8,
          4,
          12,
          12
        ],
        [
          9,
          6,
          11,
          9,
          9,
          11
        ],
        [
          10,
          12,
          10,
          12,
          9,
          10
        ],
        [
          12,
          11,
          12,
          5,
          8,
          10
        ],
        [
          11,
          11,
          9,
          10,
          8,
          6
        ],
        [
          7,
          11,
          9,
          10,
          10,
          9
        ],
        [
          4,
          8,
          7,
          10,
          5,
          7
        ],
        [
          5,
          7,
          5,
          4,
          7,
          11
        ],
        [
          10,
          7,
          6,
          12,
          4,
          11
        ],
        [
          12,
          12,
          11,
          8,
          4,
          8
        ],
        [
          11,
          4,
          12,
          6,
          11,
          5
        ],
        [
          6,
          10,
          4,
          11,
          11,
          4
        ],
        [
          7,
          5,
          4,
          9,
          12,
          6
        ],
        [
          4,
          9,
          7,
          5,
          12,
          9
        ],
        [
          4,
          8,
          8,
          5,
          12,
          12
        ],
        [
          12,
          6,
          10,
          12,
          6,
          7
        ],
        [
          8,
          12,
          5,
          7,
          5,
          8
        ],
        [
          11,
          4,
          6,
          6,
          7,
          5
        ],
        [
          10,
          10,
          11,
          9,
          7,
          5
        ],
        [
          10,
          9,
          12,
          9,
          10,
          6
        ],
        [
          7,
          7,
          7,
          11,
          9,
          6
        ],
        [
          12,
          7,
          7,
          12,
          4,
          4
        ],
        [
          5,
          11,
          9,
          4,
          11,
          11
        ],
        [
          9,
          11,
          10,
          7,
          5,
          11
        ],
        [
          9,
          12,
          10,
          7,
          8,
          10
        ],
        [
          6,
          5,
          6,
          8,
          10,
          8
        ],
        [
          6,
          4,
          6,
          5,
          10,
          8
        ],
        [
          12,
          4,
          5,
          12,
          6,
          7
        ],
        [
          12,
          8,
          5,
          6,
          7,
          7
        ],
        [
          8,
          6,
          8,
          6,
          12,
          9
        ],
        [
          8,
          12,
          12,
          4,
          9,
          9
        ],
        [
          5,
          12,
          12,
          11,
          9,
          12
        ],
        [
          7,
          5,
          11,
          10,
          11,
          10
        ],
        [
          11,
          10,
          11,
          10,
          11,
          5
        ],
        [
          11,
          10,
          9,
          12,
          6,
          4
        ],
        [
          4,
          6,
          9,
          12,
          8,
          4
        ],
        [
          10,
          9,
          4,
          8,
          8,
          7
        ],
        [
          10,
          8,
          4,
          8,
          4,
          7
        ],
        [
          9,
          7,
          8,
          11,
          4,
          12
        ],
        [
          6,
          11,
          10,
          11,
          5,
          9
        ],
        [
          8,
          5,
          6,
          9,
          5,
          8
        ],
        [
          7,
          5,
          6,
          12,
          10,
          5
        ],
        [
          12,
          4,
          7,
          12,
          6,
          10
        ],
        [
          12,
          8,
          7,
          5,
          12,
          10
        ],
        [
          5,
          9,
          8,
          7,
          7,
          11
        ],
        [
          4,
          6,
          5,
          4,
          7,
          12
        ],
        [
          8,
          11,
          5,
          6,
          5,
          6
        ],
        [
          8,
          10,
          9,
          9,
          5,
          4
        ],
        [
          9,
          4,
          10,
          10,
          11,
          9
        ],
        [
          6,
          8,
          4,
          5,
          8,
          5
        ],
        [
          6,
          8,
          11,
          8,
          4,
          8
        ],
        [
          4,
          12,
          11,
          7,
          10,
          11
        ],
        [
          11,
          6,
          12,
          4,
          6,
          6
        ],
        [
          7,
          9,
          12,
          4,
          9,
          12
        ],
        [
          7,
          7,
          8,
          12,
          12,
          12
        ],
        [
          5,
          4,
          8,
          12,
          8,
          4
        ],
        [
          5,
          10,
          6,
          8,
          11,
          9
        ],
        [
          12,
          11,
          10,
          2,
          10,
          11
        ],
        [
          4,
          5,
          7,
          6,
          6,
          8
        ],
        [
          11,
          5,
          9,
          6,
          4,
          10
        ],
        [
          9,
          6,
          9,
          11,
          7,
          6
        ],
        [
          10,
          12,
          4,
          10,
          9,
          5
        ],
        [
          1,
          7,
          4,
          10,
          9,
          7
        ],
        [
          8,
          7,
          2,
          9,
          12,
          12
        ],
        [
          6,
          9,
          5,
          9,
          8,
          12
        ],
        [
          6,
          9,
          8,
          5,
          2,
          9
        ],
        [
          5,
          8,
          8,
          7,
          10,
          8
        ],
        [
          2,
          2,
          10,
          12,
          5,
          8
        ],
        [
          11,
          4,
          11,
          12,
          4,
          6
        ],
        [
          7,
          6,
          6,
          11,
          12,
          10
        ],
        [
          7,
          11,
          2,
          2,
          11,
          7
        ],
        [
          10,
          10,
          7,
          4,
          7,
          2
        ],
        [
          9,
          12,
          5,
          5,
          6,
          4
        ],
        [
          12,
          12,
          12,
          5,
          6,
          5
        ],
        [
          4,
          9,
          12,
          8,
          1,
          11
        ],
        [
          1,
          7,
          12,
          7,
          5,
          1
        ],
        [
          8,
          8,
          6,
          7,
          11,
          9
        ],
        [
          5,
          11,
          1,
          11,
          12,
          6
        ],
        [
          10,
          11,
          2,
          2,
          4,
          2
        ],
        [
          2,
          2,
          11,
          4,
          8,
          7
        ],
        [
          9,
          5,
          11,
          4,
          10,
          7
        ],
        [
          4,
          1,
          7,
          10,
          9,
          4
        ],
        [
          11,
          10,
          7,
          8,
          9,
          5
        ],
        [
          12,
          4,
          10,
          8,
          2,
          11
        ],
        [
          12,
          6,
          9,
          9,
          7,
          11
        ],
        [
          6,
          6,
          4,
          6,
          1,
          10
        ],
        [
          6,
          9,
          5,
          7,
          5,
          10
        ],
        [
          1,
          9,
          5,
          10,
          10,
          4
        ],
        [
          11,
          1,
          6,
          12,
          8,
          1
        ],
        [
          4,
          12,
          8,
          2,
          11,
          6
        ],
        [
          8,
          12,
          2,
          1,
          4,
          8
        ],
        [
          2,
          2,
          1,
          6,
          2,
          5
        ],
        [
          9,
          4,
          4,
          11,
          6,
          5
        ],
        [
          9,
          8,
          9,
          5,
          7,
          9
        ],
        [
          10,
          5,
          10,
          9,
          7,
          9
        ],
        [
          5,
          10,
          12,
          10,
          12,
          2
        ],
        [
          5,
          7,
          11,
          8,
          5,
          12
        ],
        [
          7,
          7,
          6,
          1,
          9,
          7
        ],
        [
          7,
          4,
          8,
          11,
          6,
          10
        ],
        [
          11,
          6,
          4,
          11,
          2,
          8
        ],
        [
          1,
          6,
          9,
          9,
          1,
          11
        ],
        [
          10,
          2,
          7,
          9,
          10,
          11
        ],
        [
          8,
          10,
          5,
          7,
          12,
          1
        ],
        [
          2,
          10,
          1,
          2,
          8,
          4
        ],
        [
          12,
          1,
          2,
          4,
          8,
          12
        ],
        [
          4,
          8,
          10,
          6,
          4,
          2
        ],
        [
          4,
          8,
          11,
          5,
          11,
          6
        ],
        [
          7,
          5,
          6,
          5,
          9,
          6
        ],
        [
          6,
          11,
          4,
          12,
          10,
          7
        ],
        [
          11,
          11,
          5,
          12,
          7,
          4
        ],
        [
          8,
          4,
          7,
          10,
          6,
          1
        ],
        [
          1,
          7,
          2,
          1,
          5,
          10
        ],
        [
          5,
          2,
          8,
          2,
          1,
          12
        ],
        [
          10,
          9,
          12,
          7,
          4,
          5
        ],
        [
          9,
          1,
          9,
          4,
          12,
          8
        ],
        [
          12,
          5,
          1,
          8,
          11,
          9
        ],
        [
          2,
          12,
          10,
          6,
          2,
          2
        ]
      ],
      "weights": [
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ],
        [
          1,
          1,
          1,
          1,
          1,
          1
        ]
      ],
      "drop_weights": [
        [
          7101,
          5000,
          6199,
          7800,
          7799,
          11900
        ],
        [
          16902,
          14599,
          20598,
          19800,
          16398,
          27300
        ],
        [
          0,
          0,
          0,
          0,
          0,
          0
        ],
        [
          33003,
          45995,
          43596,
          51000,
          70093,
          80000
        ],
        [
          91209,
          85291,
          77692,
          80200,
          102490,
          111900
        ],
        [
          78608,
          81592,
          86391,
          100000,
          110989,
          104800
        ],
        [
          95810,
          95490,
          101590,
          135200,
          111489,
          91800
        ],
        [
          99210,
          101690,
          96590,
          94400,
          119788,
          99700
        ],
        [
          114111,
          113989,
          147285,
          133200,
          129487,
          118000
        ],
        [
          134413,
          147285,
          139786,
          142300,
          110489,
          141400
        ],
        [
          155216,
          143386,
          136087,
          113000,
          104690,
          108500
        ],
        [
          174417,
          165683,
          144186,
          123100,
          116288,
          104700
        ]
      ],
      "reel_lengths": [
        300,
        300,
        300,
        300,
        300,
        300
      ]
    }
  ],
  "runtime_version": "0.0.0.0",
  "rtp_label": 94,
  "source_xlsx": "H0271.xlsx",
  "source_multiplier_xlsx": "H027194A.xlsx"
};
