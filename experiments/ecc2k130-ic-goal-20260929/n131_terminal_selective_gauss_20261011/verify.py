"""Bind the paired solver transcripts to the frozen N131 terminal XCNF."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n131_w18_terminal_fiber_20261011"
BINARY = Path("/opt/homebrew/bin/cryptominisat5")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p1 = json.loads((HERE / "protocol.json").read_text())
    p = json.loads((HERE / "protocol_v2.json").read_text())
    failed = json.loads((HERE / "failure_v1.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert p1["sha256"]["source"] == sha(HERE / "run.py")
    assert failed["status"] == "PRODUCER_FAILURE" and not failed["solver_started"]
    assert failed["protocol_sha256"] == sha(HERE / "protocol.json")
    assert p["status"] == "FROZEN_SELECTIVE_GAUSS_PAIR_V2"
    assert p["preflight_failure_sha256"] == sha(HERE / "failure_v1.json")
    assert p["sha256"] == {
        "source": sha(HERE / "run_v2.py"),
        "archive": sha(ROOT / "archive_receipt.json"),
        "gzip": sha(ROOT / "ordinary.xcnf.gz"),
        "solver": sha(BINARY)}
    archived = json.loads((ROOT / "archive_receipt.json").read_text())["ordinary"]
    assert result["status"] == "COMPLETE"
    assert result["source_sha256"] == sha(HERE / "run_v2.py")
    assert result["protocol_sha256"] == sha(HERE / "protocol_v2.json")
    assert result["raw_xcnf_sha256"] == archived["raw_sha256"]
    assert result["run_order"] == ["default", "selective"]
    counts = {}
    for name in result["run_order"]:
        row = result["cases"][name]
        stdout_path = HERE / f"{name}.stdout.txt"
        stderr_path = HERE / f"{name}.stderr.txt"
        output = stdout_path.read_text()
        assert row["stdout_sha256"] == sha(stdout_path)
        assert row["stderr_sha256"] == sha(stderr_path)
        assert row["stderr_bytes"] == stderr_path.stat().st_size == 0
        assert row["solver_started"] and "c CryptoMiniSat version 5.14.7" in output
        assert "s SATISFIABLE" not in output and "s UNSATISFIABLE" not in output
        assert row["status"] == "BOUNDED_UNKNOWN"
        assert row["stop_reason"] == "PARENT_WALL_CAP"
        assert row["exit_code"] == -15
        assert row["wall_ns"] >= p["parent_cap_seconds"] * 10**9
        assert row["peak_child_rss_bytes"] < p["rss_cap_bytes"]
        assert row["max_sampled_rss_bytes"] < p["rss_cap_bytes"]
        assert row["restart_rows"] == sum(
            line.startswith("c rst ") for line in output.splitlines())
        assert row["matrix_lines"] == [
            line for line in output.splitlines()
            if "[matrix]" in line or "[gauss]" in line]
        counts[name] = row["restart_rows"]
    assert "Using 0 matrices" in "\n".join(result["cases"]["default"]["matrix_lines"])
    selective = (HERE / "selective.stdout.txt").read_text()
    assert "Using 5 matrices" in selective
    assert "Disabling GJ-elim" in selective
    assert counts == {"default": 38, "selective": 33}
    out = {"status": "PASS_SELECTIVE_GAUSS_BOUNDARY",
           "source_xcnf_sha256": archived["raw_sha256"],
           "default_restarts": counts["default"],
           "selective_restarts": counts["selective"],
           "selective_matrices_activated": 5,
           "selective_gauss_auto_disabled": True,
           "result_sha256": sha(HERE / "result.json")}
    (HERE / "verification.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
