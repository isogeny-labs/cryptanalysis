"""Build source-root lookup formula and check independent public relation."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit as design

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "build_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_ROOT_LOOKUP_BUILD"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
receipt = json.loads(Path(cfg["sources"]["public_relation"]["path"]).read_text())
assert receipt["status"] == "PASS_INDEPENDENT_N41_PUBLIC_SIX_PAIR_RELATION"
assert [row["rotation"] for row in receipt["source_pairs"]] == cfg["rotations"]
point = tuple(receipt["raw_target_replayed"])
target = design.F.inv(point[0])
started = time.monotonic()
circ, wires, table, counts = design.build(target)
built = time.monotonic()
assignment = {}
points, witness_edges, witness_branches = [], [], []
for slot, row in enumerate(receipt["source_pairs"]):
    mask = row["masks"][0]
    edge = table["masks"].index(mask)
    point_slot = tuple(row["pair_rotated"])
    points.append(point_slot)
    unrotated_x = design.prior.frob(point_slot[0],
                                    (41 - row["rotation"]) % 41)
    root = design.F.inv(unrotated_x)
    branch = table["roots"][edge].index(root)
    witness_edges.append(edge)
    witness_branches.append(branch)
    assignment.update({wire: int(index == edge)
                       for index, wire in enumerate(wires["edge"][slot])})
    assignment[wires["branch"][slot]] = branch
assert len(set(witness_edges)) == 6
add = design.prior.replay.add
middle = [add(design.F, points[0], points[1]),
          add(design.F, points[2], points[3]),
          add(design.F, points[4], points[5])]
middle.append(add(design.F, middle[0], middle[1]))
assert add(design.F, middle[3], middle[2]) == point
for bits, middle_point in zip(wires["middle"], middle):
    assert middle_point is not None and middle_point[0]
    reciprocal = design.F.inv(middle_point[0])
    assignment.update({wire: reciprocal >> j & 1 for j, wire in enumerate(bits)})
full = design.prior.old.complete_assignment(circ, assignment)
check = design.prior.old.check_assignment(circ, full)
assert check == {"clauses": counts["clauses"],
                 "native_xor_rows": counts["native_xor_rows"]}
checked = time.monotonic()
formula = HERE / "n41_public_root_lookup.xcnf"
assert not formula.exists()
circ.write(formula)
finished = time.monotonic()
out = {"status": "PASS_N41_ROOT_LOOKUP_CIRCUIT",
       "candidate_id": None, "curve_id": cfg["curve_id"],
       "public_point": list(point), "target_reciprocal": target,
       "witness_edges": witness_edges, "witness_branches": witness_branches,
       "positive_assignment_check": check, "counts": counts,
       "formula_sha256": sha(formula), "formula_bytes": formula.stat().st_size,
       "phase_seconds": {"build": built - started,
                         "positive_assignment": checked - built,
                         "serialize": finished - checked},
       "wall_seconds": finished - started,
       "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "build_protocol.json")}
(HERE / "build_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("status", "counts", "wall_seconds")}, sort_keys=True))
