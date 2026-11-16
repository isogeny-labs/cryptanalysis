"""Independent Sage group-law replay of every accepted reduced-family candidate."""

import gzip
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, QQ, crt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BAND = ROOT / "xedni-crt-band-panel-20261115"
SHIFT = ROOT / "xedni-point-lift-shift-20261115"
PARENT = ROOT / "xedni-crt-curve-choice-20261115" / "run_v2.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert sha(HERE / "protocol.json") == result["protocol_sha256"]
    assert sha(HERE / "run.py") == result["source_sha256"]
    for key, path in (("centered_result_sha256", BAND / "result.json"),
                      ("shifted_result_sha256", SHIFT / "result.json"),
                      ("family_result_sha256", ROOT / "xedni-coefficient-family-control-20261115" / "result.json"),
                      ("arithmetic_source_sha256", ROOT / "xedni-crt-prime-panel-20261115" / "audit.py"),
                      ("candidate_order_source_sha256", ROOT / "xedni-crt-curve-choice-20261115" / "cost_audit.py"),
                      ("shift_source_sha256", SHIFT / "run.py")):
        assert sha(path) == protocol[key], key
    parent = load_module("xedni_lift_sage_parent", PARENT)
    shift = load_module("xedni_lift_sage_shift", SHIFT / "run.py")
    orders = {ell: parent.coefficient_order(ell) for ell in (7, 11)}
    vectors = [(a, b) for a in range(1, 4) for b in range(-3, 4)
               if b and math.gcd(a, abs(b)) == 1]
    totals = Counter()
    arms = []
    for arm in result["arms"]:
        label = arm["arm"]
        folder = BAND if label == "centered" else SHIFT
        reference = json.loads((folder / "result.json").read_text())
        fields = []
        for record, old in zip(arm["fields"], reference["fields"], strict=True):
            p, r = old["field_prime"], old["subgroup_order"]
            assert p == record["field_prime"] and r == record["subgroup_order"]
            Ebase = EllipticCurve(GF(p), protocol["base_curve_coefficients"])
            G = Ebase(old["generator"])
            Q = Ebase(old["public_target"])
            assert old["fixture_scalar"] * G == Q and r * G == Ebase(0)
            sampled = [Q - t * G for t in range(r)]
            row_hash = hashlib.sha256()
            hits = []
            checked = 0
            count_by_vector = Counter()
            index = 0
            for shard in old["row_shards"]:
                raw = gzip.open(folder / "rows" / shard, "rb").read()
                row_hash.update(raw)
                for line in raw.splitlines():
                    row = json.loads(line)
                    t1, t2 = divmod(index, r)
                    index += 1
                    assert row["t"] == [t1, t2]
                    U0, V0 = sampled[t1], sampled[t2]
                    if U0.is_zero() or V0.is_zero() or U0 == V0 or not row["accepted"]:
                        continue
                    reduced_vectors = [(a, b) for a, b in vectors
                                       if (a * (old["fixture_scalar"]-t1) +
                                           b * (old["fixture_scalar"]-t2)) % r == 0]
                    if not reduced_vectors:
                        continue
                    centered = [(parent.centered(P[0], p), parent.centered(P[1], p))
                                for P in (U0, V0)]
                    if label == "shifted":
                        k, points = shift.shift(centered, p)
                        assert k == row["k"]
                    else:
                        points = centered
                    i7, i11 = row["attempts_7"], row["attempts_11"]
                    assert i7 > 0 and i11 > 0
                    c7, c11 = orders[7][i7-1], orders[11][i11-1]
                    modulus = 77*p
                    free = [int(crt([0, c7[i], c11[i]], [p, 7, 11])) for i in range(3)]
                    free = [n if n <= modulus//2 else n-modulus for n in free]
                    a4, a6 = parent.solved(points, *free)
                    coeffs = [*free, a4, a6]
                    E = EllipticCurve(QQ, coeffs)
                    U, V = [E([x, y]) for x, y in points]
                    for a, b in reduced_vectors:
                        checked += 1
                        rational = bool((a*U+b*V).is_zero())
                        if (a, b) == (1, 2):
                            assert rational == row["rational_relation"]
                        if rational:
                            count_by_vector[(a, b)] += 1
                            hits.append({"query_index_one_based": index,
                                         "t": [t1, t2], "vector": [a, b],
                                         "coefficients": [str(c) for c in coeffs],
                                         "points": [list(point) for point in points]})
            assert index == r*r and row_hash.hexdigest() == old["rows_sha256"]
            expected = [{k: w[k] for k in ("query_index_one_based", "t", "vector",
                                          "coefficients", "points")}
                        for w in record["witnesses"]]
            assert hits == expected
            assert checked == record["counts"].get("rational_group_tests", 0)
            assert count_by_vector == Counter({tuple(v["c"]): v["rational_relations"]
                                               for v in record["by_vector"] if v["rational_relations"]})
            fields.append({"field_prime": p, "rational_group_tests": checked,
                           "rational_relations": len(hits)})
            totals["rational_group_tests"] += checked
            totals["rational_relations"] += len(hits)
        arms.append({"arm": label, "fields": fields})
    print(json.dumps({"schema": "xedni-coefficient-family-lift-sage-audit-v1",
                      "status": "PASS", "protocol_sha256": sha(HERE / "protocol.json"),
                      "source_sha256": sha(Path(__file__)),
                      "sage_runtime_sha256": sha(HERE / "sage-runtime-info.json"),
                      "totals": dict(totals), "arms": arms}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
