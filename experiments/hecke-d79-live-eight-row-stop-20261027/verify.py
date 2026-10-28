"""Check frozen row-level support-eight selection, producer, and audit receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def check(path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)


plan = json.loads((HERE / "inputs.json").read_text())
for item in (plan["control_gate_result"], plan["incremental_module"],
             plan["pair_index_reference"], plan["frozen_five_index"],
             plan["preflight_source_selection"], plan["preflight_six_result"],
             plan["preflight_seven_result"], plan["preflight_support_eight_result"],
             plan["preflight_support_eight_journal"],
             plan["preflight_support_eight_selection"], plan["preflight_rank_stop_index"],
             *plan["frozen"].values()):
    check(ROOT / item["path"], item["sha256"])
selection = json.loads((HERE / "post-selection.json").read_text())
for name, field in (("selection.json", "selection_sha256"),
                    ("inputs.json", "inputs_sha256"),
                    ("select_sage.py", "selector_sha256")):
    check(HERE / name, selection[field])
pre = json.loads((HERE / "pre-run.json").read_text())
for name, field in (("post-selection.json", "post_selection_sha256"),
                    ("preflight.json", "preflight_sha256"),
                    ("preflight_sage.py", "preflight_source_sha256"),
                    ("wide_index.py", "wide_index_sha256"),
                    ("rank_stop_index.py", "rank_stop_index_sha256"),
                    ("run_sage.py", "runner_sha256"),
                    ("PROTOCOL.md", "protocol_sha256"),
                    ("sage-runtime-info.txt", "sage_runtime_info_sha256")):
    check(HERE / name, pre[field])
post = json.loads((HERE / "post-run.json").read_text())
for name, field in (("pre-run.json", "pre_run_sha256"),
                    ("index.json", "index_sha256"),
                    ("run-stdout.jsonl", "stdout_sha256"),
                    ("run-stderr.txt", "stderr_sha256")):
    check(HERE / name, post[field])
audit = json.loads((HERE / "post-audit.json").read_text())
for name, field in (("audit_sage.py", "audit_source_sha256"),
                    ("audit.json", "audit_sha256"),
                    ("audit-stdout.jsonl", "audit_stdout_sha256"),
                    ("audit-stderr.txt", "audit_stderr_sha256"),
                    ("RESULT.md", "report_sha256")):
    check(HERE / name, audit[field])
index = json.loads((HERE / "index.json").read_text())
assert index["status"] == "COMPLETE" and len(index["cases"]) == 9
for item in index["cases"]:
    check(HERE / item["journal"], item["journal_sha256"])
    check(HERE / item["summary"], item["summary_sha256"])
assert json.loads((HERE / "audit.json").read_text())["status"] == "PASS"
print("PASS: nine live row-level support-eight cases, exact preflight, and independent Sage audit")
