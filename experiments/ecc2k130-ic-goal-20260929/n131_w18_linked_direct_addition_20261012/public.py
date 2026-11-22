"""Run the direct addition gate on the frozen N131 public point after controls."""

import hashlib
import json
from pathlib import Path

import direct

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "n131_w18_linked_signature_prefix_20261012"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol = json.loads((HERE / "public_protocol.json").read_text())
assert protocol["status"] == "FROZEN_BEFORE_DIRECT_ADDITION_PUBLIC_QUERY"
paths = {
    "runner": HERE / "public.py",
    "gate": HERE / "direct.py",
    "candidate_protocol": HERE / "protocol.json",
    "stage_result": HERE / "stage_result.json",
    "control_protocol": HERE / "control_protocol.json",
    "control_result": HERE / "control_result.json",
    "direct_control_result": HERE / "direct_control_result.json",
    "prior_all_root_audit": PREVIOUS / "fast_audit_result.json",
    "prior_all_root_audit_protocol": PREVIOUS / "fast_audit_protocol.json",
    "prior_root_table": PREVIOUS / "rows.tsv.gz",
}
for key, path in paths.items():
    assert protocol["sha256"][key] == sha(path), key
assert protocol["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
assert protocol["workload_id"] == "cc09e7eb202a"
assert protocol["worker_count"] == 1
assert protocol["total_target_dependent_cap_seconds"] == 600
assert protocol["combined_rss_cap_bytes"] == 4 * 1024**3
control = json.loads((HERE / "direct_control_result.json").read_text())
assert control["status"] == "PASS_FULL_N131_DIRECT_LINKED_ADDITION_CONSTRUCTED_ASSIGNMENT"
audit = json.loads((PREVIOUS / "fast_audit_result.json").read_text())
assert audit["status"] == "PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_ADDITION_FORMULAS"
assert audit["pair_output_roots"] == 66382
assert audit["audit_protocol_sha256"] == sha(PREVIOUS / "fast_audit_protocol.json")
assert direct.prior.orbit9.TOTAL_CAP_NS == 600 * 10**9
assert direct.prior.orbit9.RSS_CAP == 4 * 1024**3
direct.prior.query()
