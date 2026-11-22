"""Freeze one official-target, one-worker union ten-leaf SAT query."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SOURCE = EXP / "n131_d13_union_m10_formula_20261115"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    formula = json.loads((SOURCE / "formula_receipt.json").read_text())
    workload = json.loads((OFFICIAL / "workload.json").read_text())
    assert formula["status"] == "PASS_FORMULA_BUILD"
    assert formula["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert workload["target_count"] == 1
    assert workload["workload_id"] == "3c1992b7c92f"
    p = {"kind": "n131_d13_union_m10_ordinary_query_protocol_v1",
         "status": "FROZEN_BEFORE_QUERY",
         "frozen_utc": datetime.now(timezone.utc).isoformat(),
         "curve_id": "EC1N131Ckb1heb5f1998f20b",
         "candidate_id": None,
         "workload_id": workload["workload_id"],
         "target_count": 1,
         "public_target": workload["targets"][0],
         "workers": 1,
         "formula_sha256": sha(HERE / "ordinary.xcnf"),
         "formula_source_receipt": str(SOURCE / "formula_receipt.json"),
         "formula_source_receipt_sha256": sha(SOURCE / "formula_receipt.json"),
         "runner_sha256": sha(HERE / "run_query.py"),
         "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
         "solver_path": str(SOLVER),
         "solver_sha256": sha(SOLVER),
         "solver_flags": ["--threads=1", "--maxtime=600", "--zero-exit-status",
                          "--verb=1", "--printsol=1"],
         "solver_wall_cap_s": 600,
         "parent_wall_cap_s": 615,
         "rss_cap_bytes": 4*1024**3,
         "claim_boundary": "One unpinned ordinary SAT query on the official point. A SAT model requires independent source-bound replay before relation use."}
    path = HERE / "query_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
