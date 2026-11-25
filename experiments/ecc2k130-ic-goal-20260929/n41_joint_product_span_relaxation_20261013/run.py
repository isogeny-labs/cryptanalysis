"""Exhaust the N41 product-span relaxation before opening source masks.

The relaxed pair output c has some product p in span(t^2,...,t^12),
seed s in W6, and branch epsilon satisfying the halftrace equation.
The trace guard makes this equivalent to the exact pair polynomial for
these relaxed p and s, without requiring p to be a product of W6 sources.
"""

import hashlib
import json
import resource
import time
from collections import Counter, defaultdict
from pathlib import Path

from n41_arithmetic import N, D, MOD, multiply, square, inverse, halftrace, trace, pair_outputs

HERE = Path(__file__).resolve().parent
MAX_ENUMERATED = 1 << 23


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kernel_basis(rows, width):
    rows = rows[:]
    pivots = {}
    rank = 0
    for col in range(width):
        pivot = next((i for i in range(rank, len(rows)) if rows[i] & (1 << col)), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i] & (1 << col):
                rows[i] ^= rows[rank]
        pivots[col] = rank
        rank += 1
    assert not any(rows[rank:])
    basis = []
    for free in range(width):
        if free in pivots:
            continue
        vector = 1 << free
        for col, row in pivots.items():
            vector ^= ((rows[row] >> free) & 1) << col
        assert all(bin(row & vector).count("1") % 2 == 0 for row in rows)
        basis.append(vector)
    return basis


def enumerate_span(basis):
    # Gray order changes one basis vector at a time.
    value = 0
    yield value
    for index in range(1, 1 << len(basis)):
        value ^= basis[(index & -index).bit_length() - 1]
        yield value


def quadratic_roots(a, b, c):
    if a == 0:
        return [multiply(c, inverse(b))] if b else ([] if c else None)
    if b == 0:
        root = multiply(c, inverse(a))
        for _ in range(N - 1):
            root = square(root)
        return [root]
    scale = multiply(b, inverse(a))
    rhs = multiply(multiply(a, c), inverse(square(b)))
    if trace(rhs):
        return []
    h = halftrace(rhs)
    roots = [multiply(scale, h), multiply(scale, h ^ 1)]
    assert all(multiply(a, square(x)) ^ multiply(b, x) ^ c == 0 for x in roots)
    return roots


def s3_right_roots(c, target):
    return quadratic_roots(1 ^ square(multiply(c, target)),
                           multiply(c, target), square(c) ^ square(target))


def source_pair_map():
    support = [mask for mask in range(1, 1 << D)
               if trace((mask << 1) ^ inverse(square(mask << 1))) == 0]
    assert len(support) == 32
    out = defaultdict(set)
    for i, a in enumerate(support):
        for b in support[i + 1:]:
            for c in pair_outputs(a << 1, b << 1):
                out[c].add((a, b))
    assert len(out) == 991
    return out


def relaxed_outputs():
    field_basis = [1 << i for i in range(N)]
    seed_basis = [1 << (i + 1) for i in range(D)]
    hc = [halftrace(square(c)) for c in field_basis]
    hs = [halftrace(square(s)) for s in seed_basis]
    tc = [trace(square(c)) for c in field_basis]
    ts = [trace(square(s)) for s in seed_basis]
    output = set()
    rank_hist = Counter()
    assignments = 0
    first_witness = {}
    t0 = time.monotonic()
    for product_code in range(1 << (2 * D - 1)):
        p = product_code << 2
        columns = [hc[i] ^ multiply(p, field_basis[i]) for i in range(N)]
        columns += hs + [1]
        rows = [sum(((v >> bit) & 1) << i for i, v in enumerate(columns))
                for bit in range(N)]
        rows.append(sum(tc[i] << i for i in range(N)) ^
                    sum(ts[i] << (N + i) for i in range(D)))
        basis = kernel_basis(rows, N + D + 1)
        rank_hist[len(basis)] += 1
        assignments += 1 << len(basis)
        assert assignments <= MAX_ENUMERATED
        for solution in enumerate_span(basis):
            c = solution & ((1 << N) - 1)
            if not c:
                continue
            output.add(c)
            if c not in first_witness:
                first_witness[c] = (p, (solution >> N) & ((1 << D) - 1),
                                    (solution >> (N + D)) & 1)
    return output, first_witness, rank_hist, assignments, time.monotonic() - t0


def joined(target, outputs, source):
    t0 = time.monotonic()
    s3_proposals = 0
    relaxed = set()
    exact = set()
    for c in outputs:
        roots = s3_right_roots(c, target)
        assert roots is not None
        s3_proposals += len(roots)
        for d in roots:
            if d not in outputs:
                continue
            key = tuple(sorted((c, d)))
            relaxed.add(key)
            if c in source and d in source:
                exact.add(key)
    return {"s3_proposals": s3_proposals,
            "relaxed_unordered_hits": len(relaxed),
            "exact_unordered_hits": len(exact),
            "first_exact": list(min(exact)) if exact else None,
            "seconds": time.monotonic() - t0}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN"
    assert protocol["run_sha256"] == digest(HERE / "run.py")
    assert protocol["arithmetic_sha256"] == digest(HERE / "n41_arithmetic.py")
    assert protocol["field_modulus"] == "t^41+t^3+1"
    t0 = time.monotonic()
    source = source_pair_map()
    outputs, witnesses, ranks, assignments, enum_s = relaxed_outputs()
    assert set(source).issubset(outputs)
    for c in source:
        p, smask, eps = witnesses[c]
        s = smask << 1
        assert multiply(1 ^ square(p), square(c)) ^ multiply(p, c) ^ square(s) == 0
    ordered_source = sorted(source)
    left, right = ordered_source[0], ordered_source[1]
    constructed = s3_right_roots(left, right)
    assert constructed and len(constructed) == 2
    targets = {"constructed": constructed[0],
               "public_point_inverse_x": inverse(protocol["public_point_x"])}
    cases = {}
    for name, target in targets.items():
        cases[name] = {"target_reciprocal": target,
                       **joined(target, outputs, source)}
    assert cases["constructed"]["exact_unordered_hits"] >= 1
    result = {"status": "COMPLETE_RELAXED_N41_TWO_PAIR_CENSUS",
              "candidate_id": None,
              "protocol_sha256": digest(HERE / "protocol.json"),
              "source_pair_outputs": len(source),
              "relaxed_pair_outputs": len(outputs),
              "relaxation_expansion": len(outputs) / len(source),
              "product_count": 1 << (2 * D - 1),
              "linear_system_nullity_histogram": dict(sorted(ranks.items())),
              "linear_assignments": assignments,
              "enumeration_seconds": enum_s,
              "cases": cases,
              "runner_seconds": time.monotonic() - t0,
              "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
