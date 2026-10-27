"""Verify frozen selection, producer, and audit hashes without Sage."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def check(path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)


plan = json.loads((HERE / "inputs.json").read_text())
for item in (plan["control_gate_result"], plan["incremental_module"],
             plan["pair_index_reference"], *plan["frozen"].values()):
    check(ROOT / item["path"], item["sha256"])
selection = json.loads((HERE / "post-selection.json").read_text())
for name, key in (("selection.json", "selection_sha256"),
                  ("inputs.json", "inputs_sha256"),
                  ("select_sage.py", "selector_sha256")):
    check(HERE / name, selection[key])
pre = json.loads((HERE / "pre-run.json").read_text())
for name, key in (("post-selection.json", "post_selection_sha256"),
                  ("preflight.json", "preflight_sha256"),
                  ("preflight_sage.py", "preflight_source_sha256"),
                  ("live_index.py", "live_index_sha256"),
                  ("run_sage.py", "runner_sha256"),
                  ("PROTOCOL.md", "protocol_sha256"),
                  ("sage-runtime-info.txt", "sage_runtime_info_sha256")):
    check(HERE / name, pre[key])
post = json.loads((HERE / "post-run.json").read_text())
for name, key in (("pre-run.json", "pre_run_sha256"), ("index.json", "index_sha256"),
                  ("run-stdout.jsonl", "stdout_sha256"),
                  ("run-stderr.txt", "stderr_sha256")):
    check(HERE / name, post[key])
audit = json.loads((HERE / "post-audit.json").read_text())
for name, key in (("audit_sage.py", "audit_source_sha256"),
                  ("audit.json", "audit_sha256"),
                  ("audit-stdout.jsonl", "audit_stdout_sha256"),
                  ("audit-stderr.txt", "audit_stderr_sha256"),
                  ("RESULT.md", "report_sha256")):
    check(HERE / name, audit[key])
index = json.loads((HERE / "index.json").read_text())
assert index["status"] == "COMPLETE" and len(index["cases"]) == 9
for case in index["cases"]:
    check(HERE / case["journal"], case["journal_sha256"])
    check(HERE / case["summary"], case["summary_sha256"])
assert json.loads((HERE / "audit.json").read_text())["status"] == "PASS"
print("PASS: nine live collector cases, preflight, and independent Sage audit")
