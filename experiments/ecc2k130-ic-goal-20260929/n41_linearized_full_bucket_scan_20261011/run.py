"""Complete two-free-bucket scan using field-linear right-family membership."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
GEOMETRY = BASE / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
PRIOR = BASE / "n41_symbolic_two_bucket_20261011/protocol.json"
MOD = (1 << 41) | (1 << 3) | 1
MASK = (1 << 41) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= MOD
    return result


def square(a):
    return mul(a, a)


def power(a, exponent):
    answer = 1
    while exponent:
        if exponent & 1:
            answer = mul(answer, a)
        a = square(a)
        exponent >>= 1
    return answer


def halftrace(a):
    result = 0
    for _ in range(21):
        result ^= a
        a = square(square(a))
    return result


def trace(a):
    result = 0
    for _ in range(41):
        result ^= a
        a = square(a)
    assert result in (0, 1)
    return result


def roots(a, b, c):
    assert a
    if not b:
        return [power(mul(c, power(a, (1 << 41)-2)), 1 << 40)]
    inverse_a = power(a, (1 << 41)-2)
    ratio = mul(b, inverse_a)
    v = mul(mul(a, c), power(square(b), (1 << 41)-2))
    if trace(v):
        return []
    h = halftrace(v)
    result = [mul(ratio, h), mul(ratio, h ^ 1)]
    assert all(mul(a, square(x)) ^ mul(b, x) ^ c == 0 for x in result)
    return result


def independent(values):
    pivots = {}
    basis = []
    for value in values:
        x = value
        while x:
            bit = x.bit_length()-1
            if bit not in pivots:
                pivots[bit] = x
                basis.append(value)
                break
            x ^= pivots[bit]
    return basis


def in_span(values, target):
    pivots = {}
    for value in values:
        x = value
        while x:
            bit = x.bit_length()-1
            if bit not in pivots:
                pivots[bit] = x
                break
            x ^= pivots[bit]
    while target:
        bit = target.bit_length()-1
        if bit not in pivots:
            return False
        target ^= pivots[bit]
    return True


def xor_selected(values, mask):
    result = 0
    for i, value in enumerate(values):
        if mask >> i & 1:
            result ^= value
    return result


def bucket(basis_u, seed):
    basis_w = [square(u) ^ u for u in basis_u]
    u = xor_selected(basis_u, seed)
    w = xor_selected(basis_w, seed)
    image = independent([square(a) ^ mul(w, a) for a in basis_w])
    assert len(image) == 5
    return square(u), image


def left_domain(basis_u):
    rows = {}
    for seed in range(1, 64):
        u2, basis = bucket(basis_u, seed)
        products = {xor_selected(basis, bits) for bits in range(32)}
        assert len(products) == 32
        for p in products:
            for z in roots(1 ^ p, p, u2):
                rows.setdefault(z, set()).add(seed)
    return rows


def right_hit(z, target, right):
    zz = square(z)
    tt = square(target)
    c = mul(zz ^ z, tt ^ target)
    d = square(z ^ target)
    alpha = 1 ^ c
    e = square(d) ^ d
    cc = square(c)
    matches = []
    for seed, (u2, basis) in right.items():
        a = square(mul(alpha, u2) ^ d) ^ mul(cc, u2)
        b = mul(c, u2 ^ d)
        transformed = [mul(b, v) ^ mul(e, square(v)) for v in basis]
        if in_span(transformed, a):
            matches.append(seed)
    return matches


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    paths = {"source": Path(__file__), "geometry": GEOMETRY,
             "prior": PRIOR, "targets": HERE / "targets.json",
             "runtime": HERE / "sage_runtime_info.json"}
    assert {k: sha(v) for k, v in paths.items()} == protocol["sha256"]
    geometry = json.loads(GEOMETRY.read_text())["n41"]
    targets = json.loads((HERE / "targets.json").read_text())["rows"]
    setup = time.monotonic_ns()
    left = left_domain(geometry["window_basis_halftrace"][2])
    right = {seed: bucket(geometry["window_basis_halftrace"][3], seed)
             for seed in range(1, 64)}
    setup_ns = time.monotonic_ns()-setup
    rows = []
    for target in targets:
        start = time.monotonic_ns()
        decisions = 0
        hits = []
        status = "COMPLETE"
        for z, left_seeds in left.items():
            for right_seed in right_hit(z, target["target_z"], right):
                for left_seed in left_seeds:
                    hits.append({"left_seed": left_seed, "right_seed": right_seed,
                                 "left_z": z})
            decisions += 63
            if time.monotonic_ns()-start > protocol["per_lift_cap_seconds"]*10**9:
                status = "CENSORED_TIME"
                break
        rows.append({"kind": target["kind"], "option": target["option"],
                     "status": status, "left_coordinates": len(left),
                     "bucket_decisions": decisions, "hits": hits,
                     "query_ns": time.monotonic_ns()-start})
        print(json.dumps({"kind": target["kind"], "option": target["option"],
                          "status": status, "decisions": decisions,
                          "hits": len(hits), "query_s": rows[-1]["query_ns"]/1e9}), flush=True)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = rss if sys.platform == "darwin" else rss*1024
    result = {"status": "COMPLETE" if all(r["status"] == "COMPLETE" for r in rows)
              else "CENSORED", "candidate_id": None, "proposal_id": protocol["proposal_id"],
              "setup_ns": setup_ns, "rows": rows, "peak_rss_bytes": rss,
              "source_sha256": sha(Path(__file__)), "protocol_sha256": sha(HERE / "protocol.json")}
    (HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
