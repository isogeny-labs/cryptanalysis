"""Audit the fixed-terminal N131 source, online cap, and immutable receipts."""

import gzip
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n131_w18_terminal_fiber_20261011"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restored_sha(path):
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    archive = json.loads((HERE / "archive_receipt.json").read_text())
    prior_pool = json.loads((PRIOR / "pool.json").read_text())
    prior_source = json.loads((PRIOR / "source_count.json").read_text())
    prior_query = json.loads((PRIOR / "query_result.json").read_text())
    prior_sage = json.loads((PRIOR / "sage_audit_result.json").read_text())
    assert protocol["status"] == "FROZEN_N131_FIXED_TERMINAL_BEFORE_CONTROL_AND_QUERY"
    assert protocol["source_sha256"]["runner"] == sha(HERE / "fixed.py")
    assert protocol["source_sha256"]["prior_pool"] == sha(PRIOR / "pool.json")
    assert protocol["source_sha256"]["prior_sage_fibers"] == sha(PRIOR / "sage_audit_result.json")
    assert prior_sage["status"] == "PASS_INDEPENDENT_SAGE_TERMINAL_FIBERS"
    assert prior_pool["control_choice_index"] == protocol["terminal_state_index"] == 0
    assert protocol["terminal_state"] == prior_pool["states"][0]
    selected_edge = protocol["terminal_state"]["folded_columns"]
    rows = [row for row in prior_source["conditional_edge_rows"]
            if row["folded_columns"] == selected_edge]
    assert len(rows) == 1
    source_count = rows[0]["eight_pair_matchings"] * math.factorial(8) * 4**8
    assert str(source_count) == protocol["source_count_distinct_column_ordered_tuples"]
    assert protocol["public_target"] == prior_query["public_target"] == query["public_target"]
    assert protocol["workload_id"] == prior_query["workload_id"] == query["workload_id"]
    assert control["status"] == "PASS_FIXED_TERMINAL_N131_CONSTRUCTED_CONTROL"
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert control["residual"] == prior_sage_residual("control", prior_sage, prior_pool)
    assert query["residual"] == prior_sage_residual("ordinary", prior_sage, prior_pool)
    assert archive["status"] == "PASS_ARCHIVE_BYTE_REPLAY"
    for stem, row in (("control", control), ("ordinary", query)):
        path = HERE / (stem + ".xcnf.gz")
        assert archive[stem]["gzip_sha256"] == sha(path)
        assert archive[stem]["raw_sha256"] == restored_sha(path)
        assert archive[stem]["raw_sha256"] == row["formula"]["xcnf_sha256"]
        assert archive[stem]["raw_bytes"] == row["formula"]["xcnf_bytes"]
    phases = query["phase_ns"]
    assert set(phases) == {"target_residual_generation_ns", "formula_construction_ns",
                           "formula_serialization_ns", "solver_search_ns",
                           "terminal_parse_and_decode_ns"}
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["target_dependent_attempt_ns"] <= (protocol["online_total_cap_seconds"] + 2) * 10**9
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert not (HERE / "solver.stderr.txt").read_bytes()
    output = (HERE / "solver.stdout.txt").read_text(errors="replace")
    assert "c [find&init matx]" in output and "c rst " in output
    if query["status"] == "BOUNDED_UNKNOWN":
        assert not query["decoded_model_saved"]
        assert not any(line.startswith(("s SATISFIABLE", "s UNSATISFIABLE", "v "))
                       for line in output.splitlines())
        status = "PASS_FIXED_TERMINAL_CENSORED_RECEIPTS"
    elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert query["decoded_model_saved"] and (HERE / "decoded_model.json").is_file()
        status = "PASS_FIXED_TERMINAL_SAT_RECEIPTS_PENDING_GROUP_REPLAY"
    else:
        raise AssertionError("unexpected solver status")
    reduction = {key: prior_query["formula"][key] - query["formula"][key]
                 for key in ("variables", "and_gates", "clauses", "native_xor_rows")}
    assert all(value > 0 for value in reduction.values())
    result = {"status": status, "candidate_id": None,
              "curve_id": protocol["curve_id"], "workload_id": protocol["workload_id"],
              "public_target": protocol["public_target"],
              "source_ceiling_decimal": protocol["uniform_raw_point_mean_upper_decimal"],
              "formula_reduction_vs_terminal32": reduction,
              "solver_status": query["status"],
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "phase_sum_ns": sum(phases.values()),
              "solver_cpu_seconds_sampled": query["solver_cpu_seconds_sampled"],
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol.json"),
                                "control": sha(HERE / "control_result.json"),
                                "query": sha(HERE / "query_result.json"),
                                "archive": sha(HERE / "archive_receipt.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], reduction)


def prior_sage_residual(kind, sage, pool):
    assert sage["sha256"]["pool"] == sha(PRIOR / "pool.json")
    path = PRIOR / ("control_result.json" if kind == "control" else "query_result.json")
    assert sage["sha256"]["query" if kind == "ordinary" else "control"] == sha(path)
    receipt = json.loads(path.read_text())
    return receipt["residuals"][pool["control_choice_index"]]


if __name__ == "__main__":
    main()
