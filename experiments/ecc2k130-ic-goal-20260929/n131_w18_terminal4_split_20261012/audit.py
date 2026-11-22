"""Audit four forced terminal-sign SAT queries and their joint time budget."""

import hashlib
import json
from pathlib import Path

import split

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_terminal4_20261012"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    protocol = split.protocol()
    query = read(HERE / "query_result.json")
    prior = read(PARENT / "query_result.json")
    assert query["protocol_sha256"] == sha(HERE / "protocol.json")
    for key in ("curve_id", "workload_id", "public_target", "raw_preimage_index"):
        assert query[key] == protocol[key] == prior[key]
    assert query["raw_target"] == prior["raw_target"]
    assert query["residuals"] == prior["residuals"]
    assert query["base_formula_sha256"] == protocol["comparator_formula_sha256"]
    assert sha(HERE / "ordinary.xcnf") == query["base_formula_sha256"]
    assert len(query["formula_rows"]) == 4
    source = (HERE / "ordinary.xcnf").read_bytes()
    assert source.endswith(b"\n")
    header, _, rest = source.partition(b"\n")
    parts = header.split()
    assert parts[:2] == [b"p", b"cnf"]
    for index, row in enumerate(query["formula_rows"]):
        assert row["state_index"] == index
        path = HERE / f"state_{index}.xcnf"
        assert row["sha256"] == sha(path)
        assert row["bytes"] == path.stat().st_size
        new_header = b"p cnf " + parts[2] + b" " + str(int(parts[3]) + 1).encode() + b"\n"
        assert path.read_bytes() == (new_header + rest +
                                      str(row["forced_choice_wire"]).encode() + b" 0\n")
    assert len({row["forced_choice_wire"] for row in query["formula_rows"]}) == 4
    phases = query["phase_ns"]
    assert all(value >= 0 for value in phases.values())
    assert sum(phases.values()) == query["target_dependent_attempt_ns"]
    assert query["target_dependent_attempt_ns"] <= (
        protocol["total_target_dependent_cap_seconds"] + 2) * 10**9
    assert [row["state_index"] for row in query["outcomes"]] == list(range(len(query["outcomes"])))
    assert len(query["outcomes"]) <= 4
    for row in query["outcomes"]:
        if row["status"] == "NOT_STARTED_TOTAL_CAP":
            continue
        index = row["state_index"]
        stdout_path = HERE / f"solver_{index}.stdout.txt"
        stderr_path = HERE / f"solver_{index}.stderr.txt"
        assert row["stdout_sha256"] == sha(stdout_path)
        assert row["stderr_sha256"] == sha(stderr_path)
        stdout = stdout_path.read_text(errors="replace")
        assert row["status_lines"] == [line for line in stdout.splitlines()
                                       if line.startswith("s ")]
        assert row["restart_rows"] == sum(line.startswith("c rst")
                                           for line in stdout.splitlines())
        assert row["peak_combined_rss_bytes_sampled"] <= protocol["combined_rss_cap_bytes"]
        assert row["search_ns"] <= (protocol["per_state_parent_cap_seconds"] + 2) * 10**9
        if row["status"] == "BOUNDED_UNKNOWN":
            assert row["decoded_model"] is None
            assert not any(line in ("s SATISFIABLE", "s UNSATISFIABLE")
                           for line in row["status_lines"])
        elif row["status"] == "SAT_PENDING_GROUP_REPLAY":
            assert row["decoded_model"] is not None
        else:
            assert row["status"] == "UNSAT" and "s UNSATISFIABLE" in row["status_lines"]
    result = {"status": "PASS_FOUR_STATE_SPLIT_RECEIPT_AUDIT",
              "query_status": query["status"],
              "state_statuses": [row["status"] for row in query["outcomes"]],
              "target_dependent_attempt_ns": query["target_dependent_attempt_ns"],
              "phase_sum_ns": sum(phases.values()),
              "sha256": {name: sha(HERE / name) for name in (
                  "audit.py", "split.py", "protocol.json", "query_result.json",
                  "ordinary.xcnf")}}
    with (HERE / "audit_result.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(result["status"], result["state_statuses"])


if __name__ == "__main__":
    main()
