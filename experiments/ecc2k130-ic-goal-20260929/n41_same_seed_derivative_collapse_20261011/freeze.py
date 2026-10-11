"""Freeze the exact N41 shared-seed four-point census before execution."""

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
    assert not (HERE / "protocol.json").exists()
    geom = json.loads(GEOMETRY.read_text())["n41"]
    assert geom["curve_id"] == "EC1N41Ckb1h7d5e80d3c4d0"
    record = {"status": "FROZEN_N41_SAME_SEED_DERIVATIVE_CENSUS",
              "candidate_id": None, "curve_id": geom["curve_id"],
              "input_law": "all supported W6 masks, sign-zero and all sixteen signs, same nonzero XOR seed, four distinct folded columns",
              "rotations": [0, 10], "workers": 1,
              "cap_seconds": 120, "rss_cap_bytes": 4 * 1024**3,
              "sha256": {"run": sha(HERE / "run.py"),
                         "geometry": sha(GEOMETRY), "arithmetic": sha(ARITH)}}
    (HERE / "protocol.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": record["status"], "rotations": record["rotations"]}))


if __name__ == "__main__":
    main()
