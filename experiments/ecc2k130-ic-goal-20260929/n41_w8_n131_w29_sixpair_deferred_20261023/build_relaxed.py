"""Construct a fully deferred source-validity control on the same N41 point."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit_deferred as design

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "relaxed_build_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_ALL_DEFERRED_BUILD"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
F = design.F
prior = design.prior
receipt = json.loads(Path(cfg["sources"]["public_relation"]["path"]).read_text())
point = tuple(receipt["raw_target_replayed"])
target = F.inv(point[0])
started = time.monotonic()
circ, wires, counts = design.build(target, ())
built = time.monotonic()
assignment = {}


def bind(bits, value):
    assignment.update({wire: value >> j & 1 for j, wire in enumerate(bits)})


points, codes = [], []
for slot, row in enumerate(receipt["source_pairs"]):
    mask = row["masks"][0]
    code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(design.BITS))
    codes.append(code)
    bind(wires["mask"][slot], code)
    pair_point = tuple(row["pair_rotated"])
    points.append(pair_point)
    x = prior.frob(pair_point[0], (41 - row["rotation"]) % 41)
    bind(wires["out"][slot], F.inv(x))
assert len(set(codes)) == 6
add = prior.replay.add
middle = [add(F, points[0], points[1]),
          add(F, points[2], points[3]),
          add(F, points[4], points[5])]
middle.append(add(F, middle[0], middle[1]))
assert add(F, middle[3], middle[2]) == point
for bits, p in zip(wires["middle"], middle):
    assert p is not None and p[0]
    bind(bits, F.inv(p[0]))
full = prior.old.complete_assignment(circ, assignment)
checked = prior.old.check_assignment(circ, full)
assert checked == {"clauses": counts["clauses"],
                   "native_xor_rows": counts["native_xor_rows"]}
after_check = time.monotonic()
formula = HERE / "n41_public_all_deferred.xcnf"
assert not formula.exists()
circ.write(formula)
finished = time.monotonic()
out = {"status": "PASS_N41_ALL_DEFERRED_CIRCUIT",
       "candidate_id": None, "curve_id": cfg["curve_id"],
       "public_point": list(point), "target_reciprocal": target,
       "constructed_codes": codes, "positive_assignment_check": checked,
       "counts": counts, "formula_sha256": sha(formula),
       "formula_bytes": formula.stat().st_size,
       "phase_seconds": {"build": built - started,
                         "positive_assignment": after_check - built,
                         "serialize": finished - after_check},
       "wall_seconds": finished - started,
       "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "relaxed_build_protocol.json")}
(HERE / "relaxed_build_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("status", "counts", "wall_seconds")}, sort_keys=True))
