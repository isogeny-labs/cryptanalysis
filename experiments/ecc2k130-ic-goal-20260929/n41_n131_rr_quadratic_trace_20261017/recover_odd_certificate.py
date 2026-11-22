"""Construct four odd-power trace coefficients for the frozen N131 panel."""
import hashlib
import importlib.util
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
protocol = json.loads((D / "certificate_protocol.json").read_text())
assert protocol["runner_sha256"] == sha(D / "recover_odd_certificate.py")
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
spec = importlib.util.spec_from_file_location("quad_trace_tool", D / "run.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
rr = tool.load_rr()
panel = json.loads((ROOT / "n41_n131_rr_code_family_span_20261017/panel_n131_v2.json").read_text())
field = rr.Field(panel["field_degree"], panel["field_modulus"])
powers = (1, 3, 5, 7)
basis = {}
values = []
for variant in panel["variants"]:
    for root in variant["roots"]:
        points = [root[0]] + panel["fixed_points"]
        c = rr.coefficients([p[0] for p in points], [p[1] for p in points],
                            panel["target"], field)
        assert c is not None
        chart_values = [rr.evaluate(c, signs) for signs in range(64)]
        power_coefficients = []
        for exponent in powers:
            evaluated = []
            for value in chart_values:
                power = 1
                for _ in range(exponent):
                    power = field.mul(power, value)
                evaluated.append(power)
            for bit in range(6):
                for mask in range(64):
                    if mask >> bit & 1:
                        evaluated[mask] ^= evaluated[mask ^ (1 << bit)]
            power_coefficients.append(evaluated)
        for mask in range(64):
            word = sum(coeff[mask] << (i * field.n)
                       for i, coeff in enumerate(power_coefficients))
            index = len(values)
            values.append((word, int(mask == 0)))
            assert tool.insert(basis, word, int(mask == 0), 1 << index) is None
assert len(values) == len(basis) == 512
functional = tool.solve(basis)
assert all(((functional & word).bit_count() & 1) == label for word, label in values)
dual = tool.trace_dual(field)
coefficients = [tool.trace_coefficient(dual, (functional >> (i * field.n)) & ((1 << field.n) - 1))
                for i in range(4)]
trace_mask = tool.trace_mask(field)
def trace(value):
    return (value & trace_mask).bit_count() & 1
for variant in panel["variants"]:
    for root in variant["roots"]:
        points = [root[0]] + panel["fixed_points"]
        c = rr.coefficients([p[0] for p in points], [p[1] for p in points],
                            panel["target"], field)
        for signs in range(64):
            value = rr.evaluate(c, signs)
            total = 0
            for a, exponent in zip(coefficients, powers):
                power = 1
                for _ in range(exponent):
                    power = field.mul(power, value)
                total ^= field.mul(a, power)
            assert trace(total) == 1
out = {"status": "PASS_FOUR_POWER_SHARED_TRACE_CERTIFICATE",
       "candidate_id": None, "protocol_sha256": sha(D / "certificate_protocol.json"),
       "odd_powers": list(powers), "trace_coefficients": coefficients,
       "feature_rank": len(basis), "chart_count": 8,
       "signed_determinants_checked": 512}
(D / "odd_certificate.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
