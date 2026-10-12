"""Frozen single-point N131 seven-pair affine IC search."""

import hashlib
import json
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CORE = ROOT / "n131_w18_four_seed_sevenpair_circuit_20261011"
AFFINE = ROOT / "n131_w18_four_seed_sevenpair_affine_control_20261011"
COUNT = ROOT / "n131_w18_four_seed_sevenpair_source_20261011"
PRIOR = ROOT / "n131_w18_all_fibers_inverse_20261011"
sys.path.insert(0, str(CORE))
import circuit as method  # noqa: E402

CPU_SOFT = 300
CPU_HARD = 305
WALL_CAP = 4500
RSS_CAP = 4 * 1024**3
FLAGS = ["--threads=1", "--maxtime=4500", "--zero-exit-status",
         "--verb=1", "--printsol=1"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    prior = method.prior
    return {"runner": Path(__file__),
            "core_circuit": CORE / "circuit.py",
            "source_count": COUNT / "result.json",
            "affine_control": AFFINE / "control_result.json",
            "affine_sage_audit": AFFINE / "sage_audit_result.json",
            "prior_target": PRIOR / "query_result.json",
            "support": method.SUPPORT,
            "terminal_pool": prior.ROOT / "n131_w18_terminal_fiber_20261011" / "pool.json",
            "solver": prior.terminal.base.SOLVER}


def freeze():
    prior = method.prior
    previous = json.loads((PRIOR / "query_result.json").read_text())
    affine = json.loads((AFFINE / "sage_audit_result.json").read_text())
    count = json.loads((COUNT / "result.json").read_text())
    assert previous["status"] == "BOUNDED_UNKNOWN"
    assert affine["status"] == "PASS_INDEPENDENT_SAGE_ALL_FOUR_AFFINE_SEEDS"
    assert count["status"] == "PASS_EXACT_FOUR_SEED_SEVENPAIR_MATCHING_COUNT"
    target = prior.terminal.base.target_record()
    assert target["public_target"] == previous["public_target"]
    assert target["workload_id"] == previous["workload_id"]
    assert prior.terminal.base.SOLVER.is_file()
    save("protocol.json", {
        "status": "FROZEN_N131_SEVENPAIR_AFFINE_ORDINARY_QUERY",
        "candidate_id": None,
        "curve_id": previous["curve_id"],
        "workload_id": previous["workload_id"],
        "public_target": previous["public_target"],
        "source_policy": "seven_w18_pairs_affine_seeds_212_215_plus_32_terminal_states",
        "pair_rotations": list(method.ROTATIONS),
        "terminal_states": 32, "raw_fibers": 4,
        "signed_source_mean_upper_exact": count["uniform_public_point_mean_upper_exact"],
        "worker_count": 1, "solver_flags": FLAGS,
        "solver_cpu_soft_limit_seconds": CPU_SOFT,
        "solver_cpu_hard_limit_seconds": CPU_HARD,
        "total_online_wall_cap_seconds": WALL_CAP,
        "combined_rss_cap_bytes": RSS_CAP,
        "solver_path": str(prior.terminal.base.SOLVER),
        "source_sha256": {name: sha(path) for name, path in sources().items()},
    })
    print("FROZEN_N131_SEVENPAIR_AFFINE_ORDINARY_QUERY", flush=True)


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SOFT, CPU_HARD))


def query():
    protocol = json.loads((HERE / "protocol.json").read_text())
    prior = method.prior
    assert protocol["status"] == "FROZEN_N131_SEVENPAIR_AFFINE_ORDINARY_QUERY"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    runtime = json.loads((HERE / "sage_runtime_info.json").read_text())
    assert runtime["status"] == "verified"
    target = prior.terminal.base.target_record()
    assert target["public_target"] == protocol["public_target"]
    # Reusable support and terminal input loading precede the online interval.
    support_cache = method.support()
    pool_cache = prior.terminal.pool()
    method.support = lambda: support_cache
    prior.terminal.pool = lambda: pool_cache
    t0 = time.monotonic_ns()
    preimages = prior.public_preimages(protocol["public_target"])
    assert [list(point) for point in preimages] == json.loads(
        (PRIOR / "query_result.json").read_text())["raw_preimages"]
    t1 = time.monotonic_ns()
    residuals = prior.residuals(preimages)
    t2 = time.monotonic_ns()
    circuit, wires = method.build([row["standard_reciprocal"] for row in residuals])
    t3 = time.monotonic_ns()
    formula = HERE / "ordinary.xcnf"
    circuit.write(formula)
    t4 = time.monotonic_ns()
    profile = prior.terminal.base.profile(circuit, formula,
                                         (t3-t2)/1e9, (t4-t3)/1e9)
    del circuit
    print(json.dumps({"phase": "frozen_public_formula", "formula": profile}), flush=True)
    parent = psutil.Process()
    peak, cpu_sample, stop = 0, 0.0, None
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout_path, stderr_path = HERE / "solver.stdout.txt", HERE / "solver.stderr.txt"
    with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
        child = subprocess.Popen([str(prior.terminal.base.SOLVER), *FLAGS,
                                  str(formula)], stdout=stdout, stderr=stderr,
                                 preexec_fn=limits)
        process = psutil.Process(child.pid)
        print(json.dumps({"solver_pid": child.pid,
                          "formula_sha256": profile["xcnf_sha256"]}), flush=True)
        while child.poll() is None:
            try:
                cpu = process.cpu_times()
                cpu_sample = max(cpu_sample, cpu.user + cpu.system)
                combined = parent.memory_info().rss + process.memory_info().rss
                peak = max(peak, combined)
            except psutil.NoSuchProcess:
                pass
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() - t0 >= WALL_CAP * 10**9:
                stop = "TOTAL_ONLINE_WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.2)
        code = child.wait()
    t5 = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = (after.ru_utime + after.ru_stime -
                 before.ru_utime - before.ru_stime)
    output = stdout_path.read_text(errors="replace")
    status_lines = [line for line in output.splitlines() if line.startswith("s ")]
    status = ("SAT_PENDING_GROUP_REPLAY" if "s SATISFIABLE" in status_lines else
              "UNSAT" if "s UNSATISFIABLE" in status_lines else "BOUNDED_UNKNOWN")
    if status == "BOUNDED_UNKNOWN" and stop is None:
        stop = ("CPU_SOFT_LIMIT" if code == -signal.SIGXCPU else
                "CPU_HARD_LIMIT" if code == -signal.SIGKILL and child_cpu >= CPU_SOFT else
                "SOLVER_EXIT_WITHOUT_STATUS")
    decoded = None
    decode_error = None
    if status == "SAT_PENDING_GROUP_REPLAY":
        try:
            positive = {int(token) for line in output.splitlines()
                        if line.startswith("v ") for token in line.split()[1:]
                        if token.isdigit() and int(token) > 0}

            def bits_value(bits):
                return sum(int(wire in positive) << bit
                           for bit, wire in enumerate(bits))

            selected = [i for i, wire in enumerate(wires["choices"])
                        if wire in positive]
            assert len(selected) == 1
            decoded = {
                "selected_codes": [bits_value(bits) for bits in wires["selectors"]],
                "seed_deltas": [bits_value(bits) for bits in wires["seeds"]],
                "pair_reciprocals": [bits_value(bits) for bits in wires["outputs"]],
                "middle_reciprocals": [bits_value(bits) for bits in wires["middle"]],
                "group_branch_bits": [int(wire in positive) for wire in wires["branches"]],
                "inverse_witnesses": [[bits_value(bits) for bits in pair]
                                      for pair in wires["inverse_witnesses"]],
                "selected_choice_index": selected[0],
                "selected_preimage_index": selected[0] // 32,
                "selected_terminal_state_index": selected[0] % 32,
                "formula_sha256": profile["xcnf_sha256"],
            }
            save("decoded_model.json", decoded)
        except Exception as exc:
            status = "MODEL_DECODE_FAILURE"
            decode_error = f"{type(exc).__name__}: {exc}"
    t6 = time.monotonic_ns()
    phases = {"public_raw_preimages_ns": t1-t0,
              "target_residual_generation_ns": t2-t1,
              "formula_construction_ns": t3-t2,
              "formula_serialization_ns": t4-t3,
              "solver_search_ns": t5-t4,
              "terminal_parse_and_decode_ns": t6-t5}
    assert sum(phases.values()) == t6-t0
    save("query_result.json", {
        "status": status, "candidate_id": None,
        "curve_id": protocol["curve_id"],
        "workload_id": protocol["workload_id"],
        "public_target": protocol["public_target"],
        "raw_preimages": [list(point) for point in preimages],
        "residuals": residuals,
        "phase_ns": phases, "target_dependent_attempt_ns": t6-t0,
        "formula": profile,
        "worker_count": 1, "solver_flags": FLAGS,
        "solver_exit_code": code,
        "solver_cpu_seconds_rusage": child_cpu,
        "solver_cpu_seconds_sampled": cpu_sample,
        "stop_reason": stop, "decode_error": decode_error,
        "peak_combined_rss_bytes_sampled": peak,
        "status_lines": status_lines,
        "restart_rows": sum(line.startswith("c rst")
                            for line in output.splitlines()),
        "decoded_model_saved": decoded is not None,
        "stdout_sha256": sha(stdout_path),
        "stderr_sha256": sha(stderr_path),
        "protocol_sha256": sha(HERE / "protocol.json"),
        "sage_runtime_sha256": sha(HERE / "sage_runtime_info.json"),
    })
    print(json.dumps({"status": status, "stop_reason": stop,
                      "online_attempt_seconds": (t6-t0)/1e9,
                      "solver_cpu_seconds": child_cpu}), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"freeze", "query"}:
        raise SystemExit("usage: query.py freeze|query")
    {"freeze": freeze, "query": query}[sys.argv[1]]()
