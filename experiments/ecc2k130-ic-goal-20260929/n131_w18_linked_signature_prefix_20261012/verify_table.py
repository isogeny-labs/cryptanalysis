"""Read-only structural audit of the complete linked signature table."""

import gzip
import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
SEED = 212
PIVOT = SEED.bit_length() - 1
SOURCE_BITS = [bit for bit in range(18) if bit != PIVOT]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "table_audit_protocol.json").read_text())
for key, path in {
    "audit_source": Path(__file__),
    "rows": HERE / "rows.tsv.gz",
    "census": HERE / "census_result.json",
    "hash_manifest": HERE / "hash_manifest.json",
    "support": SUPPORT,
}.items():
    assert sha(path) == protocol["sha256"][key], key

columns = {int(mask): int(column) for mask, column in
           (line.split() for line in SUPPORT.read_text().splitlines())}
expected = {(mask, mask ^ SEED) for mask in columns
            if mask < (mask ^ SEED) and (mask ^ SEED) in columns
            and columns[mask] != columns[mask ^ SEED]}
assert len(expected) == 33191
manifest = json.loads((HERE / "hash_manifest.json").read_text())
assert manifest["first_passing_seed"] == 42
masks = list(map(int, manifest["masks"]))
assert len(masks) == 14
rng = random.Random(42)
assert masks == [rng.getrandbits(131) for _ in masks]


def signature(value):
    return sum((bin(value & mask).count("1") & 1) << index
               for index, mask in enumerate(masks))


seen_pairs = set()
seen_codes = set()
roots = 0
max_equal_low_bits = 0
with gzip.open(HERE / "rows.tsv.gz", "rt") as stream:
    assert stream.readline().strip().split("\t") == [
        "code", "mask_a", "mask_b", "root_bit", "a0", "a1",
        "plus0", "minus0", "plus1", "minus1"]
    for line in stream:
        code, a, b, root_bit, a0, a1, plus0, minus0, plus1, minus1 = \
            map(int, line.split())
        assert (a, b) in expected and (a, b) not in seen_pairs
        seen_pairs.add((a, b))
        assert a >> PIVOT & 1 == 0
        encoded = sum(((a >> bit) & 1) << index
                      for index, bit in enumerate(SOURCE_BITS))
        assert code == encoded and code not in seen_codes
        seen_codes.add(code)
        assert a0 < a1 and a0 != 0 and a1 != 0
        assert root_bit == ((a0 ^ a1) & -(a0 ^ a1)).bit_length() - 1
        for plus, minus in ((plus0, minus0), (plus1, minus1)):
            diff = plus ^ minus
            assert diff and signature(diff) != 0
            assert (diff & ((1 << 24) - 1)) != 0
            max_equal_low_bits = max(max_equal_low_bits,
                                     (diff & -diff).bit_length() - 1)
            roots += 1
assert seen_pairs == expected and len(seen_codes) == 33191 and roots == 66382
result = {
    "status": "PASS_FULL_W18_SOURCE_AND_14_BIT_SIGNATURE_TABLE_AUDIT",
    "candidate_id": None,
    "source_codes": len(seen_codes),
    "pair_output_roots": roots,
    "signature_width_bits": len(masks),
    "low_bits_needed_if_unmixed": max_equal_low_bits + 1,
    "zero_signature_differences": 0,
    "protocol_sha256": sha(HERE / "table_audit_protocol.json"),
}
with (HERE / "table_audit_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(result["status"], roots, result["low_bits_needed_if_unmixed"])
