"""Freeze the source, public formula, solver, and cap before SAT search."""
import hashlib
import json
from pathlib import Path


D = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


build = json.loads((D / "build_result.json").read_text())
assert build["status"] == "PASS_PUBLIC_S3_RATIONALITY_FORMULA_BUILD"
assert sha(D / "public.xcnf") == build["formula_sha256"]
solver = Path("/opt/homebrew/bin/cryptominisat5")
record = {
    "schema": 1,
    "candidate_id": None,
    "input_law": "one frozen public point, no source mask or pair state pinned in solver input",
    "sources": {name: sha(D / name) for name in (
        "protocol.json", "circuit.py", "build.py", "build_result.json",
        "public.xcnf", "sage_runtime_info.json")},
    "solver_path": str(solver),
    "solver_sha256": sha(solver),
    "solver_flags": ["--threads=1", "--maxtime=180", "--zero-exit-status",
                     "--verb=1", "--printsol=1"],
    "parent_wall_cap_s": 185,
    "rss_cap_bytes": 4 * 1024 ** 3,
    "worker_count": 1,
    "runner_sha256": sha(D / "run_public.py"),
    "producer_sha256": sha(Path(__file__)),
}
(D / "query_protocol.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
print(sha(D / "query_protocol.json"))
