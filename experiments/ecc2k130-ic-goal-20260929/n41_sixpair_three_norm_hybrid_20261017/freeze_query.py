"""Freeze the exact formula, solver binary, and public-query resource envelope."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build = json.loads((D / "build_result.json").read_text())
    assert build["status"] == "PASS_UNPINNED_THREE_NORM_HYBRID_BUILD"
    assert build["formula_sha256"] == sha(D / "public.xcnf")
    solver = Path("/opt/homebrew/bin/cryptominisat5")
    assert solver.exists()
    sources = ("build.py", "build_result.json", "circuit.py",
               "protocol.json", "public.xcnf", "sage_runtime_info.json",
               "build_v1_failure.json")
    protocol = {"schema": 1, "candidate_id": None,
                "input_law": "one N41 public raw point with six free pair codes",
                "solver_path": str(solver), "solver_sha256": sha(solver),
                "solver_flags": ["--threads=1", "--maxtime=590",
                                 "--zero-exit-status", "--verb=1", "--printsol=1"],
                "runner_sha256": sha(D / "query.py"),
                "sources": {name: sha(D / name) for name in sources},
                "worker_count": 1, "parent_wall_cap_s": 600,
                "rss_cap_bytes": 4 * (1 << 30)}
    (D / "query_protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"query_protocol_sha256": sha(D / "query_protocol.json"),
                      "formula_sha256": build["formula_sha256"]}))


if __name__ == "__main__":
    main()
