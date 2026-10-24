"""Independent exact N41 audit of the four-code quotient and residual table."""
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
assert result["status"] == "PASS_N41_FOUR_CODE_SUFFIX_QUOTIENT"
spec = importlib.util.spec_from_file_location("independent_sage_curve", CFG["sources"]["sage_curve_audit"]["path"])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
geo = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
terms = json.loads(Path(CFG["sources"]["root_polynomial"]["path"]).read_text())["terms"]
cases = {(c["left_code"], c["right_code"]): c for c in
         (json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open())}
target_table = json.loads(Path(CFG["sources"]["target_table"]["path"]).read_text())
witness = json.loads(Path(CFG["sources"]["witness_protocol"]["path"]).read_text())
s = elem(geo["blocks"][2]["s"])
started = time.monotonic()


def eval_code(c, p, q, r, w):
    def low2(a):
        a0, a1, a2, a3 = [elem(x) for x in a]
        return a0 + a1*p + a2*q + a3*p*q
    def low3(a):
        return low2(a[0]) + r*low2(a[1])
    return low3(c[0]) + w*low3(c[1])


def eval_root(cs, p, q, r, w, u):
    value = elem(0)
    for c in reversed(cs):
        value = value*u + eval_code(c, p, q, r, w)
    return value


def direct_h(p, q):
    a, b = (elem(geo["blocks"][i]["s"]) for i in (0, 1))
    h = [elem(0) for _ in range(9)]
    for ea, eb, ep, eq, eu in terms:
        h[eu] += a**ea*b**eb*p**ep*q**eq
    assert h[8]
    return [x/h[8] for x in h]


def direct_q(u, r, t):
    a = t*t + u*(u+1)*t*(t+1) + (t+1)*(t+1)
    b = u*(u+1)*t*(t+1)
    d = (u+1)**2*t*t + u*u*(t+1)**2
    l = 1+r
    m = l*b+r*a
    n = l*d+s*s*a
    return l*n*n+r*n*m+s*s*m*m


raw_target = curve(*(elem(x) for x in witness["raw_target"]))
suffix = curve(0)
for axis, state_id in enumerate(CFG["suffix_state_ids"], 4):
    suffix += curve(*(elem(x) for x in geo["blocks"][axis]["states"][state_id]["raw_sum"]))
for code in range(40):
    for offset in range(4):
        state = geo["blocks"][3]["states"][4*code+offset]
        point = curve(*(elem(x) for x in state["raw_sum"]))
        residual = raw_target - suffix - point
        assert integer(1/(residual[0]+1)) == target_table["rows"][code][offset]["chart"]

families = roots = coefficients = norm_zeros = 0
zero_locations = []
for row in result["rows"]:
    found = False
    for quad in row["code_quads"]:
        left, right, third, fourth = quad
        i, j, k, l = [row["code_lists"][axis].index(quad[axis]) for axis in range(4)]
        p, q, r, w = (elem(row[key][index]) for key, index in
                      zip(("p_values", "q_values", "r_values", "w_values"), (i, j, k, l)))
        assert [eval_code(c, p, q, r, w) for c in row["h"]] == direct_h(p, q)
        coefficients += 9
        for z_integer in cases[left, right]["reciprocal_coordinates"]:
            z = elem(z_integer)
            u = z/(z+1)
            assert eval_root(row["h"], p, q, r, w, u) == 0
            target_values = [elem(target_table["rows"][fourth][offset]["chart"])
                             for offset in range(4)]
            qvalues = [direct_q(u, r, t) for t in target_values]
            product = elem(1)
            for value in qvalues:
                product *= value
            assert eval_root(row["upper_norm"], p, q, r, w, u) == product
            for check in row["fingerprint_checks"]:
                observed = eval_root(check["residue"], p, q, r, w, u)
                expected = int(integer(product) & ((1 << check["bits"]) - 1) == 0)
                assert observed == expected
            if product == 0:
                norm_zeros += 1
                found = True
                zero_locations.append({"code_quad": quad, "first_two_chart": integer(u),
                                       "matching_fourth_offsets": [offset for offset, value in enumerate(qvalues)
                                                                   if value == 0]})
            roots += 1
        families += 1
    assert row["target_rejected"] == (not found)
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]
    assert time.monotonic() - started < CFG["wall_cap_seconds"]

assert families == 16 * len(result["rows"]) and roots == 8 * families
assert coefficients == 9 * families
assert len(zero_locations) == 1 and zero_locations[0]["code_quad"] == [24, 37, 10, 0]
assert zero_locations[0]["matching_fourth_offsets"] == [0]
ids = [97, 151, 42, 0, 14, 109, 51]
raw_sum = curve(0)
for axis, state_id in enumerate(ids):
    raw_sum += curve(*(elem(x) for x in geo["blocks"][axis]["states"][state_id]["raw_sum"]))
assert raw_sum == raw_target
assert [integer((4*raw_sum)[0]), integer((4*raw_sum)[1])] == witness["public_target"]
audit = {"status": "PASS_INDEPENDENT_SAGE_FOUR_CODE_QUOTIENT_AUDIT",
         "candidate_id": None, "families_checked": families, "roots_checked": roots,
         "coefficients_checked": coefficients, "norm_zeros": norm_zeros,
         "zero_locations": zero_locations, "target_charts_checked": 160,
         "wall_seconds": time.monotonic() - started,
         "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "result_sha256": sha(HERE / "result.json"),
         "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": audit["status"], "roots_checked": roots,
                  "norm_zeros": norm_zeros}, sort_keys=True))
