"""Preserve the completed N131 child and failed second parent monitor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE / "attempt2"
assert not DEST.exists()
paths = [HERE / "n131.stdout", HERE / "n131.stderr", HERE / "n131_result.json"]
assert all(path.exists() for path in paths)
result = json.loads(paths[2].read_text())
assert result["status"] == "PASS_N131_BLOCK_NORM_GATE"
assert [(r["gate"]["gcd_degree"], r["individual_retained_codes"])
        for r in result["data"]["rows"]] == [(1, [3]), (0, [])]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {"status": "PARENT_MONITOR_FAILURE_CHILD_COMPLETED",
           "monitor_failure": "parent saw a macOS process permission failure; killpg then raised PermissionError after the worker wrote its terminal result",
           "child_result_status": result["status"],
           "sources": {path.name: sha(path) for path in paths},
           "protocol_sha256": sha(HERE / "protocol_n131.json"),
           "supervisor_sha256": sha(HERE / "supervise_v2.py")}
DEST.mkdir()
for path in paths:
    path.rename(DEST / path.name)
(DEST / "attempt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True))
