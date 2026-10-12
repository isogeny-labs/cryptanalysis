"""Independent receipt and log audit for the matched matrix-policy gate."""

import gzip
import hashlib
import json
import re
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent
SOURCE = run.SOURCE


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    frozen = run.load(HERE / "protocol.json")
    prepared = run.load(HERE / "formula_prepare.json")
    source_control = run.load(SOURCE / "control_result.json")
    source_sage = run.load(SOURCE / "sage_fixture_result.json")
    assert frozen["status"] == "FROZEN_BEFORE_MATCHED_SOLVER_ARMS"
    assert frozen["source_sha256"] == run.source_hashes()
    assert frozen["arm_order"] == ["default", "nogauss"]
    assert frozen["solver_flags"]["nogauss"] == frozen["solver_flags"]["default"] + [
        "--maxnummatrices=0"]
    assert source_control["status"] == "PASS_FULL_N131_TENPAIR_ORBIT_CONSTRUCTED_WITNESS"
    assert source_sage["status"] == "PASS_INDEPENDENT_SAGE_TENPAIR_CONSTRUCTED_GROUP_REPLAY"
    assert source_sage["distinct_folded_columns"] == 20
    assert prepared["status"] == "PASS_FORMULA_BYTE_REPLAY"
    assert prepared["protocol_sha256"] == sha(HERE / "protocol.json")
    assert prepared["sha256"] == source_control["formula"]["xcnf_sha256"]
    assert sha(HERE / "control.xcnf") == frozen["formula_sha256"]
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as stream:
        digest = hashlib.sha256()
        size = 0
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
            size += len(block)
    assert digest.hexdigest() == frozen["formula_sha256"]
    assert size == frozen["formula_bytes"] == (HERE / "control.xcnf").stat().st_size
    arms = {}
    for arm in frozen["arm_order"]:
        result = run.load(HERE / f"{arm}_result.json")
        stdout = HERE / f"{arm}.stdout.txt"
        stderr = HERE / f"{arm}.stderr.txt"
        output = stdout.read_text(errors="replace")
        lines = output.splitlines()
        assert result["arm"] == arm
        assert result["status"] == "CENSORED_TIME"
        assert result["solver_status_lines"] == []
        assert result["solver_started"] and "CryptoMiniSat version 5.14.7" in output
        assert result["exit_code"] == -9 and result["stop_reason"] == "WALL_CAP"
        assert 120 <= result["elapsed_seconds_exploratory"] < 121
        assert 0 < result["child_cpu_seconds"] < result["elapsed_seconds_exploratory"]
        assert result["sampled_peak_combined_rss_bytes"] < frozen["rss_cap_bytes"]
        assert result["stdout_sha256"] == sha(stdout)
        assert result["stderr_sha256"] == sha(stderr)
        assert stderr.stat().st_size == 0 == result["stderr_bytes"]
        assert result["formula_sha256"] == frozen["formula_sha256"]
        assert result["protocol_sha256"] == sha(HERE / "protocol.json")
        assert result["solver_flags"] == frozen["solver_flags"][arm]
        assert all(flag in output.splitlines()[10] for flag in result["solver_flags"])
        assert "c -- clauses added: 528850" in output
        assert "c -- xor clauses added: 81064" in output
        assert result["actual_restart_rows"] == sum(line.startswith("c rst") for line in lines)
        assert result["gauss_disable_diagnostics"] == output.count(
            "TODO disable matrix, performing badly")
        matrix_counts = [int(match.group(1)) for line in lines
                         if (match := re.search(r"\[matrix\] Using (\d+) matrices", line))]
        assert len(matrix_counts) == 6
        assert matrix_counts == ([5] * 6 if arm == "default" else [0] * 6)
        arms[arm] = {"status": result["status"],
                     "actual_restart_rows": result["actual_restart_rows"],
                     "matrix_counts_at_six_initializations": matrix_counts,
                     "matrix_disable_diagnostics": result["gauss_disable_diagnostics"],
                     "child_cpu_seconds": result["child_cpu_seconds"],
                     "elapsed_seconds_exploratory": result["elapsed_seconds_exploratory"],
                     "sampled_peak_combined_rss_bytes": result[
                         "sampled_peak_combined_rss_bytes"]}
    record = {"status": "PASS_MATCHED_TENPAIR_MATRIX_POLICY_AUDIT",
              "candidate_id": None,
              "source_formula_sha256": frozen["formula_sha256"],
              "source_constructed_assignment": source_control["status"],
              "source_sage_replay": source_sage["status"],
              "arms": arms,
              "sha256": {"auditor": sha(Path(__file__)),
                         "protocol": sha(HERE / "protocol.json"),
                         "prepared": sha(HERE / "formula_prepare.json"),
                         "default_receipt": sha(HERE / "default_result.json"),
                         "nogauss_receipt": sha(HERE / "nogauss_result.json"),
                         "default_stdout": sha(HERE / "default.stdout.txt"),
                         "nogauss_stdout": sha(HERE / "nogauss.stdout.txt")}}
    run.save("audit_result.json", record)
    print(record["status"], flush=True)


if __name__ == "__main__":
    main()
