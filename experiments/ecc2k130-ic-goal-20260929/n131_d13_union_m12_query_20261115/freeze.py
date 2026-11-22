"""Freeze the official-target twelve-leaf union query before solver launch."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SCREEN = EXP / "n131_d13_union_arity_20261115"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    screen = json.loads((SCREEN / "result.json").read_text())
    planted = json.loads((SCREEN / "planted_result.json").read_text())
    sage = json.loads((SCREEN / "sage_result.json").read_text())
    workload = json.loads((OFFICIAL / "workload.json").read_text())
    assert screen["status"] == "PASS_EXACT_FORMULA_AND_CLASS_COUNTS"
    assert screen["rows"]["12"]["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert planted["status"] == "PASS_FULL_ASSIGNMENT"
    assert sage["status"] == "PASS_ALL_TWELVE_LEAVES_AND_TARGET_FIBER"
    assert workload["target_count"] == 1
    assert workload["workload_id"] == "3c1992b7c92f"
    p = {
        "kind": "n131_d13_union_m12_ordinary_query_protocol_v1",
        "status": "FROZEN_BEFORE_QUERY",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "candidate_id": None,
        "workload_id": workload["workload_id"],
        "target_count": 1,
        "public_target": workload["targets"][0],
        "workers": 1,
        "formula_sha256": sha(HERE / "ordinary.xcnf"),
        "formula_source_receipt": str(SCREEN / "result.json"),
        "formula_source_receipt_sha256": sha(SCREEN / "result.json"),
        "planted_control_sha256": sha(SCREEN / "planted_result.json"),
        "independent_sage_replay_sha256": sha(SCREEN / "sage_result.json"),
        "runner_sha256": sha(HERE / "run_query.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "solver_path": str(SOLVER),
        "solver_sha256": sha(SOLVER),
        "solver_flags": ["--threads=1", "--maxtime=600", "--zero-exit-status",
                         "--verb=1", "--printsol=1"],
        "solver_wall_cap_s": 600,
        "parent_wall_cap_s": 615,
        "rss_cap_bytes": 4 * 1024**3,
        "claim_boundary": "One unpinned ordinary SAT query on the official point. A SAT model requires independent source-bound replay before relation use.",
    }
    path = HERE / "query_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
