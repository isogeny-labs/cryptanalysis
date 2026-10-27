"""Check frozen input, producer, and audit receipt hashes without Sage."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check(path, expected):
    assert hashlib.sha256((HERE / path).read_bytes()).hexdigest() == expected, path


post = json.loads((HERE / "post-selection.json").read_text())
for path, field in (("selection.json", "selection_sha256"),
                    ("inputs.json", "inputs_sha256"),
                    ("select_sage.py", "selector_sha256")):
    check(path, post[field])
pre = json.loads((HERE / "pre-run.json").read_text())
for path, field in (("post-selection.json", "post_selection_sha256"),
                    ("run_sage.py", "runner_sha256"),
                    ("PROTOCOL.md", "protocol_sha256")):
    check(path, pre[field])
run = json.loads((HERE / "post-run.json").read_text())
for path, field in (("pre-run.json", "pre_run_sha256"),
                    ("result.json", "result_sha256"),
                    ("run-stdout.jsonl", "stdout_sha256"),
                    ("run-stderr.txt", "stderr_sha256")):
    check(path, run[field])
audit = json.loads((HERE / "post-audit.json").read_text())
for path, field in (("audit_sage.py", "audit_source_sha256"),
                    ("audit.json", "audit_sha256"),
                    ("audit-stdout.jsonl", "audit_stdout_sha256"),
                    ("audit-stderr.txt", "audit_stderr_sha256"),
                    ("RESULT.md", "result_report_sha256")):
    check(path, audit[field])
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "COMPLETE"
for item in result["cases"]:
    check(item["path"], item["sha256"])
assert json.loads((HERE / "audit.json").read_text())["status"] == "PASS"
print("PASS: frozen selection, eight producer cases, and Sage audit receipts")
