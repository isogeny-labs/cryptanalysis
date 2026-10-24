"""Frozen N131 block-norm scaling against same-row individual GCDs."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "protocol_scaling.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_BLOCK_NORM_SCALING"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
for item in cfg["sources"].values():
    assert sha(item["path"]) == item["sha256"]
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("scaling wall cap")))
signal.alarm(cfg["worker_alarm_seconds"])


def balanced_product(values, one):
    level = list(values)
    while len(level) > 1:
        level = [level[i] * level[i + 1] if i + 1 < len(level) else level[i]
                 for i in range(0, len(level), 2)]
    return level[0] if level else one


def lin_coefficients(F, basis):
    coefficients = [F.one()]
    for value in basis:
        w = F.zero()
        x = value
        for c in coefficients:
            w += c * x
            x *= x
        assert w
        coefficients = ([w * coefficients[0]] +
            [coefficients[j - 1]**2 + w * coefficients[j] for j in range(1, len(coefficients))] +
            [coefficients[-1]**2])
    return coefficients


def gate(P, h, coefficients):
    if any(not f for f in h):
        return -1, True
    norm = balanced_product(h, P.one())
    x = P.gen() % norm
    rem = P.zero()
    for c in coefficients:
        rem = (rem + c * x) % norm
        x = (x * x) % norm
    degree = int(norm.gcd(rem).degree())
    return degree, degree > 0


started = time.monotonic()
B = PolynomialRing(GF(2), "u")
u = B.gen()
F = GF(2**131, name="u", modulus=u**131 + u**13 + u**2 + u + 1)
P = PolynomialRing(F, "z")
z = P.gen()
dec = F.from_integer
coeff_data = json.loads(Path(cfg["sources"]["coefficients"]["path"]).read_text())
reference = json.loads(Path(cfg["sources"]["reference"]["path"]).read_text())
assert reference["status"] == "COMPLETE_N131_NATIVE_REFERENCE"
seed_mask = 898618
bits = [i for i in range(33) if i != seed_mask.bit_length() - 1]
seed = dec(seed_mask << 1)


def product(code, rotation):
    a = sum((dec(1 << (bit + 1)) for j, bit in enumerate(bits)
             if code >> j & 1), F.zero())
    return (a * a + seed * a)**(1 << rotation)


right_basis = [product(1 << j, 18) for j in range(32)]
linear = lin_coefficients(F, right_basis)
assert len(linear) == 33
setup_seconds = time.monotonic() - started
results = []
sizes = cfg["block_sizes"]
assert sizes == [4, 8, 16, 32, 64]
for target_index in cfg["target_indexes"]:
    terms = [(i, j, dec(c)) for i, j, c in coeff_data["rows"][target_index]["terms"]]
    assert len(terms) == 13
    quartics = []
    for code in range(64):
        p = product(code, 0)
        powers = [p**i for i in range(5)]
        quartics.append(sum((c * powers[i] * z**j for i, j, c in terms), P.zero()))
    assert all(int(h.degree()) == 4 for h in quartics)
    refs = sorted((r for r in reference["rows"] if r["target_index"] == target_index and
                   r["p_code"] < 64), key=lambda r: r["p_code"])
    assert [r["p_code"] for r in refs] == list(range(64))
    per_code_seconds = []
    per_code_degrees = []

    def individual():
        for h in quartics:
            begin = time.monotonic()
            degree, _ = gate(P, [h], linear)
            per_code_seconds.append(time.monotonic() - begin)
            per_code_degrees.append(degree)
        assert all((degree > 0 or degree == -1) == (not ref["reject"])
                   for degree, ref in zip(per_code_degrees, refs))

    block_rows = []

    def blocks():
        for size in sizes:
            begin = time.monotonic()
            degree, retain = gate(P, quartics[:size], linear)
            seconds = time.monotonic() - begin
            assert retain == any(not r["reject"] for r in refs[:size])
            block_rows.append({"size": size, "norm_degree": 4 * size,
                               "gcd_degree": degree, "retain": retain,
                               "block_seconds": seconds})

    if target_index == 0:
        individual()
        blocks()
    else:
        blocks()
        individual()
    for row in block_rows:
        row["individual_prefix_seconds"] = sum(per_code_seconds[:row["size"]])
        row["retained_first_codes"] = [r["p_code"] for r in refs[:row["size"]] if not r["reject"]]
    results.append({"target_index": target_index, "block_rows": block_rows,
                    "individual_total_seconds": sum(per_code_seconds),
                    "individual_gcd_degrees": per_code_degrees})
    print(json.dumps({"event": "TARGET_DONE", "target_index": target_index,
                      "block_rows": block_rows}, sort_keys=True), flush=True)

signal.alarm(0)
result = {"status": "PASS_N131_BLOCK_NORM_SCALING", "candidate_id": None,
          "curve_id": cfg["curve_id"], "rows": results,
          "setup_seconds": setup_seconds, "worker_seconds": time.monotonic() - started,
          "peak_self_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "protocol_scaling.json"),
          "script_sha256": sha(__file__)}
(HERE / "scaling_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps({"status": result["status"], "worker_seconds": result["worker_seconds"]}, sort_keys=True), flush=True)
