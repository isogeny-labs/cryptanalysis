"""Read-only verification of trace-reduced sparse-quadratic census and audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


p = read("protocol.json")
assert p["status"] == "FROZEN" and p["candidate_id"] is None
for path, digest in p["sources"].items():
    assert sha(Path(path)) == digest, path
r = read("run_result.json")
assert r["status"] == "EXIT_0" and r["stop_reason"] is None
assert not r["monitor_degraded"] and r["wall_ns"] < 120 * 10**9
assert r["sampled_peak_combined_rss_bytes"] < 4 * 1024**3
assert r["protocol_sha256"] == sha(HERE / "protocol.json")
for name, digest in r["sha256"].items():
    assert sha(HERE / name) == digest, name
out = read("result.json")
assert out["status"] == "COMPLETE_N41_SPARSE_QUADRATIC_CENSUS"
assert len(out["cases"]) == 8
assert [row["case_id"] for row in out["cases"]] == [-1, 0, 1, 2, 3, 4, 5, 7]
assert all(row["left_zero_terms"] == row["right_zero_terms"] == 0
           and row["left_min_support_le4"] == row["right_min_support_le4"] == 5
           for row in out["cases"])
assert out["cases"][0]["s3_hits"] == 1
assert all(row["s3_hits"] == 0 for row in out["cases"][1:])
old = json.loads((ROOT / "n41_w8_sparse_quadratic_gate_20261013/result.json").read_text())
for a, b in zip(old["cases"], out["cases"]):
    assert a["starts"] == b["starts"] and a["s3_hits"] == b["s3_hits"]
    assert a["left_unique"] == b["left_unique"]
    assert a["right_unique"] == b["right_unique"]
audit_protocol = read("audit_protocol.json")
assert audit_protocol["status"] == "FROZEN"
for path, digest in audit_protocol["sources"].items():
    assert sha(Path(path)) == digest, path
audit = read("audit_result.json")
assert audit["status"] == "PASS_INDEPENDENT_N41_SPARSE_QUADRATIC_AUDIT"
assert len(audit["checks"]) == 4
assert all(row["monomials"] == 821 and row["minimum_support_le4"] == 5
           for row in audit["checks"])
assert read("sage_runtime_info.json")["status"] == "verified"
print("PASS_FROZEN_N41_TRACE_REDUCED_SPARSE_QUADRATIC_V2")
