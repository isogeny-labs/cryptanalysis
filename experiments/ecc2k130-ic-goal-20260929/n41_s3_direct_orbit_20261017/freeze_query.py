"""Bind the unpinned public SAT query before launching its one worker."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build = json.loads((D / "build_result.json").read_text())
    assert build["status"] == "PASS_DIRECT_LEAF_ORBIT_FORMULA_BUILD"
    assert sha(D / "public.xcnf") == build["formula_sha256"]
    assert SOLVER.is_file()
    sources = ("build.py", "build_result.json", "circuit.py", "protocol.json",
               "public.xcnf", "sage_runtime_info.json")
    protocol = {
        "schema": 1,
        "candidate_id": None,
        "input_law": "one public subgroup point with 41 raw Frobenius target choices and six free source slots",
        "worker_count": 1,
        "parent_wall_cap_s": 600,
        "rss_cap_bytes": 4 * (1 << 30),
        "solver_path": str(SOLVER),
        "solver_flags": ["--threads=1", "--maxtime=590", "--zero-exit-status",
                         "--verb=1", "--printsol=1"],
        "solver_sha256": sha(SOLVER),
        "runner_sha256": sha(D / "run_public_v2.py"),
        "sources": {name: sha(D / name) for name in sources},
    }
    (D / "query_protocol_v2.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(json.dumps({key: protocol[key] for key in (
        "worker_count", "parent_wall_cap_s", "solver_sha256", "sources")}, sort_keys=True))


if __name__ == "__main__":
    main()
