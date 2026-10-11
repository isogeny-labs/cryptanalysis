"""Verify frozen input, formula, search transcript, and phase accounting."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOINT = ROOT / "n131_w16_joint_prefix_20261010"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    inputs = json.loads((HERE / "inputs.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_W16_PUBLISHED_QUERY"
    assert protocol["curve_id"] == inputs["curve_id"]
    assert protocol["target_q"] == inputs["target_q"] == result["target_q"]
    assert protocol["target_id"] == inputs["target_id"] == "ecc2k-130"
    assert protocol["prefix_count"] == inputs["prefix_count"] == 32
    assert protocol["target_branch_count"] == 128
    assert protocol["workers"] == 1
    assert protocol["online_cap_seconds"] == 600
    assert protocol["rss_cap_bytes"] == 4 * 1024**3
    source_paths = {"query": HERE / "query.py", "prepare": HERE / "prepare.py",
                    "inputs": HERE / "inputs.json", "runtime": HERE / "sage_runtime_info.json",
                    "joint_runner": JOINT / "run.py", "joint_circuit": JOINT / "circuit.py",
                    "joint_prefixes": JOINT / "prefixes.json",
                    "w16_source": ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w16.tsv",
                    "solver": Path("/opt/homebrew/bin/cryptominisat5")}
    assert protocol["source_sha256"] == {key: sha(path) for key, path in source_paths.items()}
    assert result["source_sha256"] == protocol["source_sha256"]
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    archived = json.loads((JOINT / "prefixes.json").read_text())
    assert len(inputs["prefixes"]) == len(archived["prefixes"]) == 32
    for current, prior in zip(inputs["prefixes"], archived["prefixes"]):
        for key in ("masks", "signs", "columns", "projected_sum"):
            assert current[key] == prior[key]
        assert len(current["preimages"]) == len(current["target_reciprocals"]) == 4
    formula = result["formula"]
    assert sha(HERE / "system.xcnf") == formula["sha256"]
    with (HERE / "system.xcnf").open("rb") as stream:
        header = stream.readline().decode().split()
    assert header[:2] == ["p", "cnf"]
    assert int(header[2]) == formula["variables"]
    assert int(header[3]) == formula["cnf_clauses"] + formula["native_xor_rows"]
    assert (HERE / "system.xcnf").stat().st_size == formula["bytes"]
    for name in ("stdout", "stderr"):
        assert sha(HERE / f"solver.{name}.txt") == result["output_sha256"][name]
    stdout = (HERE / "solver.stdout.txt").read_text(errors="replace")
    lines = [line for line in stdout.splitlines() if line.startswith("s ")]
    assert result["solver_status_lines"] == lines
    assert result["model_lines"] == sum(line.startswith("v ") for line in stdout.splitlines())
    assert "c rst " in stdout or "c [branch]" in stdout
    phases = result["phase_ns"]
    assert sum(value for key, value in phases.items() if key != "total_online_ns") == phases["total_online_ns"]
    assert phases["total_online_ns"] / 1e9 <= 601
    assert result["sampled_peak_combined_rss_bytes"] < protocol["rss_cap_bytes"]
    if result["status"] == "GROUP_RELATION_FOUND":
        lift = json.loads((HERE / "group_lift.json").read_text())
        assert result["group_lift_status"] == lift["status"] == "GROUP_LIFT_FOUND"
        assert result["selected_choice"] is not None
    elif result["status"] == "CENSORED_TIME":
        assert result["stop_reason"] == "SAFE_WALL_STOP" or "s INDETERMINATE" in lines
        assert not result["model_lines"]
        assert not any(line in ("s SATISFIABLE", "s UNSATISFIABLE") for line in lines)
    elif result["status"] == "UNSAT_COMPLETE":
        assert lines == ["s UNSATISFIABLE"]
    else:
        raise AssertionError("unexpected terminal status: " + result["status"])
    audit = {"status": "PASS_W16_JOINT_PUBLIC_RECEIPT_AUDIT",
             "query_status": result["status"],
             "protocol_sha256": sha(HERE / "protocol.json"),
             "result_sha256": sha(HERE / "result.json"),
             "formula_sha256": formula["sha256"],
             "online_seconds": phases["total_online_ns"] / 1e9,
             "solver_cpu_seconds": result["sampled_solver_cpu_seconds"]}
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
