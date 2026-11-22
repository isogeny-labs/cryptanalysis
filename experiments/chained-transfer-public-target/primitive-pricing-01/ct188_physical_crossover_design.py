#!/usr/bin/env python3
"""CT188 randomized physical A/B crossover design + SOURCE-ONLY algebraic diagnostic.

No subprocess, network, fixture mutation, executable, paid compute or native
execution path exists here. Supplied durations are unverified and never imply
an ECDLP speedup. See CT188_RANDOMIZED_PHYSICAL_CROSSOVER_PROTOCOL.md.
[pcc:unverified]
"""
import hashlib
import json
import math
import random
import statistics
from fractions import Fraction

SCHEMA = "ct188-randomized-physical-crossover-source/v1"
SEED = 20261119
PACKETS = 48
BLOCKS = 8
SLOTS = 6
N = PACKETS * BLOCKS * SLOTS
ARMS = {"A": "direct_composite", "B": "strongest_retained_lift_chain"}
SEQUENCES = ("AABB", "ABAB", "ABBA", "BAAB", "BABA", "BBAA",
             "ABBA", "BAAB")
FIXTURE_GIT_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
INPUT_FIELDS = {"block", "packet_index", "position", "arm", "wall_ns"}
COLUMNS = ("intercept", "period_1", "period_2", "period_3",
           "physical_B", "previous_B", "physical_B_x_previous_B")


def packet_sequences(packet):
    if type(packet) is not int or not 0 <= packet < PACKETS:
        raise ValueError("packet out of range")
    result = list(SEQUENCES)
    random.Random(SEED + 7_919 * packet).shuffle(result)
    return tuple(result)


def order(block, packet):
    if type(block) is not int or not 0 <= block < BLOCKS:
        raise ValueError("block out of range")
    sequence = packet_sequences(packet)[block]
    return sequence + "AA"


def roster():
    for block in range(BLOCKS):
        packets = list(range(PACKETS))
        random.Random(SEED + 982_451_653 + 104_729 * block).shuffle(packets)
        for packet in packets:
            for position, symbol in enumerate(order(block, packet)):
                yield (block, packet, position, ARMS[symbol])


def roster_sha256():
    raw = json.dumps(list(roster()), ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def model_row(sequence, position):
    if sequence not in SEQUENCES or type(position) is not int or not 0 <= position < 4:
        raise ValueError("invalid treatment design row")
    x = int(sequence[position] == "B")
    z = int(position > 0 and sequence[position - 1] == "B")
    return (1, int(position == 1), int(position == 2), int(position == 3),
            x, z, x * z)


def exact_rank(rows):
    """Exact rational Gaussian elimination; not a numerical rank guess."""
    matrix = [[Fraction(v) for v in row] for row in rows]
    if not matrix:
        return 0
    ncols = len(matrix[0])
    if any(len(row) != ncols for row in matrix):
        raise ValueError("ragged rank input")
    pivotrow = 0
    for col in range(ncols):
        candidate = next((r for r in range(pivotrow, len(matrix))
                          if matrix[r][col]), None)
        if candidate is None:
            continue
        matrix[pivotrow], matrix[candidate] = matrix[candidate], matrix[pivotrow]
        pivot = matrix[pivotrow][col]
        matrix[pivotrow] = [v / pivot for v in matrix[pivotrow]]
        for r in range(pivotrow + 1, len(matrix)):
            factor = matrix[r][col]
            if factor:
                matrix[r] = [a - factor * b
                             for a, b in zip(matrix[r], matrix[pivotrow])]
        pivotrow += 1
        if pivotrow == len(matrix):
            break
    return pivotrow


def assert_design():
    r = list(roster())
    if len(r) != N or len(set((b, p, i) for b, p, i, _ in r)) != N:
        raise ValueError("incorrect crossover roster")
    for packet in range(PACKETS):
        sequences = packet_sequences(packet)
        if sorted(sequences) != sorted(SEQUENCES):
            raise ValueError("packet missing treatment sequence")
        if any(sum(seq[position] == "A" for seq in sequences) != 4
               for position in range(4)):
            raise ValueError("unbalanced physical treatment by period")
        if any(order(block, packet)[4:] != "AA" for block in range(BLOCKS)):
            raise ValueError("missing physical A/A control")
        m = [model_row(seq, position)
             for seq in sequences for position in range(4)]
        if exact_rank(m) != len(COLUMNS):
            raise ValueError("physical treatment/carryover not identifiable")
    return True


def _least_squares(rows, ys):
    """Small full-rank 7-column normal-equation solution for SOURCE diagnostics."""
    n = len(COLUMNS)
    if len(rows) != len(ys) or len(rows) < n:
        raise ValueError("insufficient source-only observations")
    lhs = [[sum(float(row[i]) * row[j] for row in rows)
            for j in range(n)] for i in range(n)]
    rhs = [sum(float(row[i]) * value for row, value in zip(rows, ys))
           for i in range(n)]
    # Scale-free partial-pivot Gauss-Jordan; rank is verified exactly upstream.
    for k in range(n):
        i = max(range(k, n), key=lambda r: abs(lhs[r][k]))
        if abs(lhs[i][k]) < 1e-11:
            raise ValueError("singular source design")
        lhs[k], lhs[i] = lhs[i], lhs[k]
        rhs[k], rhs[i] = rhs[i], rhs[k]
        d = lhs[k][k]
        lhs[k] = [v / d for v in lhs[k]]
        rhs[k] /= d
        for r in range(n):
            if r == k:
                continue
            d = lhs[r][k]
            if d:
                lhs[r] = [a - d * b for a, b in zip(lhs[r], lhs[k])]
                rhs[r] -= d * rhs[k]
    if any(not math.isfinite(x) for x in rhs):
        raise ValueError("nonfinite coefficient")
    return dict(zip(COLUMNS, rhs))


def adjudicate_untrusted_times(records):
    """ONLY analyze caller-supplied durations. NO native/PCC authenticity claim."""
    assert_design()
    if type(records) is not list or len(records) != N:
        raise ValueError("incomplete physical-arm population")
    treatment_rows = [[] for _ in range(PACKETS)]
    treatment_log = [[] for _ in range(PACKETS)]
    aa = {}
    for (block, packet, pos, expected_arm), rec in zip(roster(), records):
        if type(rec) is not dict or set(rec) != INPUT_FIELDS:
            raise ValueError("unexpected physical sample fields")
        expected = {"block": block, "packet_index": packet,
                    "position": pos, "arm": expected_arm}
        if any(type(rec.get(k)) is not type(v) or rec[k] != v
               for k, v in expected.items()):
            raise ValueError("missing/reordered/wrong physical arm sample")
        t = rec["wall_ns"]
        if type(t) is not int or t <= 0:
            raise ValueError("duration not positive integer ns")
        if pos < 4:
            treatment_rows[packet].append(model_row(order(block, packet)[:4], pos))
            treatment_log[packet].append(math.log(t))
        else:
            aa.setdefault((packet, block), []).append(t)
    if len(aa) != PACKETS * BLOCKS or any(len(v) != 2 for v in aa.values()):
        raise ValueError("incomplete A/A control")
    coefficients = []
    for packet in range(PACKETS):
        if exact_rank(treatment_rows[packet]) != len(COLUMNS):
            raise ValueError("rank-deficient packet")
        coefficients.append(_least_squares(treatment_rows[packet],
                                           treatment_log[packet]))
    contrasts = [-c["physical_B"] for c in coefficients]
    carryovers = [c["previous_B"] for c in coefficients]
    interactions = [c["physical_B_x_previous_B"] for c in coefficients]
    drift = [abs(math.log(x[0] / x[1])) for x in aa.values()]
    return {
        "schema": SCHEMA + "-diagnostic/v1",
        "standing": "[pcc:unverified]",
        "scope": "SOURCE-ONLY untrusted input times; no native evidence or causal certificate",
        "roster_sha256": roster_sha256(), "fixture_git_blob": FIXTURE_GIT_BLOB,
        "supplied_records": N, "independent_packets": PACKETS,
        "treatment_positions": PACKETS * BLOCKS * 4,
        "aa_control_positions": PACKETS * BLOCKS * 2,
        "design_rank_every_packet": len(COLUMNS),
        "median_direct_over_retained_ratio_conditional_model":
            math.exp(statistics.median(contrasts)),
        "median_previous_B_coefficient": statistics.median(carryovers),
        "median_B_x_previous_B_coefficient": statistics.median(interactions),
        "maximum_aa_abs_log_drift": max(drift),
        "per_packet_coefficients": coefficients,
        "original_full_695_701_custody_replayed": False,
        "signed_independent_pcc": False,
        "complete_single_target_ecdlp_advantage_established": False,
    }


def plan():
    assert_design()
    return {"schema": SCHEMA, "standing": "[pcc:unverified]",
            "scope": "SOURCE-ONLY design; physical native execution NOT authorized",
            "fixture_git_blob": FIXTURE_GIT_BLOB,
            "seed": SEED, "packets": PACKETS, "blocks": BLOCKS,
            "slots": SLOTS, "planned_processes": N,
            "arms": ARMS, "sequence_multiset_per_packet": list(SEQUENCES),
            "design_rank_every_packet": len(COLUMNS),
            "roster_sha256": roster_sha256()}


if __name__ == "__main__":
    print(json.dumps(plan(), sort_keys=True, allow_nan=False))
