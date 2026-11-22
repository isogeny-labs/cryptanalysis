"""Read-only custody check for the exact N41 SAT source gate."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    old, amended, failed = read("protocol.json"), read("protocol_v2.json"), read("build_v1_status.json")
    built, query_p, query = read("build_result.json"), read("query_protocol.json"), read("query_result.json")
    assert old["builder_sha256"] == sha(HERE / "build_v1.py")
    assert failed["status"] == "PRODUCER_FAILURE_IMPORT"
    assert failed["stderr_sha256"] == sha(HERE / "build.stderr")
    assert amended["amends_protocol_sha256"] == sha(HERE / "protocol.json")
    assert amended["failed_attempt_status_sha256"] == sha(HERE / "build_v1_status.json")
    assert amended["builder_sha256"] == sha(HERE / "build.py")
    assert amended["circuit_sha256"] == sha(HERE / "circuit.py")
    assert amended["helper_source_sha256"] == sha(HERE / "independent_replay.py")
    assert all(sha(ROOT / name) == digest for name, digest in amended["source_sha256"].items())
    assert built["status"] == "PASS_PLANTED_ASSIGNMENT_ON_ORDINARY_PUBLIC_TARGET"
    assert built["protocol_sha256"] == sha(HERE / "protocol_v2.json")
    assert built["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert built["variables"] == 17283 and built["ordinary_clauses"] == 61345
    assert built["native_xor_rows"] == 1703
    assert not (HERE / "build_v2.stderr").read_text()
    assert query_p["status"] == "FROZEN_BEFORE_QUERY"
    assert query_p["runner_sha256"] == sha(HERE / "run_query.py")
    assert query_p["formula_sha256"] == sha(HERE / "ordinary.xcnf")
    assert query_p["solver_sha256"] == sha(query_p["solver_path"])
    assert query["status"] == "BOUNDED_UNKNOWN"
    assert query["query_protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr")
    assert query["terminal_lines"] == [] and query["stop_reason"] == "PARENT_WALL_CAP"
    assert query["sampled_peak_combined_rss_bytes"] < query_p["rss_cap_bytes"]
    assert read("launch_v1_status.json")["solver_launched"] is False
    print(json.dumps({"status": "PASS", "control": built["status"],
                      "ordinary_query": query["status"],
                      "formula_sha256": built["formula_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
