"""Versioned 550-second continuation of the unchanged public formula."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = json.loads((D / "query_protocol.json").read_text())
pilot = json.loads((D / "query_result.json").read_text())
assert pilot["status"] == "BOUNDED_UNKNOWN"
assert sha(D / "public.xcnf") == old["sources"]["public.xcnf"]
record = dict(old)
record.update({
    "schema": 2,
    "solver_flags": ["--threads=1", "--maxtime=540", "--zero-exit-status",
                     "--verb=1", "--printsol=1"],
    "parent_wall_cap_s": 550,
    "runner_sha256": sha(D / "run_public_v2.py"),
    "supersedes_protocol_sha256": sha(D / "query_protocol.json"),
    "pilot_result_sha256": sha(D / "query_result.json"),
    "producer_v2_sha256": sha(Path(__file__)),
})
(D / "query_protocol_v2.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "query_protocol_v2.json"))
