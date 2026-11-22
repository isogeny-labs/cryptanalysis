"""Complete indexed S3 join for the exact same symbolic-label regions."""

import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

from build import N, family_basis, field_mul, square, halftrace, trace

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "exact_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path


def power(a, exponent):
    value = 1
    while exponent:
        if exponent & 1:
            value = field_mul(value, a)
        a = square(a)
        exponent >>= 1
    return value


def inverse(a):
    assert a
    value = power(a, (1 << N) - 2)
    assert field_mul(a, value) == 1
    return value


def roots(a, b, c):
    if not a:
        return () if not b else (field_mul(c, inverse(b)),)
    if not b:
        v = field_mul(c, inverse(a))
        for _ in range(N - 1):
            v = square(v)
        return (v,)
    scale = field_mul(b, inverse(a))
    rhs = field_mul(field_mul(a, c), inverse(square(b)))
    if trace(rhs):
        return ()
    first = field_mul(scale, halftrace(rhs))
    return (first, first ^ scale)


def output_map(region):
    output = defaultdict(set)
    for code in range(4 * region, 4 * region + 4):
        basis = family_basis(code)
        value = 0
        for mask in range(1, 1 << len(basis)):
            value ^= basis[(mask & -mask).bit_length() - 1] if mask == 1 else 0
            # Gray-code traversal avoids recomputing every linear combination.
            if mask > 1:
                gray = mask ^ (mask >> 1)
                previous = (mask - 1) ^ ((mask - 1) >> 1)
                changed = gray ^ previous
                value ^= basis[changed.bit_length() - 1]
            assert value
            output[value].add(code)
    return output


build = json.loads((HERE / "build_result.json").read_text())
rows = []
for case in build["cases"]:
    started = time.monotonic_ns()
    left = output_map(case["left_region"])
    right = output_map(case["right_region"])
    target = case["target_reciprocal"]
    hits = []
    proposals = 0
    for c, left_codes in left.items():
        ct = field_mul(c, target)
        for d in roots(1 ^ square(ct), ct, square(c) ^ square(target)):
            proposals += 1
            if d not in right:
                continue
            assert square(field_mul(ct, d)) ^ field_mul(ct, d) ^ square(c ^ d ^ target) == 0
            hits.append({"c": c, "d": d, "left_codes": sorted(left_codes),
                         "right_codes": sorted(right[d])})
    rows.append({"name": case["name"], "left_unique_outputs": len(left),
                 "right_unique_outputs": len(right), "root_proposals": proposals,
                 "exact_coordinate_hits": len(hits), "hits": hits,
                 "wall_ns": time.monotonic_ns() - started})
result = {"status": "COMPLETE_EXACT_REGION_JOIN", "cases": rows,
          "protocol_sha256": hashlib.sha256((HERE / "exact_protocol.json").read_bytes()).hexdigest()}
with (HERE / "exact_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print([(x["name"], x["exact_coordinate_hits"], x["wall_ns"] / 1e9)
       for x in rows])
