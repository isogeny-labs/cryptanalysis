"""Independent full group-law check for target-derived right-fiber decisions."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "subset_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
result = json.loads((HERE / "subset_result.json").read_text())
assert result["status"] == "EXACT_TARGET_DERIVED_FIBER_QUERY_FINISHED"
source_panel = json.loads((GOAL / "n41_joint_fourpair_resultant_20261012/panel.json").read_text())
fiber = json.loads((GOAL / "n41_symbolic_seed_fiber_20261012/panel.json").read_text())
geometry = json.loads((GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json").read_text())
rows = {int(row["mask"]): row for row in geometry["rows"]}
base = PolynomialRing(GF(2), "t")
t = base.gen()
field = GF(2**41, name="t", modulus=t**41+t**3+1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def decode(value):
    return field(base([(int(value) >> i) & 1 for i in range(41)]))


def encode(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def key(point):
    return None if point == curve(0) else (encode(point[0]), encode(point[1]))


def frob(point, rotation):
    if point == curve(0):
        return point
    return curve(point[0]**(1 << rotation), point[1]**(1 << rotation))


def diagonal(mask):
    raw = curve(*map(decode, rows[mask]["raw_point"]))
    return raw+frob(raw, 1)


point_cache = {mask: diagonal(mask) for family in source_panel["families"]
               for pair in family["masks"] for mask in pair}
point_cache.update({mask: diagonal(mask) for bin0 in fiber["ordered_masks"]
                    for pair in bin0 for mask in pair})


def signed_pair(masks, rotation):
    a, b = (point_cache[mask] for mask in masks)
    return [frob(sa*a+sb*b, rotation)
            for sa in (1, -1) for sb in (1, -1)]


right_slots = [[p for masks in fiber["ordered_masks"][i]
                for p in signed_pair(masks, fiber["rotations"][i])]
               for i in range(2)]
assert [len(slot) for slot in right_slots] == [128, 128]
right_counts = Counter(key(4*(a+b)) for a in right_slots[0] for b in right_slots[1])
assert sum(right_counts.values()) == 16384
target = curve(*map(decode, protocol["public_target"]))
result_by_id = {case["id"]: case for case in result["cases"]}
rows_out = []
for family in source_panel["families"]:
    if family["id"] not in result_by_id:
        continue
    left_slots = [signed_pair(family["masks"][i], source_panel["rotations"][i])
                  for i in range(2)]
    matches = sum(right_counts[key(target-4*(a+b))]
                  for a in left_slots[0] for b in left_slots[1])
    query_hits = result_by_id[family["id"]]["hits"]
    assert bool(matches) == bool(query_hits), family["id"]
    rows_out.append({"id": family["id"], "signed_left_states": 16,
                     "right_states": 16384, "group_law_matches": matches,
                     "fiber_query_hits": len(query_hits)})
    print("AUDIT", family["id"], matches, flush=True)

audit = {
    "status": "PASS_INDEPENDENT_TARGET_FIBER_GROUP_REPLAY",
    "candidate_id": None, "run_id": None,
    "target_count": 1, "cases": rows_out,
    "total_signed_combinations": len(rows_out)*16*16384,
    "source_sha256": {"protocol": hashlib.sha256((HERE / "subset_protocol.json").read_bytes()).hexdigest(),
                      "query_result": hashlib.sha256((HERE / "subset_result.json").read_bytes()).hexdigest(),
                      "auditor": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
}
with (HERE / "subset_audit.json").open("x") as stream:
    json.dump(audit, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(audit["status"], len(rows_out), flush=True)
