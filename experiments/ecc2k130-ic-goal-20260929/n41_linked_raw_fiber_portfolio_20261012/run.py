"""Four unpinned raw-fiber slices of the frozen linked N41 full-point circuit."""

import hashlib
import importlib.util
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_linked_functional_fullpoint_20261012"
V3 = PARENT / "v3"
spec = importlib.util.spec_from_file_location("linked_v3_for_fibers", V3 / "run.py")
solver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solver)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def main():
    frozen = json.loads((HERE / "protocol.json").read_text())
    assert frozen["status"] == "FROZEN_BEFORE_N41_LINKED_RAW_FIBER_PORTFOLIO"
    sources = {"runner": Path(__file__), "v3_runner": V3 / "run.py",
               "v3_protocol": V3 / "protocol.json",
               "v3_public_receipt": V3 / "public.json",
               "v3_public_build": V3 / "public.build.json",
               "v3_archive": PARENT / "archive_result.json",
               "source_input": solver.old.INPUT,
               "solver": solver.SOLVER}
    assert frozen["sha256"] == {name: sha(path) for name, path in sources.items()}
    assert frozen["fiber_order"] == [0, 1, 2, 3]
    assert frozen["slice_parent_cap_seconds"] == 38
    assert frozen["total_cap_seconds"] == 180
    assert frozen["worker_count"] == 1
    assert frozen["combined_rss_cap_bytes"] == 4 * 1024**3
    solver.HERE = HERE
    solver.CAPS = {f"fiber{index}": 38 for index in range(4)}
    lists, targets = solver.old.source()
    assert targets[0] and len(targets) == 4
    start = time.monotonic_ns()
    circuit, wires = solver.formula(lists, targets, False, None)
    built = time.monotonic_ns()
    prior = json.loads((V3 / "public.build.json").read_text())
    assert (circuit.next_var - 1, len(circuit.clauses), len(circuit.xors)) == (
        prior["variables"], prior["cnf_clauses"], prior["native_xor_rows"])
    baseline = HERE / "base.xcnf"
    circuit.write(baseline)
    archived = json.loads((PARENT / "archive_result.json").read_text())
    assert sha(baseline) == prior["sha256"] == archived["files"]["v3/public.xcnf"]["raw_sha256"]
    base_written = time.monotonic_ns()
    rows = []
    for index in frozen["fiber_order"]:
        remaining_seconds = (frozen["total_cap_seconds"] * 10**9 -
                             (time.monotonic_ns() - start)) // 10**9
        if remaining_seconds < 7:
            break
        slice_cap = min(38, int(remaining_seconds))
        solver.CAPS[f"fiber{index}"] = slice_cap
        circuit.clauses.append(f"{wires['flags'][index]} 0")
        formula = HERE / f"fiber{index}.xcnf"
        circuit.write(formula)
        serialized = time.monotonic_ns()
        solver.search(f"fiber{index}", formula, circuit, wires,
                      lists, targets)
        receipt = json.loads((HERE / f"fiber{index}.json").read_text())
        finished = time.monotonic_ns()
        circuit.clauses.pop()
        rows.append({"fiber": index, "formula_sha256": sha(formula),
                     "formula_bytes": formula.stat().st_size,
                     "slice_parent_cap_seconds": slice_cap,
                     "serialization_ns": serialized - (base_written if not rows else rows[-1]["finished_ns"]),
                     "receipt_sha256": sha(HERE / f"fiber{index}.json"),
                     "status": receipt["status"],
                     "finished_ns": finished})
        if receipt["status"] == "SAT":
            break
    end = time.monotonic_ns()
    for row in rows:
        row.pop("finished_ns")
    valid_statuses = {"SAT", "PARENT_TIME_CAP", "BOUNDED_UNKNOWN"}
    status = ("PRODUCER_FAILURE" if any(row["status"] not in valid_statuses for row in rows)
              else "GLOBAL_CAP_EXCEEDED" if end-start > frozen["total_cap_seconds"] * 10**9
              else "SAT_GROUP_REPLAYED" if rows and rows[-1]["status"] == "SAT"
              else "BOUNDED_UNKNOWN" if len(rows) == 4
              else "PARTIAL_CAP_COVERAGE")
    result = {"status": status, "candidate_id": None,
              "curve_id": frozen["curve_id"], "public_point": frozen["public_point"],
              "fiber_order": frozen["fiber_order"], "slices": rows,
              "base_formula_sha256": sha(baseline),
              "base_formula_bytes": baseline.stat().st_size,
              "base_build_ns_exploratory": built-start,
              "base_serialization_ns": base_written-built,
              "total_target_dependent_ns": end-start,
              "worker_count": 1,
              "peak_combined_rss_bytes_sampled": max((
                  json.loads((HERE / f"fiber{row['fiber']}.json").read_text())["peak_combined_rss_bytes_sampled"]
                  for row in rows), default=0),
              "protocol_sha256": sha(HERE / "protocol.json")}
    save("result.json", result)
    print(status, len(rows), (end-start)/1e9, flush=True)


if __name__ == "__main__":
    main()
