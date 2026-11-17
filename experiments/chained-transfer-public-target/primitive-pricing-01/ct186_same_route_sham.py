#!/usr/bin/env python3
"""CT186 prospective same-route *synthetic* sham planner and offline scorer.

Never invokes Rust, runs cold processes, accesses 695/701 custody, or solves
ECDLP. A sham diagnostic is not proof against treatment-dependent carryover.
[pcc:unverified]
"""
import hashlib
import json
import math
import random
import statistics

SCHEMA = "ct186-first-four-same-route-sham/v1"
PHYSICAL_ARM = "direct_composite"
SEED = 20261118
PACKETS = 48
BLOCKS = 8
SLOTS = 4
N = PACKETS * BLOCKS * SLOTS
ABBA = ("A", "B", "B", "A")
BAAB = ("B", "A", "A", "B")
KEYS = {"block", "packet_index", "position", "label", "physical_arm", "wall_ns"}


def label_order(packet, block):
    """Each packet receives exactly four of each order, uncorrelated with CT183 parity."""
    if type(packet) is not int or not 0 <= packet < PACKETS:
        raise ValueError("invalid packet index")
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("invalid block index")
    abba_blocks = set(random.Random(SEED + packet).sample(range(BLOCKS), BLOCKS // 2))
    return ABBA if block in abba_blocks else BAAB


def roster():
    for block in range(BLOCKS):
        packets = list(range(PACKETS))
        random.Random(SEED + 10_000 + block).shuffle(packets)
        for packet in packets:
            for position, label in enumerate(label_order(packet, block)):
                yield (block, packet, position, label, PHYSICAL_ARM)


def roster_sha256():
    wire = json.dumps(list(roster()), ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(wire.encode("ascii")).hexdigest()


def plan():
    """No execution flag or entry point exists in this source-only tool."""
    return {
        "schema": SCHEMA,
        "scope": "SOURCE-ONLY blinded same-route sham; not native timing",
        "seed": SEED,
        "packets": PACKETS,
        "blocks": BLOCKS,
        "processes_if_later_admitted": N,
        "physical_arm": PHYSICAL_ARM,
        "fixture_git_blob": "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3",
        "order_roster_sha256": roster_sha256(),
        "standing": "[pcc:unverified]",
    }


def adjudicate(records, schema=SCHEMA):
    """Strict offline arithmetic on supplied source-only durations.

    Accepts exactly the proposed 1536 sham records, not native evidence. Every
    record asserts physical arm A independent of its blinded placebo label.
    """
    if schema != SCHEMA or type(records) is not list or len(records) != N:
        raise ValueError("sham schema or sample count mismatch")
    grouped = {}
    order_effects = {"ABBA": [], "BAAB": []}
    for expected, record in zip(roster(), records):
        block, packet, position, label, arm = expected
        if type(record) is not dict or set(record) != KEYS:
            raise ValueError("missing/extra sham record fields")
        for field, expected_value in (
            ("block", block),
            ("packet_index", packet),
            ("position", position),
            ("label", label),
            ("physical_arm", arm),
        ):
            observed = record[field]
            if type(observed) is not type(expected_value) or observed != expected_value:
                raise ValueError("sham roster/physical-arm mismatch: " + field)
        ns = record["wall_ns"]
        if type(ns) is not int or ns <= 0:
            raise ValueError("nonpositive/noninteger sham wall_ns")
        grouped.setdefault((packet, block), []).append(ns)
    if len(grouped) != PACKETS * BLOCKS:
        raise ValueError("missing packet-block")
    per_packet = {}
    for packet in range(PACKETS):
        changes = []
        for block in range(BLOCKS):
            times = grouped[(packet, block)]
            labels = label_order(packet, block)
            if len(times) != SLOTS:
                raise ValueError("incomplete packet-block")
            at = sum(times[pos] for pos in range(SLOTS) if labels[pos] == "A")
            bt = sum(times[pos] for pos in range(SLOTS) if labels[pos] == "B")
            effect = math.log(at / bt)
            changes.append(effect)
            order_effects["".join(labels)].append(effect)
        per_packet[packet] = statistics.median(changes)
    median = statistics.median(per_packet.values())
    return {
        "schema": "ct186-first-four-same-route-sham-source-score/v1",
        "standing": "[pcc:unverified]",
        "input_scope": "provided times, not authenticated native wall durations",
        "roster_sha256": roster_sha256(),
        "complete_records": N,
        "physical_arm": PHYSICAL_ARM,
        "median_sham_log_ratio": median,
        "median_sham_ratio": math.exp(median),
        "abba_log_median": statistics.median(order_effects["ABBA"]),
        "baab_log_median": statistics.median(order_effects["BAAB"]),
        "per_packet_log_ratios": [per_packet[i] for i in range(PACKETS)],
        "complete_single_target_ecdlp_advantage_established": False,
        "signed_independent_pcc": False,
    }


if __name__ == "__main__":
    print(json.dumps(plan(), sort_keys=True, allow_nan=False))
