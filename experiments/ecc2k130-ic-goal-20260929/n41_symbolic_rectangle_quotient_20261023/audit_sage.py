"""Checked-Sage evaluation of the symbolic rectangle residue at all roots."""
import hashlib
import importlib.util
import json
import resource
import struct
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = json.loads((HERE / "protocol.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name, source in CFG["sources"].items():
    assert sha(source["path"]) == source["sha256"], name
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "PASS_N41_SYMBOLIC_TWO_CODE_RECTANGLES"
old_path = Path(CFG["sources"]["sage_curve_audit"]["path"])
spec = importlib.util.spec_from_file_location("independent_sage_curve", old_path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
curve, elem, integer = old.sage_curve()
cases = [json.loads(line) for line in Path(CFG["sources"]["coordinate_audit"]["path"]).open()]
geometry = json.loads(Path(CFG["sources"]["geometry"]["path"]).read_text())
terms = json.loads(Path(CFG["sources"]["root_polynomial"]["path"]).read_text())["terms"]
target_x = struct.unpack("<65Q", Path(CFG["sources"]["target_residuals"]["path"]).read_bytes())[0]
target_z = integer(1 / elem(target_x))
assert target_z == result["target_z"]
started = time.monotonic()


def eval_code(coefficients, p, q):
    a, b, c, d = [elem(value) for value in coefficients]
    return a + b * p + c * q + d * p * q


def eval_root(coefficients, p, q, u):
    acc = elem(0)
    for coefficient in reversed(coefficients):
        acc = acc * u + eval_code(coefficient, p, q)
    return acc


def direct_h(p, q):
    a = elem(geometry["blocks"][0]["s"])
    b = elem(geometry["blocks"][1]["s"])
    out = [elem(0) for _ in range(9)]
    for ea, eb, ep, eq, eu in terms:
        out[eu] += a**ea * b**eb * p**ep * q**eq
    assert out[8] != 0
    return [v / out[8] for v in out]


families = roots = coefficients = 0
for row in result["rows"]:
    assert len(row["left_codes"]) == len(row["right_codes"]) == 2
    values = set()
    for i, left in enumerate(row["left_codes"]):
        for j, right in enumerate(row["right_codes"]):
            case = next(cases[k] for k in row["case_indices"]
                        if cases[k]["left_code"] == left and cases[k]["right_code"] == right)
            columns_left = geometry["blocks"][0]["states"][4 * left]["columns"]
            columns_right = geometry["blocks"][1]["states"][4 * right]["columns"]
            assert set(columns_left).isdisjoint(columns_right)
            p, q = elem(row["p_values"][i]), elem(row["q_values"][j])
            specialized = [eval_code(c, p, q) for c in row["h"]]
            assert specialized == direct_h(p, q)
            coefficients += 9
            assert len(case["reciprocal_coordinates"]) == 8
            for z_integer in case["reciprocal_coordinates"]:
                z = elem(z_integer)
                assert z != 1
                u = z / (z + 1)
                assert eval_root(row["h"], p, q, u) == 0
                bit = eval_root(row["cubic_residue"], p, q, u)
                expected = int(all(z_integer >> k & 1 for k in CFG["bit_indices"]))
                assert bit == expected
                values.add(expected)
                roots += 1
            families += 1
    if row["label"] == "rejecting":
        assert values == {0}
        assert row["cubic_constant"] == 0 and row["target_rejected"] is True
    else:
        assert values == {0, 1}
        assert row["cubic_constant"] is None and row["target_rejected"] is False
        assert target_x in cases[966]["x_coordinates"]
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < CFG["rss_cap_bytes"]
    assert time.monotonic() - started < CFG["wall_cap_seconds"]

assert (families, roots, coefficients) == (8, 64, 72)
audit = {"status": "PASS_INDEPENDENT_SAGE_SYMBOLIC_RECTANGLE_AUDIT",
         "candidate_id": None, "families_checked": families,
         "roots_checked": roots, "coefficients_checked": coefficients,
         "witness_case_index": 966,
         "wall_seconds": time.monotonic() - started,
         "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         "result_sha256": sha(HERE / "result.json"),
         "protocol_sha256": sha(HERE / "protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": audit["status"], "roots_checked": roots}, sort_keys=True))
