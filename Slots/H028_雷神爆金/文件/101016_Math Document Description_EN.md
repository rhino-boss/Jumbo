# Math Document Description — 101016 Thunder Boost 1000

**Scope: Normal Bet**

| Item | Content |
| --- | --- |
| Game ID | 101016 |
| Math files | `H0281.xlsx` (shared natural-probability model); `H028188B.xlsx` (RTP 88%), `H028190B.xlsx` (RTP 90%), `H028192A.xlsx` (RTP 92%), `H028194A.xlsx` (RTP 94%); `H028192A_Bet100.xlsx`, `H028188B_Bet100.xlsx` (standalone models for single bets above $100) |
| Version | Shared model `3`; RTP models `3.5.0.0` (Bet100 included) |
| Companion programs | `Simulator.py` + `config.js` (shared model) + `config_88B.js` / `config_90B.js` / `config_92A.js` / `config_94A.js` / `config_92A_Bet100.js` / `config_88B_Bet100.js` (per RTP version) |
| Board | 6-reel Megaways; up to 5 rows per reel on the main board; 1 Extra Reel cell above each of reels 2–5 (effective window 5-6-6-6-6-5) |
| Win evaluation | Way Game (2,025–32,400 ways), consecutive adjacent reels from the left; cascading removal and refill after each win |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet |

---

## Table of Contents

- [1. Worksheet Guide](#1-worksheet-guide)
  - [1-1 How the program consumes the xlsx parameters](#1-1-how-the-program-consumes-the-xlsx-parameters)
  - [1-2 Worksheet overview](#1-2-worksheet-overview)
  - [1-3 Overview (shared model)](#1-3-overview-shared-model)
  - [1-4 Parameter](#1-4-parameter)
  - [1-5 Symbol reel sheets](#1-5-symbol-reel-sheets)
  - [1-6 Performance Wheel](#1-6-performance-wheel)
  - [1-7 Overview (RTP version files)](#1-7-overview-rtp-version-files)
  - [1-8 Multiplier_Weight](#1-8-multiplier_weight)
  - [1-9 Detail and Detail_Newbie](#1-9-detail-and-detail_newbie)
  - [1-10 OP Jackpot](#1-10-op-jackpot)
- [2. Game Parameters on the Parameter Worksheet](#2-game-parameters-on-the-parameter-worksheet)
  - [2-1 Table Selection Weight - Base Game](#2-1-table-selection-weight---base-game)
  - [2-2 Table Selection Weight - Free Game](#2-2-table-selection-weight---free-game)
  - [2-3 Table Selection Weight - Retrigger](#2-3-table-selection-weight---retrigger)
- [3. Game Logic](#3-game-logic)
  - [3-1 Board and coordinate system](#3-1-board-and-coordinate-system)
  - [3-2 Symbols and roles](#3-2-symbols-and-roles)
  - [3-3 Flow of a single spin](#3-3-flow-of-a-single-spin)
  - [3-4 Win evaluation rules](#3-4-win-evaluation-rules)
  - [3-5 Cascade and gold-frame-to-Wild conversion](#3-5-cascade-and-gold-frame-to-wild-conversion)
  - [3-6 M1 multiplier accumulation and application](#3-6-m1-multiplier-accumulation-and-application)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 Full flow of one paid spin](#3-8-full-flow-of-one-paid-spin)
  - [3-9 Key rules recap](#3-9-key-rules-recap)
- [4. Card System](#4-card-system)
  - [4-1 Purpose](#4-1-purpose)
  - [4-2 Card structure](#4-2-card-structure)
  - [4-3 Per-round decision flow](#4-3-per-round-decision-flow)
  - [4-4 Relation to the Detail worksheets](#4-4-relation-to-the-detail-worksheets)
  - [4-5 Notes](#4-5-notes)

---

## 1. Worksheet Guide

### 1-1 How the program consumes the xlsx parameters

The math documents are split into two kinds of workbooks: the **shared natural-probability model** (`H0281.xlsx`: reels, paytable, size patterns, drops, Free Game spin counts — shared by all RTP versions) and the **RTP version files** (`H0281<RTP><variant>.xlsx`: version number, card weights, SCR). Four points are essential for matching worksheet fields to program behavior:

1. **Weights are relative.**
   Every field labeled Weight is a relative weight; it need not be a probability and need not sum to 100%. The program draws a random value across the total of that weight group and lands on an item in proportion to its weight. **The sum of each weight group is that group's denominator**, so raising a single entry also dilutes every other entry in the same group.

2. **The program reads configs converted from the xlsx.**
   `Simulator.py` and the demo page load `config.js` (shared model) and `config_<RTP><variant>.js` (RTP version file). The xlsx and configs are converted through a fixed mapping (see `Source/xlsx_config_usage_mapping.md` in the project). Fields marked "Used ✅" in this document are the ones that enter the config and affect simulation. The SCR on the `OP Jackpot` worksheet is the only field the simulator reads directly from the xlsx (only when jackpot simulation is enabled).

3. **Gold-framed symbols carry two layers of information.**
   A gold-framed symbol's Id (13–23) equals its base symbol Id + 11. Win evaluation always uses the base symbol's pays; the gold-frame identity only governs the "convert to Wild after winning" behavior. The Mystery symbol (Id 24; gold-framed 25) converts board-wide into the target symbol drawn for that spin once the board settles.

4. **Not every field is consumed by the program.**
   The tally/ratio/average columns on the left of each sheet, and the `Detail` / `Detail_Newbie` and Performance Wheel worksheets, are for design and verification; the program does not read them. Each section below states this explicitly.

### 1-2 Worksheet overview

**Shared model `H0281.xlsx`**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Basic game specs, Free Game spin table, symbol paytable | Cost, win evaluation, FG spin counts | ✅ partial |
| `Parameter` | Three reel-table selection weight groups | Table selection at the start of every spin | ✅ |
| `BG_Symbol`, `BG_Symbol (2)` | Two Base Game reel sets + pattern/conversion/drop weights | BG initial board and cascade refills | ✅ |
| `FG_Symbol`, `FG_Symbol (2)`, `FG_Symbol (3)` | Three Free Game reel sets + pattern/conversion/drop weights | FG initial board and cascade refills | ✅ |
| `BG_Performance Wheel`, `FG_Performance Wheel` | Presentation-side wheel reference | — | ❌ presentation |

**RTP version files `H0281<RTP><variant>.xlsx` (four files plus two `_Bet100` files, all sharing the same structure)**

| Worksheet | Provides | Affects | Used |
| --- | --- | --- | --- |
| `Overview` | Version number, RTP breakdown per bet type | Version check, output file names | ✅ version |
| `Multiplier_Weight` | Card weights for the card system | Accept/redraw of per-round results | ✅ |
| `Detail`, `Detail_Newbie` | Derivation of the card weights (natural distribution + calibration factors) | — | ❌ design |
| `OP Jackpot` | SCR (scatter-spin rate) records | Jackpot probability conversion | ✅ when jackpot simulation is on |

### 1-3 Overview (shared model)

Provides the basic game specification.

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model code `H0281` and the shared-model version (single integer) | ✅ version check |
| Base Bet / Multiway | Bet basis 100 and maximum ways 32,400 | ✅ |
| Coin in table | Cost and multiplier per bet type | ✅ Normal Bet row |
| Reel # / Visible Window Size | 6 reels; effective window 5-6-6-6-6-5 (reels 2–5 include the Extra Reel cell) | ✅ board dimensions |
| Free Spins Setting | Scatter count → free spins: 4 scatters award 10 spins, +2 per additional scatter; total cap 50 | ✅ (see 3-7) |
| Pay Table | Symbol codes, Ids, and pays for 3/4/5/6 of a kind (per 100 credit bet) | ✅ win evaluation |

**Coin In**

```
Coin In = bet multiplier × Base Bet
```

All RTP and multiplier statistics use "total round win ÷ Coin In". Pay Table values are per 100 credit bet, i.e. value ÷ 100 = pay in bet multiples per single way.

### 1-4 Parameter

The shared model's table-selection control panel — three weight groups only. See [Chapter 2](#2-game-parameters-on-the-parameter-worksheet) block by block.

### 1-5 Symbol reel sheets

Two Base Game sheets and three Free Game sheets with identical layout. Each defines "one reel set plus that table's own pattern/conversion/drop weights".

| Field group | Content | Used |
| --- | --- | --- |
| Leftmost `Symbol` / `Description` / `R1~R7` / `ID` (A4:J29) | Symbol lookup table (name ↔ Id) and per-reel tallies | ✅ lookup table; tally columns ❌ verification |
| `Symbol` (M4:S203) | Reel strips as text, 7 strips × 200 cells | ❌ human-readable |
| `Symbol ID` (U4:AA203) | Reel strips as Ids, derived from the lookup table | ✅ actual reels |
| `Symbol Weight` (AC4:AI203) | Stop-position weight for every reel cell | ✅ stop position |
| `MegaWay` (C33:H47) | Reels 1–6 × 15 large-symbol size-pattern weights | ✅ per-reel symbol size layout |
| `MY` (C51:C63) | 13 weights for the Mystery conversion target (index = symbol Id: 0 = Wild, 1 = Scatter, 2–12 = M1–M11) | ✅ one target draw per spin |
| `Post Scatter` (B67:C74) | Weights for the number of Scatters (0–7) placed after the board settles | ✅ Scatter generation |
| `Drop1`–`Drop5` (AL4:AR145) | Cascade refill symbol weights, 7 reels × 26 symbols × 5 stages | ✅ cascade refills |

**About `Symbol Weight`**: this is not a "symbol weight" but a "**stop-position** weight". The program first draws a reel position from this column, then fills the reel from that position following the MegaWay size pattern. A symbol's actual appearance rate therefore depends on how often it appears on the strip, the weights of those positions, and the size-pattern distribution.

**About `Drop1`–`Drop5`**: when cascades open up empty cells, the program **does not pull further symbols off the reel strip — it resamples from this weight table**. The five stages correspond to successive cascade steps. Scatter is not present on the initial reel strips; it enters the board only through Post Scatter and Drops.

**The two BG sheets / three FG sheets** differ only in their weight configurations (gold-frame ratio, multiplier layout, Scatter refill rates); layout and field meanings are identical.

### 1-6 Performance Wheel

Wheel reference for the presentation layer. Not read by the program; affects no probabilities.

### 1-7 Overview (RTP version files)

| Block | Content | Used |
| --- | --- | --- |
| Model / Version | Model code and the four-part version (currently `3.5.0.0`) | ✅ version check, output file names |
| Coin in / Total RTP table | Total RTP per bet type | target values |
| Pay Back breakdown | Normal Bet Base Game / Free Game pay back, Hit%, Pulls/Hit | target values |

**Normal Bet breakdown of the four RTP version files (target values)**

| File | Base Game | Free Game | Game RTP | FG cycle |
| --- | --- | --- | --- | --- |
| `H028188B.xlsx` | 72% | 16% | 88% | 1/375.00 |
| `H028190B.xlsx` | 72% | 18% | 90% | 1/366.67 |
| `H028192A.xlsx` | 72% | 20% | 92% | 1/300.00 |
| `H028194A.xlsx` | 72% | 22% | 94% | 1/300.00 |

The total pay back including platform jackpots is `Game RTP + Bonus RTP + Link RTP`; the Bonus/Link parameters live in the platform OP Jackpot module, not in this model. This model only supplies the SCR used for the conversion (see [1-10](#1-10-op-jackpot)).

### 1-8 Multiplier_Weight

Input of the card system. Layout:

| Column | Header | Purpose |
| --- | --- | --- |
| A | `Range` | Win-multiple interval labels |
| B | `Weight_NB_BG_Newbie` | Base Game card weights for the Newbie profile |
| C | `Weight_NB_FG_Newbie` | Free Game card weights for the Newbie profile |
| D | `Weight_NB_BG` | Base Game card weights for the regular (Oldhand) profile |
| E | `Weight_NB_FG` | Free Game card weights for the regular profile |

The rows are a sequence of win-multiple intervals (win ÷ Coin In, **open on the left, closed on the right**); the final `Free Game` row is a special card that ignores the amount and only requires "this round must trigger Free Game". Every column's weights are calibrated to a total of 1,000,000,000, so a weight can be read directly as "probability of that outcome × 10⁹". Full mechanics in [Chapter 4](#4-card-system).

**The `_Bet100` models (standalone models for single bets above $100)**: `H028192A_Bet100.xlsx` / `H028188B_Bet100.xlsx` share the exact worksheet structure and columns of 92A / 88B; they differ only in the regular profile's Free Game card weights — the win cap drops from 10,000× to **2,000×**: the highest weighted interval is `(1000, 2000]`, with `(2000, 3000]` and `(9000, 10000]` at weight 0; the 20×–200× body keeps the original shape (uniform scale) and the 200×–2,000× tail is scaled up uniformly to rebalance, so the **FG pay back, trigger cycle and average multiple are identical to the original models**. Simulations with single bets above $100 run with the matching `config_92A_Bet100.js` / `config_88B_Bet100.js`; 90B / 94A serve small bets and have no `_Bet100` model.

**Differences across the files**: `Weight_NB_BG` and `Weight_NB_FG` are calibrated per version; **the two Newbie columns (B, C) are identical across all files**; a `_Bet100` model is cell-identical to its base model except for the regular profile's FG card column.

### 1-9 Detail and Detail_Newbie

Derivation worksheets for the `Multiplier_Weight` columns; not read by the program. `Detail` covers the regular profile, `Detail_Newbie` the Newbie profile, with the same layout:

| Block | Content |
| --- | --- |
| `Simulate` side (Cnt / Pay / Hit Rate / Avg. Multi.) | Natural probability of every win interval, measured over 1 billion rounds with the card system off |
| `Calculate` side (Fix Num / Fix Rate / Final Rate / Weight / Hit Rate) | Manual calibration factors (Fix Num) → derivation chain to the calibrated weights |

The tuning loop is: run natural probability with the card system off → fill the `Simulate` side → adjust `Fix Num` → obtain calibrated weights → write into `Multiplier_Weight` → re-run with the card system on to verify.

### 1-10 OP Jackpot

Records the SCR (scatter-spin rate) per profile, letting the platform jackpot module convert "theoretical trigger probability per round" into "decision probability per scatter-bearing spin".

| Field | Content |
| --- | --- |
| `Threshold` | 10,000,000,000 (denominator base of the SCR) |
| `NB_Newbie` | SCR for the Newbie profile (unified across the four files at the 92% file's measured value, 3,647,149,360) |
| `NB` | SCR for the regular profile (measured per version: 88B 3,618,838,430 / 90B 3,621,199,650 / 92A 3,641,035,800 / 94A 3,641,760,160) |

SCR definition: **number of spins containing at least one Scatter ÷ paid rounds × 10,000,000,000** (the Base Game spin and every Free Spin each count as one spin), measured over simulations of 10⁸ rounds or more.

**Jackpot probability conversion**

```
Pscatter = SCR ÷ 10,000,000,000
           (probability that any given spin shows at least one Scatter)

Ptheory  = theoretical trigger probability of a jackpot award per round
           (back-derived from the award's fixed pay back rate and prize;
            parameters live in the platform jackpot module)

Phit     = Ptheory ÷ Pscatter
           (conditional probability of running one jackpot decision on each
            scatter-bearing spin)
```

Jackpot decisions happen only on scatter-bearing spins, so running them at `Phit` (amplified by `Pscatter`) makes the long-run trigger rate equal `Ptheory`. The `_Bet100` models' FG card difference changes the scatter-spin rate by less than 0.5%, so their `OP Jackpot` worksheets carry the base models' SCR values.

---

## 2. Game Parameters on the Parameter Worksheet

Parameter holds three weight groups that control "which reel table each spin uses". This is the most upstream lever on game feel and FG content: the table choice fixes that spin's reels, size patterns, Mystery, Scatter and refill settings as a whole.

### 2-1 Table Selection Weight - Base Game

| Worksheet | Weight |
| --- | --- |
| `BG_Symbol` | 6000 |
| `BG_Symbol (2)` | 4000 |

**The first action of every BG spin** is drawing the reel table from this group (60% / 40%).

### 2-2 Table Selection Weight - Free Game

| Worksheet | Weight |
| --- | --- |
| `FG_Symbol` | 6000 |
| `FG_Symbol (2)` | 4500 |
| `FG_Symbol (3)` | 4500 |

During the Free Game's **initial spins** (those awarded at the trigger), the table is drawn from this group at the start of every spin (40% / 30% / 30%).

### 2-3 Table Selection Weight - Retrigger

| Worksheet | Weight |
| --- | --- |
| `FG_Symbol` | 6000 |
| `FG_Symbol (2)` | 4500 |
| `FG_Symbol (3)` | 4500 |

Spins added by retriggers draw their table from this group instead. The two groups currently hold the same values; keeping them separate preserves the ability to tune them independently.

---

## 3. Game Logic

### 3-1 Board and coordinate system

| Item | Value |
| --- | --- |
| Main board reels | 6 (R1–R6), Megaways variable height, up to 5 rows per reel |
| Extra Reel | one strip of 4 cells, fixed above R2–R5 (one cell each) |
| Effective window | 5-6-6-6-6-5 (the 6th cell of R2–R5 is the Extra Reel cell) |

Internally the program generates the Extra Reel's 4 symbols from a 7th strip and merges them into the top cells of R2–R5; win evaluation and Scatter counting both use the merged board.

### 3-2 Symbols and roles

| Symbol | Id | Description | Role |
| --- | --- | --- | --- |
| `WW` | 0 | Wild | Substitutes for all symbols except Scatter; appears only on R2–R5; carries no pays |
| `C1` | 1 | Scatter | Counted only; carries no pays; cannot be substituted by Wild |
| `M1` | 2 | Top symbol, doubles as the multiplier symbol | Pays; provides multipliers by size on the main board and a fixed multiplier on the Extra Reel |
| `M2`–`M6` | 3–7 | High symbols | Pay |
| `M7`–`M11` (A, K, Q, J, 10) | 8–12 | Low symbols | Pay |
| Gold-framed symbols | 13–23 | Gold-framed versions of the paying symbols (Id = base + 11) | Evaluated as the base symbol; convert to Wild in place after taking part in a win |
| `MY` | 24 (gold-framed 25) | Mystery | Converts board-wide into the target symbol drawn for the spin once the board settles |

Three derived attributes drive the program: **base-symbol mapping** (gold frame −11), **gold-frame flag** (governs Wild conversion), and **payable flag** (`WW` substitutes, `C1` interrupts during evaluation).

### 3-3 Flow of a single spin

BG and FG share the same flow; they differ only in which tables are used and the multiplier's starting value.

```
1. Choose the reel table for this spin
      BG: draw by Table Selection Weight - Base Game
      FG: initial spins draw by the Free Game group,
          retrigger spins by the Retrigger group
2. For R1–R6: draw a size pattern (1x1–1x4 blocks) from that reel's MegaWay
   weights, draw a stop position from Symbol Weight, then fill the reel from
   the strip following the pattern
3. Extra Reel: draw 4 symbols from the 7th strip and merge them into the top
   cells of R2–R5
4. Mystery conversion: draw one target symbol from the MY weights; every MY
   on the board (including gold-framed MY) converts to it (gold-framed MY
   converts to the gold-framed version)
5. Post Scatter: draw a count N (0–7); pick a combination of N of the 7
   strips uniformly; on each chosen strip replace the shortest symbol block
   with a Scatter
6. Cascade loop:
   6-1 Evaluate wins by the Way Game rules (see 3-4)
   6-2 No wins → exit the loop
   6-3 Add this step's win (multiplied by the current accumulated multiplier)
   6-4 Handle winning positions: gold-framed → convert to Wild in place;
       regular symbols → clear
   6-5 Symbols fall; empty cells refill from the Drop weights (Scatter and
       Mystery may drop in; Mystery reuses this spin's conversion target)
   6-6 Back to 6-1
7. Count Scatters on the final board (main board and Extra Reel both count;
   oversized Scatters count by the cells they occupy)
8. Decide Free Game trigger / retrigger
```

### 3-4 Win evaluation rules

```
Way Game evaluation:
    From R1, compare the same base symbol reel by reel to the right
    (Wild substitutes); 3+ consecutive reels required for a pay
    Ways = product of that symbol's symbol count on each consecutive reel
        an oversized symbol (1x2/1x3/1x4) counts as ONE symbol regardless
        of the cells it covers
    Single-symbol win = Pay Table value ÷ 100 × Ways × Coin In
    Scatter never joins a way; hitting one interrupts that reel's match
```

Key points:

- Ways must **start from R1** (leftmost); no skipping reels.
- Gold-framed symbols are evaluated as their base symbols, so they are fully equivalent for way matching.
- The sum of all symbols' way wins is this step's win, then multiplied by the current accumulated multiplier.

### 3-5 Cascade and gold-frame-to-Wild conversion

1. Winning regular symbols are removed.
2. Winning gold-framed symbols are **not removed**: the cell converts to `WW` and stays on the board for the next evaluation; the Wild lasts one cascade step only.
3. Remaining symbols fall; empty cells refill from this table's Drop weights.
4. Refilled Mystery symbols reuse this spin's conversion target; refills may bring in Scatters.
5. Evaluation repeats until the board forms no new wins.

### 3-6 M1 multiplier accumulation and application

**Sources**:

| Position | Multiplier |
| --- | --- |
| Main-board M1 (1x1) | x2 |
| Main-board M1 (1x2) | x3 |
| Main-board M1 (1x3) | x4 |
| Main-board M1 (1x4) | x5 |
| M1 on the Extra Reel | fixed x2 (size mapping does not apply) |

**Accumulation**: multiple M1s in the same step **add up** (never multiply).

**Application**: every cascade step's win is multiplied by the current accumulated total. Base Game restarts the accumulation on every new spin; Free Game starts at x2 and **carries it across spins** until the whole Free Game session ends (see 3-7).

M1 also keeps its line pays on the Pay Table; the multiplier role and the paying role coexist.

### 3-7 Free Game

**Trigger**: after the whole cascade sequence ends, **4 Scatters** on the final board (main board + Extra Reel) trigger the Free Game.

| Scatters | Free spins |
| --- | --- |
| 4 | 10 |
| 5 | 12 |
| 6 | 14 |
| 7 | 16 |
| 8+ | +2 per additional Scatter |

After entering the Free Game, **the total number of spins, retriggers included, is capped at 50**.

**Reel-table selection**: a table is drawn at the start of every FG spin — initial spins from `Table Selection Weight - Free Game`, retrigger-added spins from `Table Selection Weight - Retrigger`.

**Accumulated multiplier**: starts at **x2** on entering the FG, carries across spins without reset until the whole session ends; the next FG session starts again from x2.

**Retrigger**: reaching 4 Scatters again during the FG adds spins by the same award table (capped by the 50-spin limit). Retriggers only add spins; they never clear the accumulated multiplier.

### 3-8 Full flow of one paid spin

```
1. Cost of the round: Coin In = bet multiplier × Base Bet
2. Draw a Base Game card (see Chapter 4)
3. Run one BG spin (flow in 3-3)
4. If the final board reaches 4 Scatters:
       determine free spins by the award table (cap 50)
       draw a Free Game card (that profile's FG column; simulations with a
           single bet above $100 run on the _Bet100 model's config)
       run the Free Game:
           multiplier starts at x2
           each spin: draw reel table → run the spin → add win, carry the
                      multiplier → 4+ Scatters add spins (cap 50)
5. Round total = BG win + whole FG session win
6. Accept the round, or redraw it, by the card's condition (see 4-3)
```

### 3-9 Key rules recap

1. **Each cascade step's win is multiplied immediately by the current accumulated multiplier**; the multiplier itself accumulates by addition, never multiplication.
2. **A gold-framed symbol converts to Wild only after taking part in a win**; the Wild lasts one cascade step.
3. **The FG multiplier carries across spins**, starting at x2; retriggers add spins without clearing it.
4. **Scatters are counted only on the final board after all cascades end**; main board and Extra Reel both count, and oversized Scatters count by the cells they occupy.
5. **Scatter is absent from the initial reel strips**; it enters only via Post Scatter and cascade Drops.
6. **Oversized symbols count as one symbol in the Ways product**, but Scatter counting goes by occupied cells.
7. **Wild never stops in naturally**; the only source of Wilds is the conversion of winning gold-framed symbols.
8. **Cascade refills resample from the dedicated Drop weights**, not from the reel strip.
9. **Mystery draws its conversion target once per spin**; initial and refilled Mysteries all convert to the same symbol.
10. **M1 on the Extra Reel is fixed at x2**; the main board's size mapping does not apply there.

---

## 4. Card System

### 4-1 Purpose

The card system **does not alter the board probabilities**. It performs accept/redraw (rejection sampling) at the level of the whole round result, reshaping the natural probability into a target distribution.

It makes the following two things directly specifiable instead of being approximated through board parameters:

- **the distribution of per-round wins** (how much probability each win interval carries)
- **the FG trigger rate**

### 4-2 Card structure

Cards come from `Multiplier_Weight`, grouped by player profile and stage:

| Card group | Column | Drawn when |
| --- | --- | --- |
| Newbie Base Game cards | `Weight_NB_BG_Newbie` | Newbie profile, at the start of every round |
| Newbie Free Game cards | `Weight_NB_FG_Newbie` | Newbie profile, after an FG trigger |
| Regular Base Game cards | `Weight_NB_BG` | Regular profile, at the start of every round |
| Regular Free Game cards | `Weight_NB_FG` | Regular profile, after an FG trigger |

For single bets above $100 the simulation runs on the `_Bet100` model (`config_92A_Bet100.js` / `config_88B_Bet100.js`), whose regular-profile FG cards are that model's `Weight_NB_FG` (2,000× cap); the card-group structure is unchanged.

Two card types:

| Type | Condition |
| --- | --- |
| Interval card (`range`) | The segment's win ÷ Coin In must fall inside the interval (open left, closed right) |
| Free Game card (`free_game`) | Ignores the amount; requires only that this round triggers the Free Game |

Free Game card groups contain no `free_game`-type card, because by the time the FG decision runs, "FG triggered" is already a fact — only the amount interval is checked.

**Design of the `_Bet100` FG card group**: the win cap drops from 10,000× to **2,000×** (`(2000, 3000]` and `(9000, 10000]` at weight 0; highest weighted interval `(1000, 2000]`). Rebalancing keeps the 20×–200× body shape unchanged and scales the 200×–2,000× tail up uniformly; the weight total stays at 10⁹ and the card-weighted average FG multiple matches the base model — so **FG pay back, trigger cycle and average multiple are unchanged**; only the tail shape of the win distribution differs. 90B / 94A serve small bets and have no `_Bet100` model.

### 4-3 Per-round decision flow

```
At the start of every round: draw a Base Game card for the profile

If a free_game card is drawn:
    rerun BG spins until the final board reaches 4 Scatters
    choose the FG card column by profile and single-bet amount, draw an FG card
    rerun the WHOLE Free Game session until its total win falls inside
    the card's interval

If a range card is drawn:
    run one BG spin
        if it triggered the Free Game          → reject, redraw the round
        if the BG win is outside the interval  → reject, redraw the round
        otherwise                              → accept

Every stage is protected by a redraw cap of 10,000; on reaching the cap the
last result is kept and recorded, so cards that are practically undrawable
can be detected.
```

Key points:

- The card system decides "**what this round should look like**", then uses redraws to realize it.
- Decisions use fractional multiples (win ÷ Coin In) with open-left / closed-right intervals; the denominator is always the Normal Bet Coin In.
- **A range card rejects the whole round as soon as the FG triggers** — the FG trigger rate is therefore fixed entirely by the `Free Game` card's weight, independent of the board's natural Scatter probability.
- FG redraws operate on the **whole Free Game session**, not on single spins.

### 4-4 Relation to the Detail worksheets

`Detail` (regular profile) and `Detail_Newbie` (Newbie profile) are the derivation source of the card weights: natural probabilities per win interval are measured with the card system off (`Simulate` side), multiplied by the manual calibration factor `Fix Num`, and normalized into the weights written to `Multiplier_Weight` (`Calculate` side). The worksheets therefore hold both the "natural" and the "target" distributions, showing how much each interval was amplified or compressed.

### 4-5 Notes

1. **Card weights are the most direct lever on RTP.** Changing board weights changes the natural probability, but the final outcome is still fixed by the cards; changing the board without recalibrating the cards will not move total RTP as expected — it only raises redraw counts.
2. **Redraw counts are a health indicator.** A card whose interval is very hard to reach naturally shows sharply higher redraw counts, possibly hitting the cap. Simulation reports output redraw statistics; review them together.
3. **The BG/FG RTP split is set by the two card groups independently.** The four RTP version files differ only in the regular profile's card columns; the two Newbie columns are identical across all four.
4. **The FG trigger rate is locked by the `Free Game` card weight.** To change the FG cycle, adjust that card's weight, not the Scatter distribution on the reels.
5. **A `_Bet100` model changes only the tail shape of the FG win distribution.** Pay back and cycle are unchanged, and its SCR carries the base model's value; verification compares paired simulations with single bets on both sides of $100 (base model vs `_Bet100` model).
