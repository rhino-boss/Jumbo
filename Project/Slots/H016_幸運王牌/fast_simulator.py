"""Numba-compiled natural-probability engine for H016.

The object engine in Simulator.py remains the reference implementation and is
still used by card/retry simulations.  This module covers the high-volume,
card-off path used for natural probability and competitor comparisons.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np
from numba import njit


# Scalar result slots. Counts are kept in float64 alongside pay aggregates so
# chunks can be merged with one vector addition.
S_ROUNDS = 0
S_COIN_IN = 1
S_PAY_BG = 2
S_PAY_FG = 3
S_HIT_ROUNDS = 4
S_FG_TRIGGERS = 5
S_FG_SPINS = 6
S_RETRIGGERS = 7
S_CASCADES_BG = 8
S_CASCADES_FG = 9
S_GOLDEN = 10
S_W2_EVENTS = 11
S_BG_W2_EVENTS = 12
S_FG_W2_EVENTS = 13
S_BG_M1 = 14
S_FG_M1 = 15
S_BG_HIT = 16
S_FG_HIT = 17
S_BG_GOLD_SPINS = 18
S_FG_GOLD_SPINS = 19
S_BG_GOLD_SYMBOLS = 20
S_FG_GOLD_SYMBOLS = 21
S_MAX_MULTIPLIER = 22
S_WIN_X_SUM = 23
S_WIN_X_SQUARE = 24
SCALAR_COUNT = 25


def _cumulative(values: list[float], size: int) -> tuple[np.ndarray, float]:
    result = np.zeros(size, dtype=np.float64)
    running = 0.0
    for index, value in enumerate(values):
        running += max(0.0, float(value))
        result[index] = running
    return result, running


def prepare_config(config: dict[str, Any]) -> tuple[Any, ...]:
    names = list(config["tables"])
    name_to_id = {name: index for index, name in enumerate(names)}
    table_count = len(names)
    max_reel = max(len(reel) for table in config["tables"].values() for reel in table["reels"])
    max_drop = max(len(values) for table in config["tables"].values() for values in table["drop_values"])
    max_rw = max(len(table["random_wild"]["values"]) for table in config["tables"].values())

    reel_symbols = np.full((table_count, 5, max_reel), -1, dtype=np.int16)
    reel_cumulative = np.zeros((table_count, 5, max_reel), dtype=np.float64)
    reel_lengths = np.zeros((table_count, 5), dtype=np.int16)
    reel_totals = np.zeros((table_count, 5), dtype=np.float64)
    drop_values = np.full((table_count, 5, max_drop), -1, dtype=np.int16)
    drop_cumulative = np.zeros((table_count, 5, max_drop), dtype=np.float64)
    drop_lengths = np.zeros((table_count, 5), dtype=np.int16)
    drop_totals = np.zeros((table_count, 5), dtype=np.float64)
    rw_values = np.zeros((table_count, max_rw), dtype=np.int16)
    rw_cumulative = np.zeros((table_count, max_rw), dtype=np.float64)
    rw_lengths = np.zeros(table_count, dtype=np.int16)
    rw_totals = np.zeros(table_count, dtype=np.float64)
    multipliers = np.zeros((table_count, 4), dtype=np.int16)

    for table_id, name in enumerate(names):
        table = config["tables"][name]
        for reel in range(5):
            symbols = [int(value) for value in table["reels"][reel]]
            weights = [float(value) for value in table["weights"][reel]]
            reel_symbols[table_id, reel, : len(symbols)] = symbols
            cumulative, total = _cumulative(weights, len(symbols))
            reel_cumulative[table_id, reel, : len(symbols)] = cumulative
            reel_lengths[table_id, reel] = len(symbols)
            reel_totals[table_id, reel] = total

            values = [int(value) for value in table["drop_values"][reel]]
            weights = [float(value) for value in table["drop_weights"][reel]]
            drop_values[table_id, reel, : len(values)] = values
            cumulative, total = _cumulative(weights, len(values))
            drop_cumulative[table_id, reel, : len(values)] = cumulative
            drop_lengths[table_id, reel] = len(values)
            drop_totals[table_id, reel] = total

        random_wild = table["random_wild"]
        values = [int(value) for value in random_wild["values"]]
        weights = [float(value) for value in random_wild["weights"]]
        rw_values[table_id, : len(values)] = values
        cumulative, total = _cumulative(weights, len(values))
        rw_cumulative[table_id, : len(values)] = cumulative
        rw_lengths[table_id] = len(values)
        rw_totals[table_id] = total
        source_multipliers = list(map(int, table.get("multipliers") or [1, 2, 3, 5]))
        for index in range(4):
            multipliers[table_id, index] = source_multipliers[min(index, len(source_multipliers) - 1)]

    pays = np.zeros((19, 3), dtype=np.float64)
    for symbol, values in config["pays"].items():
        pays[int(symbol), :3] = np.asarray(values, dtype=np.float64)

    def selection(group: str, fallback: str) -> tuple[np.ndarray, np.ndarray, int, float]:
        items = config.get("table_selection", {}).get(group) or [{"table": fallback, "weight": 1}]
        ids = np.zeros(max(1, len(items)), dtype=np.int16)
        cumulative = np.zeros(max(1, len(items)), dtype=np.float64)
        running = 0.0
        for index, item in enumerate(items):
            ids[index] = name_to_id[str(item["table"])]
            running += max(0.0, float(item["weight"]))
            cumulative[index] = running
        return ids, cumulative, len(items), running

    base_ids, base_cum, base_len, base_total = selection("base", "bg_high")
    free_ids, free_cum, free_len, free_total = selection("free", "fg_low")
    retrigger_ids, retrigger_cum, retrigger_len, retrigger_total = selection("retrigger", "fg_low")
    super_id = name_to_id.get("super", name_to_id.get("fg_2", int(free_ids[0])))
    return (
        reel_symbols, reel_cumulative, reel_lengths, reel_totals,
        drop_values, drop_cumulative, drop_lengths, drop_totals,
        rw_values, rw_cumulative, rw_lengths, rw_totals,
        multipliers, pays,
        base_ids, base_cum, base_len, base_total,
        free_ids, free_cum, free_len, free_total,
        retrigger_ids, retrigger_cum, retrigger_len, retrigger_total,
        int(super_id), int(config["free_spins"]), int(config["retrigger_spins"]),
        int(config["free_spin_cap"]), float(config["buy_price"]), float(config["super_buy_price"]),
    )


@njit(nogil=True, inline="always", cache=True)
def _pick_index(cumulative, length, total):
    if length <= 0 or total <= 0.0:
        return 0
    target = np.random.random() * total
    low = 0
    high = length
    while low < high:
        middle = (low + high) // 2
        if cumulative[middle] < target:
            low = middle + 1
        else:
            high = middle
    return min(low, length - 1)


@njit(nogil=True, inline="always", cache=True)
def _canonical(symbol):
    return symbol - 8 if 11 <= symbol <= 18 else symbol


@njit(nogil=True, cache=True)
def _spin(
    table_id, free_game, scene, bet_multi,
    reel_symbols, reel_cumulative, reel_lengths, reel_totals,
    drop_values, drop_cumulative, drop_lengths, drop_totals,
    rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
    symbol_hits, symbol_pay, length_hits, length_pay, initial_symbols, dropped_symbols,
    w2_counts,
):
    board = np.empty((5, 4), dtype=np.int16)
    m1_present = 0
    initial_gold = 0
    for reel in range(5):
        length = int(reel_lengths[table_id, reel])
        stop = _pick_index(reel_cumulative[table_id, reel], length, reel_totals[table_id, reel])
        for row in range(4):
            symbol = int(reel_symbols[table_id, reel, (stop + row) % length])
            board[reel, row] = symbol
            initial_symbols[scene, reel, symbol] += 1
            if _canonical(symbol) == 3:
                m1_present = 1
            if 11 <= symbol <= 18:
                initial_gold += 1

    pending_reel = np.empty(20, dtype=np.int16)
    pending_row = np.empty(20, dtype=np.int16)
    candidate_reel = np.empty(16, dtype=np.int16)
    candidate_row = np.empty(16, dtype=np.int16)
    hit_mask = np.zeros((5, 4), dtype=np.uint8)
    pending_count = 0
    w2_used = 0
    pay_total = 0.0
    cascades = 0
    max_multiplier = 1
    golden_converted = 0
    w2_events = 0

    while True:
        if pending_count > 0 and (free_game or w2_used == 0):
            rw_index = _pick_index(rw_cumulative[table_id], int(rw_lengths[table_id]), rw_totals[table_id])
            made = int(rw_values[table_id, rw_index])
            if made > 0:
                candidate_count = 0
                for reel in range(1, 5):
                    for row in range(4):
                        symbol = int(board[reel, row])
                        if symbol != 0 and symbol != 1 and symbol != 2:
                            candidate_reel[candidate_count] = reel
                            candidate_row[candidate_count] = row
                            candidate_count += 1
                if candidate_count >= made:
                    source_index = np.random.randint(0, pending_count)
                    board[pending_reel[source_index], pending_row[source_index]] = 1
                    for index in range(made):
                        picked = index + np.random.randint(0, candidate_count - index)
                        temp_reel = candidate_reel[index]
                        temp_row = candidate_row[index]
                        candidate_reel[index] = candidate_reel[picked]
                        candidate_row[index] = candidate_row[picked]
                        candidate_reel[picked] = temp_reel
                        candidate_row[picked] = temp_row
                        board[candidate_reel[index], candidate_row[index]] = 1
                    w2_events += 1
                    if made < w2_counts.shape[1]:
                        w2_counts[scene, made] += 1
                    w2_used = 1
        pending_count = 0
        hit_mask[:, :] = 0
        raw_total = 0.0
        detail_ways = np.zeros(19, dtype=np.int64)
        detail_length = np.zeros(19, dtype=np.int16)
        detail_raw = np.zeros(19, dtype=np.float64)
        for target in range(3, 11):
            ways = 1
            matched_reels = 0
            for reel in range(5):
                count = 0
                for row in range(4):
                    symbol = int(board[reel, row])
                    if symbol == 0 or symbol == 1 or _canonical(symbol) == target:
                        count += 1
                if count == 0:
                    break
                ways *= count
                matched_reels += 1
            if matched_reels < 3:
                continue
            raw_pay = pays[target, matched_reels - 3] * ways
            if raw_pay <= 0.0:
                continue
            raw_total += raw_pay
            detail_ways[target] = ways
            detail_length[target] = matched_reels
            detail_raw[target] = raw_pay
            for reel in range(matched_reels):
                for row in range(4):
                    symbol = int(board[reel, row])
                    if symbol == 0 or symbol == 1 or _canonical(symbol) == target:
                        hit_mask[reel, row] = 1
        if raw_total <= 0.0:
            break
        multiplier = int(multipliers[table_id, min(cascades, 3)])
        if multiplier > max_multiplier:
            max_multiplier = multiplier
        pay_total += raw_total * multiplier * 100.0 * bet_multi
        cascades += 1
        for target in range(3, 11):
            if detail_length[target] <= 0:
                continue
            symbol_hits[target] += detail_ways[target]
            award = detail_raw[target] * multiplier * 100.0 * bet_multi
            symbol_pay[target] += award
            length_index = int(detail_length[target]) - 3
            length_hits[scene, target, length_index] += 1
            length_pay[scene, target, length_index] += award
        for reel in range(5):
            for row in range(4):
                if hit_mask[reel, row] == 0:
                    continue
                symbol = int(board[reel, row])
                if 11 <= symbol <= 18:
                    board[reel, row] = 0
                    pending_reel[pending_count] = reel
                    pending_row[pending_count] = row
                    pending_count += 1
                    golden_converted += 1
                else:
                    board[reel, row] = -1
        for reel in range(5):
            length = int(drop_lengths[table_id, reel])
            for row in range(4):
                if board[reel, row] != -1:
                    continue
                index = _pick_index(drop_cumulative[table_id, reel], length, drop_totals[table_id, reel])
                symbol = int(drop_values[table_id, reel, index])
                board[reel, row] = symbol
                dropped_symbols[scene, reel, symbol] += 1
                if _canonical(symbol) == 3:
                    m1_present = 1

    scatter_count = 0
    for reel in range(5):
        for row in range(4):
            if board[reel, row] == 2:
                scatter_count += 1
    return (
        pay_total, scatter_count, cascades, max_multiplier, golden_converted,
        w2_events, m1_present, initial_gold,
    )


@njit(nogil=True, cache=True)
def _free_session(
    super_mode, bet_multi,
    reel_symbols, reel_cumulative, reel_lengths, reel_totals,
    drop_values, drop_cumulative, drop_lengths, drop_totals,
    rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
    free_ids, free_cum, free_len, free_total,
    retrigger_ids, retrigger_cum, retrigger_len, retrigger_total,
    super_id, free_spins, retrigger_spins, free_spin_cap,
    scalars, combo_fg, symbol_hits, symbol_pay, length_hits, length_pay,
    initial_symbols, dropped_symbols, w2_counts,
):
    queue = np.empty(free_spin_cap, dtype=np.int16)
    queue_size = min(free_spins, free_spin_cap)
    for index in range(queue_size):
        queue[index] = free_ids[_pick_index(free_cum, free_len, free_total)]
    queue_head = 0
    remaining = queue_size
    played = 0
    session_pay = 0.0
    session_max = 1
    while remaining > 0 and played < free_spin_cap:
        remaining -= 1
        played += 1
        table_id = super_id if super_mode else int(queue[queue_head])
        queue_head += 1
        spin = _spin(
            table_id, True, 1, bet_multi,
            reel_symbols, reel_cumulative, reel_lengths, reel_totals,
            drop_values, drop_cumulative, drop_lengths, drop_totals,
            rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
            symbol_hits, symbol_pay, length_hits, length_pay, initial_symbols,
            dropped_symbols, w2_counts,
        )
        pay, scatter, cascades, max_mult, golden, w2_events, m1, gold_count = spin
        session_pay += pay
        session_max = max(session_max, max_mult)
        scalars[S_FG_SPINS] += 1
        scalars[S_CASCADES_FG] += cascades
        scalars[S_GOLDEN] += golden
        scalars[S_W2_EVENTS] += w2_events
        scalars[S_FG_W2_EVENTS] += w2_events
        scalars[S_FG_M1] += m1
        scalars[S_FG_HIT] += pay > 0.0
        scalars[S_FG_GOLD_SPINS] += gold_count > 0
        scalars[S_FG_GOLD_SYMBOLS] += gold_count
        combo_fg[min(cascades, 5)] += 1
        if scatter >= 3 and played + remaining < free_spin_cap:
            add = min(retrigger_spins, free_spin_cap - played - remaining)
            if add > 0:
                scalars[S_RETRIGGERS] += 1
                for _ in range(add):
                    queue[queue_size] = retrigger_ids[_pick_index(retrigger_cum, retrigger_len, retrigger_total)]
                    queue_size += 1
                remaining += add
    return session_pay, session_max


@njit(nogil=True, cache=True)
def _chunk(rounds, bet_mode, bet_multi, seed, packed):
    (
        reel_symbols, reel_cumulative, reel_lengths, reel_totals,
        drop_values, drop_cumulative, drop_lengths, drop_totals,
        rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
        base_ids, base_cum, base_len, base_total,
        free_ids, free_cum, free_len, free_total,
        retrigger_ids, retrigger_cum, retrigger_len, retrigger_total,
        super_id, free_spins, retrigger_spins, free_spin_cap, buy_price, super_buy_price,
    ) = packed
    np.random.seed(seed)
    scalars = np.zeros(SCALAR_COUNT, dtype=np.float64)
    w2_counts = np.zeros((2, 5), dtype=np.int64)
    combo_bg = np.zeros(6, dtype=np.int64)
    combo_fg = np.zeros(6, dtype=np.int64)
    buckets = np.zeros(5, dtype=np.int64)
    symbol_hits = np.zeros(19, dtype=np.int64)
    symbol_pay = np.zeros(19, dtype=np.float64)
    length_hits = np.zeros((2, 19, 3), dtype=np.int64)
    length_pay = np.zeros((2, 19, 3), dtype=np.float64)
    initial_symbols = np.zeros((2, 5, 19), dtype=np.int64)
    dropped_symbols = np.zeros((2, 5, 19), dtype=np.int64)
    wager_factor = 1.0 if bet_mode == 0 else buy_price if bet_mode == 2 else super_buy_price
    wager = 100.0 * bet_multi * wager_factor

    for _ in range(rounds):
        pay_bg = 0.0
        pay_fg = 0.0
        round_max = 1
        if bet_mode == 0:
            table_id = int(base_ids[_pick_index(base_cum, base_len, base_total)])
            spin = _spin(
                table_id, False, 0, bet_multi,
                reel_symbols, reel_cumulative, reel_lengths, reel_totals,
                drop_values, drop_cumulative, drop_lengths, drop_totals,
                rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
                symbol_hits, symbol_pay, length_hits, length_pay, initial_symbols,
                dropped_symbols, w2_counts,
            )
            pay_bg, scatter, cascades, max_mult, golden, w2_events, m1, gold_count = spin
            round_max = max(round_max, max_mult)
            scalars[S_CASCADES_BG] += cascades
            scalars[S_GOLDEN] += golden
            scalars[S_W2_EVENTS] += w2_events
            scalars[S_BG_W2_EVENTS] += w2_events
            scalars[S_BG_M1] += m1
            scalars[S_BG_HIT] += pay_bg > 0.0
            scalars[S_BG_GOLD_SPINS] += gold_count > 0
            scalars[S_BG_GOLD_SYMBOLS] += gold_count
            combo_bg[min(cascades, 5)] += 1
            if scatter >= 3:
                scalars[S_FG_TRIGGERS] += 1
                pay_fg, fg_max = _free_session(
                    False, bet_multi,
                    reel_symbols, reel_cumulative, reel_lengths, reel_totals,
                    drop_values, drop_cumulative, drop_lengths, drop_totals,
                    rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
                    free_ids, free_cum, free_len, free_total,
                    retrigger_ids, retrigger_cum, retrigger_len, retrigger_total,
                    super_id, free_spins, retrigger_spins, free_spin_cap,
                    scalars, combo_fg, symbol_hits, symbol_pay, length_hits, length_pay,
                    initial_symbols, dropped_symbols, w2_counts,
                )
                round_max = max(round_max, fg_max)
        else:
            scalars[S_FG_TRIGGERS] += 1
            pay_fg, round_max = _free_session(
                bet_mode == 3, bet_multi,
                reel_symbols, reel_cumulative, reel_lengths, reel_totals,
                drop_values, drop_cumulative, drop_lengths, drop_totals,
                rw_values, rw_cumulative, rw_lengths, rw_totals, multipliers, pays,
                free_ids, free_cum, free_len, free_total,
                retrigger_ids, retrigger_cum, retrigger_len, retrigger_total,
                super_id, free_spins, retrigger_spins, free_spin_cap,
                scalars, combo_fg, symbol_hits, symbol_pay, length_hits, length_pay,
                initial_symbols, dropped_symbols, w2_counts,
            )
            combo_bg[0] += 1
        total_pay = pay_bg + pay_fg
        ratio = total_pay / wager if wager > 0.0 else 0.0
        scalars[S_ROUNDS] += 1
        scalars[S_COIN_IN] += wager
        scalars[S_PAY_BG] += pay_bg
        scalars[S_PAY_FG] += pay_fg
        scalars[S_HIT_ROUNDS] += total_pay > 0.0
        scalars[S_MAX_MULTIPLIER] = max(scalars[S_MAX_MULTIPLIER], round_max)
        scalars[S_WIN_X_SUM] += ratio
        scalars[S_WIN_X_SQUARE] += ratio * ratio
        bucket = 0 if ratio == 0.0 else 1 if ratio < 1.0 else 2 if ratio < 10.0 else 3 if ratio < 100.0 else 4
        buckets[bucket] += 1
    return (
        scalars, w2_counts, combo_bg, combo_fg, buckets, symbol_hits, symbol_pay,
        length_hits, length_pay, initial_symbols, dropped_symbols,
    )


def _merge(chunks):
    merged = [np.zeros_like(value) for value in chunks[0]]
    maximum = 1.0
    for chunk in chunks:
        maximum = max(maximum, float(chunk[0][S_MAX_MULTIPLIER]))
        for index, value in enumerate(chunk):
            merged[index] += value
    merged[0][S_MAX_MULTIPLIER] = maximum
    return tuple(merged)


def warm(packed, bet_mode: int, bet_multi: int, seed: int = 46046) -> None:
    """Compile/load the exact kernel signature before simulation timing."""
    _chunk(1, int(bet_mode), int(bet_multi), int(seed), packed)


def run_prepared(packed, rounds: int, bet_mode: int, bet_multi: int, threads: int, seed: int = 46046):
    threads = max(1, min(int(threads), int(rounds)))
    base, extra = divmod(int(rounds), threads)
    sizes = [base + (1 if index < extra else 0) for index in range(threads)]
    if threads == 1:
        return _chunk(sizes[0], int(bet_mode), int(bet_multi), int(seed), packed)
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = [
            pool.submit(_chunk, size, int(bet_mode), int(bet_multi), int(seed + index * 100003), packed)
            for index, size in enumerate(sizes) if size
        ]
        return _merge([future.result() for future in futures])


def run(config: dict[str, Any], rounds: int, bet_mode: int, bet_multi: int, threads: int, seed: int = 46046):
    packed = prepare_config(config)
    warm(packed, bet_mode, bet_multi, seed)
    return run_prepared(packed, rounds, bet_mode, bet_multi, threads, seed)


def to_stats(result) -> dict[str, Any]:
    (
        s, w2, combo_bg, combo_fg, buckets, symbol_hits, symbol_pay,
        length_hits, length_pay, initial_symbols, dropped_symbols,
    ) = result
    integer = lambda index: int(round(float(s[index])))
    stats: dict[str, Any] = {
        "rounds": integer(S_ROUNDS), "coin_in": float(s[S_COIN_IN]),
        "pay_bg": float(s[S_PAY_BG]), "pay_fg": float(s[S_PAY_FG]),
        "hit_rounds": integer(S_HIT_ROUNDS), "fg_triggers": integer(S_FG_TRIGGERS),
        "fg_spins": integer(S_FG_SPINS), "retriggers": integer(S_RETRIGGERS),
        "cascades_bg": integer(S_CASCADES_BG), "cascades_fg": integer(S_CASCADES_FG),
        "golden_converted": integer(S_GOLDEN), "w2_events": integer(S_W2_EVENTS),
        "bg_w2_events": integer(S_BG_W2_EVENTS), "fg_w2_events": integer(S_FG_W2_EVENTS),
        "bg_m1_spins": integer(S_BG_M1), "fg_m1_spins": integer(S_FG_M1),
        "bg_hit_spins": integer(S_BG_HIT), "fg_hit_spins": integer(S_FG_HIT),
        "bg_gold_spins": integer(S_BG_GOLD_SPINS), "fg_gold_spins": integer(S_FG_GOLD_SPINS),
        "bg_gold_symbols": integer(S_BG_GOLD_SYMBOLS), "fg_gold_symbols": integer(S_FG_GOLD_SYMBOLS),
        "max_multiplier": integer(S_MAX_MULTIPLIER), "win_x_sum": float(s[S_WIN_X_SUM]),
        "win_x_square": float(s[S_WIN_X_SQUARE]),
        "combo_bg": Counter({index: int(value) for index, value in enumerate(combo_bg) if value}),
        "combo_fg": Counter({index: int(value) for index, value in enumerate(combo_fg) if value}),
        "buckets": Counter({label: int(value) for label, value in zip(("0", "(0,1)", "[1,10)", "[10,100)", "100+"), buckets) if value}),
        "symbol_hits": Counter({symbol: int(symbol_hits[symbol]) for symbol in range(19) if symbol_hits[symbol]}),
        "symbol_pay": Counter({symbol: float(symbol_pay[symbol]) for symbol in range(19) if symbol_pay[symbol]}),
        "bg_w2_counts": Counter({index: int(w2[0, index]) for index in range(5) if w2[0, index]}),
        "fg_w2_counts": Counter({index: int(w2[1, index]) for index in range(5) if w2[1, index]}),
    }
    for scene, prefix in ((0, "bg"), (1, "fg")):
        stats[f"{prefix}_symbol_length_hits"] = Counter({
            (symbol, length + 3): int(length_hits[scene, symbol, length])
            for symbol in range(19) for length in range(3) if length_hits[scene, symbol, length]
        })
        stats[f"{prefix}_symbol_length_pay"] = Counter({
            (symbol, length + 3): float(length_pay[scene, symbol, length])
            for symbol in range(19) for length in range(3) if length_pay[scene, symbol, length]
        })
        stats[f"{prefix}_initial_symbols"] = Counter({
            (reel, symbol): int(initial_symbols[scene, reel, symbol])
            for reel in range(5) for symbol in range(19) if initial_symbols[scene, reel, symbol]
        })
        stats[f"{prefix}_drop_symbols"] = Counter({
            (reel, symbol): int(dropped_symbols[scene, reel, symbol])
            for reel in range(5) for symbol in range(19) if dropped_symbols[scene, reel, symbol]
        })
    return stats
