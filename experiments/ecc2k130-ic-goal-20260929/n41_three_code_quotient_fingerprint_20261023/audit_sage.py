"""Independent checked-Sage audit of all 64 specialized H/Q families and roots."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, source in CFG["sources"].items():
    assert sha(source["path"]) == source["sha256"], name
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "PASS_N41_THREE_CODE_QUOTIENT_FINGERPRINT"
spec = importlib.util.spec_from_file_location("independent_sage_curve", CFG["sources"]["sage_curve_audit"]["path"])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
geo = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
terms = json.loads(Path(CFG["sources"]["root_polynomial"]["path"]).read_text())["terms"]
cases = {(c["left_code"], c["right_code"]): c for c in
         (json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open())}
witness_protocol = json.loads(Path(CFG["sources"]["witness_protocol"]["path"]).read_text())
t = elem(result["target_chart"])
s = elem(geo["blocks"][2]["s"])
started = time.monotonic()


def eval_code(c, p, q, r):
    def low(a):
        a0, a1, a2, a3 = [elem(x) for x in a]
        return a0 + a1*p + a2*q + a3*p*q
    return low(c[0]) + r*low(c[1])


def eval_root(cs, p, q, r, u):
    value = elem(0)
    for c in reversed(cs):
        value = value*u + eval_code(c, p, q, r)
    return value


def direct_h(p, q):
    a, b = (elem(geo["blocks"][i]["s"]) for i in (0, 1))
    h = [elem(0) for _ in range(9)]
    for ea, eb, ep, eq, eu in terms:
        h[eu] += a**ea*b**eb*p**ep*q**eq
    assert h[8]
    return [x/h[8] for x in h]


def direct_q(u, r):
    a = t*t + u*(u+1)*t*(t+1) + (t+1)*(t+1)
    b = u*(u+1)*t*(t+1)
    d = (u+1)**2*t*t + u*u*(t+1)**2
    l = 1+r
    m = l*b+r*a
    n = l*d+s*s*a
    return l*n*n+r*n*m+s*s*m*m


families = roots = coefficient_checks = norm_zeros = witness_zeros = 0
for row in result["rows"]:
    values = set()
    for left, right, third in row["code_triples"]:
        i = row["code_lists"][0].index(left)
        j = row["code_lists"][1].index(right)
        k = row["code_lists"][2].index(third)
        p, q, r = elem(row["p_values"][i]), elem(row["q_values"][j]), elem(row["r_values"][k])
        assert [eval_code(c, p, q, r) for c in row["h"]] == direct_h(p, q)
        coefficient_checks += 9
        case = cases[left, right]
        assert len(case["reciprocal_coordinates"]) == 8
        for z_integer in case["reciprocal_coordinates"]:
            z = elem(z_integer)
            assert z != 1
            u = z/(z+1)
            assert eval_root(row["h"], p, q, r, u) == 0
            qvalue = direct_q(u, r)
            assert eval_root(row["upper_norm"], p, q, r, u) == qvalue
            for check in row["fingerprint_checks"]:
                observed = eval_root(check["residue"], p, q, r, u)
                expected = int(integer(qvalue) & ((1 << check["bits"]) - 1) == 0)
                assert observed == expected
            norm_zeros += int(qvalue == 0)
            witness_zeros += int(qvalue == 0 and row["label"] == "witness")
            values.add(int(qvalue == 0))
            roots += 1
        families += 1
    assert row["target_rejected"] == (1 not in values)
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]
    assert time.monotonic() - started < CFG["wall_cap_seconds"]

ids = [97, 151, 42, 0, 14, 109, 51]
raw_sum = curve(0)
for axis, state_id in enumerate(ids):
    x, y = geo["blocks"][axis]["states"][state_id]["raw_sum"]
    raw_sum += curve(elem(x), elem(y))
assert [integer(raw_sum[0]), integer(raw_sum[1])] == witness_protocol["raw_target"]
public = 4*raw_sum
assert [integer(public[0]), integer(public[1])] == witness_protocol["public_target"]
assert (families, roots, coefficient_checks) == (64, 512, 576)
assert witness_zeros >= 1
audit = {"status": "PASS_INDEPENDENT_SAGE_THREE_CODE_QUOTIENT_AUDIT",
         "candidate_id": None, "families_checked": families, "roots_checked": roots,
         "coefficients_checked": coefficient_checks, "norm_zeros": norm_zeros,
         "witness_box_norm_zeros": witness_zeros,
         "witness_raw_target": witness_protocol["raw_target"],
         "witness_public_target": witness_protocol["public_target"],
         "wall_seconds": time.monotonic() - started,
         "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "result_sha256": sha(HERE / "result.json"),
         "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": audit["status"], "roots_checked": roots,
                  "norm_zeros": norm_zeros}, sort_keys=True))
