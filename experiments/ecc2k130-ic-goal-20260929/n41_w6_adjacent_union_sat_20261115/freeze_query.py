"""Freeze the ordinary SAT solver, exact formula, and local resource envelope."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    built = json.loads((HERE / "build_result.json").read_text())
    assert built["status"] == "PASS_PLANTED_ASSIGNMENT_ON_ORDINARY_PUBLIC_TARGET"
    assert built["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert SOLVER.is_file()
    record = {
        "kind": "n41_w6_adjacent_union_s3_unpinned_query_protocol_v1",
        "status": "FROZEN_BEFORE_QUERY",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": None,
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "workload_id": "0a9ad56165ec",
        "target_count": 1,
        "public_target": built["target"],
        "formula_sha256": sha(HERE / "ordinary.xcnf"),
        "build_result_sha256": sha(HERE / "build_result.json"),
        "builder_protocol_sha256": sha(HERE / "protocol_v2.json"),
        "runner_sha256": sha(HERE / "run_query.py"),
        "solver_path": str(SOLVER),
        "solver_sha256": sha(SOLVER),
        "solver_flags": ["--threads=1", "--maxtime=120", "--zero-exit-status",
                          "--verb=1", "--printsol=1"],
        "workers": 1,
        "solver_wall_cap_s": 120,
        "parent_wall_cap_s": 135,
        "rss_cap_bytes": 4 * 1024**3,
        "claim_boundary": "One unpinned ordinary SAT attempt; positive complete assignment verifies encoding but is not a natural-yield estimate. SAT requires independent source-bound model replay.",
    }
    path = HERE / "query_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
