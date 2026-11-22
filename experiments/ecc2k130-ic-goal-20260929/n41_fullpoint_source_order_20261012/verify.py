"""Read-only exact permutation and terminal audit for source-first XCNF."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n41_fullpoint_functional_slope_20261012"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load("source_order_runner", HERE / "run.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    runner.check_build_inputs()
    build = json.loads((HERE / "build.json").read_text())
    protocol = json.loads((HERE / "query_protocol.json").read_text())
    result = json.loads((HERE / "query.json").read_text())
    assert build["status"] == "PASS_EXACT_FUNCTIONAL_FULLPOINT_RENUMBER"
    for path, digest in protocol["sha256"].items():
        assert sha(path) == digest, path
    assert sha(HERE / "query_protocol.json") == result["query_protocol_sha256"]
    assert sha(HERE / "ordered.xcnf") == build["ordered_xcnf_sha256"]
    assert (HERE / "ordered.xcnf").stat().st_size == build["ordered_xcnf_bytes"]
    circuit, wires, chart, chosen = runner.primary()
    order, mapping = runner.permutation(chosen, circuit.next_var - 1)
    assert len(order) == build["variables"] == 121456
    assert [mapping[v] for v in wires["flags"]] == build["target_flags_new"] == [1, 2, 3, 4]
    assert len([v for row in wires["selectors"] for v in row]) == build["source_selector_count"] == 1400
    clauses = xors = 0
    with (SOURCE / "public.xcnf").open() as old, (HERE / "ordered.xcnf").open() as new:
        assert old.readline() == new.readline() == "p cnf 121456 378056\n"
        for before, after in zip(old, new, strict=True):
            a, b = before.split(), after.split()
            is_xor = a[0] == "x"
            assert is_xor == (b[0] == "x") and a[-1] == b[-1] == "0"
            old_lits = list(map(int, a[1:-1] if is_xor else a[:-1]))
            new_lits = list(map(int, b[1:-1] if is_xor else b[:-1]))
            assert new_lits == [mapping[abs(v)] * (1 if v > 0 else -1) for v in old_lits]
            xors += is_xor
            clauses += not is_xor
    assert {"cnf_clauses": clauses, "native_xor_rows": xors} == build["checks"]
    original = json.loads((SOURCE / "control.json").read_text())
    assert original["status"] == "SAT"
    assert original["group_replay"]["selected_state_ids"] == chart["state_ids"]
    assert original["group_replay"]["raw_preimage_index"] == chart["target_index"]
    assert sha(HERE / "solver.stdout") == result["stdout_sha256"]
    assert sha(HERE / "solver.stderr") == result["stderr_sha256"]
    log = (HERE / "solver.stdout").read_text(errors="replace")
    assert [line for line in log.splitlines() if line.startswith("s ")] == result["terminal_lines"] == []
    assert sum(line.startswith("c rst") for line in log.splitlines()) == result["restart_rows"]
    assert result["status"] == result["stop"] == "PARENT_TIME_CAP"
    assert result["exit_code"] == -9
    assert 180 <= result["solver_wall_ns_exploratory"] / 1e9 < 181
    assert result["peak_combined_rss_bytes_sampled"] < protocol["combined_rss_cap_bytes"]
    receipt = {"status": "PASS_EXACT_SOURCE_ORDER_AND_TERMINAL_AUDIT",
               "variables": build["variables"], "cnf_clauses_replayed": clauses,
               "native_xor_rows_replayed": xors,
               "target_flags_new": build["target_flags_new"],
               "source_selectors_new": [5, 1404],
               "query_status": result["status"],
               "restart_rows": result["restart_rows"],
               "verifier_sha256": sha(HERE / "verify.py")}
    archive = HERE / "audit.json"
    if archive.exists():
        assert json.loads(archive.read_text()) == receipt
    else:
        archive.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(receipt["status"])


if __name__ == "__main__":
    main()
