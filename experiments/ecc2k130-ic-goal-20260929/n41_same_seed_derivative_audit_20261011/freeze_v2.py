"""Freeze the JSON-key-corrected independent Sage audit."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n41_same_seed_derivative_collapse_20261011"
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "protocol_v2.json").exists()
    assert json.loads((HERE / "failure_v1.json").read_text())["status"] == \
           "AUDITOR_SERIALIZATION_KEY_MISMATCH"
    p = {"status": "FROZEN_SAGE_N41_SHARED_SEED_AUDIT_V2",
         "candidate_id": None, "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
         "workers": 1, "cap_seconds": 120, "rss_cap_bytes": 4 * 1024**3,
         "prior_failure_sha256": sha(HERE / "failure_v1.json"),
         "sha256": {"audit": sha(HERE / "sage_audit_v2.py"),
                    "geometry": sha(GEOMETRY),
                    "producer": sha(PRIOR / "result_v2.json"),
                    "runtime": sha(HERE / "sage_runtime_info.json")}}
    (HERE / "protocol_v2.json").write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(p["status"])


if __name__ == "__main__":
    main()
