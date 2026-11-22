"""Read-only verification of the first sparse-quadratic census."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


p = read("protocol.json")
assert p["status"] == "FROZEN" and p["candidate_id"] is None
for path, digest in p["sources"].items():
    assert sha(Path(path)) == digest, path
r = read("run_result.json")
assert r["status"] == "EXIT_0" and not r["monitor_degraded"]
assert r["protocol_sha256"] == sha(HERE / "protocol.json")
for name, digest in r["sha256"].items():
    assert sha(HERE / name) == digest, name
out = read("result.json")
assert out["status"] == "COMPLETE_N41_SPARSE_QUADRATIC_CENSUS"
assert len(out["cases"]) == 8
assert all(row["left_zero_terms"] == row["right_zero_terms"] == 41
           for row in out["cases"])
assert out["cases"][0]["kind"] == "witness" and out["cases"][0]["s3_hits"] == 1
assert "ModuleNotFoundError: No module named 'psutil'" in (HERE / "first_launch_failure.txt").read_text()
assert read("sage_runtime_info.json")["status"] == "verified"
print("PASS_FROZEN_N41_SPARSE_QUADRATIC_V1")
