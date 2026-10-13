"""Enumerate exact W18 pair roots and Frobenius-linked subtotal signatures."""

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
SIGNATURE_WIDTH = 24
PIVOT = SEED.bit_length() - 1
SOURCE_BITS = [bit for bit in range(18) if bit != PIVOT]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["sha256"] == {
    "source": sha(Path(__file__)),
    "support": sha(SUPPORT),
    "sage_runtime": sha(HERE / "sage_runtime_info.json"),
}
assert protocol["source_codes"] == 33191

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


def trace(value):
    result = field.zero()
    for _ in range(N):
        result += value
        value = value**2
    assert result in (0, 1)
    return result


def linked_reciprocals(a):
    x = 1 / a
    X = x**(1 << ROTATION)
    d = x + X
    assert d != 0
    rhs = x**3 + 1
    A, B = field.zero(), field.one()
    for _ in range(ROTATION):
        B2 = B**2
        A, B = A**2 + B2 * rhs, B2 * x
    numerator = A**2 + (1 + B)**2 * rhs + d * A
    plus_x = d + numerator / d**2
    delta = (X / d)**2 + X / d
    minus_x = plus_x + delta
    assert plus_x not in (0, 1) and minus_x not in (0, 1)
    return plus_x, minus_x


columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}
codes = [(a, a ^ SEED) for a in sorted(columns)
         if a < (a ^ SEED) and (a ^ SEED) in columns
         and columns[a] != columns[a ^ SEED]]
assert len(codes) == protocol["source_codes"]
h2 = (halftrace(dec(SEED << 1)))**2
c = 1 + h2
assert c != 0
start = time.monotonic_ns()
collisions = 0
sample_checks = 0
rows = 0
outfile = HERE / "rows.tsv.gz"
with outfile.open("xb") as raw:
    with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                       compresslevel=6, mtime=0) as packed:
        packed.write(b"code\tmask_a\tmask_b\troot_bit\ta0\ta1\tplus0\tminus0\tplus1\tminus1\n")
        for mask_a, mask_b in codes:
            assert mask_a >> PIVOT & 1 == 0
            code = sum(((mask_a >> bit) & 1) << index
                       for index, bit in enumerate(SOURCE_BITS))
            # Source coordinates are x-only masks shifted by one bit.
            product = dec(mask_a << 1) * dec(mask_b << 1)
            q = c * h2 / product**2
            z = halftrace(q)
            roots = sorted((enc(product * z / c), enc(product * (z + 1) / c)))
            assert roots[0] != roots[1]
            diff = roots[0] ^ roots[1]
            root_bit = (diff & -diff).bit_length() - 1
            values = []
            for a_int in roots:
                a = dec(a_int)
                assert c * a**2 + product * a + h2 == 0
                plus_x, minus_x = linked_reciprocals(a)
                if sample_checks < 32:
                    for point in curve.lift_x(1 / a, all=True):
                        image = curve(point[0]**(1 << ROTATION),
                                      point[1]**(1 << ROTATION))
                        assert (point + image)[0] == plus_x
                        assert (point - image)[0] == minus_x
                        sample_checks += 1
                up, um = enc(1 / plus_x), enc(1 / minus_x)
                if (up ^ um) & ((1 << SIGNATURE_WIDTH) - 1) == 0:
                    collisions += 1
                values.extend((up, um))
                rows += 1
            fields = [code, mask_a, mask_b, root_bit,
                      roots[0], roots[1], *values]
            packed.write(("\t".join(map(str, fields)) + "\n").encode())
elapsed = time.monotonic_ns() - start
assert rows == 2 * protocol["source_codes"]
save("census_result.json", {
    "status": "PASS_EXACT_W18_LINKED_SIGNATURE_SOURCE_CENSUS",
    "candidate_id": None,
    "source_codes": len(codes),
    "pair_output_roots": rows,
    "signature_width": SIGNATURE_WIDTH,
    "low_signature_collisions": collisions,
    "sage_point_checks": sample_checks,
    "elapsed_ns": elapsed,
    "rows_gzip_sha256": sha(outfile),
    "rows_gzip_bytes": outfile.stat().st_size,
    "protocol_sha256": sha(HERE / "protocol.json"),
})
print("PASS_EXACT_W18_LINKED_SIGNATURE_SOURCE_CENSUS", rows,
      "collisions", collisions, "seconds", elapsed / 1e9)
