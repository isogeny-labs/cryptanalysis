"""Recover an explicit 25-power trace certificate for the lexical N41 box."""
import hashlib
import importlib.util
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
read = lambda path: json.loads(path.read_text())
protocol = read(D / "certificate_protocol.json")
assert sha(D / "recover_certificate.py") == protocol["runner_sha256"]
for path, digest in protocol["sources"].items():
    assert sha(ROOT / path) == digest, path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


quad = load("quad_trace_recover", ROOT / "n41_n131_rr_quadratic_trace_20261017/run.py")
rr = quad.load_rr()
field = rr.Field(41, (1 << 41) | (1 << 3) | 1)
charts = read(D / "result.json")["boxes"][0]["charts"]
assert len(charts) == 16


def anf(values):
    out = values[:]
    for bit in range(6):
        for mask in range(64):
            if mask >> bit & 1:
                out[mask] ^= out[mask ^ (1 << bit)]
    return out


basis = {}
rows = []
for chart in charts:
    values = chart["values"]
    square = [field.mul(value, value) for value in values]
    current = values[:]
    power_coefficients = []
    for j in range(25):
        power_coefficients.append(anf(current))
        if j < 24:
            current = [field.mul(a, b) for a, b in zip(current, square)]
    for mask in range(64):
        word = sum(coeff[mask] << (j*41) for j, coeff in enumerate(power_coefficients))
        label = int(mask == 0)
        index = len(rows)
        rows.append((word, label))
        assert quad.insert(basis, word, label, 1 << index) is None
assert len(rows) == len(basis) == 1024
functional = quad.solve(basis)
assert all(((functional & word).bit_count() & 1) == label for word, label in rows)
dual = quad.trace_dual(field)
coefficients = [quad.trace_coefficient(dual, (functional >> (j*41)) & ((1 << 41) - 1))
                for j in range(25)]
trace_mask = quad.trace_mask(field)
for chart in charts:
    for value in chart["values"]:
        power = value
        square = field.mul(value, value)
        total = 0
        for j, coefficient in enumerate(coefficients):
            total ^= field.mul(coefficient, power)
            if j < 24:
                power = field.mul(power, square)
        assert ((total & trace_mask).bit_count() & 1) == 1
out = {"status": "PASS_EXPLICIT_N41_25_POWER_CERTIFICATE",
       "protocol_sha256": sha(D / "certificate_protocol.json"),
       "odd_powers": list(range(1, 50, 2)),
       "trace_coefficients": coefficients,
       "feature_rank": len(basis), "signed_determinants_checked": len(rows)}
(D / "certificate.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
print(out["status"])
