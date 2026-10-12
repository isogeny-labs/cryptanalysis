"""Split one N131 W18 terminal-fiber query into four signed-state SAT searches."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n131_w18_terminal4_20261012"
sys.path.insert(0, str(PARENT))
import terminal  # noqa: E402

TOTAL_CAP_NS = 600 * 10**9
PER_STATE_CAP_NS = 132 * 10**9
SOLVER_FLAGS = ["--threads=1", "--maxtime=132", "--zero-exit-status",
                "--verb=1", "--printsol=1"]
SOURCE_NAMES = ("terminal.py", "prepare.py", "pool.json", "source_count.json",
                "protocol.json", "control_result.json", "query_result.json",
                "sage_audit_result.json", "audit_result.json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    with (HERE / name).open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def freeze():
    old = terminal.check_protocol()
    receipt = json.loads((PARENT / "audit_result.json").read_text())
    assert receipt["status"] == "PASS_N131_TERMINAL4_RECEIPT_AUDIT"
    pool = terminal.pool()
    assert len(pool["states"]) == 4
    assert len({row["code"] for row in pool["states"]}) == 1
    save("protocol.json", {
        "status": "FROZEN_FOUR_SIGN_DISJUNCTION_SPLIT_BEFORE_QUERY",
        "candidate_id": None,
        "curve_id": old["curve_id"],
        "workload_id": old["workload_id"],
        "public_target": old["public_target"],
        "raw_preimage_index": old["raw_preimage_index"],
        "terminal_state_indices": [0, 1, 2, 3],
        "source_law": "same four-state union as parent; each search forces one choice true",
        "per_state_parent_cap_seconds": PER_STATE_CAP_NS // 10**9,
        "total_target_dependent_cap_seconds": TOTAL_CAP_NS // 10**9,
        "worker_count": 1,
        "combined_rss_cap_bytes": old["combined_rss_cap_bytes"],
        "solver_flags": SOLVER_FLAGS,
        "source_sha256": {name: sha(PARENT / name) for name in SOURCE_NAMES},
        "script_sha256": sha(Path(__file__)),
        "solver_sha256": sha(terminal.base.SOLVER.resolve()),
        "comparator_formula_sha256": json.loads((PARENT / "query_result.json").read_text())["formula"]["xcnf_sha256"]})


def protocol():
    data = json.loads((HERE / "protocol.json").read_text())
    assert data["status"] == "FROZEN_FOUR_SIGN_DISJUNCTION_SPLIT_BEFORE_QUERY"
    assert data["source_sha256"] == {name: sha(PARENT / name) for name in SOURCE_NAMES}
    assert data["script_sha256"] == sha(Path(__file__))
    assert data["solver_sha256"] == sha(terminal.base.SOLVER.resolve())
    assert data["solver_flags"] == SOLVER_FLAGS
    terminal.check_protocol()
    return data


def forced_xcnf(data, choice, output):
    header, sep, rows = data.partition(b"\n")
    assert sep == b"\n" and rows.endswith(b"\n")
    words = header.split()
    assert words[:2] == [b"p", b"cnf"] and len(words) == 4
    new_header = b"p cnf " + words[2] + b" " + str(int(words[3]) + 1).encode() + b"\n"
    output.write_bytes(new_header + rows + str(choice).encode() + b" 0\n")
    return {"sha256": sha(output), "bytes": output.stat().st_size,
            "forced_choice_wire": choice,
            "variables": int(words[2]), "constraints": int(words[3]) + 1}


def run_solver(index, formula, choice_wires, t0, rss_cap):
    outpath = HERE / f"solver_{index}.stdout.txt"
    errpath = HERE / f"solver_{index}.stderr.txt"
    parent = psutil.Process()
    start = time.monotonic_ns()
    peak, stop_reason = 0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        process = subprocess.Popen([str(terminal.base.SOLVER), *SOLVER_FLAGS,
                                    str(formula)], stdout=stdout, stderr=stderr)
        child = psutil.Process(process.pid)
        while process.poll() is None:
            now = time.monotonic_ns()
            try:
                combined = parent.memory_info().rss + child.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > rss_cap:
                stop_reason = "RSS_CAP"
            elif now - t0 >= TOTAL_CAP_NS:
                stop_reason = "TOTAL_QUERY_TIMEOUT"
            elif now - start >= PER_STATE_CAP_NS:
                stop_reason = "STATE_TIMEOUT"
            if stop_reason:
                process.kill()
                break
            time.sleep(0.05)
        exit_code = process.wait()
    end = time.monotonic_ns()
    stdout_text = outpath.read_text(errors="replace")
    status = ("BOUNDED_UNKNOWN" if stop_reason else
              "SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in stdout_text else
              "UNSAT" if "s UNSATISFIABLE" in stdout_text else "BOUNDED_UNKNOWN")
    decoded_name = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        positive = {int(token) for line in stdout_text.splitlines() if line.startswith("v ")
                    for token in line.split()[1:] if token.isdigit() and int(token) > 0}
        assert choice_wires[index] in positive
        assert all(wire not in positive for j, wire in enumerate(choice_wires) if j != index)
        decoded_name = f"decoded_{index}.json"
        save(decoded_name, {"positive_literals": sorted(positive), "state_index": index})
    return {"state_index": index, "status": status, "stop_reason": stop_reason,
            "exit_code": exit_code, "search_ns": end - start,
            "peak_combined_rss_bytes_sampled": peak,
            "status_lines": [line for line in stdout_text.splitlines() if line.startswith("s ")],
            "restart_rows": sum(line.startswith("c rst") for line in stdout_text.splitlines()),
            "stdout_sha256": sha(outpath), "stderr_sha256": sha(errpath),
            "decoded_model": decoded_name}


def query():
    frozen = protocol()
    t0 = time.monotonic_ns()
    target = terminal.base.target_record()
    raw_target = target["preimages"][0]["point"]
    _, root, nodes = terminal.base.source_domain()
    residuals = terminal.residuals(raw_target, terminal.pool()["states"])
    t1 = time.monotonic_ns()
    circuit, wires = terminal.build([row["standard_reciprocal"] for row in residuals],
                                    root, nodes)
    t2 = time.monotonic_ns()
    original = HERE / "ordinary.xcnf"
    circuit.write(original)
    t3 = time.monotonic_ns()
    assert sha(original) == frozen["comparator_formula_sha256"]
    choices = wires["choices"]
    assert len(choices) == 4
    data = original.read_bytes()
    del circuit
    formula_rows = []
    for index, choice in enumerate(choices):
        formula = HERE / f"state_{index}.xcnf"
        row = forced_xcnf(data, choice, formula)
        row["state_index"] = index
        formula_rows.append(row)
    del data
    t4 = time.monotonic_ns()
    print(json.dumps({"phase": "four_forced_formulas", "formula_rows": formula_rows}), flush=True)
    outcomes = []
    for index in range(4):
        if time.monotonic_ns() - t0 >= TOTAL_CAP_NS:
            outcomes.append({"state_index": index, "status": "NOT_STARTED_TOTAL_CAP"})
            continue
        result = run_solver(index, HERE / f"state_{index}.xcnf", choices, t0,
                            frozen["combined_rss_cap_bytes"])
        outcomes.append(result)
        print(json.dumps({"phase": "state_complete", "result": result}), flush=True)
        if result["status"] == "SAT_PENDING_GROUP_REPLAY":
            break
    t5 = time.monotonic_ns()
    phase = {"target_residual_generation_ns": t1 - t0,
             "formula_construction_ns": t2 - t1,
             "base_formula_serialization_ns": t3 - t2,
             "forced_formula_serialization_ns": t4 - t3,
             "solver_search_and_parse_ns": t5 - t4}
    assert sum(phase.values()) == t5 - t0
    save("query_result.json", {"status": "SAT_PENDING_GROUP_REPLAY" if any(
             row["status"] == "SAT_PENDING_GROUP_REPLAY" for row in outcomes)
             else "BOUNDED_UNKNOWN" if any(row["status"] == "BOUNDED_UNKNOWN" for row in outcomes)
             else "UNSAT" if len(outcomes) == 4 and all(row["status"] == "UNSAT" for row in outcomes)
             else "INCOMPLETE_TOTAL_CAP",
          "candidate_id": None, "curve_id": frozen["curve_id"],
          "workload_id": frozen["workload_id"],
          "public_target": frozen["public_target"],
          "raw_preimage_index": frozen["raw_preimage_index"],
          "raw_target": raw_target, "residuals": residuals,
          "phase_ns": phase, "target_dependent_attempt_ns": t5 - t0,
          "base_formula_sha256": sha(original), "formula_rows": formula_rows,
          "outcomes": outcomes, "protocol_sha256": sha(HERE / "protocol.json")})
    print(json.dumps({"status": "FINISHED", "seconds": (t5-t0)/1e9}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "query")
    {"freeze": freeze, "query": query}[sys.argv[1]]()
