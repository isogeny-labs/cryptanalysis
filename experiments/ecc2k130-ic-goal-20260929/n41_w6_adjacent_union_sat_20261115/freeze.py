"""Freeze exact union SAT source, target, and positive-control witness."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source_names = [
        "n41_w6_adjacent_union_screen_20261115/union_rows.json",
        "n41_w6_adjacent_union_screen_20261115/ordinary_receipt.json",
        "n41_w6_adjacent_union_screen_20261115/replay_result.json",
        "n41_sixpair_shared_target_20261017/circuit.py",
        "n131_w20_selector_elimination_v2_20261013/selector.py",
        "n131_w20_output_inverse_linear_20261012/linear.py",
        "n41_basis_aware_quartic_20261011/replay.py",
    ]
    receipt = json.loads((ROOT / source_names[1]).read_text())
    assert receipt["status"] == "VERIFIED_SIX_POINT_ROW"
    assert json.loads((ROOT / source_names[2]).read_text())["status"] == "PASS_CONTROL_AND_ORDINARY"
    record = {
        "kind": "n41_w6_adjacent_union_s3_formula_protocol_v1",
        "status": "FROZEN_BEFORE_BUILD",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": None,
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "workload_id": "0a9ad56165ec",
        "target_count": 1,
        "public_target": receipt["target"],
        "positive_control_ids": receipt["chosen_ids"],
        "source_sha256": {name: sha(ROOT / name) for name in source_names},
        "circuit_sha256": sha(HERE / "circuit.py"),
        "builder_sha256": sha(HERE / "build.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "wall_cap_seconds": 180,
        "rss_cap_bytes": 4 * 1024**3,
        "hypothesis": "A six-bit exact lookup for each 64-x union slot combined with the balanced five-link S3 circuit accepts the known ordinary N41 relation without pinning its selectors.",
        "decision_gate": "First require complete-assignment positive control; then freeze a one-worker ordinary SAT query and independently replay any model. Formula size alone is diagnostic.",
    }
    path = HERE / "protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
