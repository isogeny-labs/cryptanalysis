"""One-worker, 600-second, 4-GiB charged inverse-trace public attempt."""

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
TARGET = GOAL / "n41_common_frob_factor_20261012/n131_projection_result.json"
PUBLIC_PREIMAGES = GOAL / "n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json"
ORIGINAL = GOAL / "n131_common_frob_inverse_trace_20261012"
N41_CONTROL = ORIGINAL / "n41_control_result.json"
CONTROL = ORIGINAL / "control_result.json"
FAILED_ATTEMPT = ORIGINAL / "query_result.json"
SOURCE_EQUIV = GOAL / "n131_w18_inverse_trace_terminal_20261011/gate_equivalence.json"
SAGE = HERE.parents[2] / "sage"
PARENT = GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py"
SPARSE = GOAL / "n41_basis_aware_quartic_20261011/sparse.py"
KARATSUBA = HERE.parents[1] / "koblitz-polynomial-w-pair-20260925/karatsuba_circuit.py"
SUPPORT = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
TOTAL_CAP_NS = 600*10**9
RSS_CAP = 4*1024**3
SOLVER_MAX_S = 540


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(result):
    with (HERE / "query_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k: result[k] for k in ("status", "target_dependent_attempt_ns",
                                              "peak_combined_rss_bytes_sampled")}), flush=True)


def execute(command, label, deadline):
    stdout, stderr = HERE / f"{label}.stdout", HERE / f"{label}.stderr"
    start = time.monotonic_ns()
    peak, stop = 0, None
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(command, stdout=out, stderr=err)
        owner, worker = psutil.Process(os.getpid()), psutil.Process(child.pid)
        while child.poll() is None:
            try:
                peak = max(peak, owner.memory_info().rss + worker.memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak > RSS_CAP:
                stop = "RSS_CAP"
            elif time.monotonic_ns() >= deadline:
                stop = "PARENT_TIME_CAP"
            if stop:
                child.kill()
                break
            time.sleep(0.025)
        code = child.wait()
    ended = time.monotonic_ns()
    return {"exit_code": code, "stop_reason": stop, "wall_ns": ended-start,
            "sampled_peak_combined_rss_bytes": peak,
            "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}


def main():
    protocol = json.loads((HERE / "query_protocol.json").read_text())
    files = {"runner": HERE / "run_public.py", "builder": HERE / "build_public.py",
             "target_projector": HERE / "target_project_sage.py",
             "circuit": HERE / "circuit.py", "parent": PARENT,
             "sparse": SPARSE, "karatsuba": KARATSUBA,
             "support": SUPPORT, "prior_target": TARGET,
             "public_preimages": PUBLIC_PREIMAGES,
             "fixture": HERE / "fixture.json", "control": CONTROL,
             "n41_control": N41_CONTROL, "source_equivalence": SOURCE_EQUIV,
             "failed_attempt": FAILED_ATTEMPT,
             "sage_runtime": HERE / "sage_runtime_info.json",
             "sage_launcher": SAGE, "solver": SOLVER}
    assert protocol["status"] == "FROZEN_BEFORE_N131_INVERSE_TRACE_PUBLIC_QUERY"
    assert protocol["sha256"] == {name: sha(path) for name, path in files.items()}
    assert protocol["one_worker"] is True and protocol["total_cap_seconds"] == 600
    assert protocol["solver_max_seconds"] == SOLVER_MAX_S
    assert protocol["combined_rss_cap_bytes"] == RSS_CAP
    assert json.loads(CONTROL.read_text())["status"] == "PASS_COMPLETE_N131_FIVEPAIR_ASSIGNMENT"
    assert json.loads(N41_CONTROL.read_text())["status"] == \
        "PASS_CHECKED_SAGE_N41_INVERSE_TRACE_SOURCE_AND_PUBLIC_CONTROL"
    start = time.monotonic_ns()
    deadline = start+TOTAL_CAP_NS
    target_stage = execute([str(SAGE), "-python", str(HERE / "target_project_sage.py")],
                           "target_project", deadline)
    peak = target_stage["sampled_peak_combined_rss_bytes"]
    if target_stage["exit_code"] != 0 or target_stage["stop_reason"]:
        end = time.monotonic_ns()
        save({"status": target_stage["stop_reason"] or "PRODUCER_FAILURE_TARGET",
              "target_projection": target_stage, "build": None, "solver": None,
              "target_dependent_attempt_ns": end-start,
              "bookkeeping_ns": end-start-target_stage["wall_ns"],
              "peak_combined_rss_bytes_sampled": peak,
              "protocol_sha256": sha(HERE / "query_protocol.json")})
        return
    build = execute(["python3", str(HERE / "build_public.py")], "build", deadline)
    peak = max(peak, build["sampled_peak_combined_rss_bytes"])
    if build["exit_code"] != 0 or build["stop_reason"]:
        end = time.monotonic_ns()
        save({"status": build["stop_reason"] or "PRODUCER_FAILURE_BUILD",
              "target_projection": target_stage, "build": build, "solver": None,
              "target_dependent_attempt_ns": end-start,
              "bookkeeping_ns": end-start-target_stage["wall_ns"]-build["wall_ns"],
              "peak_combined_rss_bytes_sampled": peak,
              "protocol_sha256": sha(HERE / "query_protocol.json")})
        return
    built = json.loads((HERE / "public_build_result.json").read_text())
    assert built["status"] == "PUBLIC_FORMULA_BUILT"
    assert built["protocol_sha256"] == sha(HERE / "query_protocol.json")
    assert built["xcnf_sha256"] == sha(HERE / "public.xcnf")
    remaining = (deadline-time.monotonic_ns())/10**9
    assert remaining > 60
    cap = min(SOLVER_MAX_S, int(remaining)-5)
    assert cap > 0
    command = [str(SOLVER), "--threads=1", f"--maxtime={cap}",
               "--maxmatrixrows=4000", "--maxmatrixcols=10000",
               "--maxnummatrices=6",
               "--zero-exit-status", "--verb=1", "--printsol=1",
               str(HERE / "public.xcnf")]
    solver = execute(command, "solver", deadline)
    peak = max(peak, solver["sampled_peak_combined_rss_bytes"])
    text = (HERE / "solver.stdout").read_text(errors="replace")
    terminals = [line for line in text.splitlines() if line.startswith("s ")]
    if "s SATISFIABLE" in terminals:
        status = "SAT_PENDING_INDEPENDENT_REPLAY"
    elif "s UNSATISFIABLE" in terminals:
        status = "UNSAT_ON_ENCODED_CHART"
    elif solver["stop_reason"]:
        status = solver["stop_reason"]
    elif "s INDETERMINATE" in terminals:
        status = "BOUNDED_UNKNOWN"
    else:
        status = "UNKNOWN_SOLVER_TERMINAL"
    end = time.monotonic_ns()
    save({"status": status, "candidate_id": None,
          "curve_id": protocol["curve_id"], "public_point": protocol["public_point"],
          "transformed_target": protocol["transformed_target"],
          "target_projection": target_stage,
          "build": build, "solver": solver, "solver_command": command,
          "solver_terminal_lines": terminals,
          "solver_restart_rows": sum(line.startswith("c rst") for line in text.splitlines()),
          "target_dependent_attempt_ns": end-start,
          "bookkeeping_ns": end-start-target_stage["wall_ns"]-build["wall_ns"]-solver["wall_ns"],
          "peak_combined_rss_bytes_sampled": peak,
          "protocol_sha256": sha(HERE / "query_protocol.json")})


if __name__ == "__main__":
    main()
