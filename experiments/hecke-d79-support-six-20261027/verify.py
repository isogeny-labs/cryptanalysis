"""Check frozen inputs, eight producer cases, and Sage audit receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def check(path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)


plan = json.loads((HERE / "inputs.json").read_text())
for name in ("source_selection", "source_index", "relation_helpers", "incremental_module"):
    item = plan[name]
    check(ROOT / item["path"], item["sha256"])
for item in plan["cases"]:
    for name in ("journal", "summary"):
        artifact = item[name]
        check(ROOT / artifact["path"], artifact["sha256"])
pre = json.loads((HERE / "pre-run.json").read_text())
for name, field in (("inputs.json", "inputs_sha256"),
                    ("PROTOCOL.md", "protocol_sha256"),
                    ("run_sage.py", "runner_sha256"),
                    ("sage-runtime-info.txt", "sage_runtime_info_sha256")):
    check(HERE / name, pre[field])
post = json.loads((HERE / "post-run.json").read_text())
for name, field in (("pre-run.json", "pre_run_sha256"),
                    ("result.json", "result_sha256"),
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
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "COMPLETE" and len(result["cases"]) == 8
for item in result["cases"]:
    check(HERE / item["path"], item["sha256"])
assert json.loads((HERE / "audit.json").read_text())["status"] == "PASS"
print("PASS: eight complete six-source cases and independent Sage audit")
