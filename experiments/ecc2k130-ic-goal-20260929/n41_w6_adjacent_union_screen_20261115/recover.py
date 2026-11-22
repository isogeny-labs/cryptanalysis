"""Recover the public N41 scalar from the union row and verified factor logs."""

import hashlib
import json
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = json.loads((HERE / "recovery_protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_RECOVERY"
    assert p["source_sha256"] == sha(__file__)
    for name, digest in p["input_sha256"].items():
        assert sha(p["inputs"][name]) == digest
    rows = json.loads((HERE / "union_rows.json").read_text())
    receipt = json.loads((HERE / "ordinary_receipt.json").read_text())
    logs = json.loads(Path(p["inputs"]["logs"]).read_text())
    base = json.loads(Path(p["inputs"]["base_map"]).read_text())
    public = json.loads(Path(p["inputs"]["public"]).read_text())
    fixture = json.loads(Path(p["inputs"]["fixture"]).read_text())
    assert receipt["status"] == "VERIFIED_SIX_POINT_ROW"
    assert logs["status"] == base["status"] == "PASS"
    r = 549756390943
    lam = int(base["frobenius_eigenvalue_mod_r"])
    ring = PolynomialRing(GF(2), "t")
    t = ring.gen()
    field = GF(2**41, name="t", modulus=t**41+t**3+1)
    curve = EllipticCurve(field, [1, 0, 0, 0, 1])

    def point(xy):
        return curve(field.from_integer(xy[0]), field.from_integer(xy[1]))

    generator = point(public["generator"])
    target = point(public["target_q"])
    assert receipt["target"] == public["target_q"]
    assert r*generator == r*target == curve(0)
    representatives = [point(row) for row in base["column_representatives"]]
    factors = [int(x) for x in logs["logs_by_column"]]
    assert len(representatives) == len(factors) == 26
    assert all(factors[i]*generator == representatives[i] for i in range(26))
    binding = {}
    for col, representative in enumerate(representatives):
        current = representative
        for j in range(41):
            binding[current] = (col, pow(lam, j, r))
            binding[-current] = (col, -pow(lam, j, r) % r)
            current = curve(current[0]**2, current[1]**2)
    assert len(binding) == 26*82
    for block in rows:
        for row in block["rows"]:
            source = point(row["original"])
            image = point(row["image"])
            col, coeff = binding[source]
            assert col == row["column"]
            assert image == ((lam+1)*coeff % r)*representatives[col]
    start = time.perf_counter_ns()
    terms = []
    selected_sum = curve(0)
    for slot, idx in enumerate(receipt["chosen_ids"]):
        row = rows[slot]["rows"][idx % 64]
        source = point(row["original"])
        col, coeff = binding[source]
        if idx >= 64:
            coeff = coeff*(lam+1) % r
            selected = point(row["image"])
        else:
            selected = source
        assert selected == coeff*representatives[col]
        selected_sum += selected
        terms.append([col, coeff, factors[col]])
    assert selected_sum == target
    scalar = sum(coeff*log for _, coeff, log in terms) % r
    replay_start = time.perf_counter_ns()
    assert scalar*generator == target
    replay_ns = time.perf_counter_ns()-replay_start
    recovery_ns = time.perf_counter_ns()-start
    assert scalar == int(fixture["scalar_for_validation_only"])
    print(json.dumps({
        "kind": "n41_w6_adjacent_union_verified_factor_log_recovery",
        "status": "PASS_VERIFIED_PUBLIC_SCALAR",
        "protocol_sha256": sha(HERE / "recovery_protocol.json"),
        "target": receipt["target"], "scalar": scalar,
        "chosen_ids": receipt["chosen_ids"], "terms": terms,
        "original_rows_bound_to_verified_logs": 384,
        "image_rows_bound_by_endomorphism": 384,
        "recovery_and_replay_ns": recovery_ns,
        "scalar_replay_ns": replay_ns,
        "native_join_online_ns": receipt["online_ns"],
        "diagnostic_combined_online_ns": receipt["online_ns"]+recovery_ns,
        "scalar_group_replay": "PASS",
        "matches_validation_only_fixture": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
