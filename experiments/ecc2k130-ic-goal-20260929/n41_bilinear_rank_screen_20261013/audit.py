"""Independent Python replay of selected bilinear family decisions."""

import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "n41_joint_product_span_relaxation_20261013"
sys.path.insert(0, str(PRIOR))
import run  # noqa: E402
from n41_arithmetic import D, N, halftrace, multiply, square, trace  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field_rank(values):
    pivots = {}
    for value in values:
        while value:
            high = value.bit_length() - 1
            if high not in pivots:
                pivots[high] = value
                break
            value ^= pivots[high]
    return len(pivots)


def basis_for(code):
    p = code << 2
    coordinates = [1 << i for i in range(N)]
    seeds = [1 << (i + 1) for i in range(D)]
    columns = [halftrace(square(c)) ^ multiply(p, c) for c in coordinates]
    columns += [halftrace(square(s)) for s in seeds] + [1]
    rows = [sum(((value >> bit) & 1) << i for i, value in enumerate(columns))
            for bit in range(N)]
    rows.append(sum(trace(square(c)) << i for i, c in enumerate(coordinates)) ^
                sum(trace(square(s)) << (N + i) for i, s in enumerate(seeds)))
    projected = [v & ((1 << N) - 1) for v in run.kernel_basis(rows, N + D + 1)]
    assert len(projected) == field_rank(projected)
    return projected


def rank_screen(left, right, target):
    a = [square(c) for c in left]
    b = [square(d) for d in right]
    m = [(multiply(square(target), square(multiply(c, d))) ^
          multiply(target, multiply(c, d))) for c in left for d in right]
    columns = a + b + m
    rank = field_rank(columns)
    return rank, field_rank(columns + [square(target)]) == rank


def direct_hits(left, right, target):
    right_set = set(run.enumerate_span(right)) - {0}
    count = 0
    for c in run.enumerate_span(left):
        if c:
            count += sum(d in right_set for d in run.s3_right_roots(c, target))
    return count


def main():
    protocol = json.loads((HERE / "audit_protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    assert protocol["audit_source_sha256"] == sha(HERE / "audit.py")
    assert protocol["main_protocol_sha256"] == sha(HERE / "protocol.json")
    assert protocol["native_cases_sha256"] == sha(HERE / "cases.jsonl")
    assert protocol["prior_run_sha256"] == sha(PRIOR / "run.py")
    rows = [json.loads(line) for line in (HERE / "cases.jsonl").read_text().splitlines()]
    native = json.loads((HERE / "stdout.log").read_text())
    receipt = json.loads((HERE / "receipt.json").read_text())
    assert receipt["status"] == "COMPLETE" and len(rows) == native["cases"] == 1026
    assert receipt["cases_sha256"] == sha(HERE / "cases.jsonl")
    assert sum(not row["rank_consistent"] for row in rows) == native["rank_rejects"]
    assert sum(row["pivot_hits"] for row in rows) == native["pivot_hits"]
    assert sum(row["direct_hits"] for row in rows) == native["direct_hits"]
    assert all(row["pivot_complete"] and row["pivot_hits"] == row["direct_hits"] for row in rows)
    rng = random.Random(protocol["selection_seed"])
    fixed = [0, 1, 151, 732]
    chosen = fixed + rng.sample([i for i in range(len(rows)) if i not in fixed], 60)
    full = set(fixed + chosen[4:16])
    cache = {}
    for index in chosen:
        row = rows[index]
        for code in (row["left_product"], row["right_product"]):
            if code not in cache:
                cache[code] = basis_for(code)
        left = cache[row["left_product"]]
        right = cache[row["right_product"]]
        rank, consistent = rank_screen(left, right, row["target"])
        assert rank == row["rank"] and consistent == row["rank_consistent"], index
        if index in full:
            assert direct_hits(left, right, row["target"]) == row["direct_hits"], index
    result = {"status": "PASS_INDEPENDENT_FAMILY_RANK_AND_DIRECT_JOIN",
              "protocol_sha256": sha(HERE / "audit_protocol.json"),
              "rank_cases_checked": len(chosen),
              "direct_cases_checked": len(full),
              "native_cases": len(rows),
              "rank_histogram": dict(sorted(Counter(row["rank"] for row in rows).items())),
              "rank_rejects": native["rank_rejects"],
              "pivot_hits": native["pivot_hits"],
              "direct_hits": native["direct_hits"]}
    (HERE / "audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
