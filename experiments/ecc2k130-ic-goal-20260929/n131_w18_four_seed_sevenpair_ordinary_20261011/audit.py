"""Archive and audit the frozen seven-pair ordinary-query receipt."""

import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = ROOT / "n131_w18_four_seed_sevenpair_circuit_20261011"
AFFINE = ROOT / "n131_w18_four_seed_sevenpair_affine_control_20261011"
COUNT = ROOT / "n131_w18_four_seed_sevenpair_source_20261011"
PRIOR = ROOT / "n131_w18_all_fibers_inverse_20261011"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def uncompressed(path):
    digest = hashlib.sha256()
    length = 0
    with gzip.open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
            length += len(chunk)
    return digest.hexdigest(), length


def archive():
    raw, packed = HERE / "ordinary.xcnf", HERE / "ordinary.xcnf.gz"
    query = json.loads((HERE / "query_result.json").read_text())
    assert sha(raw) == query["formula"]["xcnf_sha256"]
    with raw.open("rb") as source, packed.open("xb") as target:
        with gzip.GzipFile(filename="", mode="wb", fileobj=target,
                           compresslevel=1, mtime=0) as stream:
            for chunk in iter(lambda: source.read(1 << 20), b""):
                stream.write(chunk)
    restored, length = uncompressed(packed)
    assert restored == sha(raw)
    assert length == raw.stat().st_size == query["formula"]["xcnf_bytes"]
    data = {"status": "PASS_ORDINARY_FORMULA_BYTE_REPLAY",
            "raw_sha256": restored, "raw_bytes": length,
            "gzip_sha256": sha(packed), "gzip_bytes": packed.stat().st_size,
            "query_result_sha256": sha(HERE / "query_result.json")}
    with (HERE / "archive_receipt.json").open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(data["status"], flush=True)


def audit():
    protocol = json.loads((HERE / "protocol.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    archive_row = json.loads((HERE / "archive_receipt.json").read_text())
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    sage = json.loads((HERE / "sage_audit_result.json").read_text())
    count = json.loads((COUNT / "result.json").read_text())
    affine = json.loads((AFFINE / "sage_audit_result.json").read_text())
    previous = json.loads((PRIOR / "query_result.json").read_text())
    assert protocol["status"] == "FROZEN_N131_SEVENPAIR_AFFINE_ORDINARY_QUERY"
    assert protocol["source_sha256"] == {
        "runner": sha(HERE / "query.py"),
        "core_circuit": sha(CORE / "circuit.py"),
        "source_count": sha(COUNT / "result.json"),
        "affine_control": sha(AFFINE / "control_result.json"),
        "affine_sage_audit": sha(AFFINE / "sage_audit_result.json"),
        "prior_target": sha(PRIOR / "query_result.json"),
        "support": sha(ROOT / "n131_w16_w18_sixpair_width_gate_20261010" /
                       "support_w18.tsv"),
        "terminal_pool": sha(ROOT / "n131_w18_terminal_fiber_20261011" /
                             "pool.json"),
        "solver": sha(Path(protocol["solver_path"])),
    }
    assert runtime["status"] == "verified"
    assert sage["sha256"]["query"] == sha(HERE / "query_result.json")
    assert sage["sha256"]["runtime"] == sha(HERE / "sage_runtime_info.json")
    assert affine["status"] == "PASS_INDEPENDENT_SAGE_ALL_FOUR_AFFINE_SEEDS"
    assert count["status"] == "PASS_EXACT_FOUR_SEED_SEVENPAIR_MATCHING_COUNT"
    assert protocol["signed_source_mean_upper_exact"] == count["uniform_public_point_mean_upper_exact"]
    assert query["public_target"] == protocol["public_target"] == previous["public_target"]
    assert query["curve_id"] == protocol["curve_id"]
    assert query["workload_id"] == protocol["workload_id"]
    assert query["raw_preimages"] == previous["raw_preimages"]
    assert len(query["raw_preimages"]) == 4 and len(query["residuals"]) == 128
    assert len({row["standard_reciprocal"] for row in query["residuals"]}) == 128
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["sage_runtime_sha256"] == sha(HERE / "sage_runtime_info.json")
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["solver_flags"] == protocol["solver_flags"]
    assert query["formula"]["xcnf_sha256"] == archive_row["raw_sha256"]
    assert query["formula"]["xcnf_bytes"] == archive_row["raw_bytes"]
    assert archive_row["status"] == "PASS_ORDINARY_FORMULA_BYTE_REPLAY"
    assert archive_row["gzip_sha256"] == sha(HERE / "ordinary.xcnf.gz")
    assert (archive_row["raw_sha256"], archive_row["raw_bytes"]) == uncompressed(
        HERE / "ordinary.xcnf.gz")
    assert archive_row["query_result_sha256"] == sha(HERE / "query_result.json")
    phases = query["phase_ns"]
    assert set(phases) == {"public_raw_preimages_ns", "target_residual_generation_ns",
                           "formula_construction_ns", "formula_serialization_ns",
                           "solver_search_ns", "terminal_parse_and_decode_ns"}
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["solver_cpu_seconds_rusage"] >= 0
    assert query["solver_cpu_seconds_sampled"] >= 0
    assert query["peak_combined_rss_bytes_sampled"] > 0
    assert query["status_lines"] == [line for line in
                                      (HERE / "solver.stdout.txt").read_text(errors="replace").splitlines()
                                      if line.startswith("s ")]
    assert query["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert query["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    output = (HERE / "solver.stdout.txt").read_text(errors="replace")
    assert query["restart_rows"] == sum(line.startswith("c rst")
                                        for line in output.splitlines())
    if query["status"] == "BOUNDED_UNKNOWN":
        assert query["stop_reason"] is not None
        assert not query["decoded_model_saved"]
        assert "s SATISFIABLE" not in query["status_lines"]
        assert "s UNSATISFIABLE" not in query["status_lines"]
        assert sage["status"] == "PASS_INDEPENDENT_SAGE_ALL_128_PUBLIC_RESIDUALS"
        result_status = "PASS_CENSORED_N131_SEVENPAIR_QUERY_RECEIPT"
    elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert query["decoded_model_saved"]
        assert "s SATISFIABLE" in query["status_lines"]
        model = json.loads((HERE / "decoded_model.json").read_text())
        assert model["formula_sha256"] == query["formula"]["xcnf_sha256"]
        assert sage["status"] == "PASS_INDEPENDENT_SAGE_ORDINARY_SEVENPAIR_RELATION"
        result_status = "PASS_VERIFIED_ORDINARY_SEVENPAIR_RELATION_RECEIPT"
    elif query["status"] == "UNSAT":
        assert "s UNSATISFIABLE" in query["status_lines"]
        assert sage["status"] == "PASS_INDEPENDENT_SAGE_ALL_128_PUBLIC_RESIDUALS"
        result_status = "PASS_UNSAT_FORMULA_RECEIPT"
    elif query["status"] == "MODEL_DECODE_FAILURE":
        assert query["decode_error"] and "s SATISFIABLE" in query["status_lines"]
        assert sage["status"] == "PASS_INDEPENDENT_SAGE_ALL_128_PUBLIC_RESIDUALS"
        result_status = "PASS_MODEL_DECODE_FAILURE_RECEIPT"
    else:
        raise AssertionError("unexpected solver status")
    receipt = {"status": result_status, "candidate_id": None,
               "curve_id": protocol["curve_id"],
               "workload_id": protocol["workload_id"],
               "public_target": protocol["public_target"],
               "query_status": query["status"],
               "stop_reason": query["stop_reason"],
               "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
               "phase_sum_ns": sum(phases.values()),
               "solver_cpu_seconds_rusage": query["solver_cpu_seconds_rusage"],
               "solver_restart_rows": query["restart_rows"],
               "source_sha256": {"audit": sha(Path(__file__)),
                                 "protocol": sha(HERE / "protocol.json"),
                                 "query": sha(HERE / "query_result.json"),
                                 "archive": sha(HERE / "archive_receipt.json"),
                                 "runtime": sha(HERE / "sage_runtime_info.json"),
                                 "sage": sha(HERE / "sage_audit_result.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result_status, flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"archive", "audit"}:
        raise SystemExit("usage: audit.py archive|audit")
    {"archive": archive, "audit": audit}[sys.argv[1]]()
