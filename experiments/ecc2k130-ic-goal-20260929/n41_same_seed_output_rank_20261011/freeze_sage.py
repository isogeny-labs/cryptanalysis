"""Freeze independent Sage rank replay and checked local runtime."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "sage_protocol.json").exists()
    rank = json.loads((HERE / "result.json").read_text())
    trace = json.loads((HERE / "trace_result.json").read_text())
    assert rank["status"] == "COMPLETE" and trace["status"] == \
           "PASS_UNIVERSAL_TRACE_HYPERPLANE"
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    p = {"status": "FROZEN_SAGE_SHARED_SEED_RANK_AUDIT",
         "candidate_id": None, "curve_id": rank["curve_id"],
         "workers": 1, "cap_seconds": 120, "rss_cap_bytes": 4 * 1024**3,
         "sha256": {"source": sha(HERE / "sage_audit.py"),
                    "rank": sha(HERE / "result.json"),
                    "trace": sha(HERE / "trace_result.json"),
                    "geometry": sha(GEOMETRY),
                    "runtime": sha(HERE / "sage_runtime_info.json")}}
    (HERE / "sage_protocol.json").write_text(json.dumps(p, indent=2, sort_keys=True)+"\n")
    print(p["status"])


if __name__ == "__main__":
    main()
