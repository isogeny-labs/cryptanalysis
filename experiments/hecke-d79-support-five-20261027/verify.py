"""Check immutable input, producer, and audit receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def check(path, expected):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, str(path)


plan = json.loads((HERE / "inputs.json").read_text())
for key in ("source_selection", "source_result", "relation_helpers",
            "incremental_module", "pair_index_reference"):
    item = plan[key]
    check(ROOT / item["path"], item["sha256"])
for item in plan["cases"]:
    check(ROOT / item["path"], item["sha256"])
pre = json.loads((HERE / "pre-run.json").read_text())
for name, key in (("inputs.json", "inputs_sha256"), ("PROTOCOL.md", "protocol_sha256"),
                  ("run_sage.py", "runner_sha256"),
                  ("sage-runtime-info.txt", "sage_runtime_info_sha256")):
    check(HERE / name, pre[key])
post = json.loads((HERE / "post-run.json").read_text())
for name, key in (("pre-run.json", "pre_run_sha256"), ("result.json", "result_sha256"),
                  ("run-stdout.jsonl", "stdout_sha256"),
                  ("run-stderr.txt", "stderr_sha256")):
    check(HERE / name, post[key])
audit = json.loads((HERE / "post-audit.json").read_text())
for name, key in (("audit_sage.py", "audit_source_sha256"), ("audit.json", "audit_sha256"),
                  ("audit-stdout.jsonl", "audit_stdout_sha256"),
                  ("audit-stderr.txt", "audit_stderr_sha256"),
                  ("RESULT.md", "result_report_sha256")):
    check(HERE / name, audit[key])
result = json.loads((HERE / "result.json").read_text())
assert result["status"] == "COMPLETE" and len(result["cases"]) == 8
for item in result["cases"]:
    check(HERE / item["path"], item["sha256"])
assert json.loads((HERE / "audit.json").read_text())["status"] == "PASS"
print("PASS: eight complete five-source cases and independent Sage audit")
