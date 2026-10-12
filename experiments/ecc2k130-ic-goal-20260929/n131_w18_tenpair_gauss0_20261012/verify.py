"""Check frozen matrix-policy variant receipts against the parent formula."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / "protocol.json").read_text())
smoke = json.loads((HERE / "smoke_result.json").read_text())
control = json.loads((HERE / "control_result.json").read_text())
ordinary = json.loads((HERE / "ordinary_result.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
parent = json.loads((PARENT / "query_result.json").read_text())
assert protocol["status"] == "FROZEN_N131_TENPAIR_GAUSS0_SOLVER_VARIANT"
assert smoke["status"] == "PASS_GAUSS0_NATIVE_XOR_SAT_UNSAT_SMOKE"
assert smoke["solver_sha256"] == sha(Path("/opt/homebrew/bin/cryptominisat5").resolve())
for label in ("sat", "unsat"):
    row = smoke["tests"][label]
    assert row["input_sha256"] == sha(HERE / (label + ".xcnf"))
    assert row["stdout_sha256"] == sha(HERE / (label + ".stdout.txt"))
    assert row["expected"] in (HERE / (label + ".stdout.txt")).read_text().splitlines()
assert audit["status"] == "PASS_N131_TENPAIR_GAUSS0_RECEIPT_AUDIT"
assert audit["same_ordinary_formula"] and audit["same_public_point"]
assert audit["changed_flag"] == "--maxnummatrices=0"
assert audit["sha256"]["source"] == sha(HERE / "audit.py")
assert audit["sha256"]["protocol"] == sha(HERE / "protocol.json")
assert audit["sha256"]["parent_query"] == sha(PARENT / "query_result.json")
assert audit["sha256"]["control_receipt"] == sha(HERE / "control_result.json")
assert audit["sha256"]["ordinary_receipt"] == sha(HERE / "ordinary_result.json")
assert ordinary["formula_sha256"] == parent["formula"]["xcnf_sha256"]
assert ordinary["worker_count"] == control["worker_count"] == 1
assert ordinary["matrix_disable_diagnostics"] == control["matrix_disable_diagnostics"] == 0
assert ordinary["peak_combined_rss_bytes_sampled"] < 4 * 1024**3
assert ordinary["stop_reason"] == "TOTAL_WALL_CAP"
assert 600 * 10**9 <= ordinary["solver_wall_ns"] < 601 * 10**9
if ordinary["status"] == "SAT_PENDING_GROUP_REPLAY":
    replay = json.loads((HERE / "model_replay_sage.json").read_text())
    assert replay["status"] == "PASS_INDEPENDENT_N131_TENPAIR_GAUSS0_PUBLIC_RELATION"
elif ordinary["status"] == "BOUNDED_UNKNOWN":
    assert ordinary["status_lines"] in ([], ["s INDETERMINATE"])
else:
    assert ordinary["status"] == "UNSAT"
print("PASS_N131_TENPAIR_GAUSS0_VARIANT_RECEIPTS", ordinary["status"],
      ordinary["solver_wall_ns"], ordinary["actual_restart_rows"])
