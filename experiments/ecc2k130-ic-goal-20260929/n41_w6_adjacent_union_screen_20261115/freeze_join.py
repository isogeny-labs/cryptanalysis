"""Freeze native join controls and public query before execution."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HELPER = HERE.parent / "n41_w6_s8_distinct_window_geometry" / "native_join" / "frozen_source" / "three_pair_s7_native.cpp"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = json.loads((HERE / "join_input_manifest.json").read_text())
    assert manifest["status"] == "FROZEN_INPUTS"
    assert manifest["ordinary_input_sha256"] == sha(HERE / "ordinary_input.txt")
    assert manifest["control_input_sha256"] == sha(HERE / "control_input.txt")
    assert not (HERE / "compile.stderr").read_text()
    record = {
        "kind": "n41_w6_adjacent_union_3plus3_join_protocol_v1",
        "status": "FROZEN_BEFORE_CONTROL_AND_ORDINARY",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": None,
        "curve_id": manifest["curve_id"],
        "workload_id": manifest["workload_id"],
        "target_count": 1,
        "ordinary_target": manifest["ordinary_target"],
        "control_target": manifest["control_target"],
        "control_row_ids": manifest["control_row_ids"],
        "rotations": manifest["rotations"],
        "input_manifest_sha256": sha(HERE / "join_input_manifest.json"),
        "ordinary_input_sha256": sha(HERE / "ordinary_input.txt"),
        "control_input_sha256": sha(HERE / "control_input.txt"),
        "screen_result_sha256": sha(HERE / "result.json"),
        "join_source_sha256": sha(HERE / "join.cpp"),
        "included_helper_sha256": sha(HELPER),
        "join_binary_sha256": sha(HERE / "join"),
        "compiler": "c++ -std=c++17 -O3 -Wall -Wextra join.cpp -o join",
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "workers": 1,
        "setup_wall_cap_seconds": 120,
        "online_wall_cap_seconds": 120,
        "rss_cap_bytes": 4 * 1024**3,
        "duplicate_folded_column_policy": "allow and combine coefficients during later row reconstruction",
        "claim_boundary": "Source-bound exact group-sum method control only; factor logs, full IC recovery, and matched rho are separate stages.",
    }
    path = HERE / "join_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
