"""Independent all-root replay using binary-curve addition formulas in Sage."""

import gzip
import hashlib
import json
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
N = 131
SEED = 212
ROTATION = 16


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "fast_audit_protocol.json").read_text())
for key, path in {
    "source": Path(__file__),
    "table": HERE / "rows.tsv.gz",
    "census": HERE / "census_result.json",
    "hash": HERE / "hash_manifest.json",
    "support": SUPPORT,
    "runtime": HERE / "sage_fast_audit_runtime_info.json",
}.items():
    assert sha(path) == protocol["sha256"][key], key

ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**N, name="t", modulus=t**N + t**13 + t**2 + t + 1)


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


columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}
h2 = halftrace(dec(SEED << 1))**2
c = 1 + h2
assert c != 0
manifest = json.loads((HERE / "hash_manifest.json").read_text())
masks = list(map(int, manifest["masks"]))


def signature(value):
    return sum((bin(value & mask).count("1") & 1) << index
               for index, mask in enumerate(masks))


seen = set()
roots = 0
additions = 0
start = time.monotonic_ns()
with gzip.open(HERE / "rows.tsv.gz", "rt") as stream:
    next(stream)
    for line in stream:
        code, mask_a, mask_b, bit, a0, a1, plus0, minus0, plus1, minus1 = \
            map(int, line.split())
        assert code not in seen and mask_a ^ mask_b == SEED
        assert mask_a in columns and mask_b in columns
        seen.add(code)
        product = dec(mask_a << 1) * dec(mask_b << 1)
        for a_int, want_plus, want_minus in ((a0, plus0, minus0),
                                              (a1, plus1, minus1)):
            a = dec(a_int)
            assert a != 0 and c * a**2 + product * a + h2 == 0
            x = 1 / a
            lam = halftrace(x + a**2)
            X = x**(1 << ROTATION)
            denominator = x + X
            assert denominator != 0
            for lam_choice in (lam, lam + 1):
                y = x * lam_choice
                assert y**2 + x * y == x**3 + 1
                Y = y**(1 << ROTATION)
                for signed_y, want in ((Y, want_plus),
                                       (Y + X, want_minus)):
                    slope = (y + signed_y) / denominator
                    subtotal_x = slope**2 + slope + denominator
                    assert subtotal_x not in (0, 1)
                    assert enc(1 / subtotal_x) == want
                    additions += 1
            assert signature(want_plus) != signature(want_minus)
            roots += 1
        if len(seen) % 5000 == 0:
            print("FAST_AUDIT_PROGRESS", len(seen), roots, flush=True)
assert len(seen) == 33191 and roots == 66382
elapsed = time.monotonic_ns() - start
result = {
    "status": "PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_ADDITION_FORMULAS",
    "candidate_id": None,
    "source_codes": len(seen),
    "pair_output_roots": roots,
    "signed_additions_replayed": additions,
    "signature_width_bits": len(masks),
    "zero_signature_differences": 0,
    "elapsed_ns": elapsed,
    "audit_protocol_sha256": sha(HERE / "fast_audit_protocol.json"),
}
with (HERE / "fast_audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], additions, elapsed / 1e9)
