"""Bind the checked Lean literals to the archived group-law vectors."""

import ast
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / "rank_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_NEAR_CHARACTER_RANK_AUDIT"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
vectors = json.loads((HERE / "vectors.json").read_text())["train"]
certificate = json.loads((HERE / "rank_certificate.json").read_text())
lean = (HERE / "NearCharacterRank.lean").read_text()


def declaration(name):
    match = re.search(r"^def " + name + r" : List(?: \(List Nat\)| Nat) := (.+)$", lean, re.M)
    assert match, name
    return ast.literal_eval(match.group(1))


rows = {}
for name, coordinate, key in (("X", 2, "x"), ("Inverse", 3, "inverse_x")):
    samples = declaration("samples" + name)
    witnesses = declaration("witnessLists" + name)
    assert samples == [row[coordinate] for row in vectors[:48]]
    indices = certificate["sample_indices"][key]
    assert len(witnesses) == len(indices) == 40
    for bit, (listed, locations) in enumerate(zip(witnesses, indices), start=1):
        assert all(0 <= index < 48 for index in locations)
        assert listed == [samples[index] for index in locations]
        value = 0
        for item in listed:
            value ^= item
        assert value == 1 << bit
    rows[key] = {"sample_count": 48, "basis_witnesses": 40,
                 "pivots": list(range(1, 41))}

output = {"status": "PASS_INDEPENDENT_NEAR_CHARACTER_RANK_BINDING",
          "candidate_id": None, "coordinates": rows,
          "lean_sha256": hashlib.sha256((HERE / "NearCharacterRank.lean").read_bytes()).hexdigest(),
          "vectors_sha256": hashlib.sha256((HERE / "vectors.json").read_bytes()).hexdigest()}
with (HERE / "rank_audit.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"])
