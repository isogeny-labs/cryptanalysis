"""Check the eliminated third-pair norm against direct S3 roots."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "protocol.json").read_text())
result = json.loads((HERE / "result.json").read_text())
spec = importlib.util.spec_from_file_location("independent_sage_curve", CFG["sources"]["sage_curve_audit"]["path"])
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
geo = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
cases = {(c["left_code"], c["right_code"]): c for c in
         (json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open())}
t = elem(result["target_chart"])
s = elem(geo["blocks"][2]["s"])


def norm(u, r):
    a = t*t + u*(u+1)*t*(t+1) + (t+1)*(t+1)
    b = u*(u+1)*t*(t+1)
    d = (u+1)**2*t*t + u*u*(t+1)**2
    l = 1+r
    m = l*b+r*a
    n = l*d+s*s*a
    return l*n*n+r*n*m+s*s*m*m


def s3(u, v):
    return (u+v+1)**2*t*t + u*v*(u+1)*(v+1)*t*(t+1) + (u+v)**2*(t+1)**2


roots = zero_norms = zero_s3 = 0
matches = []
for row in result["rows"]:
    for left, right, third in row["code_triples"]:
        k = row["code_lists"][2].index(third)
        r = elem(row["r_values"][k])
        v_values = {elem(geo["blocks"][2]["states"][j]["z"])
                    for j in range(4*third, 4*third+4)}
        assert len(v_values) == 2
        for z_integer in cases[left, right]["reciprocal_coordinates"]:
            z = elem(z_integer)
            u = z/(z+1)
            norm_zero = norm(u, r) == 0
            s3_zero = any(s3(u, v) == 0 for v in v_values)
            assert norm_zero == s3_zero
            roots += 1
            zero_norms += int(norm_zero)
            zero_s3 += int(s3_zero)
            if norm_zero:
                matches.append({"code_triple": [left, right, third],
                                "first_two_chart": integer(u),
                                "third_pair_charts": sorted(map(integer, v_values))})
assert (roots, zero_norms, zero_s3) == (512, 1, 1)
assert len(matches) == 1 and matches[0]["code_triple"] == [24, 37, 10]
receipt = {"status": "PASS_DIRECT_THIRD_PAIR_GEOMETRY",
           "roots_checked": roots, "norm_zeros": zero_norms,
           "s3_zeros": zero_s3, "matches": matches,
           "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "result_sha256": hashlib.sha256((HERE / "result.json").read_bytes()).hexdigest()}
(HERE / "geometry_audit_result.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True))
