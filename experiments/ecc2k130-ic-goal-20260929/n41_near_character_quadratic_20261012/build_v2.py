"""Freeze exact quadratic feature rank and Lean XOR-span certificates."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_near_character_20261012"
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_N41_QUADRATIC_RANK"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
vectors = json.loads((PARENT / "vectors.json").read_text())


def feature(value):
    bits = [(value >> i) & 1 for i in range(1, 41)]
    row = 1
    for i, bit in enumerate(bits):
        row |= bit << (i + 1)
    position = 41
    for i in range(40):
        for j in range(i + 1, 40):
            row |= (bits[i] & bits[j]) << position
            position += 1
    assert position == 821
    return row


def certificate(coordinate):
    input_rows = [feature(row[coordinate]) for row in vectors["train"][:1024]]
    pivots = {}
    selected_indices = []
    selected_rows = []
    for source_index, original in enumerate(input_rows):
        value = original
        combination = 1 << len(selected_rows)
        while value:
            bit = value.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = (value, combination)
                selected_indices.append(source_index)
                selected_rows.append(original)
                break
            value ^= pivots[bit][0]
            combination ^= pivots[bit][1]
        if len(pivots) == 821:
            break
    assert len(pivots) == len(selected_rows) == 821
    assert set(pivots) == set(range(821))
    witnesses = []
    for bit in range(821):
        value = 1 << bit
        combination = 0
        while value:
            pivot = value.bit_length() - 1
            value ^= pivots[pivot][0]
            combination ^= pivots[pivot][1]
        check = 0
        for index, row in enumerate(selected_rows):
            if combination >> index & 1:
                check ^= row
        assert check == 1 << bit
        witnesses.append(combination)
    return selected_indices, selected_rows, witnesses


output = {"status": "EXACT_N41_SOURCE_ERROR_QUADRATIC_FULL_RANK", "candidate_id": None,
          "feature_count": 821, "sample_prefix": 1024, "coordinates": {},
          "vectors_sha256": hashlib.sha256((PARENT / "vectors.json").read_bytes()).hexdigest(),
          "protocol_sha256": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest()}
data = {}
for name, coordinate in (("X", 2), ("Inverse", 3)):
    indices, rows, witnesses = certificate(coordinate)
    data[name] = (indices, rows, witnesses)
    output["coordinates"][name] = {"rank": 821, "selected_source_indices": indices,
                                    "last_selected_source_index": max(indices)}
with (HERE / "certificate.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")

source = '''import Std
set_option maxRecDepth 8192
set_option maxHeartbeats 0

namespace QuadraticRank

def xorSelected (rows : Array Nat) (mask : Nat) : Nat :=
  (List.range rows.size).foldl
    (fun acc index => if mask.testBit index then Nat.xor acc rows[index]! else acc) 0

'''
for name, (_, rows, witnesses) in data.items():
    source += f"def rows{name} : Array Nat := #[{', '.join(map(str, rows))}]\n\n"
    source += f"def witnesses{name} : Array Nat := #[{', '.join(map(str, witnesses))}]\n\n"
    source += f"theorem certificate{name} : ∀ bit : Fin 821, xorSelected rows{name} witnesses{name}[bit.val]! = 2 ^ bit.val := by decide\n\n"
source += '''#print axioms QuadraticRank.certificateX
#print axioms QuadraticRank.certificateInverse

end QuadraticRank
'''
with (HERE / "QuadraticRank.lean").open("x") as stream:
    stream.write(source)
print(output["status"], len(source))
