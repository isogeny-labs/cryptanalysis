"""Replay the formula and classify CryptoMiniSat's capped terminal status."""

import gzip
import hashlib
import json
import tempfile
from pathlib import Path

import tenpair

HERE = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    frozen, fixture, control, plan, solver, sage, archive = (
        json.loads((HERE / name).read_text()) for name in (
            "protocol.json", "fixture.json", "control_result.json",
            "solver_protocol.json", "solver_result.json", "sage_audit_result.json",
            "archive_receipt.json"))
    assert frozen["status"] == "FROZEN_BEFORE_TENPAIR_CONTROL"
    assert frozen["source_sha256"] == {
        **{key: sha(path) for key, path in tenpair.sources().items()},
        "fixture": sha(HERE / "fixture.json")}
    assert plan["runner_sha256"] == sha(HERE / "run_preflight.py")
    assert plan["solver_sha256"] == sha(tenpair.base.SOLVER)
    assert plan["formula_sha256"] == control["formula"]["xcnf_sha256"]
    assert solver["solver_protocol_sha256"] == sha(HERE / "solver_protocol.json")
    assert sage["status"] == "PASS_SAGE_TENPAIR_SOURCE_SUM_AND_TARGET"
    assert sage["raw_target"] == fixture["raw_target"]
    assert sage["public_target"] == fixture["public_target"]
    assert control["assignment_check"] == {
        "clauses": control["formula"]["clauses"],
        "native_xor_rows": control["formula"]["native_xor_rows"]}
    with gzip.open(HERE / "control.xcnf.gz", "rb") as stream:
        digest = hashlib.sha256()
        byte_count = 0
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
            byte_count += len(block)
    assert digest.hexdigest() == archive["raw_sha256"] == plan["formula_sha256"]
    assert byte_count == archive["raw_bytes"] == control["formula"]["xcnf_bytes"]
    rows = tenpair.orbit9.orbit_rows(tenpair.orbit9.constructed_preimages(
        tuple(fixture["raw_target"])))
    _, root, bdd = tenpair.base.source_domain()
    circuit, _ = tenpair.build([row["standard_reciprocal"] for row in rows], root, bdd)
    with tempfile.TemporaryDirectory(dir=HERE) as directory:
        replay = Path(directory) / "replay.xcnf"
        circuit.write(replay)
        assert sha(replay) == plan["formula_sha256"]
    output = (HERE / "solver.stdout.txt").read_text(errors="replace")
    stderr = (HERE / "solver.stderr.txt").read_text(errors="replace")
    assert solver["stdout_sha256"] == sha(HERE / "solver.stdout.txt")
    assert solver["stderr_sha256"] == sha(HERE / "solver.stderr.txt")
    assert stderr == ""
    assert "CryptoMiniSat version 5.14.7" in output
    assert "--maxtime=110" in output
    assert "c -- xor clauses added: 319282" in output
    assert "[matrix] Too many rows in matrix: 245675 -> set usage to NO" in output
    assert solver["status_lines"] == ["s INDETERMINATE"]
    assert solver["status"] == "SOLVER_ERROR"  # Frozen runner misclassified this status.
    assert solver["exit_code"] == 0 and solver["stop_reason"] is None
    assert 110 <= solver["elapsed_seconds_exploratory"] <= 120
    assert solver["peak_combined_rss_bytes_sampled"] < plan["combined_rss_cap_bytes"]
    bracket_rows = sum(line.startswith("c [") for line in output.splitlines())
    actual_restart_rows = sum(line.startswith("c rst") for line in output.splitlines())
    assert solver["restart_rows"] == bracket_rows
    assert actual_restart_rows > 0
    result = {"status": "PASS_N131_TENPAIR_PREFLIGHT_AUDIT",
              "classified_solver_status": "CENSORED_TIME",
              "raw_runner_status": solver["status"],
              "reason": "CryptoMiniSat emitted s INDETERMINATE at frozen --maxtime=110",
              "solver_started": True, "formula_rebuilt_byte_for_byte": True,
              "gaussian_matrix_admitted": False,
              "rejected_matrix_rows": 245675,
              "rejected_matrix_columns": 365925,
              "actual_solver_restart_rows": actual_restart_rows,
              "raw_runner_bracket_rows": bracket_rows,
              "elapsed_seconds_exploratory": solver["elapsed_seconds_exploratory"],
              "sha256": {"auditor": sha(Path(__file__)),
                         "protocol": sha(HERE / "protocol.json"),
                         "control": sha(HERE / "control_result.json"),
                         "solver_protocol": sha(HERE / "solver_protocol.json"),
                         "solver_result": sha(HERE / "solver_result.json"),
                         "sage_audit": sha(HERE / "sage_audit_result.json"),
                         "archive_receipt": sha(HERE / "archive_receipt.json")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(result["status"], result["classified_solver_status"], flush=True)


if __name__ == "__main__":
    main()
