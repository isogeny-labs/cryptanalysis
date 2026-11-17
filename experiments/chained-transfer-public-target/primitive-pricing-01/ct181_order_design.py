#!/usr/bin/env python3
"""CT181 pre-admission synthetic ABBA/BAAB counterbalance design, not a benchmark.

This module does not invoke Rust, access a measured panel, or solve a DLP.
It is a negative-control calculation for the position-confounded CT179 design.
"""
import math
import random
import statistics

PACKETS = 48
BLOCKS = 8
SEED = 20261117
ABBA = ("A", "B", "B", "A", "A", "A")
BAAB = ("B", "A", "A", "B", "A", "A")
SLOT_FACTORS = (3, 2, 2, 3, 3, 3)


def order(block, packet, counterbalanced=True):
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("invalid block")
    if type(packet) is not int or not 0 <= packet < PACKETS:
        raise ValueError("invalid packet")
    return BAAB if counterbalanced and (block + packet) % 2 else ABBA


def roster(counterbalanced=True):
    for block in range(BLOCKS):
        packet_ids = list(range(PACKETS))
        random.Random(SEED + block).shuffle(packet_ids)
        for packet in packet_ids:
            for position, arm in enumerate(order(block, packet, counterbalanced)):
                yield block, packet, position, arm


def one_block_log_ratio(arms, a_time, b_time, slot_factors=SLOT_FACTORS):
    """Exact A/B assignment to the four treatment slots; A/A is diagnostic."""
    if len(arms) != 6 or len(slot_factors) != 6:
        raise ValueError("six slots required")
    if sorted(arms[:4]) != ["A", "A", "B", "B"] or arms[4:] != ("A", "A"):
        raise ValueError("must have two A and two B plus two A/A controls")
    if any(type(v) is not int or v <= 0 for v in (a_time, b_time, *slot_factors)):
        raise ValueError("all synthetic times/factors must be positive integers")
    durations = [slot_factors[pos] * (a_time if arm == "A" else b_time)
                 for pos, arm in enumerate(arms)]
    a_sum = sum(durations[pos] for pos in range(4) if arms[pos] == "A")
    b_sum = sum(durations[pos] for pos in range(4) if arms[pos] == "B")
    return math.log(a_sum / b_sum), abs(math.log(durations[4] / durations[5]))


def packet_ratio(packet, a_time, b_time, counterbalanced=True):
    effects = [one_block_log_ratio(order(block, packet, counterbalanced),
                                   a_time, b_time)[0]
               for block in range(BLOCKS)]
    return math.exp(statistics.median(effects))


def null_diagnostic():
    return {
        "scope": "synthetic slot-confounding counterexample only; no native timing or ECDLP",
        "legacy_null_direct_over_retained": packet_ratio(0, 200, 200, False),
        "balanced_null_direct_over_retained": packet_ratio(0, 200, 200, True),
        "legacy_true_5_over_4": packet_ratio(0, 125, 100, False),
        "balanced_true_5_over_4": packet_ratio(0, 125, 100, True),
        "total_roster_entries": sum(1 for _ in roster(True)),
        "complete_single_target_ecdlp_advantage_established": False,
        "standing": "[pcc:unverified]",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(null_diagnostic(), sort_keys=True, allow_nan=False))
