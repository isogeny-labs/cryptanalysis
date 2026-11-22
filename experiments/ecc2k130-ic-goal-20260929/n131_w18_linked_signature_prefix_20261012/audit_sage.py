"""Independently replay every saved W18 linked signature with Sage points."""

import gzip
import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
N = 131
SEED = 212
ROTATION = 16
PIVOT = SEED.bit_length() - 1
SOURCE_BITS = [bit for bit in range(18) if bit != PIVOT]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())
for key, path in {
    "audit_source": HERE / "audit_sage.py",
    "rows": HERE / "rows.tsv.gz",
    "census": HERE / "census_result.json",
    "support": SUPPORT,
    "sage_runtime": HERE / "sage_audit_runtime_info.json",
}.items():
    assert sha(path) == audit_protocol["sha256"][key], key

columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}
ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**N, name="t", modulus=t**N + t**13 + t**2 + t + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(value):
    return field(ring([(int(value) >> i) & 1 for i in range(N)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def halftrace(value):
    result, power = field.zero(), value
    for _ in range((N + 1) // 2):
        result += power
        power = power**4
    assert result**2 + result == value
    return result


h2 = halftrace(dec(SEED << 1))**2
c = 1 + h2
seen = set()
roots = 0
point_additions = 0
collisions = 0
start = time.monotonic_ns()
with gzip.open(HERE / "rows.tsv.gz", "rt") as stream:
    assert stream.readline().strip().split("\t") == [
        "code", "mask_a", "mask_b", "root_bit", "a0", "a1",
        "plus0", "minus0", "plus1", "minus1"]
    for line in stream:
        code, mask_a, mask_b, bit, a0, a1, plus0, minus0, plus1, minus1 = \
            map(int, line.split())
        assert code not in seen
        seen.add(code)
        assert mask_a < mask_b and mask_a ^ mask_b == SEED
        assert mask_a in columns and mask_b in columns
        assert columns[mask_a] != columns[mask_b]
        assert mask_a >> PIVOT & 1 == 0
        assert code == sum(((mask_a >> source_bit) & 1) << index
                           for index, source_bit in enumerate(SOURCE_BITS))
        assert a0 < a1 and bit == ((a0 ^ a1) & -(a0 ^ a1)).bit_length() - 1
        product = dec(mask_a << 1) * dec(mask_b << 1)
        for a_int, plus_int, minus_int in ((a0, plus0, minus0),
                                            (a1, plus1, minus1)):
            a = dec(a_int)
            assert a != 0 and c * a**2 + product * a + h2 == 0
            points = curve.lift_x(1 / a, all=True)
            assert len(points) == 2
            for point in points:
                image = curve(point[0]**(1 << ROTATION),
                              point[1]**(1 << ROTATION))
                plus, minus = point + image, point - image
                assert plus != curve(0) and minus != curve(0)
                assert plus[0] not in (0, 1) and minus[0] not in (0, 1)
                assert enc(1 / plus[0]) == plus_int
                assert enc(1 / minus[0]) == minus_int
                point_additions += 2
            roots += 1
            if (plus_int ^ minus_int) & ((1 << 24) - 1) == 0:
                collisions += 1
        if len(seen) % 5000 == 0:
            print("AUDIT_PROGRESS", len(seen), roots, flush=True)
assert len(seen) == 33191 and roots == 66382 and collisions == 0
elapsed = time.monotonic_ns() - start
result = {
    "status": "PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_SIGNATURES",
    "candidate_id": None,
    "source_codes": len(seen),
    "pair_output_roots": roots,
    "point_additions_replayed": point_additions,
    "low24_collisions": collisions,
    "elapsed_ns": elapsed,
    "audit_protocol_sha256": sha(HERE / "audit_protocol.json"),
}
with (HERE / "audit_result.json").open("x") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(result["status"], roots, point_additions, elapsed / 1e9)
