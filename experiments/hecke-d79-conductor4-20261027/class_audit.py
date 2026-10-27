"""Independent exhaustive rational-fiber census for the p=317 D=-79 class."""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve_from_j, hilbert_class_polynomial

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "experiments/ecdlp-hecke-floor-rank-20261012/tools/hecke11.py"
EXPECTED = "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
spec = importlib.util.spec_from_file_location("hecke11_conductor4_audit", SOURCE)
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
funcs, jfun = H.build([2])
R = H.Reduced(317, funcs, jfun, [2])
E = R.E
points = list(E.points())
fiber = {}
exceptional = Counter()
for P in points:
    if P.is_zero():
        exceptional["identity"] += 1
        continue
    j = R.j(P)
    if j is None:
        exceptional["j_pole"] += 1
        continue
    fiber.setdefault(int(j), []).append([int(P[0]), int(P[1])])
    if j == 0:
        exceptional["j_zero"] += 1
    elif j == 1728:
        exceptional["j_1728"] += 1
strata = []
all_class_points = set()
for d in (1, 2, 4):
    D = -79*d*d
    roots = [int(j) for j in hilbert_class_polynomial(D).change_ring(R.Fp).roots(multiplicities=False)]
    entries = []
    for j in sorted(roots):
        tr = abs(int(EllipticCurve_from_j(R.Fp(j)).trace_of_frobenius()))
        coords = sorted(fiber.get(j, []))
        if tr == 2:
            all_class_points.update(tuple(P) for P in coords)
        entries.append({"j": j, "trace_magnitude": tr, "rational_fiber": coords,
                        "fiber_size": len(coords)})
    strata.append({"conductor": d, "discriminant": D, "roots": entries,
                   "j_count": len(entries), "point_count": sum(x["fiber_size"] for x in entries)})
trace_cache = {}
full_class = set()
for j, coords in fiber.items():
    if j in (0, 1728 % 317):
        continue
    if j not in trace_cache:
        trace_cache[j] = abs(int(EllipticCurve_from_j(R.Fp(j)).trace_of_frobenius()))
    if trace_cache[j] == 2:
        full_class.update(tuple(P) for P in coords)
result = {"schema": "hecke-d79-conductor4-class-audit-v1", "p": 317,
          "ambient_order": len(points), "exceptional": dict(exceptional),
          "strata": strata, "strata_point_union": len(all_class_points),
          "full_trace_magnitude_two_class": len(full_class),
          "strata_equals_full_trace_class": all_class_points == full_class,
          "class_points": [list(P) for P in sorted(full_class)]}
(HERE / "class-audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"ambient_order": len(points), "strata_counts":
                  [(s["conductor"], s["j_count"], s["point_count"]) for s in strata],
                  "full_class_points": len(full_class), "exceptional": dict(exceptional)},
                 sort_keys=True))
