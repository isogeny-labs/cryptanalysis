"""Freeze source-law product tuples around the N41 four-pair public witness."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
FOURPAIR = GOAL / "n131_w18_allseed_fourpair_20261012"
FIXTURE = FOURPAIR / "n41_diagonal/control_fixture.json"
PAIRS = FOURPAIR / "n41_diagonal/pairs.tsv"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
UNIVERSAL = GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


fixture = json.loads(FIXTURE.read_text())
geometry = json.loads(GEOMETRY.read_text())
columns = {int(row["mask"]): int(row["column"]) for row in geometry["rows"]}
positive = [sorted(pair) for pair in fixture["masks"]]
assert len(positive) == 4 and len({columns[m] for pair in positive for m in pair}) == 8
sets = [set() for _ in range(4)]
with PAIRS.open() as stream:
    assert stream.readline().strip() == "ECC2K41_ALLSEED4 4 4"
    for line in stream:
        parts = line.split()
        if parts[0] != "S":
            continue
        slot, state_id, a, b, ca, cb = map(int, parts[1:7])
        assert a < b and columns[a] == ca and columns[b] == cb
        sets[slot].add((a, b))
assert all(len(s) > 0 for s in sets)
panels = [{"id": "positive", "masks": positive, "kind": "known_public_witness"}]
for slot in range(4):
    seed = positive[slot][0] ^ positive[slot][1]
    other_cols = {columns[m] for i, pair in enumerate(positive) if i != slot for m in pair}
    alternatives = [pair for pair in sorted(sets[slot])
                    if pair != tuple(positive[slot]) and pair[0] ^ pair[1] == seed
                    and columns[pair[0]] not in other_cols
                    and columns[pair[1]] not in other_cols]
    assert len(alternatives) >= 8, (slot, len(alternatives))
    # Deterministic source-law neighboring families; no target-dependent choice.
    for number, pair in enumerate(alternatives[:8]):
        masks = [list(x) for x in positive]
        masks[slot] = list(pair)
        assert len({columns[m] for row in masks for m in row}) == 8
        panels.append({"id": f"slot{slot}_alternative{number}",
                       "masks": masks, "kind": "same_seed_source_control"})
output = {"status": "FROZEN_N41_JOINT_RESULTANT_PANEL", "candidate_id": None,
          "curve_id": fixture["curve_id"], "target_reciprocal": fixture["target_reciprocal"],
          "public_target": fixture["public_target"], "rotations": fixture["rotations"],
          "families": panels,
          "sha256": {"fixture": sha(FIXTURE), "pairs": sha(PAIRS),
                     "geometry": sha(GEOMETRY), "universal_resultant": sha(UNIVERSAL),
                     "source": sha(__file__)}}
with (HERE / "panel.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], len(panels))
