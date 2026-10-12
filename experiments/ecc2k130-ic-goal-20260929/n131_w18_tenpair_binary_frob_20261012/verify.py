"""Verify frozen ten-pair control, ordinary search, audit, and archives."""

import hashlib
import json
from pathlib import Path

from archive import verify as verify_archive
import ten


HERE = Path(__file__).resolve().parent
N41 = HERE.parent / "n41_w8_tenpair_density_control_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = ten.protocol()
control = json.loads((HERE / "control_result.json").read_text())
query = json.loads((HERE / "query_result.json").read_text())
audit = json.loads((HERE / "audit_result.json").read_text())
sage = json.loads((HERE / "sage_fixture_result.json").read_text())
n41 = json.loads((N41 / "audit_result.json").read_text())
assert protocol["status"] == "FROZEN_N131_TENPAIR_ORBIT_BEFORE_CONTROL_AND_QUERY"
assert protocol["source_pair_slots"] == 10
assert protocol["distinct_folded_columns_required"] == 20
assert n41["status"] == "PASS_INDEPENDENT_N41_PUBLIC_TENPAIR_RELATION"
assert sage["status"] == "PASS_INDEPENDENT_SAGE_TENPAIR_CONSTRUCTED_GROUP_REPLAY"
assert sage["distinct_folded_columns"] == 20
assert control["status"] == "PASS_FULL_N131_TENPAIR_ORBIT_CONSTRUCTED_WITNESS"
assert control["formula"]["xcnf_sha256"] == json.loads((HERE / "archive_receipt.json").read_text())["formulas"]["control"]["raw_sha256"]
assert query["status"] == audit["query_status"] == "BOUNDED_UNKNOWN"
assert query["status_lines"] == ["s INDETERMINATE"]
assert query["stop_reason"] is None and query["solver_exit_code"] == 0
assert query["worker_count"] == 1
assert query["target_dependent_attempt_ns"] < 600 * 10**9
assert query["target_dependent_attempt_ns"] == sum(query["phase_ns"].values())
assert query["peak_combined_rss_bytes_sampled"] < 4 * 1024**3
assert query["public_target"] == protocol["public_target"]
assert query["workload_id"] == protocol["workload_id"]
assert query["target_choice_count"] == query["distinct_target_reciprocals"] == 524
assert query["decoded_model_saved"] is False
assert audit["status"] == "PASS_N131_TENPAIR_BINARY_FROBENIUS_RECEIPT_AUDIT"
assert audit["ordinary_xcnf_rebuilt_byte_for_byte"] is True
assert audit["target_dependent_attempt_ns"] == query["target_dependent_attempt_ns"]
assert audit["sha256"]["auditor"] == sha(HERE / "audit.py")
assert audit["sha256"]["query"] == sha(HERE / "query_result.json")
assert audit["sha256"]["ordinary_formula"] == query["formula"]["xcnf_sha256"]
assert audit["sha256"]["stdout"] == sha(HERE / "solver.stdout.txt")
assert audit["sha256"]["stderr"] == sha(HERE / "solver.stderr.txt")
verify_archive(HERE)
print("PASS_N131_TENPAIR_ARCHIVED_RECEIPTS", query["status"],
      query["target_dependent_attempt_ns"], audit["actual_solver_restart_rows"])
