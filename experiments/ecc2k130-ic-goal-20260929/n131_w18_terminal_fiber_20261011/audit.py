"""Audit the frozen terminal-fiber formula, capped query, and replay receipts."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n131_fixed_seed_ninepair_cubic_20261011"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def raw_archive_sha(path):
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    pool = json.loads((HERE / "pool.json").read_text())
    source = json.loads((HERE / "source_count.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    sage = json.loads((HERE / "sage_audit_result.json").read_text())
    archive = json.loads((HERE / "archive_receipt.json").read_text())
    serial = json.loads((BASE / "query_result.json").read_text())
    assert protocol["status"] == "FROZEN_TERMINAL_FIBER_BEFORE_QUERY"
    assert protocol["source_sha256"]["pool"] == sha(HERE / "pool.json")
    assert protocol["source_sha256"]["source_count"] == sha(HERE / "source_count.json")
    assert protocol["source_sha256"]["terminal"] == sha(HERE / "terminal.py")
    assert protocol["source_sha256"]["preparer"] == sha(HERE / "prepare.py")
    assert pool["status"] == "PASS_FROZEN_TARGET_INDEPENDENT_TERMINAL_POOL"
    assert len(pool["states"]) == source["selected_signed_states"] == 32
    assert source["status"] == "PASS_EXACT_SELECTED_TERMINAL_SOURCE_COUNT"
    assert source["uniform_raw_point_mean_upper_decimal"] == "1133.04389441"
    assert control["status"] == "PASS_EXACT_N131_TERMINAL_FIBER_CONTROL"
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_TERMINAL_FIBERS"
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert sage["sha256"]["query"] == sha(HERE / "query_result.json")
    assert sage["sha256"]["control"] == sha(HERE / "control_result.json")
    assert archive["status"] == "PASS_ARCHIVE_BYTE_REPLAY"
    for stem, receipt in (("control", control), ("ordinary", query)):
        name = stem + ".xcnf.gz"
        assert archive[stem]["gzip_sha256"] == sha(HERE / name)
        assert archive[stem]["raw_sha256"] == raw_archive_sha(HERE / name)
        assert archive[stem]["raw_sha256"] == receipt["formula"]["xcnf_sha256"]
        assert archive[stem]["raw_bytes"] == receipt["formula"]["xcnf_bytes"]
    phases = query["phase_ns"]
    assert set(phases) == {"target_residual_generation_ns", "formula_construction_ns",
                           "formula_serialization_ns", "solver_search_ns",
                           "terminal_parse_and_model_decode_ns"}
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    assert query["public_target"] == protocol["public_target"] == serial["public_target"]
    assert query["workload_id"] == protocol["workload_id"] == serial["workload_id"]
    assert query["status"] == "BOUNDED_UNKNOWN"
    assert query["stop_reason"] == "PARENT_TIMEOUT"
    assert not query["decoded_model_saved"] and not query["status_lines"]
    stdout = (HERE / "solver.stdout.txt").read_text(errors="replace")
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert not (HERE / "solver.stderr.txt").read_bytes()
    assert "c [find&init matx]" in stdout and "c rst " in stdout
    assert not any(line.startswith(("s SATISFIABLE", "s UNSATISFIABLE", "v "))
                   for line in stdout.splitlines())
    delta = {key: serial["formula"][key] - query["formula"][key]
             for key in ("variables", "and_gates", "clauses", "native_xor_rows")}
    assert all(value > 0 for value in delta.values())
    result = {"status": "PASS_TERMINAL_FIBER_RECEIPT_AUDIT",
              "candidate_id": None,
              "workload_id": protocol["workload_id"],
              "public_target": protocol["public_target"],
              "source_ceiling_decimal": source["uniform_raw_point_mean_upper_decimal"],
              "formula_reduction_vs_serial": delta,
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "phase_sum_ns": sum(phases.values()),
              "solver_status": query["status"],
              "solver_restart_rows": query["restart_rows"],
              "peak_combined_rss_bytes_sampled": query["peak_combined_rss_bytes_sampled"],
              "sha256": {"script": sha(Path(__file__)),
                         "protocol": sha(HERE / "protocol.json"),
                         "query": sha(HERE / "query_result.json"),
                         "control": sha(HERE / "control_result.json"),
                         "sage": sha(HERE / "sage_audit_result.json"),
                         "archive": sha(HERE / "archive_receipt.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], delta)


if __name__ == "__main__":
    main()
