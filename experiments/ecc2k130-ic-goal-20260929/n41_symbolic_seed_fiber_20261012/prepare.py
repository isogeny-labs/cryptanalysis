"""Freeze nested source-product fibers around a known public-point block."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal"
fixture = json.loads((PARENT / "control_fixture.json").read_text())
right = [tuple(sorted(fixture["masks"][i])) for i in (2, 3)]
seeds = [a ^ b for a, b in right]
bins = [set(), set()]
with (PARENT / "pairs.tsv").open() as source:
    assert source.readline().strip() == "ECC2K41_ALLSEED4 4 4"
    for line in source:
        parts = line.split()
        if parts[0] != "S":
            continue
        slot, _, a, b, _, _ = map(int, parts[1:7])
        if slot in (2, 3) and a ^ b == seeds[slot - 2]:
            bins[slot - 2].add((a, b))
assert all(pair in source for pair, source in zip(right, bins))
ordered = [[pair] + sorted(source - {pair}) for pair, source in zip(right, bins)]
negative = int.from_bytes(hashlib.sha256((PARENT / "control_fixture.json").read_bytes()).digest()[:8], "big") % (1 << 41)
assert negative not in (0, fixture["intermediate_reciprocals"][1])
output = {"status": "FROZEN_N41_SYMBOLIC_SEED_FIBER_PANEL", "candidate_id": None,
          "curve_id": fixture["curve_id"], "slots": [2, 3],
          "rotations": fixture["rotations"][2:], "seeds": seeds,
          "bin_sizes": list(map(len, ordered)), "ordered_masks": ordered,
          "positive_reciprocal": fixture["intermediate_reciprocals"][1],
          "negative_reciprocal": negative, "sizes": [4, 8, 16, 32],
          "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (PARENT / "control_fixture.json", PARENT / "pairs.tsv", 
                                      GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json")}}
assert all(len(x) >= 32 for x in ordered)
with (HERE / "panel.json").open("x") as stream:
    json.dump(output, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(output["status"], output["bin_sizes"], negative)
