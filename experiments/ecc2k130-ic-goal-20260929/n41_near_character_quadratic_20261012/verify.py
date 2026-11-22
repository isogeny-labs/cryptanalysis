"""Independent feature expansion, low-pivot rank, and certificate replay."""

import ast
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_near_character_20261012"
vectors = json.loads((PARENT / "vectors.json").read_text())["train"]
certificate = json.loads((HERE / "certificate.json").read_text())
source = (HERE / "QuadraticRank.lean").read_text()


def definition(name):
    match = re.search(r"^def " + name + r" : Array Nat := #\[(.+)\]$", source, re.M)
    assert match, name
    return ast.literal_eval("[" + match.group(1) + "]")


def independent_feature(value):
    bits = {i for i in range(1, 41) if value & (1 << i)}
    features = [1] + [int(i in bits) for i in range(1, 41)]
    features += [int(i in bits and j in bits) for i in range(1, 41) for j in range(i + 1, 41)]
    assert len(features) == 821
    return sum(bit << index for index, bit in enumerate(features))


checks = {}
for name, coordinate in (("X", 2), ("Inverse", 3)):
    indices = certificate["coordinates"][name]["selected_source_indices"]
    rows = definition("rows" + name)
    masks = definition("witnesses" + name)
    assert len(indices) == len(rows) == len(masks) == 821
    assert rows == [independent_feature(vectors[i][coordinate]) for i in indices]
    pivots = {}
    for row in rows:
        value = row
        while value:
            bit = (value & -value).bit_length() - 1
            if bit not in pivots:
                pivots[bit] = value
                break
            value ^= pivots[bit]
    assert len(pivots) == 821
    for bit, mask in enumerate(masks):
        value = 0
        while mask:
            low = mask & -mask
            value ^= rows[low.bit_length() - 1]
            mask ^= low
        assert value == 1 << bit
    checks[name] = {"rank": len(pivots), "basis_certificates": len(masks),
                    "last_source_index": max(indices)}

output = {"status": "PASS_INDEPENDENT_N41_QUADRATIC_RANK_CERTIFICATE",
          "candidate_id": None, "coordinates": checks,
          "lean_source_sha256": hashlib.sha256((HERE / "QuadraticRank.lean").read_bytes()).hexdigest()}
with (HERE / "verification.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"])
