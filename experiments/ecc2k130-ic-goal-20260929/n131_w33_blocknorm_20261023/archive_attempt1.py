"""Preserve the completed N41 child and failed first parent monitor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEST = HERE / "attempt1"
assert not DEST.exists()
paths = [HERE / "n41.stdout", HERE / "n41.stderr", HERE / "n41_result.json"]
assert all(path.exists() for path in paths)
result = json.loads(paths[2].read_text())
assert result["status"] == "PASS_N41_BLOCK_NORM_GATE"
assert result["data"]["rows"][0]["direct_hits"] == [[253, 63]]
assert result["data"]["rows"][1]["direct_hits"] == []
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = {"status": "PARENT_MONITOR_FAILURE_CHILD_COMPLETED",
           "monitor_failure": "psutil.children(recursive=True) called macOS pids sysctl and raised PermissionError",
           "child_result_status": result["status"],
           "sources": {path.name: sha(path) for path in paths},
           "protocol_sha256": sha(HERE / "protocol_n41.json"),
           "supervisor_sha256": sha(HERE / "supervise.py")}
DEST.mkdir()
for path in paths:
    path.rename(DEST / path.name)
(DEST / "attempt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True))
