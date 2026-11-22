"""Freeze the N41 union source screen before computation."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n41_w6_s8_distinct_window_geometry"
GEOMETRY = SOURCE / "geometry.json"
CANDIDATE = SOURCE / "candidate_manifest.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    geometry = json.loads(GEOMETRY.read_text())
    record = {
        "kind": "n41_w6_adjacent_union_source_screen_v1",
        "status": "FROZEN_BEFORE_SCREEN",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": None,
        "curve_id": geometry["curve_id"],
        "workload_id": geometry["workload_id"],
        "rotations": [0, 5, 10, 15, 20, 25],
        "inputs": {"geometry": str(GEOMETRY), "candidate": str(CANDIDATE)},
        "input_sha256": {"geometry": sha(GEOMETRY), "candidate": sha(CANDIDATE)},
        "source_sha256": sha(HERE / "screen.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "wall_cap_seconds": 120,
        "rss_cap_bytes": 4 * 1024**3,
        "hypothesis": "The exact N41 W6 subgroup point source and its 1+tau image are disjoint in six fixed Frobenius slots, giving 128 usable points per slot with unchanged independent log columns.",
        "claim_boundary": "Exact source census and conditional uniform-subgroup tuple mean only; the join has not yet run.",
    }
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
