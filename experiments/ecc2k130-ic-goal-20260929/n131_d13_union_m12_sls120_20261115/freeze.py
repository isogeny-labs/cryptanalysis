"""Freeze an ordinary-point local-search activation probe."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SCREEN = EXP / "n131_d13_union_arity_20261115"
DEFAULT = EXP / "n131_d13_union_m12_query_20261115"
GAUSS = EXP / "n131_d13_union_m12_gauss600_20261115"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    screen = json.loads((SCREEN / "result.json").read_text())
    workload = json.loads((OFFICIAL / "workload.json").read_text())
    assert screen["status"] == "PASS_EXACT_FORMULA_AND_CLASS_COUNTS"
    assert screen["rows"]["12"]["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert workload["target_count"] == 1
    assert workload["workload_id"] == "3c1992b7c92f"
    p = {
        "kind": "n131_d13_union_m12_sls_probe_protocol_v1",
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
        "default_protocol_sha256": sha(DEFAULT / "query_protocol.json"),
        "default_result_sha256": sha(DEFAULT / "query_result.json"),
        "gauss_protocol_sha256": sha(GAUSS / "query_protocol.json"),
        "gauss_result_sha256": sha(GAUSS / "query_result.json"),
        "runner_sha256": sha(HERE / "run_query.py"),
        "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
        "solver_path": str(SOLVER),
        "solver_sha256": sha(SOLVER),
        "solver_flags": ["--threads=1", "--maxtime=120", "--zero-exit-status",
                         "--verb=1", "--printsol=1", "--maxnummatrices=0",
                         "--sls=1", "--slseveryn=1"],
        "solver_wall_cap_s": 120,
        "parent_wall_cap_s": 135,
        "rss_cap_bytes": 4 * 1024**3,
        "question": "Does suppressing Gaussian matrices keep CCNR local search active on this exact ordinary query?",
        "promotion_gate": "The log shows at least one local-search execution, no parser failure, and resource bounds; a SAT line additionally requires independent group replay.",
    }
    path = HERE / "query_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
