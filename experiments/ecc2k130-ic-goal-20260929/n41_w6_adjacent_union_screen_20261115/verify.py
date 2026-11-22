"""Read-only custody checks for the six-slot union recovery."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    screen_p, screen = read("protocol.json"), read("result.json")
    manifest, join_p = read("join_input_manifest.json"), read("join_protocol.json")
    control, ordinary = read("control_receipt.json"), read("ordinary_receipt.json")
    replay_p, replay = read("replay_protocol.json"), read("replay_result.json")
    recovery_p, recovery = read("recovery_protocol.json"), read("recovery_result.json")
    assert screen_p["status"] == "FROZEN_BEFORE_SCREEN"
    assert screen_p["source_sha256"] == sha(HERE / "screen.py")
    for name, digest in screen_p["input_sha256"].items():
        assert sha(screen_p["inputs"][name]) == digest
    assert screen["status"] == "PASS_EXACT_GROUP_CENSUS"
    assert screen["protocol_sha256"] == sha(HERE / "protocol.json")
    assert screen["global_union_points"] == 768 and screen["global_overlap"] == 0
    assert all(row["union_points"] == 128 and row["overlap"] == 0 for row in screen["slot_stats"])
    assert screen["union_rows_sha256"] == sha(HERE / "union_rows.json")
    assert manifest["status"] == "FROZEN_INPUTS"
    assert manifest["source_sha256"] == sha(HERE / "prepare_join.py")
    assert manifest["ordinary_input_sha256"] == sha(HERE / "ordinary_input.txt")
    assert manifest["control_input_sha256"] == sha(HERE / "control_input.txt")
    assert join_p["status"] == "FROZEN_BEFORE_CONTROL_AND_ORDINARY"
    assert join_p["join_source_sha256"] == sha(HERE / "join.cpp")
    assert join_p["join_binary_sha256"] == sha(HERE / "join")
    assert join_p["input_manifest_sha256"] == sha(HERE / "join_input_manifest.json")
    for arm, receipt in (("control", control), ("ordinary", ordinary)):
        assert receipt["status"] == "VERIFIED_SIX_POINT_ROW"
        assert receipt["left_rows"] == 128**3 and receipt["exact_hits"] >= 1
        assert len(receipt["chosen_ids"]) == 6
        assert receipt["peak_rss_bytes"] < join_p["rss_cap_bytes"]
        assert receipt["setup_ns"] < join_p["setup_wall_cap_seconds"] * 10**9
        assert receipt["online_ns"] < join_p["online_wall_cap_seconds"] * 10**9
        assert not (HERE / f"{arm}.stderr").read_text()
    assert control["chosen_ids"] == manifest["control_row_ids"]
    assert ordinary["target"] == manifest["ordinary_target"]
    assert replay_p["status"] == "FROZEN_BEFORE_REPLAY"
    assert replay_p["source_sha256"] == sha(HERE / "replay.py")
    assert all(sha(HERE / name) == digest for name, digest in replay_p["input_sha256"].items())
    assert replay["status"] == "PASS_CONTROL_AND_ORDINARY"
    assert replay["source_rows_orbit_checked"] == 384
    assert not (HERE / "replay.stderr").read_text()
    assert recovery_p["status"] == "FROZEN_BEFORE_RECOVERY"
    assert recovery_p["source_sha256"] == sha(HERE / "recover.py")
    assert all(sha(recovery_p["inputs"][name]) == digest
               for name, digest in recovery_p["input_sha256"].items())
    assert recovery["status"] == "PASS_VERIFIED_PUBLIC_SCALAR"
    assert recovery["scalar_group_replay"] == "PASS"
    assert recovery["scalar"] == 12172994855
    assert recovery["diagnostic_combined_online_ns"] == ordinary["online_ns"] + recovery["recovery_and_replay_ns"]
    assert not (HERE / "recovery.stderr").read_text()
    assert not (HERE / "screen.stderr.txt").read_text()
    assert not (HERE / "prepare.stderr").read_text()
    assert not (HERE / "compile.stderr").read_text()
    print(json.dumps({"status": "PASS", "B": 768, "K": 26,
                      "scalar": recovery["scalar"],
                      "diagnostic_online_ns": recovery["diagnostic_combined_online_ns"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
