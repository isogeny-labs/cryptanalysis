"""Freeze the follow-up trace-hyperplane identification."""

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
    assert not (HERE / "trace_protocol.json").exists()
    rank = json.loads((HERE / "result.json").read_text())
    assert rank["status"] == "COMPLETE"
    p = {"status": "FROZEN_N41_SHARED_SEED_TRACE_IDENTIFICATION",
         "candidate_id": None, "curve_id": rank["curve_id"],
         "workers": 1, "cap_seconds": 120,
         "rss_cap_bytes": 4 * 1024**3,
         "sha256": {"source": sha(HERE / "trace.py"),
                    "rank": sha(HERE / "result.json"),
                    "geometry": sha(GEOMETRY),
                    "arithmetic": sha(ARITH)}}
    (HERE / "trace_protocol.json").write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(p["status"])


if __name__ == "__main__":
    main()
