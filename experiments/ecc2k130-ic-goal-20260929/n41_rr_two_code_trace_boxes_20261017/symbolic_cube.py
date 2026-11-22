"""Measure the sign-free D-cubed construction on the same frozen N41 charts."""
import hashlib
import importlib.util
import json
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())
protocol = read(D / "symbolic_protocol.json")
assert protocol["runner_sha256"] == sha(D / "symbolic_cube.py")
for path, digest in protocol["sources"].items():
    assert sha(ROOT / path) == digest, path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rr = load("rr_symbolic_box", ROOT / "n41_n131_sixpair_rr_root_span_20261016/run.py")
quad = load("quadratic_symbolic_box", ROOT / "n41_n131_rr_quadratic_trace_20261017/run.py")
parent = load("two_code_box_parent", D / "run.py")
geometry = read(ROOT / "n41_w8_fixed_sum_table_20261009/geometry.json")
hit = read(ROOT / "n41_sixpair_shared_target_20261017/join_audit_result.json")
result = read(D / "result.json")
field = parent.CountedField(rr.Field(41, (1 << 41) | (1 << 3) | 1))
fixed = []
for slot in range(2, 6):
    witness = hit["pair_rows"][slot]["raw_sum"]
    choices = [s["raw_sum"] for s in geometry["blocks"][slot]["states"]
               if s["raw_sum"][0] == witness[0]]
    fixed.append(min(choices, key=lambda p: p[1]))
charts = result["boxes"][0]["charts"]
records = []
for chart in charts:
    points = [chart["point_a"], chart["point_b"]] + fixed
    c = rr.coefficients([p[0] for p in points], [p[1] for p in points],
                        hit["raw_target"], field)
    assert hashlib.sha256(json.dumps(c).encode()).hexdigest() == chart["coefficient_sha256"]
    before = field.mul_count
    start = time.monotonic_ns()
    cube = quad.cube_anf(c, field)
    ns = time.monotonic_ns() - start
    assert all(rr.evaluate(cube, sign) == field.f.mul(
        field.f.mul(rr.evaluate(c, sign), rr.evaluate(c, sign)), rr.evaluate(c, sign))
        for sign in range(64))
    records.append({"code_a": chart["code_a"], "code_b": chart["code_b"],
                    "cube_ns": ns, "cube_field_mul": field.mul_count - before})
out = {"status": "COMPLETE_SYMBOLIC_CUBE_COST_SCREEN", "candidate_id": None,
       "protocol_sha256": sha(D / "symbolic_protocol.json"),
       "charts": len(records), "cube_ns": sum(row["cube_ns"] for row in records),
       "cube_field_mul": sum(row["cube_field_mul"] for row in records),
       "direct_sign_ns": result["boxes"][0]["direct_sign_ns"],
       "records": records}
(D / "symbolic_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ("status", "charts", "cube_ns", "cube_field_mul", "direct_sign_ns")}))
