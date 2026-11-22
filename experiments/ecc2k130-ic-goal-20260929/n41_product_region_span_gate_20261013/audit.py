"""Independent binary-field replay of every W6 product-region rank."""

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "audit_protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, expected in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
native = json.loads((HERE / "result.json").read_text())

N = 41
MASK = (1 << N) - 1
MOD = (1 << N) | (1 << 3) | 1


def mul(a, b):
    product = 0
    while b:
        if b & 1:
            product ^= a
        b >>= 1
        a <<= 1
    while product.bit_length() > N:
        product ^= MOD << (product.bit_length() - N - 1)
    return product


def square(a):
    return mul(a, a)


def halftrace(a):
    total = 0
    for _ in range(21):
        total ^= a
        a = square(square(a))
    return total


def trace(a):
    total = 0
    for _ in range(N):
        total ^= a
        a = square(a)
    assert total in (0, 1)
    return total


coordinate_columns = []
for i in range(N):
    c2 = square(1 << i)
    coordinate_columns.append((halftrace(c2), trace(c2)))
seed_columns = []
for i in range(6):
    s2 = square(1 << (i + 1))
    seed_columns.append((halftrace(s2), trace(s2)))


def family_basis(code):
    product = code << 2
    columns = [(value ^ mul(product, 1 << i), bit)
               for i, (value, bit) in enumerate(coordinate_columns)]
    columns += seed_columns + [(1, 0)]
    assert len(columns) == 48
    rows = [0] * 42
    for j, (value, trace_bit) in enumerate(columns):
        for i in range(N):
            if value & (1 << i):
                rows[i] ^= 1 << j
        if trace_bit:
            rows[N] ^= 1 << j
    pivots = [-1] * 48
    rank = 0
    for col in range(48):
        found = next((i for i in range(rank, 42) if rows[i] & (1 << col)), None)
        if found is None:
            continue
        rows[rank], rows[found] = rows[found], rows[rank]
        for i in range(42):
            if i != rank and rows[i] & (1 << col):
                rows[i] ^= rows[rank]
        pivots[col] = rank
        rank += 1
    assert all(row == 0 for row in rows[rank:])
    output = []
    for free in range(48):
        if pivots[free] >= 0:
            continue
        vector = 1 << free
        for col in range(48):
            if pivots[col] >= 0 and rows[pivots[col]] & (1 << free):
                vector ^= 1 << col
        c = vector & MASK
        assert c != 0
        output.append(c)
    assert len(output) in (6, 7)
    return output


def insert(value, pivots):
    while value:
        bit = value.bit_length() - 1
        if bit in pivots:
            value ^= pivots[bit]
        else:
            pivots[bit] = value
            return True
    return False


families = [family_basis(code) for code in range(2048)]
assert Counter(map(len, families)) == {6: 2026, 7: 22}
levels = []
for free_bits in range(12):
    region_count = 2048 >> free_bits
    histogram = Counter()
    for region in range(region_count):
        pivots = {}
        for code in range(region << free_bits, (region + 1) << free_bits):
            for value in families[code]:
                insert(value, pivots)
        histogram[len(pivots)] += 1
    native_level = native["levels"][free_bits]
    assert native_level["free_product_bits"] == free_bits
    assert native_level["region_count"] == region_count
    assert {int(key): value for key, value in native_level["union_rank_histogram"].items()} == histogram
    levels.append({"free_product_bits": free_bits, "families_per_region": 1 << free_bits,
                   "region_count": region_count, "rank_histogram": dict(sorted(histogram.items()))})

public_t = native["public_target_reciprocal"]
assert trace(public_t) == trace(square(public_t)) == 0

# Check cross-span ranks for deterministic region pairs with a second
# multiplication and elimination path. The general all-pairs claim uses
# the dimension argument in RESULT.md, not this sample.
cross_checks = []
for free_bits in (0, 1, 2, 3):
    first = {}
    second = {}
    for code in range(1 << free_bits):
        for value in families[code]:
            insert(value, first)
    for code in range(1 << free_bits, 2 << free_bits):
        for value in families[code]:
            insert(value, second)
    cross = {}
    for c in first.values():
        for d in second.values():
            z = mul(mul(public_t, c), d)
            value = square(z) ^ z
            assert trace(value) == 0
            insert(value, cross)
    assert len(cross) == 40 if free_bits >= 1 else len(cross) <= 40
    cross_checks.append({"free_bits": free_bits, "left_rank": len(first),
                         "right_rank": len(second), "cross_rank": len(cross)})

result = {
    "status": "PASS_INDEPENDENT_N41_REGION_RANK_CENSUS",
    "families_rebuilt": len(families),
    "levels": levels,
    "public_target_trace": 0,
    "cross_checks": cross_checks,
    "source_sha256": {"protocol": hashlib.sha256((HERE / "audit_protocol.json").read_bytes()).hexdigest(),
                      "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "native_result": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()},
}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], [row["rank_histogram"] for row in levels[:5]])
