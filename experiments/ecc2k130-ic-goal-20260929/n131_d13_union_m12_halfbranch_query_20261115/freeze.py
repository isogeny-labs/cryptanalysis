"""Freeze one unpinned official-point query on the half-fixed m12 formula."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SOURCE = EXP / "n131_d13_union_m12_halfbranch_20261115"
SLS = EXP / "n131_d13_union_m12_sls600_20261115"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    formula = json.loads((SOURCE / "formula_receipt.json").read_text())
    classes = json.loads((SOURCE / "class_result.json").read_text())
    planted = json.loads((SOURCE / "planted_result.json").read_text())
    sage = json.loads((SOURCE / "sage_result.json").read_text())
    workload = json.loads((OFFICIAL / "workload.json").read_text())
    assert formula["status"] == "PASS_FORMULA_BUILD"
    assert classes["status"] == "PASS_EXACT_CLASS_COUNTS"
    assert planted["status"] == "PASS_FULL_ASSIGNMENT"
    assert sage["status"] == "PASS_ALL_TWELVE_LEAVES_AND_TARGET_FIBER"
    assert formula["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert workload["target_count"] == 1
    assert workload["workload_id"] == "3c1992b7c92f"
    p = {
        "kind": "n131_d13_halfbranch_m12_sls600_protocol_v1",
        "status": "FROZEN_BEFORE_QUERY",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "candidate_id": None,
        "workload_id": workload["workload_id"],
        "target_count": 1,
        "public_target": workload["targets"][0],
        "workers": 1,
        "fixed_original_positions": [0, 2, 4, 6, 8, 10],
        "formula_sha256": sha(HERE / "ordinary.xcnf"),
        "formula_source_receipt": str(SOURCE / "formula_receipt.json"),
        "formula_source_receipt_sha256": sha(SOURCE / "formula_receipt.json"),
        "class_result_sha256": sha(SOURCE / "class_result.json"),
        "planted_control_sha256": sha(SOURCE / "planted_result.json"),
        "independent_sage_replay_sha256": sha(SOURCE / "sage_result.json"),
        "prior_sls_protocol_sha256": sha(SLS / "query_protocol.json"),
        "prior_sls_result_sha256": sha(SLS / "query_result.json"),
        "runner_sha256": sha(HERE / "run_query.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "solver_path": str(SOLVER),
        "solver_sha256": sha(SOLVER),
        "solver_flags": ["--threads=1", "--maxtime=600", "--zero-exit-status",
                         "--verb=1", "--printsol=1", "--maxnummatrices=0",
                         "--sls=1", "--slseveryn=1"],
        "solver_wall_cap_s": 600,
        "parent_wall_cap_s": 615,
        "rss_cap_bytes": 4 * 1024**3,
        "claim_boundary": "One unpinned official-point query on the frozen half-fixed source; SAT requires independent source-bound group replay.",
    }
    path = HERE / "query_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
