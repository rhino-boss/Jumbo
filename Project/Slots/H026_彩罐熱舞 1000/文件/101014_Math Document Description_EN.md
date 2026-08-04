# Math Document Description — 101014 Pinata Beat 1000

**Scope: Normal Bet only**

| Item | Content |
| --- | --- |
| Game ID | 101014 |
| Math files | `H026192.xlsx` (RTP 92%), `H026194.xlsx` (RTP 94%) |
| Version | 4.0.0.8 |
| Programs | `Simulator.py` + `config_92.js` / `config_94.js` |
| Layout | 5 reels × 3 scoring rows (the program holds 4 rows; the top row does not score) |
| Paylines | 20 fixed lines, left to right |
| Coin In | 100 (Base Bet 100 × Price 1) |
| Bet mode | Normal Bet only |

---

## Table of Contents

- [1. Worksheet Function Introduction](#1-worksheet-function-introduction)
  - [1-1 How the program uses the xlsx parameters](#1-1-how-the-program-uses-the-xlsx-parameters)
  - [1-2 Worksheet overview](#1-2-worksheet-overview)
  - [1-3 Overview](#1-3-overview)
  - [1-4 Description](#1-4-description)
  - [1-5 Parameter](#1-5-parameter)
  - [1-6 Multiplier_Weight](#1-6-multiplier_weight)
  - [1-7 Multiplier_Weight_Detail](#1-7-multiplier_weight_detail)
  - [1-8 OP Jackpot](#1-8-op-jackpot)
  - [1-9 Base Game reel tables](#1-9-base-game-reel-tables)
  - [1-10 Free Game reel tables](#1-10-free-game-reel-tables)
- [2. Game Parameters on the Parameter Worksheet](#2-game-parameters-on-the-parameter-worksheet)
  - [2-1 Line](#2-1-line)
  - [2-2 Table Selection Weight - Base Game](#2-2-table-selection-weight---base-game)
  - [2-3 Multiplier Range](#2-3-multiplier-range)
  - [2-4 Used Special Pool Weight](#2-4-used-special-pool-weight)
  - [2-5 Multiple Selection Weight (five blocks)](#2-5-multiple-selection-weight-five-blocks)
  - [2-6 Eliminate Table Weight](#2-6-eliminate-table-weight)
- [3. Game Logic](#3-game-logic)
  - [3-1 Layout and coordinate system](#3-1-layout-and-coordinate-system)
  - [3-2 Symbols and roles](#3-2-symbols-and-roles)
  - [3-3 Flow of a single spin](#3-3-flow-of-a-single-spin)
  - [3-4 Win evaluation](#3-4-win-evaluation)
  - [3-5 Cascading and gold-framed symbols turning into Wild](#3-5-cascading-and-gold-framed-symbols-turning-into-wild)
  - [3-6 Multiplier assignment, collection and application](#3-6-multiplier-assignment-collection-and-application)
  - [3-7 Free Game](#3-7-free-game)
  - [3-8 Flow of one round (one paid spin)](#3-8-flow-of-one-round-one-paid-spin)
  - [3-9 Key rules summary](#3-9-key-rules-summary)
- [4. Card System](#4-card-system)
  - [4-1 Purpose](#4-1-purpose)
  - [4-2 Card structure](#4-2-card-structure)
  - [4-3 Per-round evaluation flow](#4-3-per-round-evaluation-flow)
  - [4-4 Relationship with Multiplier_Weight_Detail](#4-4-relationship-with-multiplier_weight_detail)
  - [4-5 Notes](#4-5-notes)

---

## 1. Worksheet Function Introduction

### 1-1 How the program uses the xlsx parameters

`Simulator.py` uses the parameters in the xlsx to run the simulation. Three points must be understood before mapping worksheet fields to program behaviour:

1. **Weights are relative values only.**
   Every field labelled Weight is a relative weight. It does not need to be a probability and does not need to sum to 100%. When drawing, the program takes a random value within the total of that weight group, then maps it to the corresponding entry in proportion to the weights. **The total of each weight group is that group's denominator**, so raising one entry within a group simultaneously dilutes the others.

2. **A gold-framed symbol is held as two layers of information.**
   The board stores the *base symbol* (for example, the gold-framed `G1` is stored on the board as `M1`). Two separate masks record whether each cell is gold-framed and what multiplier that cell carries.
   Consequently the program never reads the pay values of the `G1`–`GJ` rows in the `Overview` Pay Table; win evaluation always uses the base symbol's pay values. Those 9 rows exist for reference, to confirm that a gold-framed symbol pays the same as its base symbol.

3. **Not every field is used by the program.**
   The symbol-count statistics, ratios and averages on the left side of each worksheet, together with the `Description`, `Multiplier_Weight_Detail` and `OP Jackpot` worksheets, are for design and verification purposes only. Each section below states which fields the program uses.

### 1-2 Worksheet overview

| Worksheet | Provides | Affects | Used by program |
| --- | --- | --- | --- |
| `Overview` | Game specification, RTP breakdown, free-spin settings, symbol pay table | Cost calculation, win evaluation, free-spin count | Yes (partly) |
| `Description` | Text description of the parameter flow | — | No (document only) |
| `Parameter` | Paylines, all weight groups, multiplier list | Table selection, multiplier assignment, cascade fill mode | Yes |
| `Multiplier_Weight` | The two card-weight columns of the card system | Accept / re-draw of a round result | Yes |
| `Multiplier_Weight_Detail` | Derivation of the above weights and the target values | — | No (design only) |
| `OP Jackpot` | Simulation record statistics (spin count, Scatter count) | — | No (verification record) |
| `BG_Symbol`<br>`BG_Symbol (2)`<br>`BG_Symbol (3)` | Three Base Game reel strips and cascade-fill wheels | Base Game initial board and cascade fill | Yes |
| `FG_Symbol`<br>`FG_Symbol (2)`<br>`FG_Symbol (3)` | Three Free Game reel strips and cascade-fill wheels | Free Game initial board and cascade fill | Yes |

Both math files have an identical worksheet structure.

### 1-3 Overview

Provides the game specification and the mathematical target values.

| Block | Content | Used by program |
| --- | --- | --- |
| Model / Version | Model code and version | Yes (written into the output file name) |
| Base Bet | Bet basis | Yes (Coin In calculation) |
| Coin in / Price(x) / Total RTP / Bet Type | Cost multiplier and total RTP of the bet mode | Yes (Price(x) for cost) |
| Total Pay Back Percentage | Splits the total RTP into the Base Game and Free Game contributions, and records the Free Game trigger rate and cycle | No (target values) |
| Reel # / Visible Window Size | Reel count and scoring row count | Yes (board dimensions) |
| Free Spins Setting | Free-spin count per Scatter count, and the overall cap | Yes (see 3-7) |
| Pay Table | Symbol code, Id and 3 / 4 / 5-of-a-kind pay values | Yes (win evaluation) |

**Coin In calculation**

```
Coin In = bet multiplier × Base Bet × Price(x)
```

All RTP and multiplier statistics are expressed as "total win of the round ÷ Coin In".

> In the `Total Pay Back Percentage` block, the `Hit%` field holds the **Free Game trigger rate** (it is the reciprocal of `Pulls/Hit`, which is the Free Game cycle). It is not the line-win hit rate; for that, refer to the `hit_rate` fields of the simulation report.

### 1-4 Description

Lists, in text form, the order in which the parameters are used during the Base Game and Free Game flows. The content matches Section 3 of this document. Document only; not read by the program.

### 1-5 Parameter

The central control panel of the model. Each block is described in [Section 2](#2-game-parameters-on-the-parameter-worksheet).

### 1-6 Multiplier_Weight

The input to the card system. Layout:

| Column | Header | Purpose |
| --- | --- | --- |
| `Range` | Win-multiple range label | Defines the bounds of each card |
| `Weight_NB_BG` | Base Game card weights | One card is drawn at the start of every round |
| `Weight_NB_FG` | Free Game card weights | One card is drawn after Free Game is triggered |

The rows are a series of win-multiple ranges (total win ÷ Coin In, left-open and right-closed). The last row, `Free Game`, is a special card: it does not check an amount, it only requires that the round must trigger Free Game.

The totals of the two columns are each calibrated to the same base value, so a weight can be read directly as the probability of that outcome. The mechanism is described in [Section 4](#4-card-system).

**The only parameter difference between the two math files is the `Weight_NB_FG` column** — that is, the Free Game pay distribution. `Weight_NB_BG`, the entire `Parameter` worksheet and all six reel tables are identical in both files.

### 1-7 Multiplier_Weight_Detail

The worksheet from which the two weight columns of `Multiplier_Weight` are derived. Not read by the program.

| Block | Content |
| --- | --- |
| Threshold | Normalisation base of the weights |
| Coin in | References the Base Bet on `Overview` |
| Target rows | Target RTP, hit rate, Free Game cycle and average multiplier for Normal Bet (the RTP breakdown on `Overview` references these) |
| `Base Game (Normal Bet)` block | Natural-probability simulation results per win range (count, pay, hit rate, average multiplier), the manual adjustment factor, and the calibrated weights |
| `Free Game (Normal Bet)` block | The same, applied to the total win of a Free Game session |
| Comparison columns | Current versus benchmark values, for reference while tuning |

The tuning loop is: run with the card system disabled to obtain the natural probabilities, enter the simulation results, adjust the factors, obtain the calibrated weights, write them into `Multiplier_Weight`, then re-run with the card system enabled to verify.

> The two weight columns of `Multiplier_Weight` were originally spilled from this worksheet by dynamic-array formulas. In this submission version they have been converted to static values, so the two worksheets hold identical values but are no longer linked.

### 1-8 OP Jackpot

Records the spin count, the scoring-area Scatter count and the cumulative Scatter count of each simulation run, for verification. Not read by the program, and contains no jackpot probability or pay parameters.

### 1-9 Base Game reel tables

`BG_Symbol`, `BG_Symbol (2)` and `BG_Symbol (3)` are the three Base Game reel settings. The three worksheets share an identical layout; each defines one reel strip plus one cascade-fill wheel.

| Field group | Content | Used by program |
| --- | --- | --- |
| Leftmost Symbol / Description / R1–R5 / ID | Symbol counts on that table's reel strip and the per-reel totals | No (verification) |
| Normal / Golden Symbol ratio | Ratio of normal to gold-framed symbols | No (verification) |
| Combined statistics | Combined count of a base symbol and its gold-framed version | No (verification) |
| `Symbol` | Reel strip content (text) | No (human readable) |
| `Symbol ID R1~R5` | Reel strip content (codes) | Yes (the actual reel strip) |
| `Symbol Weight R1~R5` | Weight of each reel-strip position | Yes (determines the stop position) |
| `Eliminate Wheel Weight A` | Cascade-fill wheel weights, group A | Yes (cascade fill) |
| `Eliminate Wheel Weight B` | Cascade-fill wheel weights, group B | Yes (cascade fill) |

**Roles of the three tables**

| Table | Role | Characteristics |
| --- | --- | --- |
| `BG_Symbol` | Ordinary round | Gold frames appear on reels 2, 3 and 4 only; the Scatter distribution cannot reach the trigger threshold |
| `BG_Symbol (2)` | Full gold-frame round | Reel 3 is entirely gold-framed and always carries a multiplier; Scatter distribution as above |
| `BG_Symbol (3)` | Free Game trigger round | Scatters are distributed across all five reels; the gold-frame multiplier configuration is zero, so no large multiplier is collected before entering Free Game |

> It follows that in Normal Bet, **Free Game can only be triggered in a round that draws `BG_Symbol (3)`**.

**About `Symbol Weight`**

This column is not the weight of a symbol; it is the weight of a **reel-strip position**. The program first draws a strip position according to this column, then takes the consecutive cells from that position to fill the board. The effective appearance rate of a symbol therefore depends both on how many times it occurs on the strip and on the weights of those positions.

**About `Eliminate Wheel Weight`**

This is a symbol × reel weight table, entirely independent of the reel strip. When cascading creates empty positions, **the program does not continue taking symbols from the reel strip; it draws again from this table**. Groups A and B are both provided, and `Eliminate Table Weight` decides which group the round uses (see [2-6](#2-6-eliminate-table-weight)).

The field group is laid out as three blocks, `1 Combo`, `2 Combo` and `3+ Combo`, so that different cascade counts can use different fill rates.

> The program currently uses the `2 Combo` block; the values of the three blocks are currently identical. Distinguishing by cascade count would also require changing which block the program reads.

### 1-10 Free Game reel tables

`FG_Symbol`, `FG_Symbol (2)` and `FG_Symbol (3)` are the three Free Game reel settings. The layout and field meanings are the same as [1-9](#1-9-base-game-reel-tables).

The three tables are switched according to the current accumulated multiplier (see [3-7](#3-7-free-game)). Their common characteristics are:

- Reel 3 is always gold-framed and always carries a multiplier
- Reel 3 contains no Scatter, so **the maximum number of Scatters obtainable inside Free Game is one reel fewer than in the Base Game**
- The tables differ in the expected value of their multiplier configuration, so that growth slows down as the accumulated multiplier rises

---

## 2. Game Parameters on the Parameter Worksheet

Each block below states what the parameter group controls and at which point in a round the program uses it.

### 2-1 Line

Defines the 20 fixed paylines. Each row is one line; the five numbers state, for reels 1 to 5, which scoring row that line uses (0 = top, 1 = middle, 2 = bottom).

For example, `1, 1, 1, 1, 1` is the straight centre line, and `0, 1, 2, 1, 0` is a V-shaped line.

At each win evaluation the program checks these 20 lines in order. Each line pays only one award, and the awards are then summed. See [3-4](#3-4-win-evaluation).

### 2-2 Table Selection Weight - Base Game

Lists the three Base Game reel tables and their weights.

**The first action of every Base Game spin** is to draw the reel table for that round from this weight group. That single step also determines which reel strip, cascade-fill wheel and multiplier weights the rest of the round will use, which makes it the most upstream parameter affecting both game feel and the Free Game trigger rate.

Free Game has no corresponding block, because Free Game reel tables are not drawn; they are switched by the accumulated multiplier.

### 2-3 Multiplier Range

The list of multipliers a gold-framed symbol may carry. **This is an index table** — the column order of every `Multiple Selection Weight` block below corresponds to this list.

Drawing a multiplier always follows the same sequence: draw an *index* from a weight group, then convert it to the actual multiplier through this list. The first entry of the list is `0`, meaning "this gold-framed symbol carries no multiplier" (the frame exists, but no multiplier can be collected).

The non-zero multipliers of the list, in order, are: `x2`, `x3`, `x5`, `x8`, `x10`, `x15`, `x20`, `x25`, `x50`, `x100`, `x500`, `x1000`.

### 2-4 Used Special Pool Weight

Decides whether the special multiplier pool is activated.

- The columns are the **number of gold-framed symbols in the scoring area** (the more gold frames, the higher the activation chance)
- Each row corresponds to one reel table
- The denominator is fixed at 10000

**Logic**

1. Before multipliers are assigned at the start of a spin, count the gold-framed symbols in the scoring area.
2. Look up the weight by that count and the reel table of the round, and decide whether the special pool activates.
3. If it activates, **one** gold-framed symbol in the scoring area is chosen with equal probability, and that symbol draws its multiplier from `Multiple Selection Weight - Special Pool` instead.

Notes:

- The special pool is evaluated **only once, at the initial multiplier assignment**. Gold-framed symbols added by cascading never get this chance.
- At most **one** gold-framed symbol per round receives a special-pool multiplier.
- Only gold-framed symbols in the scoring area are eligible. Those in the top preview row are neither counted nor selected.

### 2-5 Multiple Selection Weight (five blocks)

The columns of all five blocks correspond to the multiplier list in [2-3](#2-3-multiplier-range), and the rows correspond to the reel tables. They differ only in **which position and which moment** uses which block.

| Block | When it is used |
| --- | --- |
| `Special Pool` | The single gold-framed symbol that hits the special pool at the start of a spin |
| `Before Eliminate` | Gold-framed symbols at the start of a spin, in the **scoring area**, not on reel 3 |
| `After Eliminate` | Gold-framed symbols at the start of a spin located in the **preview row** (not reel 3), and gold-framed symbols added by cascading (not reel 3) |
| `Reel3 Before Eliminate` | Gold-framed symbols at the start of a spin, in the scoring area, on **reel 3** (specific reel tables only) |
| `Reel3 After Eliminate` | Reel-3 gold-framed symbols at the start of a spin located in the preview row, and reel-3 gold-framed symbols added by cascading (specific reel tables only) |

**When the reel-3 blocks apply**

Only reel tables whose third reel is entirely gold-framed (the Base Game full gold-frame table and the three Free Game tables) use the two reel-3 blocks for their third reel. On all other reel tables, reel 3 still uses the ordinary Before / After blocks.

**Full selection order**

```
Initial assignment (every gold-framed symbol on the board, preview row included)
    |- the single symbol that hit the special pool ------> Special Pool
    |- reel 3 AND the table uses the reel-3 blocks
    |      |- in the scoring area --------------------> Reel3 Before Eliminate
    |      +- in the preview row ---------------------> Reel3 After  Eliminate
    +- otherwise
           |- in the scoring area --------------------> Before Eliminate
           +- in the preview row ---------------------> After  Eliminate

Cascade fill (newly added gold-framed symbols)
    |- reel 3 AND the table uses the reel-3 blocks ---> Reel3 After Eliminate
    +- otherwise -------------------------------------> After Eliminate
```

> Although the preview row (the non-scoring top row) is produced at the start of a spin, it can only take part in a win after it has dropped down. It therefore uses **After Eliminate**, not Before Eliminate. This is the single easiest point to misread on these worksheets.

Each block has one further field on its right holding an average multiplier, defined as the average multiplier excluding the value 0. It is for design reference and is not read by the program.

### 2-6 Eliminate Table Weight

Decides whether the cascading of the round uses `Eliminate Wheel Weight A` or `B`. The Base Game and Free Game can be configured separately.

**One draw is made at the start of each spin, and the chosen group is used for the whole cascade sequence of that spin; it is never switched mid-spin.**

---

## 3. Game Logic

### 3-1 Layout and coordinate system

| Item | Value |
| --- | --- |
| Reels | 5 |
| Scoring rows | 3 |
| Rows held by the program | 4 (3 scoring rows plus 1 preview row at the top) |

```
preview row   <- does not pay, is not counted for Scatters,
                 but its gold-framed symbols do receive a multiplier
scoring row 1 -+
scoring row 2  |- 3 x 5: line evaluation and Scatter counting use only this area
scoring row 3 -+
```

At each stop, four consecutive cells of the reel strip fill these four rows. The values 0 / 1 / 2 on the `Line` worksheet refer to scoring rows 1 to 3.

### 3-2 Symbols and roles

| Symbol | Description | Role |
| --- | --- | --- |
| `WW` | Wild | Substitutes for all paying symbols; carries no pay value of its own |
| `C1` | Scatter | Counted only; breaks a line; carries no pay value of its own |
| `M1`–`M5` | High-pay symbols | Paying |
| `A`, `K`, `Q`, `J` | Low-pay symbols | Paying |
| `G1`–`G5`, `GA`, `GK`, `GQ`, `GJ` | Gold-framed versions of the paying symbols above | Treated as the corresponding base symbol for win evaluation; may additionally carry a multiplier |

Three derived lookups are used by the program:

- **Base symbol mapping**: which ordinary symbol a gold-framed symbol maps back to (used when writing the board at stop and at cascade fill)
- **Is gold-framed**: decides whether a cell enters multiplier assignment
- **Is paying**: `WW`, `C1` and every gold-framed code are false; win evaluation filters on this

**`WW` never lands from a reel stop.** Neither the reel strips nor the cascade-fill wheels of the six reel tables contain `WW`. A Wild on the board has exactly one source: a winning gold-framed symbol turning into a Wild in place (see [3-5](#3-5-cascading-and-gold-framed-symbols-turning-into-wild)).

### 3-3 Flow of a single spin

The Base Game and Free Game share the same flow; only the parameter groups differ.

```
1. Determine the reel table for this spin
      Base Game: draw from Table Selection Weight - Base Game
      Free Game: switch by the current accumulated multiplier (see 3-7)
2. Draw cascade-fill group A or B from Eliminate Table Weight (fixed for this spin)
3. Draw a stop position per reel from Symbol Weight, then expand Symbol ID into the 4 x 5 board
4. Assign a multiplier to every gold-framed symbol on the board, preview row included
      First evaluate the special pool, then select the weight block by position and
      timing (see 2-4 and 2-5)
5. Cascade loop:
   5-1 Evaluate the 20 paylines
   5-2 If no award at all -> exit the loop
   5-3 Add this pass's line awards to the running total
   5-4 Process the winning positions:
          gold-framed -> collect its multiplier; the cell does not disappear but
                         turns into a Wild
          otherwise   -> clear the cell
   5-5 Remaining symbols in the reel drop down; empty positions are filled from the
       cascade-fill wheel of this spin
          a newly added gold-framed symbol draws its multiplier from the block
          matching its position
          if the reel already holds a Scatter, drawing a Scatter is re-drawn
   5-6 Return to 5-1
6. Count the Scatters in the scoring area of the final board
7. If any multiplier was actually collected in this spin, apply the accumulated
   multiplier once to the total line award of this spin
```

### 3-4 Win evaluation

```
For each payline:
    Take the symbol on reel 1 at that line's position
        if Scatter  -> the line does not pay
        if Wild     -> evaluate once for every paying symbol and keep the highest pay
        otherwise   -> use its base symbol as the target
    Compare from reel 1 rightwards, reel by reel:
        same base symbol OR the cell is a Wild -> line length + 1
        Scatter                                -> break immediately
        anything else                          -> break
    A line length of 3 or more pays; take the value from the Pay Table and multiply
    by the bet multiplier
    Each line keeps only its single highest-paying interpretation; no double counting
```

Notes:

- A line must start from **reel 1** (leftmost).
- A gold-framed symbol has already been reduced to its base symbol at evaluation time, so it is exactly equivalent to that base symbol for line purposes.
- The sum of the 20 lines is the total line award of that evaluation pass.

### 3-5 Cascading and gold-framed symbols turning into Wild

1. Winning ordinary symbols are removed.
2. A winning gold-framed symbol is **not** removed: its multiplier is collected first, and the position becomes `WW` and stays on the board, so it is not treated as an empty position.
3. Remaining symbols in that reel drop down.
4. Positions that are still empty are filled by drawing again from the cascade-fill wheel selected for this spin.
5. If a newly added symbol is gold-framed, its multiplier is drawn from the block matching its reel.
6. **A second Scatter is never added to the same reel**: if the reel already holds a Scatter, a drawn Scatter is re-drawn.
7. After filling, win evaluation runs again, until no new winning combination is formed.

### 3-6 Multiplier assignment, collection and application

**Assignment (start of a spin)**: every gold-framed symbol on the board is assigned a multiplier, which may be 0. The weight block is selected by three conditions: whether the special pool was hit, whether the symbol is on reel 3 of a table that uses the reel-3 blocks, and whether it sits in the scoring area or the preview row (see [2-4](#2-4-used-special-pool-weight) and [2-5](#2-5-multiple-selection-weight-five-blocks)).

**Collection**: a gold-framed symbol first takes part in line evaluation as its base symbol. **Its multiplier is collected only if that symbol is actually cleared by a win.** A gold-framed symbol that does not win contributes no multiplier.

**Application**: within a single spin the multipliers are only accumulated; they are **not applied immediately**. Once the board forms no further winning combination, the accumulated multiplier is applied once to the total line award of that spin.

If no multiplier greater than 0 was collected during the spin, no multiplier is applied.

### 3-7 Free Game

**Trigger**: after the entire cascade sequence has finished, count the Scatters in the **scoring area** of the final board. Three or more triggers the feature.

| Scatters in the scoring area | Free spins |
| --- | --- |
| 3 | 12 |
| 4 | 14 |
| 5 | 16 |

Once Free Game is entered, the total number of free spins, **including retriggers, is capped at 50**.

**Reel table switching**: Free Game does not draw a reel table; it switches directly by the current accumulated multiplier.

| Current accumulated multiplier | Reel table used |
| --- | --- |
| < 10 | `FG_Symbol` |
| < 20 | `FG_Symbol (2)` |
| >= 20 | `FG_Symbol (3)` |

**Carrying the accumulated multiplier**: the accumulated multiplier is **carried across spins** and is cleared only when the whole Free Game session ends. It also determines which reel table the next spin uses.

**Retrigger**: reaching the Scatter threshold again during Free Game adds spins according to the same table, but the total remaining spins are still capped at 50. A retrigger only adds spins; it never clears the accumulated multiplier.

> Because reel 3 of the three Free Game tables contains no Scatter, the maximum number of Scatters obtainable inside Free Game is one reel fewer than in the Base Game.

### 3-8 Flow of one round (one paid spin)

```
1. Compute the cost: Coin In = bet multiplier x Base Bet x Price(x)
2. Draw one Base Game card (see Section 4)
3. Run one Base Game spin (flow as in 3-3)
4. If the scoring area of the final board reaches the Scatter threshold:
       determine the free-spin count from the table (capped at 50)
       draw one Free Game card
       enter Free Game:
           reset the accumulated multiplier to zero
           for each spin:
               select the reel table by the current accumulated multiplier
               run one spin (flow as in 3-3, multipliers starting from the current
               accumulated value)
               add this spin's win, update the accumulated multiplier (carried over)
               if this spin reaches the Scatter threshold -> add spins (cap 50)
5. Total win of the round = Base Game win + total Free Game win
6. Accept the round, or re-draw the whole round, according to the card condition
   (see 4-3)
```

### 3-9 Key rules summary

1. **Multipliers are not applied immediately.** They accumulate within a spin and are applied once, to that spin's total line award, when no further cascade is possible.
2. **A gold-framed symbol must win before its multiplier is collected.** After being cleared it turns into a Wild and stays on the board; it neither disappears nor drops.
3. **The accumulated multiplier of Free Game does not apply on every spin.** It applies only on those spins that actually collected a multiplier greater than 0.
4. **The accumulated multiplier is carried across Free Game spins and determines the reel table of the next spin.** A retrigger only adds spins; it does not clear the accumulated value.
5. **Scatters are counted only on the final board after the whole cascade sequence has finished** — not while cascading, and never in the preview row.
6. **In Normal Bet, Free Game can only be triggered in a round that draws `BG_Symbol (3)`.**
7. **Gold-framed symbols in the preview row use `After Eliminate`, not `Before Eliminate`.**
8. **Only reel tables whose third reel is entirely gold-framed use the reel-3 multiplier blocks for reel 3.**
9. **Cascade fill draws again from an independent cascade-fill wheel**; it does not continue taking symbols from the reel strip.
10. **`WW` never lands from a reel stop**; every Wild on the board comes from a winning gold-framed symbol.

---

## 4. Card System

### 4-1 Purpose

The card system **does not change the probability settings of the board**. It performs accept / re-draw (rejection sampling) at the level of the whole round result, reshaping the natural probabilities into a target distribution.

Because of it, the following two properties can be specified directly instead of being approached by tuning board parameters:

- **The distribution of the win of a round** (what share each win range takes)
- **The Free Game trigger rate**

### 4-2 Card structure

The cards come from `Multiplier_Weight` and form two groups:

| Card group | When drawn | Contents |
| --- | --- | --- |
| Base Game cards | At the start of every round | A series of win-multiple ranges, plus one `Free Game` card |
| Free Game cards | After Free Game is triggered | A series of win-multiple ranges |

Two card types:

| Type | Condition |
| --- | --- |
| Range card (`range`) | Requires that segment's win ÷ Coin In to fall inside the given range (left-open, right-closed) |
| Free-game card (`free_game`) | Does not check an amount; requires only that the round triggers Free Game |

The Free Game card group contains no `free_game` type card, because by the time the Free Game condition is evaluated the feature has already been triggered; only the amount range needs to be matched.

### 4-3 Per-round evaluation flow

```
At the start of every round: draw one Base Game card

If a free_game card is drawn:
    repeat Base Game spins until the final board reaches the Scatter threshold
    then draw one Free Game card
    repeat the whole Free Game session until its total win falls inside that
    card's range

If a range card is drawn:
    run one Base Game spin
        if Free Game was triggered      -> reject, re-draw the whole round
        if the Base Game win is outside
        the card's range                -> reject, re-draw the whole round
        otherwise                       -> accept

Both cases are protected by a re-draw limit. On reaching the limit the round is
abandoned and counted, so that a card which cannot in practice be satisfied can
be identified.
```

Notes:

- The card system decides **what the round must look like**, and re-drawing is used to produce it.
- Evaluation uses the fractional multiple (win ÷ Coin In); ranges are **left-open and right-closed**.
- **A range card rejects the whole round as soon as Free Game is triggered.** The Free Game trigger rate is therefore determined entirely by the weight of the `Free Game` card, independently of the natural Scatter probability of the board.
- Free Game re-draws operate on the **whole Free Game session**, not on a single free spin.

### 4-4 Relationship with Multiplier_Weight_Detail

`Multiplier_Weight_Detail` is the source from which the card weights are derived: the natural probability of each win range is first obtained with the card system disabled, then multiplied by a manual adjustment factor and normalised to produce the weights written into `Multiplier_Weight`. The worksheet therefore holds both the natural and the target probabilities, which makes it possible to see how much each range has been amplified or compressed.

### 4-5 Notes

1. **The card weights are the most direct parameters affecting RTP.** Adjusting board weights changes the natural probabilities, but the final outcome is still decided by the cards. Changing the board without updating the card weights will not move the total RTP as intended; it will only increase the number of re-draws.
2. **Re-draw counts are a health indicator.** If the range of a card is very hard to reach under the natural probabilities, the re-draw count rises noticeably and may reach the limit. The simulation report outputs re-draw statistics, which should be reviewed together with the RTP.
3. **The RTP split between the Base Game and Free Game is decided by the two card groups separately.** This is why the two math files differ only in `Weight_NB_FG`: only the Free Game pay distribution was adjusted.
4. **The Free Game trigger rate is locked by the weight of the `Free Game` card.** To change the Free Game cycle, adjust that weight rather than the Scatter distribution on the reel strips.
