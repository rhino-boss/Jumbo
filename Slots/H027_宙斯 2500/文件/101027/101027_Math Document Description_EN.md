# Math Document Description — 101027 Zeus 2500

**Scope: Normal Bet**

| Item | Content |
| --- | --- |
| Game ID | 101027 |
| Math files | `H0271.xlsx` (shared natural model); `H027192.xlsx` (RTP 92%), `H027194.xlsx` (RTP 94%) |
| Version | Shared model `7`; RTP models `7.4.0.0` |
| Programs | `Simulator.py` + `config.js` (shared model) + `config_92.js` / `config_94.js` (RTP versions) |
| Reels | 6 reels × 5 rows, fixed window, 30 positions |
| Win evaluation | Pay Anywhere: a regular symbol pays when it appears 8 or more times anywhere on the screen; winning symbols are removed and refilled (Cascade) |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet |

---

## Contents

- [1. Worksheets](#1-worksheets)
  - [1-1 How the program uses the xlsx parameters](#1-1-how-the-program-uses-the-xlsx-parameters)
  - [1-2 Worksheet overview](#1-2-worksheet-overview)
  - [1-3 Overview (shared model)](#1-3-overview-shared-model)
  - [1-4 Parameter](#1-4-parameter)
  - [1-5 Symbol reel sheets](#1-5-symbol-reel-sheets)
  - [1-6 Overview (RTP version files)](#1-6-overview-rtp-version-files)
  - [1-7 Multiplier_Weight](#1-7-multiplier_weight)
  - [1-8 OP Jackpot](#1-8-op-jackpot)
- [2. Game Parameters in the Parameter Sheet](#2-game-parameters-in-the-parameter-sheet)
  - [2-1 weight_base_game_table](#2-1-weight_base_game_table)
  - [2-2 free_game_table_setting](#2-2-free_game_table_setting)
  - [2-3 multiplier_level_C2_C3](#2-3-multiplier_level_c2_c3)
  - [2-4 weight_multiplier (C2 values)](#2-4-weight_multiplier-c2-values)
  - [2-5 weight_multiplier_C3 (C3 values)](#2-5-weight_multiplier_c3-c3-values)
  - [2-6 weight_C2_to_C3_by_initial_count](#2-6-weight_c2_to_c3_by_initial_count)
  - [2-7 weight_C2_to_C3_by_drop_combo](#2-7-weight_c2_to_c3_by_drop_combo)
- [3. Game Logic](#3-game-logic)
  - [3-1 Screen layout](#3-1-screen-layout)
  - [3-2 Symbols and roles](#3-2-symbols-and-roles)
  - [3-3 Flow of a single spin](#3-3-flow-of-a-single-spin)
  - [3-4 Win evaluation](#3-4-win-evaluation)
  - [3-5 Cascade and C3 upgrade](#3-5-cascade-and-c3-upgrade)
  - [3-6 Multiplier calculation](#3-6-multiplier-calculation)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 Complete flow of one paid game](#3-8-complete-flow-of-one-paid-game)
  - [3-9 Key rules](#3-9-key-rules)
- [4. Card System](#4-card-system)
  - [4-1 Purpose](#4-1-purpose)
  - [4-2 Card structure](#4-2-card-structure)
  - [4-3 Acceptance flow of one game](#4-3-acceptance-flow-of-one-game)
  - [4-4 Retry limit and weight calibration](#4-4-retry-limit-and-weight-calibration)
  - [4-5 Notes](#4-5-notes)

---

## 1. Worksheets

### 1-1 How the program uses the xlsx parameters

The math documents are split into two kinds of workbooks: the **shared natural model** (`H0271.xlsx`: reels, stop weights, paytable, table selection, multiplier symbol settings and Free Game spin counts, shared by both RTP versions) and the **RTP version files** (`H027192.xlsx` / `H027194.xlsx`: version, card weights, SCR). Three points are needed to map worksheet fields to program behaviour:

1. **Only relative weight matters.**
   Every field labelled Weight is a relative weight; it need not be a probability or sum to 100%. The program draws a random value within the sum of the group and maps it to an item in proportion to its weight. **The sum of each group is its denominator**, so raising one item also dilutes the others. The exception is the C2→C3 conversion weights in 2-6 and 2-7, whose denominator is fixed at 10,000.

2. **The program reads configs converted from the xlsx.**
   `Simulator.py` loads `config.js` (shared model) and `config_92.js` / `config_94.js` (RTP version files); the RTP configs point to `config.js` through their `base_config` field. Fields marked "used ✅" in this document are carried into the configs and affect the simulation.

3. **Not every field is used by the program.**
   The symbol count statistics on the left of each reel sheet and the text `Symbol` columns are for checking only and are not read. Each section below states which fields are used.

### 1-2 Worksheet overview

**Shared natural model `H0271.xlsx`**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Basic specification, Free Game spin settings, paytable | Cost, win evaluation, Scatter pay, Free Game spins | ✅ partly |
| `Parameter` | Base Game table selection weights, Free Game reel table allocation, multiplier levels, C2/C3 value weights, C2→C3 conversion weights | Table selection, multiplier symbols | ✅ |
| `BG_Symbol`, `BG_Symbol (2)`, `BG_Symbol (3)` | Three Base Game reel sets with stop weights | Base Game initial screen and cascade refill | ✅ |
| `FG_Symbol`, `FG_Symbol (2)`, `FG_Symbol (3)` | Three Free Game reel sets with stop weights | Free Game initial screen and cascade refill | ✅ (`FG_Symbol (3)` is allocated 0 spins and never used) |

**RTP version files `H027192.xlsx` / `H027194.xlsx` (identical structure)**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Version, RTP breakdown | Version check, output file name | ✅ version |
| `Multiplier_Weight` | Base Game / Free Game card weights | Acceptance / retry of each game result | ✅ |
| `OP Jackpot` | SCR (Scatter spin rate) | Probability conversion in the jackpot module | Only when jackpot simulation is enabled |

### 1-3 Overview (shared model)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model `H0271`, shared model version `7` | ✅ version check |
| Base Bet | Bet base 100 | ✅ |
| Coin in table | Normal Bet cost (100 × Price 1) | ✅ |
| Reel # / Visible Window Size | 6 reels, 5 positions each | ✅ screen size |
| Free Spins Setting | Free spins and retrigger spins by number of Scatters (C1); total limit 50 | ✅ (see 3-7) |
| Pay Table | Symbol code, Id, C1 pays for 4 / 5 / 6, regular symbol pays for 8~9 / 10~11 / 12+ (per 100-credit bet) | ✅ win evaluation |

**Pay Table (per 100-credit bet; divide by 100 for the multiple)**

| Symbol | Id | 4 | 5 | 6 | 8~9 | 10~11 | 12+ |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 (Scatter) | 1 | 300 | 500 | 10000 | — | — | — |
| C2 (Multiplier) | 2 | — | — | — | — | — | — |
| C3 (Super Multiplier) | 3 | — | — | — | — | — | — |
| M1 | 4 | — | — | — | 1000 | 2500 | 5000 |
| M2 | 5 | — | — | — | 250 | 1000 | 2500 |
| M3 | 6 | — | — | — | 200 | 500 | 1500 |
| M4 | 7 | — | — | — | 150 | 200 | 1200 |
| A | 8 | — | — | — | 100 | 150 | 1000 |
| K | 9 | — | — | — | 80 | 120 | 800 |
| Q | 10 | — | — | — | 50 | 100 | 500 |
| J | 11 | — | — | — | 40 | 90 | 400 |
| TE | 12 | — | — | — | 25 | 75 | 200 |

**Coin In**

```
Coin In = bet multiplier × Base Bet
```

All RTP and multiple statistics are expressed as "total win of the game ÷ Coin In".

### 1-4 Parameter

The control panel of the shared model; see [Section 2](#2-game-parameters-in-the-parameter-sheet).

### 1-5 Symbol reel sheets

Three Base Game and three Free Game sheets with identical layout. Each sheet defines one set of six circular reel strips with stop weights.

| Field group | Content | Used |
| --- | --- | --- |
| Left `Symbol` / `Description` / `R1~R6` / `ID` | Symbol counts per reel and the symbol Id map | ❌ check only |
| `Symbol` (`L:Q`) | Reel strips (text), 63 or 64 positions per reel | ❌ for reading |
| `Symbol ID` (`S:X`) | Reel strips (codes) | ✅ actual strips |
| `Symbol Weight` (`Z:AE`) | Stop weight of each reel position | ✅ stop position |

**About `Symbol Weight`**: this is the weight of a **stop position**, not of a symbol. The program draws a reel position by this column and fills the reel with the 5 consecutive positions from there. A symbol's actual frequency therefore depends on how often it appears on the strip and on the weights of those positions.

**Cascade refill**: empty positions are refilled **from the same reel strip**, continuing from the positions above the visible window (the strip is circular). No separate refill weight table is used.

**Roles of the six sheets**

| Sheet | C1 (Scatter) | C2 (multiplier symbol) | Role |
| --- | --- | --- | --- |
| `BG_Symbol` | 1–2 per reel | none | Regular game; can trigger Free Game |
| `BG_Symbol (2)` | 1–2 per reel | none | Regular game; can trigger Free Game |
| `BG_Symbol (3)` | none | 1 per reel | Multiplier game; cannot trigger Free Game |
| `FG_Symbol` | 1 per reel | 1–2 per reel | Free Game spins; can retrigger |
| `FG_Symbol (2)` | none | 1–2 per reel | Free Game spins; cannot retrigger |
| `FG_Symbol (3)` | 1 per reel | 1–2 per reel | Not used (allocated 0 spins) |

> Multiplier symbols in the Base Game therefore appear only in games that select `BG_Symbol (3)`, and the Free Game can only be triggered from games that select `BG_Symbol` or `BG_Symbol (2)`.
>
> On any reel of any strip, two C1 are at least 6 positions apart (including wrap-around), and the first and last 5 positions hold no C1, so **at most one C1 can be visible on a reel**; a cascade refill never adds a second C1 to a reel that already shows one.

### 1-6 Overview (RTP version files)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model `H027192` / `H027194`, four-part version `7.4.0.0` | ✅ version check, output file name |
| Coin in table | Normal Bet cost and Game RTP | Target |
| Jackpot row | `Bonus RTP`, `Link RTP`, `Total RTP`, `Hit JP Symbol appear rate` | Target |
| Total Pay Back table | Base Game / Free Game pay back, Free Game trigger rate (Hit%) and cycle (Pulls/Hit) | Target |

**Targets of the two RTP versions**

| File | Base Game | Free Game | Game RTP | Bonus RTP | Link RTP | Total RTP | FG cycle |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `H027192.xlsx` | 72% | 20% | 92% | 2% | 2% | 96% | 1/450.83 |
| `H027194.xlsx` | 72% | 22% | 94% | 2% | 0% | 96% | 1/450.83 |

- `Total RTP = Game RTP + Bonus RTP + Link RTP`. Bonus / Link parameters belong to the platform OP Jackpot module and are not part of this model; this model only provides the SCR for conversion (see [1-8](#1-8-op-jackpot)).
- `Hit JP Symbol appear rate` is the NB SCR of the `OP Jackpot` sheet, expressed over the Threshold 10,000,000,000.

### 1-7 Multiplier_Weight

The input of the card system. Layout:

| Column | Header | Use |
| --- | --- | --- |
| A | `Range` | Win multiple range label |
| B | `Weight_NB_BG` | Base Game card weights |
| C | `Weight_NB_FG` | Free Game card weights |

The rows are 64 win multiple ranges (win ÷ Coin In, **left-open, right-closed**). The last row, `Free Game`, is a special card that ignores the amount and only requires the game to trigger the Free Game. Each column sums to 1,000,000,000, so a weight can be read as "the assigned probability of that result × 10⁹". See [Section 4](#4-card-system).

| Item | 92 version | 94 version |
| --- | --- | --- |
| `Weight_NB_BG` | Weighted ranges up to `(200, 250]`; `Free Game` card 2,218,131 | Identical to the 92 version |
| `Weight_NB_FG` | Weighted ranges `(20, 25]` to `(10000, 20000]` (Free Game mean 90.17×) | Same span, Free Game mean 99.18× |

**The two RTP versions differ only in the `Weight_NB_FG` column**, i.e. the Free Game pay distribution. `Weight_NB_BG` and the entire shared model are identical in both versions.

### 1-8 OP Jackpot

Records the SCR (Scatter spin rate) used by the platform jackpot module to convert "the theoretical trigger rate per game" into "the hit probability per spin that contains a Scatter".

| Field | Content |
| --- | --- |
| `Threshold` | 10,000,000,000 (SCR denominator) |
| `NB` | SCR = 4,617,665,500 (same for the 92 and 94 versions) |

SCR definition: **number of spins containing at least one C1 ÷ number of paid games × 10,000,000,000** (the Base Game spin and every Free Game spin each count as one spin), measured from 10⁸ games with the card system on.

**Jackpot probability conversion**

```
Pscatter = SCR ÷ 10,000,000,000
           (average number of spins with at least one C1 per game)

Ptheory  = theoretical trigger probability of a jackpot prize per game
           (derived from the prize's fixed pay back and amount; parameters are in the platform jackpot module)

Phit     = Ptheory ÷ Pscatter
           (conditional probability of a jackpot check on each spin containing C1)
```

Jackpot checks only happen on spins containing C1, so checking with `Phit` (scaled by `Pscatter`) gives a long-run trigger rate equal to `Ptheory`.

---

## 2. Game Parameters in the Parameter Sheet

### 2-1 weight_base_game_table

| Sheet | Weight |
| --- | ---: |
| `BG_Symbol` | 9,698 |
| `BG_Symbol (2)` | 19,298 |
| `BG_Symbol (3)` | 6,110 |

**The first action of every Base Game spin** is to select the reel table with these weights. This decides whether the game is a regular game that can trigger the Free Game (first two tables) or a multiplier game (`BG_Symbol (3)`); it is the most upstream parameter for game feel and Free Game frequency.

### 2-2 free_game_table_setting

| Sheet | free game (initial spins) | retrigger (added spins) |
| --- | ---: | ---: |
| `FG_Symbol` | 6 | 2 |
| `FG_Symbol (2)` | 9 | 3 |
| `FG_Symbol (3)` | 0 | 0 |

These are **spin allocations**, not weights:

- When the Free Game is triggered, 15 spins are awarded: 6 spins on `FG_Symbol` and 9 on `FG_Symbol (2)`, **shuffled** and played in that order.
- Each retrigger adds 5 spins: 2 on `FG_Symbol` and 3 on `FG_Symbol (2)`, shuffled and appended to the remaining spins.
- The total number of spins is limited to 50; spins beyond the limit are not awarded.

### 2-3 multiplier_level_C2_C3

Multiplier level table with 25 levels:

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17–25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Multiplier | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 | 500 | 1000 | 2500 |

**This is an index table**: the columns of 2-4 and 2-5 follow these levels, and a C3 upgrade moves to the next level of this table (see [3-5](#3-5-cascade-and-c3-upgrade)). Levels 17–25 are all 2500, so a C3 that reaches 2500 stays at 2500.

### 2-4 weight_multiplier (C2 values)

When a C2 is generated, its value is drawn with the row of **its reel table** (columns follow the levels of 2-3).

| Reel table | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 | 500 | 1000 | 2500 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol` to `(3)` | 1143 | 961 | 1031 | 1430 | 1822 | 1544 | 935 | 478 | 152 | 205 | 100 | 100 | 75 | 25 | 75 | 75 | 0 |
| `FG_Symbol`, `(2)` | 4340 | 2375 | 1393 | 1151 | 290 | 185 | 128 | 32 | 24 | 16 | 8 | 8 | 20 | 20 | 20 | 20 | 20 |

Levels 18–25 (all 2500) have weight 0.

### 2-5 weight_multiplier_C3 (C3 values)

When a C2 converts to a C3 (see 2-6 and 2-7), the C3 starting value is drawn again with this row.

| Reel table | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 15 | 20 | 25 | 50 | 100 | 250 and above |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol` to `(3)` | 1143 | 961 | 1031 | 1430 | 1822 | 1544 | 935 | 239 | 76 | 102 | 50 | 50 | 37 | 0 |
| `FG_Symbol`, `(2)` | 4340 | 2375 | 1393 | 1151 | 290 | 185 | 128 | 16 | 12 | 8 | 4 | 4 | 10 | 250 / 500 / 1000: 10 each; 2500: 0 |

C3 starting values are capped lower, but each winning cascade upgrades a C3 by one level, up to 2500.

### 2-6 weight_C2_to_C3_by_initial_count

For each C2 on the **initial screen**, the column is selected by the total number of C2 on the initial screen, and each C2 **independently** converts to C3 with probability "weight ÷ 10,000".

| Reel table | 1 | 2 | 3 | 4 | 5 | 6 or more |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`, `BG_Symbol (3)`, `FG_Symbol`, `FG_Symbol (2)` | 4000 | 2600 | 1900 | 1500 | 1300 | 1100 |
| `BG_Symbol (2)` | 800 | 520 | 380 | 300 | 260 | 220 |

### 2-7 weight_C2_to_C3_by_drop_combo

For each C2 added by a **cascade refill**, the column is selected by the current cascade count, and the C2 converts to C3 with probability "weight ÷ 10,000".

| Reel table | Combo 1 | 2 | 3 | 4 | 5+ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `BG_Symbol`, `BG_Symbol (3)`, `FG_Symbol`, `FG_Symbol (2)` | 2000 | 1300 | 950 | 750 | 650 |
| `BG_Symbol (2)` | 400 | 260 | 190 | 150 | 130 |

A C2 is checked for conversion only **once, when it is generated**. A C2 already on the screen is not checked again in later cascades, and a C3 never converts back.

---

## 3. Game Logic

### 3-1 Screen layout

| Item | Value |
| --- | --- |
| Reels | 6 (R1–R6) |
| Positions per reel | 5 (fixed) |
| Total positions | 30 |

Each reel takes 5 consecutive strip positions from its stop; win evaluation and C1 counting use the whole 6 × 5 screen.

### 3-2 Symbols and roles

| Symbol | Id | Description | Role |
| --- | --- | --- | --- |
| `C1` | 1 | Scatter | Counted only; 4 or more on the final screen trigger the Free Game and pay a Scatter award; not part of Pay Anywhere and never removed |
| `C2` | 2 | Multiplier | Carries a fixed multiplier; not part of Pay Anywhere and never removed |
| `C3` | 3 | Super Multiplier | Carries a multiplier that is upgraded one level after each winning cascade; not part of Pay Anywhere and never removed |
| `M1`–`M4` | 4–7 | High symbols | Pay |
| `A`, `K`, `Q`, `J`, `TE` | 8–12 | Low symbols | Pay |

**There is no Wild.** A regular symbol is counted on its own; no symbol substitutes for it.

**C3 is not on the reels.** The strips only hold C2; each generated C2 is checked for conversion to C3 by 2-6 / 2-7.

### 3-3 Flow of a single spin

Base Game and Free Game share the same flow; only the reel table differs.

```
1. Decide the reel table of this spin
      Base Game: drawn by weight_base_game_table
      Free Game: taken from the spin order allocated by free_game_table_setting (see 3-7)
2. For R1–R6: draw a stop position by Symbol Weight and fill the reel with 5 consecutive positions
3. For each C2 on the initial screen:
      draw its value by the table's weight_multiplier
      look up weight_C2_to_C3_by_initial_count by the initial C2 total and check conversion independently;
      a converted C3 draws its starting value by weight_multiplier_C3
4. Cascade loop:
   4-1 Evaluate Pay Anywhere wins (see 3-4)
   4-2 No win → exit the loop
   4-3 Add this round's regular symbol win (before multiplier)
   4-4 Upgrade every C3 that was on the screen before this removal by one level (see 3-5)
   4-5 Remove winning regular symbols; C1, C2 and C3 stay in place
   4-6 Symbols fall; empty positions are refilled from the same strip
          a refilled C2 is checked by weight_C2_to_C3_by_drop_combo using the cascade count
          no second C1 is refilled into a reel that already shows one
   4-7 Back to 4-1
5. Count C1 on the final screen and calculate the Scatter award
6. Sum the multipliers of all C2 and C3 on the final screen and calculate the spin win by 3-6
7. Check Free Game trigger / retrigger
```

### 3-4 Win evaluation

```
For each regular symbol (M1–M4, A, K, Q, J, TE):
    count its number N on the whole 6 × 5 screen
    pays only when N ≥ 8:
        8–9   → column 8~9 of the Pay Table
        10–11 → column 10~11
        12+   → column 12+
    symbol win = Pay Table value ÷ 100 × Coin In
Round win = sum of all winning symbols
```

Key points:

- Position does not matter and symbols need not be adjacent; **only the screen-wide count matters**.
- Several symbols can win on the same screen; each is paid and the wins are added.
- C1, C2 and C3 are not regular symbols and do not take part in win evaluation.

**Scatter award**: after all cascades, the final number of C1 pays 3× (4 C1), 5× (5 C1) or 100× (6 C1) Coin In; 3 or fewer pay nothing. The Scatter award is **not multiplied** by C2 / C3.

### 3-5 Cascade and C3 upgrade

1. Winning regular symbols are removed; C1, C2 and C3 are not removed and stay in place.
2. **On each winning removal, every C3 already on the screen before the removal moves to the next level of the 2-3 table** (e.g. 5 → 6, 50 → 100); a removal with several winning symbols still counts as one upgrade.
3. A C3 that drops in after a removal is not upgraded retroactively; it waits for the next winning removal.
4. A C3 that reaches 2500 stays at 2500. C2 values never change.
5. The remaining symbols fall and the empty positions are refilled from the same strip.
6. Wins are evaluated again after the refill until no regular symbol reaches 8.

### 3-6 Multiplier calculation

Let:

- `R` = total regular symbol win of all cascades in the spin (before multiplier)
- `M_now` = **sum** of all C2 and C3 values on the **final screen** of the spin (added, not multiplied)
- `S` = Scatter award of the spin

**Base Game**

```
C2 / C3 on the final screen (M_now > 0): Base Game win = R × M_now + S
No C2 / C3 on the final screen:          Base Game win = R + S
```

The Base Game multiplier applies to that spin only and is not carried to the next game.

**Free Game (accumulated multiplier)**

Let `M_acc` be the accumulated multiplier, reset to 0 when the Free Game starts:

```
If R > 0 and M_now > 0:     M_acc = M_acc + M_now       (accumulates only on spins with a regular win)
If M_now > 0 and M_acc > 0: spin win = R × M_acc + S    (applies only when this spin ends with a multiplier symbol)
Otherwise:                  spin win = R + S            (paid at 1×; M_acc is kept, not reset)
```

- The multiplier is applied once to the spin's total regular win after all cascades, not round by round.
- A spin with only a Scatter award (`R = 0`) does not accumulate, even if its final screen shows multiplier symbols.
- A winning spin whose final screen has no C2 / C3 is paid at 1× regardless of `M_acc`.
- `M_acc` carries over between spins and is cleared only when the whole Free Game ends.

### 3-7 Free Game

**Trigger**: after all Base Game cascades, **4 or more** C1 on the final screen trigger the Free Game with **15 spins** (same for 4, 5 and 6 C1), plus the Scatter award of 3-4.

**Spin allocation**: the 15 spins consist of 6 `FG_Symbol` spins and 9 `FG_Symbol (2)` spins in shuffled order (see [2-2](#2-2-free_game_table_setting)); each spin uses its allocated reel table.

**Retrigger**: when a Free Game spin ends with **3 or more** C1, **5 spins** are added (2 `FG_Symbol` + 3 `FG_Symbol (2)`, shuffled and appended); 4 or more C1 also pay the Scatter award. The last spin can retrigger.

**Spin limit**: at most **50 spins** per Free Game, including retriggers.

**Accumulated multiplier**: reset to 0 when the Free Game starts and accumulated by 3-6 until the Free Game ends; a retrigger only adds spins and does not clear the multiplier.

> `FG_Symbol (2)` holds no C1, so only `FG_Symbol` spins can retrigger.

### 3-8 Complete flow of one paid game

```
1. Cost: Coin In = bet multiplier × Base Bet
2. Draw a Base Game card (see Section 4)
3. Play one Base Game spin (flow in 3-3) and get the Base Game win
4. If the final screen has 4 or more C1:
       award 15 spins (6 FG_Symbol + 9 FG_Symbol (2), shuffled)
       draw a Free Game card
       play the Free Game:
           accumulated multiplier = 0
           each spin: play on its allocated table → accumulate and pay by 3-6
                      → 3 or more C1 add 5 spins (limited to 50)
5. Total game win = Base Game win + total Free Game win
6. Accept the game or retry according to the card (see 4-3)
```

### 3-9 Key rules

1. **Pay Anywhere only counts screen-wide**; 8 or more of a symbol pay, with no adjacency and no Wild.
2. **C1, C2 and C3 are never removed** and stay until the spin ends.
3. **Multipliers are added, not multiplied**, and applied once to the regular win after all cascades; the Scatter award is not multiplied.
4. **A C3 is upgraded one level per winning removal**; C2 is never upgraded; a newly dropped C3 is not upgraded retroactively.
5. **C2→C3 conversion is checked once at generation**: by the initial C2 total on the initial screen, by the cascade count on refill.
6. **The Base Game multiplier applies to that spin only**; the Free Game multiplier accumulates but applies only when the spin's final screen shows a multiplier symbol.
7. **In the Base Game only `BG_Symbol (3)` shows multiplier symbols**, and that table cannot trigger the Free Game.
8. **The 15 Free Game spins use two reel tables in a fixed proportion, shuffled**, instead of a per-spin table draw.
9. **At most one C1 per reel**; a cascade refill never adds a second one.

---

## 4. Card System

### 4-1 Purpose

The card system **does not change the reel probabilities**. It accepts or retries (rejection sampling) at the level of the whole game result, reshaping the natural distribution into the target distribution. It allows two things to be set directly:

- **the distribution of the game win** (the share of each win range)
- **the Free Game trigger rate**

### 4-2 Card structure

Cards come from `Multiplier_Weight` in two groups:

| Card group | Drawn when | Content |
| --- | --- | --- |
| Base Game cards | At the start of every game | 64 win multiple ranges plus one `Free Game` card |
| Free Game cards | After the Free Game is triggered | 64 win multiple ranges (applied to the total Free Game win) |

| Type | Condition |
| --- | --- |
| Range card (`range`) | The win ÷ Coin In must fall in the range (left-open, right-closed) |
| Free Game card (`free_game`) | Ignores the amount and requires the game to trigger the Free Game; the Base Game win of the triggering spin must also not exceed the upper bound of the highest weighted Base Game range (250×) |

### 4-3 Acceptance flow of one game

```
Start of each game: draw one Base Game card (the card stays fixed during retries)

If a free_game card is drawn:
    repeat the Base Game spin until "final C1 ≥ 4" and "Base Game win ≤ 250×"
    draw one Free Game card
    repeat the whole Free Game until its total win falls in the card's range

If a range card is drawn:
    play one Base Game spin
        Free Game triggered             → reject and retry the whole game
        Base Game win outside the range → reject and retry the whole game
        otherwise                       → accept

Every retry regenerates a complete result with the natural table selection; the retry limit is 10,000 (see 4-4).
```

Key points:

- The check uses the exact multiple (win ÷ Coin In); ranges are **left-open, right-closed**.
- **A range card that triggers the Free Game is always rejected**, so the Free Game trigger rate is set by the weight of the `Free Game` card (1/450.83).
- Free Game retries are done for the whole Free Game, not per spin.

### 4-4 Retry limit and weight calibration

- Each card is retried at most **10,000 times**; at the limit, the last result is kept and counted in the statistics.
- For a card on range `i`, each attempt hits with the range's natural probability `p_i`, so the chance of hitting within 10,000 attempts is `s_i = 1 − (1 − p_i)^10000`. For high-multiple Base Game ranges with low natural probability, `s_i` is clearly below 1, and the result kept on a miss is a natural result.
- The calibration of `Weight_NB_BG` therefore includes this effect: the mean multiple of each range is taken as "`s_i` × range mean multiple + (1 − `s_i`) × natural mean multiple of one spin", so that the Base Game pay back **including the retry limit** equals 72%. Multiplying weights by range mean multiples directly gives a Base Game pay back slightly above 72% (about 72.21%); the difference is the effect of the retry limit.
- The Free Game card ranges have sufficiently high natural probabilities (`s_i ≈ 1`) and are not affected.
- Simulation with the card system on (10⁸ games each): Base Game 71.96% (92 version) and 72.04% (94 version), both within statistical error.

### 4-5 Notes

1. **Card weights are the most direct RTP control.** Changing reels or table selection changes the natural probabilities, but the final distribution is still decided by the cards; changing the screen settings without updating the card weights does not move the total RTP as expected and only raises the retry count.
2. **The retry count is a health indicator.** The simulation report outputs retry statistics and the `Retry Limit Exceeded` count; review them together.
3. **The two RTP versions differ only in `Weight_NB_FG`.** The Base Game cards, the Free Game trigger rate and the shared model are identical for 92 and 94.
4. **The Free Game trigger rate is fixed by the weight of the `Free Game` card.** To change the Free Game cycle, adjust that weight rather than the C1 distribution on the reels.
