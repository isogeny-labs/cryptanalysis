"""Build and check the unpinned N41 public-point deferred-source formula."""
import hashlib
import json
import resource
import time
from pathlib import Path

import circuit_deferred as design

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "build_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N41_SIXPAIR_DEFERRED_BUILD"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
prior = design.prior
F = design.F
receipt = json.loads(Path(cfg["sources"]["public_relation"]["path"]).read_text())
assert receipt["status"] == "PASS_INDEPENDENT_N41_PUBLIC_SIX_PAIR_RELATION"
assert receipt["raw_target_preimage_index"] == 0
assert [row["rotation"] for row in receipt["source_pairs"]] == design.ROTATIONS
target_point = tuple(receipt["raw_target_replayed"])
target_reciprocal = F.inv(target_point[0])
assert target_reciprocal

allowed = set()
for code in range(128):
    a = design.prior.xor(design.BASE[j] for j in range(7) if code >> j & 1)
    p = F.mul(a, a ^ design.SEED)
    if not a or not p or prior.trace(a):
        continue
    v = F.inv(p)
    if prior.trace(F.mul(a, v)) or prior.trace(F.mul(design.SEED, v)):
        continue
    allowed.add(code)
assert len(allowed) == 40
geometry = prior.geometry()
expected = {sum(((mask >> bit) & 1) << j for j, bit in enumerate(design.BITS))
            for mask in geometry["permitted_canonical_a"]}
assert allowed == expected

started = time.monotonic()
circ, wires, counts = design.build(target_reciprocal, tuple(cfg["exact_slots"]))
built = time.monotonic()
assignment = {}


def bind(bits, value):
    assignment.update({wire: (value >> j) & 1 for j, wire in enumerate(bits)})


codes = []
points = []
for slot, row in enumerate(receipt["source_pairs"]):
    mask = row["masks"][0]
    code = sum(((mask >> bit) & 1) << j for j, bit in enumerate(design.BITS))
    assert code in allowed
    codes.append(code)
    bind(wires["mask"][slot], code)
    p = design.prior.xor(design.PB[j] for j in range(7) if code >> j & 1)
    if wires["source_inverse"][slot] is not None:
        bind(wires["source_inverse"][slot], F.inv(p))
    point = tuple(row["pair_rotated"])
    assert prior.replay.on_curve(F, point)
    points.append(point)
    unrotated_x = prior.frob(point[0], (41 - row["rotation"]) % 41)
    bind(wires["out"][slot], F.inv(unrotated_x))
assert len(set(codes)) == 6
add = prior.replay.add
middle = [add(F, points[0], points[1]),
          add(F, points[2], points[3]),
          add(F, points[4], points[5])]
middle.append(add(F, middle[0], middle[1]))
assert add(F, middle[3], middle[2]) == target_point
for bits, point in zip(wires["middle"], middle):
    assert point is not None and point[0]
    bind(bits, F.inv(point[0]))
full = prior.old.complete_assignment(circ, assignment)
check = prior.old.check_assignment(circ, full)
assert check == {"clauses": counts["clauses"],
                 "native_xor_rows": counts["native_xor_rows"]}
checked = time.monotonic()

formula = HERE / "n41_public_deferred.xcnf"
assert not formula.exists()
circ.write(formula)
finished = time.monotonic()
result = {"status": "PASS_N41_SIXPAIR_DEFERRED_CIRCUIT",
          "candidate_id": None, "curve_id": cfg["curve_id"],
          "target_point": list(target_point),
          "target_reciprocal": target_reciprocal,
          "constructed_codes": codes,
          "exact_slots": cfg["exact_slots"],
          "positive_assignment_check": check,
          "counts": counts,
          "formula_sha256": sha(formula),
          "formula_bytes": formula.stat().st_size,
          "phase_seconds": {"build": built - started,
                            "positive_assignment": checked - built,
                            "serialize": finished - checked},
          "wall_seconds": finished - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "build_protocol.json")}
(HERE / "build_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("status", "counts", "wall_seconds",
                                           "formula_bytes", "constructed_codes")}, sort_keys=True))
