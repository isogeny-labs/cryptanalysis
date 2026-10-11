"""Freeze cached-pair N41 census after the capped first producer."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITH = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "protocol_v2.json").exists()
    assert json.loads((HERE / "failure_v1.json").read_text())["status"] == \
           "CAP_EXCEEDED_AT_ROTATION_BOUNDARY"
    original = json.loads((HERE / "protocol.json").read_text())
    p = {"status": "FROZEN_N41_SAME_SEED_DERIVATIVE_CENSUS_V2",
         "candidate_id": None, "curve_id": original["curve_id"],
         "input_law": original["input_law"],
         "optimization": "cache four signed point sums per source edge; exactly the same quartet and sign sets",
         "rotations": [0], "workers": 1,
         "cap_seconds": 120, "rss_cap_bytes": 4 * 1024**3,
         "prior_protocol_sha256": sha(HERE / "protocol.json"),
         "prior_failure_sha256": sha(HERE / "failure_v1.json"),
         "sha256": {"run": sha(HERE / "run_v2.py"),
                    "geometry": sha(GEOMETRY), "arithmetic": sha(ARITH)}}
    (HERE / "protocol_v2.json").write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": p["status"], "rotations": p["rotations"]}))


if __name__ == "__main__":
    main()
