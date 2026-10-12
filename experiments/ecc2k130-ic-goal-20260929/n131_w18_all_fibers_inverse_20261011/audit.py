"""Audit source, independent fibers, online accounting, and XCNF archives."""

import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / "n131_w18_terminal_fiber_20261011"
GATE = ROOT / "n131_w18_inverse_trace_terminal_20261011"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def restored_sha(path):
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def archive():
    rows = {}
    for stem in ("control", "ordinary"):
        raw = HERE / (stem + ".xcnf")
        packed = HERE / (stem + ".xcnf.gz")
        with raw.open("rb") as source, packed.open("xb") as target:
            with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as stream:
                while chunk := source.read(1 << 20):
                    stream.write(chunk)
        rows[stem] = {"raw_sha256": sha(raw), "raw_bytes": raw.stat().st_size,
                      "gzip_sha256": sha(packed), "gzip_bytes": packed.stat().st_size}
    with (HERE / "archive_receipt.json").open("x") as stream:
        json.dump({"status": "PASS_ARCHIVE_BYTE_REPLAY", **rows},
                  stream, sort_keys=True, indent=2)
        stream.write("\n")
    print("PASS_ARCHIVE_BYTE_REPLAY", flush=True)


def audit():
    protocol = json.loads((HERE / "protocol.json").read_text())
    control = json.loads((HERE / "control_result.json").read_text())
    query = json.loads((HERE / "query_result.json").read_text())
    sage = json.loads((HERE / "sage_audit_result.json").read_text())
    archive_row = json.loads((HERE / "archive_receipt.json").read_text())
    prior = json.loads((PRIOR / "source_count.json").read_text())
    gate = json.loads((GATE / "gate_equivalence.json").read_text())
    assert protocol["status"] == "FROZEN_N131_ALL_FIBERS_BEFORE_CONTROL_AND_QUERY"
    assert protocol["source_sha256"]["runner"] == sha(HERE / "all_fibers.py")
    assert protocol["source_sha256"]["sage_audit"] == sha(HERE / "audit_sage.py")
    assert protocol["source_sha256"]["gate_equivalence"] == sha(GATE / "gate_equivalence.json")
    assert prior["status"] == "PASS_EXACT_SELECTED_TERMINAL_SOURCE_COUNT"
    assert gate["status"] == "PASS_EXACT_SOURCE_GATE_EQUIVALENCE"
    assert protocol["terminal_pool"] == json.loads((PRIOR / "pool.json").read_text())["states"]
    assert len(protocol["terminal_pool"]) == 32 and protocol["residual_choices"] == 128
    assert control["status"] == "PASS_N131_ALL_FIBERS_CONSTRUCTED_CONTROL"
    assert control["selected_choice_index"] == 0
    assert control["assignment_check"]["clauses"] == control["formula"]["clauses"]
    assert control["assignment_check"]["native_xor_rows"] == control["formula"]["native_xor_rows"]
    assert sage["status"] == "PASS_INDEPENDENT_SAGE_ALL_128_RESIDUALS"
    assert sage["sha256"]["control"] == sha(HERE / "control_result.json")
    assert sage["sha256"]["query"] == sha(HERE / "query_result.json")
    assert control["protocol_sha256"] == query["protocol_sha256"] == sha(HERE / "protocol.json")
    assert query["public_target"] == protocol["public_target"]
    assert query["workload_id"] == protocol["workload_id"]
    assert len(query["raw_preimages"]) == 4 and len(query["residuals"]) == 128
    assert len({row["standard_reciprocal"] for row in query["residuals"]}) == 128
    assert archive_row["status"] == "PASS_ARCHIVE_BYTE_REPLAY"
    for stem, row in (("control", control), ("ordinary", query)):
        packed = HERE / (stem + ".xcnf.gz")
        assert archive_row[stem]["gzip_sha256"] == sha(packed)
        assert archive_row[stem]["raw_sha256"] == restored_sha(packed)
        assert archive_row[stem]["raw_sha256"] == row["formula"]["xcnf_sha256"]
        assert archive_row[stem]["raw_bytes"] == row["formula"]["xcnf_bytes"]
    phases = query["phase_ns"]
    assert set(phases) == {"public_raw_preimages_ns", "target_residual_generation_ns",
                           "formula_construction_ns", "formula_serialization_ns",
                           "solver_search_ns", "terminal_parse_and_decode_ns"}
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["target_dependent_attempt_ns"] <= (protocol["online_total_cap_seconds"] + 2) * 10**9
    assert query["worker_count"] == protocol["worker_count"] == 1
    assert query["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    stdout, stderr = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    assert query["stdout_sha256"] == sha(stdout) and query["stderr_sha256"] == sha(stderr)
    assert not stderr.read_bytes()
    output = stdout.read_text(errors="replace")
    assert "c [find&init matx]" in output and re.search(r"^c rst\s", output, re.M)
    if query["status"] == "BOUNDED_UNKNOWN":
        assert not query["decoded_model_saved"]
        assert not any(line.startswith(("s SATISFIABLE", "s UNSATISFIABLE", "v "))
                       for line in output.splitlines())
        status = "PASS_ALL_FIBERS_CENSORED_RECEIPTS"
    elif query["status"] == "SAT_PENDING_GROUP_REPLAY":
        assert query["decoded_model_saved"] and (HERE / "decoded_model.json").is_file()
        status = "PASS_ALL_FIBERS_SAT_RECEIPTS_PENDING_GROUP_REPLAY"
    else:
        raise AssertionError("unexpected solver status")
    result = {"status": status, "candidate_id": None,
              "curve_id": protocol["curve_id"], "workload_id": protocol["workload_id"],
              "public_target": protocol["public_target"],
              "residual_choices": 128, "solver_status": query["status"],
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "phase_sum_ns": sum(phases.values()),
              "solver_cpu_seconds_sampled": query["solver_cpu_seconds_sampled"],
              "source_sha256": {"script": sha(Path(__file__)),
                                "protocol": sha(HERE / "protocol.json"),
                                "control": sha(HERE / "control_result.json"),
                                "query": sha(HERE / "query_result.json"),
                                "sage": sha(HERE / "sage_audit_result.json"),
                                "archive": sha(HERE / "archive_receipt.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(status, flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("archive", "audit")
    {"archive": archive, "audit": audit}[sys.argv[1]]()
