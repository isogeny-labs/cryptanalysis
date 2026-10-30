"""Verify frozen support-eight inputs, two runs, and independent audit receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path, digest):
    assert sha(path) == digest, str(path)


for directory in (HERE, HERE / "full"):
    pre = json.loads((directory / "pre-run.json").read_text())
    for path, digest in pre["inputs"].items():
        check(ROOT / path, digest)
    for name, field in (("PROTOCOL.md", "protocol_sha256"),
                        ("run_sage.py", "runner_sha256"),
                        ("sage-runtime-info.txt", "runtime_info_sha256")):
        check(directory / name, pre[field])
post = json.loads((HERE / "post-audit.json").read_text())
for name, field in (("result.json", "initial_result_sha256"),
                    ("run-stdout.jsonl", "initial_stdout_sha256"),
                    ("run-stderr.txt", "initial_stderr_sha256"),
                    ("full/result.json", "full_result_sha256"),
                    ("full/run-stdout.jsonl", "full_stdout_sha256"),
                    ("full/run-stderr.txt", "full_stderr_sha256"),
                    ("audit_sage.py", "audit_source_sha256"),
                    ("audit.json", "audit_sha256"),
                    ("audit-stdout.jsonl", "audit_stdout_sha256"),
                    ("audit-stderr.txt", "audit_stderr_sha256"),
                    ("RESULT.md", "report_sha256")):
    check(HERE / name, post[field])
initial = json.loads((HERE / "result.json").read_text())
full = json.loads((HERE / "full/result.json").read_text())
assert initial["status"] == "CENSORED_PROBE_CAP" and initial["rank_after"] == 38
assert full["status"] == "RANK_39_FOUND" and full["rank_after"] == 39
assert full["anchored_log_replay"] == "PASS" and len(full["anchored_logs"]) == 40
assert json.loads((HERE / "audit.json").read_text())["status"] == "PASS"
print("PASS: sealed capped and full runs, rank-39 row, and independent Sage audit")
