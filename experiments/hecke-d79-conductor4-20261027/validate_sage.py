"""Exhaustive p=317 class and degree-13 factor-pattern replay."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve_from_j

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "experiments/ecdlp-hecke-floor-rank-20261012/tools/hecke11.py"
EXPECTED = "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
R = json.loads((HERE / "result.json").read_text())
assert R["p"] == 317 and R["class_size"] == 39
spec = importlib.util.spec_from_file_location("hecke11_conductor4_factor_audit", SOURCE)
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)
funcs, jfun = H.build([13])
reduced = H.Reduced(317, funcs, jfun, [13])
E = reduced.E
assert int(E.order()) == 305
traces = {}
class_set = set()
for P in E.points():
    if P.is_zero():
        continue
    j = reduced.j(P)
    if j is None or j in (0, 1728):
        continue
    if j not in traces:
        traces[j] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
    if traces[j] == 2:
        class_set.add((int(P[0]), int(P[1])))
saved_set = {tuple(P) for P in R["class_points"]}
assert class_set == saved_set
patterns = {}
cusp_root_sources = []
for item in R["degree13_sources"]:
    x, y = R["class_points"][item["source"]]
    P = E([x, y, 1])
    poly = reduced.neighbour_x(13, P)
    factors = poly.factor()
    pattern = [[int(f.degree()), int(m)] for f, m in factors]
    assert pattern == item["factor_pattern"]
    if poly(reduced.Fp(16)) == 0:
        cusp_root_sources.append(item["source"])
    patterns[str(pattern)] = patterns.get(str(pattern), 0) + 1
assert cusp_root_sources == [7, 22]
V = {"schema": "hecke-d79-conductor4-sage-validation-v1", "status": "PASS",
     "enumerated_curve_points": 305, "matching_class_points": len(class_set),
     "j_values_checked": len(traces), "degree13_patterns": patterns,
     "cusp_x_root_sources": cusp_root_sources}
(HERE / "sage-validation.json").write_text(json.dumps(V, indent=2, sort_keys=True) + "\n")
print("D79_CONDUCTOR4_SAGE_PASS", len(class_set), "points", len(patterns), "patterns")
