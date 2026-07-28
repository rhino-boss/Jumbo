"""H046 幸運王牌 / Lucky Ace simulator.

Structure and command-line ergonomics follow the H026 simulator project, while
the actual board flow follows 101003: weighted symbol sampling, Ways,
Cascade, golden-symbol retention, and WW2 replication.
"""

from __future__ import annotations

import argparse
import bisect
import json
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = BASE_DIR / "Source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from xlsx_to_config import ID_TO_SYMBOL, load_game_config  # noqa: E402


# ===== User Settings (used when no command-line override is provided) =====

SOURCE_XLSX = "H016192.xlsx"
TOTAL_ROUNDS = 100_000
BET_MODE = 0  # 0=Normal Bet, 1=Buy Feature, 2=Buy Super Feature
BET = 100.0
SEED = 46016
OUTPUT_JSON = False
CARD_SYSTEM_ENABLED = True
CARD_PROFILE = "weight_2"  # Weight 1=newbie, Weight 2=oldhand, Weight 3=alternate
CARD_RETRY_LIMIT = 200_000


WW1 = 0
WW2 = 1
SCATTER = 2
BASE_SYMBOLS = tuple(range(3, 11))
GOLD_START = 11
GOLD_END = 18


def canonical_symbol(symbol: int) -> int:
    if GOLD_START <= symbol <= GOLD_END:
        return symbol - 8
    return symbol


def weighted_pick(rng: random.Random, values: list[Any], weights: list[float]) -> Any:
    total = sum(weights)
    if not values:
        raise ValueError("weighted_pick received no values")
    if total <= 0:
        return values[0]
    target = rng.random() * total
    running = 0.0
    for value, weight in zip(values, weights):
        running += weight
        if target < running:
            return value
    return values[-1]


@dataclass
class PreparedReel:
    symbols: list[int]
    cumulative: list[float]
    total: float

    def pick(self, rng: random.Random) -> int:
        if self.total <= 0:
            raise ValueError("Reel has no positive weights")
        index = bisect.bisect_left(self.cumulative, rng.random() * self.total)
        return self.symbols[min(index, len(self.symbols) - 1)]


@dataclass
class PreparedTable:
    reels: list[PreparedReel]
    random_wild_values: list[int]
    random_wild_weights: list[float]
    multipliers: list[int]


@dataclass
class WinResult:
    raw_pay: float
    hit_positions: set[tuple[int, int]]
    details: list[dict[str, Any]]


@dataclass
class SpinResult:
    pay: float
    scatter_count: int
    cascades: int
    max_multiplier: int
    golden_converted: int
    ww2_events: int
    initial_board: list[list[int]] = field(default_factory=list)
    final_board: list[list[int]] = field(default_factory=list)


@dataclass
class SessionResult:
    pay: float = 0.0
    free_spins: int = 0
    retriggers: int = 0
    cascades: int = 0
    max_multiplier: int = 1
    golden_converted: int = 0
    ww2_events: int = 0
    triggered_free_game: bool = False


class LuckyAceGame:
    def __init__(
        self,
        config: dict[str, Any],
        seed: int | None = None,
        *,
        card_enabled: bool = CARD_SYSTEM_ENABLED,
        card_profile: str = CARD_PROFILE,
    ):
        self.config = config
        self.rng = random.Random(seed)
        self.card_enabled = card_enabled
        self.card_profile = card_profile
        self.tables = {
            name: self._prepare_table(raw) for name, raw in config["tables"].items()
        }

    @staticmethod
    def _prepare_table(raw: dict[str, Any]) -> PreparedTable:
        prepared_reels = []
        for symbols, weights in zip(raw["reels"], raw["weights"]):
            cumulative = []
            running = 0.0
            for weight in weights:
                running += max(0.0, float(weight))
                cumulative.append(running)
            prepared_reels.append(PreparedReel(list(map(int, symbols)), cumulative, running))
        random_wild = raw["random_wild"]
        return PreparedTable(
            reels=prepared_reels,
            random_wild_values=list(map(int, random_wild["values"])),
            random_wild_weights=list(map(float, random_wild["weights"])),
            multipliers=list(map(int, raw["multipliers"])),
        )

    def _pick_bg_table(self) -> str:
        weights = self.config["base_table_weights"]
        choice = weighted_pick(
            self.rng,
            ["bg_high", "bg_low"],
            [float(weights["high"]), float(weights["low"])],
        )
        return str(choice)

    def _draw(self, table_name: str, reel: int) -> int:
        return self.tables[table_name].reels[reel].pick(self.rng)

    def generate_board(self, table_name: str) -> list[list[int]]:
        # Internal shape is [reel][row], row 0 at the bottom.
        return [[self._draw(table_name, reel) for _ in range(4)] for reel in range(5)]

    def evaluate(self, board: list[list[int]]) -> WinResult:
        total = 0.0
        hit_positions: set[tuple[int, int]] = set()
        details: list[dict[str, Any]] = []
        pays = self.config["pays"]

        for target in BASE_SYMBOLS:
            counts: list[int] = []
            matching_positions: list[list[tuple[int, int]]] = []
            for reel in range(5):
                positions = []
                for row, symbol in enumerate(board[reel]):
                    canonical = canonical_symbol(symbol)
                    if symbol in (WW1, WW2) or canonical == target:
                        positions.append((reel, row))
                if not positions:
                    break
                counts.append(len(positions))
                matching_positions.append(positions)

            length = len(counts)
            if length < 3:
                continue
            ways = 1
            for count in counts:
                ways *= count
            pay = float(pays[str(target)][length - 3]) * ways
            if pay <= 0:
                continue
            total += pay
            for reel_positions in matching_positions:
                hit_positions.update(reel_positions)
            details.append(
                {
                    "symbol": ID_TO_SYMBOL[target],
                    "length": length,
                    "ways": ways,
                    "raw_pay": pay,
                }
            )
        return WinResult(total, hit_positions, details)

    def _apply_random_wild(
        self,
        board: list[list[int]],
        table: PreparedTable,
        converted_positions: list[tuple[int, int]],
    ) -> int:
        if not converted_positions:
            return 0
        extra_count = int(
            weighted_pick(
                self.rng,
                table.random_wild_values,
                table.random_wild_weights,
            )
        )
        if extra_count <= 0:
            return 0

        source_reel, source_row = self.rng.choice(converted_positions)
        if board[source_reel][source_row] == WW1:
            board[source_reel][source_row] = WW2

        candidates = [
            (reel, row)
            for reel in range(1, 5)
            for row, symbol in enumerate(board[reel])
            if symbol not in (WW1, WW2, SCATTER)
        ]
        self.rng.shuffle(candidates)
        for reel, row in candidates[:extra_count]:
            board[reel][row] = WW2
        return min(extra_count, len(candidates))

    def play_spin(self, table_name: str, *, free_game: bool = False) -> SpinResult:
        table = self.tables[table_name]
        multipliers = table.multipliers or ([2, 4, 6, 10] if free_game else [1, 2, 3, 5])
        board = self.generate_board(table_name)
        initial_board = [reel[:] for reel in board]
        total_pay = 0.0
        combo = 0
        golden_converted = 0
        ww2_events = 0
        pending_gold: list[tuple[int, int]] = []
        bg_ww2_used = False

        while True:
            if pending_gold and (free_game or not bg_ww2_used):
                placed = self._apply_random_wild(board, table, pending_gold)
                if placed > 0:
                    ww2_events += 1
                    if not free_game:
                        bg_ww2_used = True
            pending_gold = []

            win = self.evaluate(board)
            if win.raw_pay <= 0:
                break

            multiplier = multipliers[min(combo, len(multipliers) - 1)]
            total_pay += win.raw_pay * multiplier * BET
            combo += 1

            # Golden winners remain in place as Wild; all other winning cells vanish.
            for reel, row in win.hit_positions:
                symbol = board[reel][row]
                if GOLD_START <= symbol <= GOLD_END:
                    board[reel][row] = WW1
                    pending_gold.append((reel, row))
                    golden_converted += 1
                else:
                    board[reel][row] = -1

            # Gravity per reel: row 0 is bottom, refill the empty cells above.
            for reel in range(5):
                remaining = [symbol for symbol in board[reel] if symbol != -1]
                board[reel] = remaining + [
                    self._draw(table_name, reel) for _ in range(4 - len(remaining))
                ]

        return SpinResult(
            pay=total_pay,
            scatter_count=sum(symbol == SCATTER for reel in board for symbol in reel),
            cascades=combo,
            max_multiplier=multipliers[min(max(combo - 1, 0), len(multipliers) - 1)],
            golden_converted=golden_converted,
            ww2_events=ww2_events,
            initial_board=initial_board,
            final_board=[reel[:] for reel in board],
        )

    def _pick_free_mix(self) -> list[str]:
        choices = self.config["free_game_mix"]["choices"]
        choice = weighted_pick(
            self.rng,
            choices,
            [float(item["weight"]) for item in choices],
        )
        sequence = ["high"] * int(choice["high"]) + ["low"] * int(choice["low"])
        self.rng.shuffle(sequence)
        return sequence

    def _pick_high_variant(self) -> str:
        return str(
            weighted_pick(
                self.rng,
                ["fg_high_a", "fg_high_k", "fg_high_q", "fg_high_j"],
                list(map(float, self.config["free_game_mix"]["high_variant_weights"])),
            )
        )

    def _pick_card(
        self,
        section: str,
        profile_override: str | None = None,
    ) -> dict[str, Any]:
        card_system = self.config.get("card_system", {})
        profiles = card_system.get("profiles", {})
        profile_name = profile_override or self.card_profile
        profile = profiles.get(profile_name)
        if profile is None:
            raise KeyError(f"Unknown card profile: {profile_name}")
        cards = list(profile.get(section, []))
        if not cards:
            raise ValueError(f"No enabled cards for {profile_name}/{section}")
        return dict(
            weighted_pick(
                self.rng,
                cards,
                [float(card.get("weight", 0)) for card in cards],
            )
        )

    @staticmethod
    def _card_matches(card: dict[str, Any], pay: float) -> bool:
        ratio = pay / BET
        return float(card["min"]) < ratio <= float(card["max"])

    def _play_card_spin(self, card: dict[str, Any]) -> SpinResult:
        if card.get("type") == "free_game":
            for _ in range(CARD_RETRY_LIMIT):
                spin = self.play_spin("bg_low", free_game=False)
                if spin.scatter_count >= 3:
                    return spin
            raise RuntimeError("Card system could not generate the selected FG trigger card")

        table_name = "bg_low" if card.get("table") == "A" else "bg_high"
        for _ in range(CARD_RETRY_LIMIT):
            spin = self.play_spin(table_name, free_game=False)
            if spin.scatter_count < 3 and self._card_matches(card, spin.pay):
                return spin
        raise RuntimeError(
            f"Card system could not match BG range ({card['min']}, {card['max']}]"
        )

    def _play_card_feature(
        self,
        section: str,
        *,
        super_mode: bool = False,
    ) -> SessionResult:
        # H016's Super Feature target distribution is stored in Weight 1.
        # Weight 2/3 in that block are the ordinary-feature comparison columns.
        profile = "weight_1" if section == "super_feature" else None
        card = self._pick_card(section, profile_override=profile)
        for _ in range(CARD_RETRY_LIMIT):
            result = self.play_free_game(super_mode=super_mode)
            if self._card_matches(card, result.pay):
                return result
        raise RuntimeError(
            f"Card system could not match {section} range "
            f"({card['min']}, {card['max']}]"
        )

    @staticmethod
    def _merge_spin(session: SessionResult, spin: SpinResult) -> None:
        session.pay += spin.pay
        session.cascades += spin.cascades
        session.max_multiplier = max(session.max_multiplier, spin.max_multiplier)
        session.golden_converted += spin.golden_converted
        session.ww2_events += spin.ww2_events

    def play_free_game(self, *, super_mode: bool = False) -> SessionResult:
        result = SessionResult(triggered_free_game=True)
        cap = int(self.config["free_spin_cap"])
        remaining = int(self.config["free_spins"])
        mode_queue = self._pick_free_mix()

        while remaining > 0 and result.free_spins < cap:
            remaining -= 1
            result.free_spins += 1
            if super_mode:
                table_name = "super"
            else:
                surface = mode_queue.pop(0) if mode_queue else "low"
                table_name = self._pick_high_variant() if surface == "high" else "fg_low"

            spin = self.play_spin(table_name, free_game=True)
            self._merge_spin(result, spin)
            if spin.scatter_count >= 3 and result.free_spins + remaining < cap:
                add = min(int(self.config["retrigger_spins"]), cap - result.free_spins - remaining)
                if add > 0:
                    remaining += add
                    result.retriggers += 1
                    if super_mode:
                        mode_queue.extend(["high"] * add)
                    else:
                        extra = ["high"] + ["low"] * max(0, add - 1)
                        self.rng.shuffle(extra)
                        mode_queue.extend(extra)
        return result

    def play_normal_round(self) -> SessionResult:
        result = SessionResult()
        card = self._pick_card("base_game") if self.card_enabled else None
        spin = (
            self._play_card_spin(card)
            if card is not None
            else self.play_spin(self._pick_bg_table(), free_game=False)
        )
        self._merge_spin(result, spin)
        if spin.scatter_count >= 3:
            free_result = (
                self._play_card_feature("free_game")
                if self.card_enabled
                else self.play_free_game()
            )
            result.triggered_free_game = True
            result.pay += free_result.pay
            result.free_spins += free_result.free_spins
            result.retriggers += free_result.retriggers
            result.cascades += free_result.cascades
            result.max_multiplier = max(result.max_multiplier, free_result.max_multiplier)
            result.golden_converted += free_result.golden_converted
            result.ww2_events += free_result.ww2_events
        return result

    def play_buy_round(self, *, super_mode: bool = False) -> SessionResult:
        if self.card_enabled:
            section = "super_feature" if super_mode else "buy_feature"
            return self._play_card_feature(section, super_mode=super_mode)

        # The Buy table is designed as a guaranteed 3+ C1 entry surface. Keep a
        # defensive retry so malformed future tables cannot enter FG without C1.
        entry = None
        for _ in range(10_000):
            candidate = self.play_spin("buy", free_game=False)
            if candidate.scatter_count >= 3:
                entry = candidate
                break
        if entry is None:
            raise RuntimeError("Buy Feature table failed to produce 3+ C1 in 10,000 attempts")

        result = SessionResult(triggered_free_game=True)
        self._merge_spin(result, entry)
        free_result = self.play_free_game(super_mode=super_mode)
        result.pay += free_result.pay
        result.free_spins = free_result.free_spins
        result.retriggers = free_result.retriggers
        result.cascades += free_result.cascades
        result.max_multiplier = max(result.max_multiplier, free_result.max_multiplier)
        result.golden_converted += free_result.golden_converted
        result.ww2_events += free_result.ww2_events
        return result


def format_board(board: list[list[int]]) -> str:
    rows = []
    for row in range(3, -1, -1):
        rows.append(" | ".join(f"{ID_TO_SYMBOL[board[reel][row]]:>3}" for reel in range(5)))
    return "\n".join(rows)


def run_simulation(
    config: dict[str, Any],
    rounds: int,
    bet_mode: int,
    seed: int | None,
    show_sample: bool,
    card_enabled: bool = CARD_SYSTEM_ENABLED,
    card_profile: str = CARD_PROFILE,
) -> dict[str, Any]:
    game = LuckyAceGame(
        config,
        seed,
        card_enabled=card_enabled,
        card_profile=card_profile,
    )
    started = time.perf_counter()
    total_pay = 0.0
    total_bet = 0.0
    hit_rounds = 0
    fg_triggers = 0
    free_spins = 0
    retriggers = 0
    cascades = 0
    golden_converted = 0
    ww2_events = 0
    max_multiplier = 1
    pay_buckets: Counter[str] = Counter()
    first_result: SessionResult | None = None

    for _ in range(rounds):
        if bet_mode == 0:
            result = game.play_normal_round()
            wager = BET
        elif bet_mode == 1:
            result = game.play_buy_round(super_mode=False)
            wager = BET * float(config["buy_price"])
        elif bet_mode == 2:
            result = game.play_buy_round(super_mode=True)
            wager = BET * float(config["super_buy_price"])
        else:
            raise ValueError(f"Unsupported bet mode: {bet_mode}")

        if first_result is None:
            first_result = result
        total_pay += result.pay
        total_bet += wager
        hit_rounds += int(result.pay > 0)
        fg_triggers += int(result.triggered_free_game)
        free_spins += result.free_spins
        retriggers += result.retriggers
        cascades += result.cascades
        golden_converted += result.golden_converted
        ww2_events += result.ww2_events
        max_multiplier = max(max_multiplier, result.max_multiplier)

        ratio = result.pay / wager if wager else 0
        if ratio == 0:
            pay_buckets["0x"] += 1
        elif ratio < 1:
            pay_buckets["(0,1)x"] += 1
        elif ratio < 10:
            pay_buckets["[1,10)x"] += 1
        elif ratio < 100:
            pay_buckets["[10,100)x"] += 1
        else:
            pay_buckets["100x+"] += 1

    duration = time.perf_counter() - started
    summary = {
        "game": f"{config['game_id']} {config['name_zh']}",
        "parsheet": config["parsheet_id"],
        "source_xlsx": config["source_xlsx"],
        "card_system": card_enabled,
        "card_profile": (
            f"{card_profile} (Super uses weight_1)"
            if card_enabled and bet_mode == 2
            else card_profile if card_enabled else "off"
        ),
        "bet_mode": bet_mode,
        "rounds": rounds,
        "bet_per_round": BET
        * (
            1
            if bet_mode == 0
            else config["buy_price"]
            if bet_mode == 1
            else config["super_buy_price"]
        ),
        "total_bet": total_bet,
        "total_pay": total_pay,
        "rtp": total_pay / total_bet if total_bet else 0,
        "hit_rate": hit_rounds / rounds if rounds else 0,
        "fg_trigger_rate": fg_triggers / rounds if rounds else 0,
        "avg_free_spins": free_spins / fg_triggers if fg_triggers else 0,
        "retriggers": retriggers,
        "avg_cascades": cascades / rounds if rounds else 0,
        "golden_converted": golden_converted,
        "ww2_events": ww2_events,
        "max_multiplier": max_multiplier,
        "duration_seconds": duration,
        "rounds_per_second": rounds / duration if duration else 0,
        "pay_buckets": dict(pay_buckets),
    }

    if show_sample:
        sample_game = LuckyAceGame(config, seed, card_enabled=False)
        sample = sample_game.play_spin(sample_game._pick_bg_table())
        print("\n=== Sample BG Spin ===")
        print("Initial:")
        print(format_board(sample.initial_board))
        print("\nFinal:")
        print(format_board(sample.final_board))
        print(
            f"pay={sample.pay:.2f}, cascades={sample.cascades}, "
            f"C1={sample.scatter_count}, max_multiplier=x{sample.max_multiplier}"
        )
    return summary


def print_summary(summary: dict[str, Any]) -> None:
    mode_labels = {0: "Normal Bet", 1: "Buy Feature", 2: "Buy Super Feature"}
    print("\n=== H046 幸運王牌 Simulation ===")
    print(f"PARsheet        : {summary['parsheet']} ({summary['source_xlsx']})")
    print(f"Mode            : {mode_labels[summary['bet_mode']]}")
    print(
        f"Card system     : "
        f"{summary['card_profile'] if summary['card_system'] else 'disabled'}"
    )
    print(f"Rounds          : {summary['rounds']:,}")
    print(f"Bet / round     : {summary['bet_per_round']:,.2f}")
    print(f"Total bet       : {summary['total_bet']:,.2f}")
    print(f"Total pay       : {summary['total_pay']:,.2f}")
    print(f"RTP             : {summary['rtp'] * 100:.6f}%")
    print(f"Hit rate        : {summary['hit_rate'] * 100:.6f}%")
    print(f"FG trigger rate : {summary['fg_trigger_rate'] * 100:.6f}%")
    print(f"Avg FG spins    : {summary['avg_free_spins']:.4f}")
    print(f"Avg cascades    : {summary['avg_cascades']:.4f}")
    print(f"Gold converted  : {summary['golden_converted']:,}")
    print(f"WW2 events      : {summary['ww2_events']:,}")
    print(f"Max multiplier  : x{summary['max_multiplier']}")
    print(f"Elapsed         : {summary['duration_seconds']:.3f}s")
    print(f"Throughput      : {summary['rounds_per_second']:,.0f} rounds/s")
    print(f"Pay buckets     : {summary['pay_buckets']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="H046 Lucky Ace simulator")
    parser.add_argument("rounds", nargs="?", type=int, default=TOTAL_ROUNDS)
    parser.add_argument(
        "bet_mode",
        nargs="?",
        type=int,
        choices=(0, 1, 2),
        default=BET_MODE,
        help="0=Normal, 1=Buy Feature, 2=Buy Super Feature",
    )
    parser.add_argument(
        "--xlsx",
        default=SOURCE_XLSX,
        help="Source xlsx filename under Source/, or an explicit path",
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument(
        "--card-profile",
        choices=("weight_1", "weight_2", "weight_3"),
        default=CARD_PROFILE,
        help="Card weight column (default: weight_2 / oldhand)",
    )
    parser.add_argument(
        "--no-card",
        action="store_true",
        help="Disable the H016 Card system and sample the raw surfaces",
    )
    parser.add_argument("--sample", action="store_true", help="Print one BG board trace")
    parser.add_argument("--json", action="store_true", default=OUTPUT_JSON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    xlsx_path = Path(args.xlsx)
    if not xlsx_path.is_absolute():
        xlsx_path = SOURCE_DIR / xlsx_path
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Source xlsx not found: {xlsx_path}")

    config = load_game_config(xlsx_path)
    summary = run_simulation(
        config,
        args.rounds,
        args.bet_mode,
        args.seed,
        args.sample,
        card_enabled=not args.no_card,
        card_profile=args.card_profile,
    )
    print_summary(summary)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
