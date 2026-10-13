"""Read-only byte and relation replay for the target-backward N41 attempt."""

import gzip
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
V4 = HERE / "v4"
spec = importlib.util.spec_from_file_location("backward_v4", V4 / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def read(path):
    return json.loads(path.read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def formula_bytes(label):
    raw = V4 / f"{label}.xcnf"
    archive = V4 / f"{label}.xcnf.gz"
    if raw.exists():
        return raw.read_bytes()
    return gzip.decompress(archive.read_bytes())


def main():
    protocol = read(V4 / "protocol.json")
    assert protocol["sha256"] == {
        "runner": sha((V4 / "run.py").read_bytes()),
        "input": sha(run.old.INPUT.read_bytes()),
        "parent_runner": sha((GOAL / "n41_linked_functional_fullpoint_20261012/run.py").read_bytes()),
        "linked_audit": sha((GOAL / "n41_n131_linked_frobenius_pair_20261012/audit_result.json").read_bytes()),
        "solver": sha(run.SOLVER.read_bytes()),
    }
    assert protocol["version"] == "v4"
    assert protocol["public_cap_seconds"] == 180
    assert protocol["control_cap_seconds"] == 30
    assert protocol["combined_rss_cap_bytes"] == 4*1024**3
    assert read(V4 / "result.json")["protocol_sha256"] == sha((V4 / "protocol.json").read_bytes())
    lists, targets = run.old.source()
    witness = run.parent.linked_witness(lists, targets)
    assert witness["target_index"] == 3
    assert len(set(witness["state_ids"])) == 9
    run.replay_values(lists, targets, witness["state_ids"], witness["target_index"])
    results = {}
    for label, pin in (("control", True), ("public", False)):
        circuit, wires = run.formula(lists, targets, pin, witness)
        result = read(V4 / f"{label}.json")
        assert result["variables"] == circuit.next_var - 1
        assert result["clauses"] == len(circuit.clauses)
        assert result["xor_rows"] == len(circuit.xors)
        assert result["and_gates"] == circuit.and_count
        raw = formula_bytes(label)
        assert len(raw) == result["xcnf_bytes"]
        assert sha(raw) == result["xcnf_sha256"]
        with tempfile.TemporaryDirectory() as tmp:
            rebuilt = Path(tmp) / "rebuilt.xcnf"
            circuit.write(rebuilt)
            assert rebuilt.read_bytes() == raw
            stdout = (V4 / f"{label}.stdout").read_text(errors="replace")
            assert sha((V4 / f"{label}.stdout").read_bytes()) == result["stdout_sha256"]
            assert sha((V4 / f"{label}.stderr").read_bytes()) == result["stderr_sha256"]
            terminals = [line for line in stdout.splitlines() if line.startswith("s ")]
            assert terminals == result["terminal_lines"]
            assert sum(line.startswith("c rst") for line in stdout.splitlines()) == result["restart_rows"]
            if label == "control":
                assert result["status"] == "SAT" and terminals == ["s SATISFIABLE"]
                replay = run.selected_model(stdout, circuit, rebuilt, wires, lists, targets)
                assert replay == result["group_replay"]
                assert replay["selected_state_ids"] == witness["state_ids"]
            else:
                assert result["status"] == result["stop"] == "PARENT_TIME_CAP"
                assert terminals == [] and result["exit_code"] == -9
                assert result["group_replay"] is None
                assert result["solver_wall_ns_exploratory"] >= 180*10**9
                assert result["peak_combined_rss_bytes_sampled"] < 4*1024**3
        results[label] = result
    summary = read(V4 / "result.json")
    build = read(V4 / "build.json")
    public = results["public"]
    assert summary["target_dependent_total_ns"] == (
        build["public_build_ns"] + public["formula_serialization_ns"] +
        public["solver_wall_ns_exploratory"] + public["model_replay_ns"])
    assert read(HERE / "failure.json")["status"] == "PRODUCER_FAILURE_ATTRIBUTE_ERROR"
    v2_failure = read(HERE / "v2/failure.json")
    v3_failure = read(HERE / "v3/failure.json")
    assert v2_failure["status"] == "PRODUCER_FAILURE_ZERO_LITERAL"
    assert v3_failure["status"] == "PRODUCER_FAILURE_MODEL_DECODER_CONSTANT_WIRE"
    assert v2_failure["parser_exit_code"] == 255
    assert "PARSE ERROR" in (HERE / "v2/control.stderr").read_text()
    assert "s SATISFIABLE" in (HERE / "v3/control.stdout").read_text()
    archive_protocol = read(HERE / "archive_protocol.json")
    archive = read(HERE / "archive_result.json")
    assert archive["status"] == "BYTE_REPLAY_PASS"
    assert archive["protocol_sha256"] == sha((HERE / "archive_protocol.json").read_bytes())
    assert archive_protocol["archive_source_sha256"] == sha((HERE / "archive.py").read_bytes())
    assert archive_protocol["inputs"] == {name: row["raw_sha256"] for name, row in archive["files"].items()}
    for name, row in archive["files"].items():
        packed = (HERE / (name + ".gz")).read_bytes()
        assert sha(packed) == row["gzip_sha256"] and len(packed) == row["gzip_bytes"]
        raw = gzip.decompress(packed)
        assert sha(raw) == row["raw_sha256"] and len(raw) == row["raw_bytes"]
    print("PASS_N41_BACKWARD_TARGET_AUDIT PARENT_TIME_CAP")


if __name__ == "__main__":
    main()
