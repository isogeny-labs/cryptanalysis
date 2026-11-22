"""Freeze the full-length Gaussian arm on the official N131 point."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
SOURCE = EXP / "n131_d13_union_m10_formula_20261115"
DEFAULT = EXP / "n131_d13_union_m10_query_20261115"
PROBE = EXP / "n131_d13_union_m10_gauss_20261115"
CONTROL = EXP / "n131_d13_union_m10_default135_20261115"
OFFICIAL = EXP / "n131_w2_m15_official_single_target_4g_r3_20261004"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    formula = json.loads((SOURCE / "formula_receipt.json").read_text())
    workload = json.loads((OFFICIAL / "workload.json").read_text())
    probe = json.loads((PROBE / "query_result.json").read_text())
    control = json.loads((CONTROL / "query_result.json").read_text())
    default = json.loads((DEFAULT / "query_result.json").read_text())
    assert formula["status"] == "PASS_FORMULA_BUILD"
    assert all(r["status"] == "BOUNDED_UNKNOWN"
               for r in (probe, control, default))
    assert formula["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert workload["target_count"] == 1
    assert workload["workload_id"] == "3c1992b7c92f"
    p = {"kind": "n131_d13_union_m10_gauss_full_protocol_v1",
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
         "default_full_protocol_sha256": sha(DEFAULT / "query_protocol.json"),
         "default_full_result_sha256": sha(DEFAULT / "query_result.json"),
         "gauss_probe_protocol_sha256": sha(PROBE / "query_protocol.json"),
         "gauss_probe_result_sha256": sha(PROBE / "query_result.json"),
         "default_short_protocol_sha256": sha(CONTROL / "query_protocol.json"),
         "default_short_result_sha256": sha(CONTROL / "query_result.json"),
         "runner_sha256": sha(HERE / "run_query.py"),
         "sage_runtime_info_sha256": sha(HERE / "sage_runtime_info.json"),
         "solver_path": str(SOLVER),
         "solver_sha256": sha(SOLVER),
         "solver_flags": ["--threads=1", "--maxtime=600", "--zero-exit-status",
                          "--verb=1", "--printsol=1",
                          "--maxmatrixrows=16000", "--maxmatrixcols=20000",
                          "--maxnummatrices=10"],
         "solver_wall_cap_s": 600,
         "parent_wall_cap_s": 615,
         "rss_cap_bytes": 4*1024**3,
         "claim_boundary": "Full-length Gaussian arm on the same public point/formula; SAT requires independent source-bound group replay before relation use."}
    path = HERE / "query_protocol.json"
    assert not path.exists()
    path.write_text(json.dumps(p, indent=2, sort_keys=True) + "\n")
    print(path)


if __name__ == "__main__":
    main()
