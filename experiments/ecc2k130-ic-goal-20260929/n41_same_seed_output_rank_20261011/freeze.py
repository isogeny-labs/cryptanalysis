"""Freeze exact shared-seed output rank computation before its run."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "n41_same_seed_derivative_collapse_20261011/result_v2.json"
GEOMETRY = ROOT / "n41_two_free_pair_occupancy_20261009/geometry_snapshot.json"
ARITH = ROOT / "n41_two_free_pair_occupancy_20261009/arithmetic_snapshot.py"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "protocol.json").exists()
    previous = json.loads(SOURCE.read_text())
    assert previous["status"] == "COMPLETE"
    p = {"status": "FROZEN_N41_SHARED_SEED_OUTPUT_RANK",
         "candidate_id": None, "curve_id": previous["curve_id"],
         "input_law": "all supported W6 four-mask quartets with shared nonzero XOR seed, four distinct folded columns, and exact signed x outputs",
         "rotation": 0, "workers": 1, "cap_seconds": 120,
         "rss_cap_bytes": 4 * 1024**3,
         "sha256": {"source": sha(HERE / "rank.py"),
                    "prior": sha(SOURCE), "geometry": sha(GEOMETRY),
                    "arithmetic": sha(ARITH)}}
    (HERE / "protocol.json").write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(p["status"])


if __name__ == "__main__":
    main()
