"""Bind the same exact ten-pair formula and new CryptoMiniSat flags."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
assert not (HERE / "protocol.json").exists()
smoke = json.loads((HERE / "smoke_result.json").read_text())
assert smoke["status"] == "PASS_GAUSS0_NATIVE_XOR_SAT_UNSAT_SMOKE"
parent_protocol = json.loads((PARENT / "protocol.json").read_text())
parent_archive = json.loads((PARENT / "archive_receipt.json").read_text())
assert parent_protocol["status"] == "FROZEN_N131_TENPAIR_ORBIT_BEFORE_CONTROL_AND_QUERY"
assert parent_archive["status"] == "PASS_FROZEN_XCNF_GZIP_BYTE_REPLAY"
paths = {
    "runner": HERE / "run.py",
    "smoke_source": HERE / "smoke.py",
    "smoke_result": HERE / "smoke_result.json",
    "parent_protocol": PARENT / "protocol.json",
    "parent_control": PARENT / "control_result.json",
    "parent_query": PARENT / "query_result.json",
    "parent_archive": PARENT / "archive_receipt.json",
    "control_formula_gzip": PARENT / "control.xcnf.gz",
    "ordinary_formula_gzip": PARENT / "ordinary.xcnf.gz",
    "solver": SOLVER.resolve(),
}
protocol = {
    "status": "FROZEN_N131_TENPAIR_GAUSS0_SOLVER_VARIANT",
    "candidate_id": None,
    "curve_id": parent_protocol["curve_id"],
    "workload_id": parent_protocol["workload_id"],
    "public_target": parent_protocol["public_target"],
    "source_formula_sha256": {
        name: parent_archive["formulas"][name]["raw_sha256"]
        for name in ("control", "ordinary")},
    "changed_solver_flag": "--maxnummatrices=0",
    "solver_flags_common": ["--threads=1", "--zero-exit-status", "--verb=1", "--printsol=1"],
    "control_solver_seconds": 60,
    "ordinary_solver_seconds": 540,
    "ordinary_total_wall_cap_seconds": 600,
    "combined_rss_cap_bytes": 4 * 1024**3,
    "worker_count": 1,
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
               for name, path in paths.items()},
}
(HERE / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
print(protocol["status"])
