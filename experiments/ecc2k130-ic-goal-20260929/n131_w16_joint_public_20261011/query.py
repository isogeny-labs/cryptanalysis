#!/usr/bin/env sage -python
"""Frozen one-worker published-point W16 joint-prefix search."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JOINT = ROOT / "n131_w16_joint_prefix_20261010"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
CAP = 600.0
RSS_CAP = 4 * 1024**3
FLAGS = ["--threads=1", "--xor=0", "--printsol=1",
         "--random=20261011", "--maxconfl=100000000", "--maxtime=580"]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


joint = load("joint_w16_public_base", JOINT / "run.py")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save(path, record):
    with Path(path).open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sources():
    return {"query": HERE / "query.py", "prepare": HERE / "prepare.py",
            "inputs": HERE / "inputs.json", "runtime": HERE / "sage_runtime_info.json",
            "joint_runner": JOINT / "run.py", "joint_circuit": JOINT / "circuit.py",
            "joint_prefixes": JOINT / "prefixes.json",
            "w16_source": ROOT / "n131_w16_w18_sixpair_width_gate_20261010/support_w16.tsv",
            "solver": SOLVER}


def freeze():
    inputs = json.loads((HERE / "inputs.json").read_text())
    assert inputs["status"] == "FROZEN_W16_32_PREFIX_PUBLISHED_INPUT"
    assert inputs["prefix_count"] == 32
    assert json.loads((HERE / "sage_runtime_info.json").read_text())["status"] == "verified"
    protocol = {"status": "FROZEN_BEFORE_W16_PUBLISHED_QUERY", "candidate_id": None,
                "curve_id": inputs["curve_id"], "target_id": inputs["target_id"],
                "target_q": inputs["target_q"], "input_law": inputs["input_law"],
                "prefix_count": 32, "target_branch_count": 128, "workers": 1,
                "online_cap_seconds": CAP, "rss_cap_bytes": RSS_CAP,
                "solver_flags": FLAGS,
                "source_sha256": {name: sha(path) for name, path in sources().items()}}
    save(HERE / "protocol.json", protocol)
    print(json.dumps({"status": protocol["status"], "branches": 128}))


def run():
    p = json.loads((HERE / "protocol.json").read_text())
    assert p["status"] == "FROZEN_BEFORE_W16_PUBLISHED_QUERY"
    assert p["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    assert p["solver_flags"] == FLAGS and p["online_cap_seconds"] == CAP
    inputs = json.loads((HERE / "inputs.json").read_text())
    prefixes = inputs["prefixes"]
    columns, field, curve, source_w, _ = joint.old.experiment.run.source()
    bases = joint.old.experiment.run.bases(field, source_w)[2:]
    rotations = joint.old.experiment.run.prior.ROTATIONS[2:]
    setup_done = time.monotonic_ns()
    q = tuple(inputs["target_q"])
    assert curve.on_curve(q)
    for prefix in prefixes:
        projected = tuple(prefix["projected_sum"])
        residual = curve.add(q, curve.neg(projected))
        assert list(residual) == prefix["residual_q"]
        preimages = joint.old.experiment.run.prior.prior.old.target_preimages(curve, residual)
        assert [list(point) for point in preimages] == prefix["preimages"]
        assert [field.inv(point[0]) for point in preimages] == prefix["target_reciprocals"]
    target_query_done = time.monotonic_ns()
    circuit = joint.old.experiment.run.base.KaratsubaCircuit(
        131, joint.old.experiment.run.LOW_TERMS)
    meta = joint.method.build(
        circuit, field, bases, columns,
        [row["target_reciprocals"] for row in prefixes],
        [row["columns"] for row in prefixes], rotations,
        joint.old.experiment.run.prior.prior.old.method.frob)
    built = time.monotonic_ns()
    formula_path = HERE / "system.xcnf"
    circuit.write(formula_path)
    formula = {"variables": circuit.next_var - 1,
               "cnf_clauses": len(circuit.clauses),
               "native_xor_rows": len(circuit.xors),
               "and_gates": circuit.and_count,
               "bytes": formula_path.stat().st_size,
               "sha256": sha(formula_path)}
    written = time.monotonic_ns()
    if (written - setup_done) / 1e9 >= CAP - 5:
        save(HERE / "result.json", {"status": "CENSORED_FORMULA_BUILD",
                                    "formula": formula, "source_sha256": p["source_sha256"],
                                    "online_seconds": (written - setup_done) / 1e9})
        return
    child_cpu = 0.0
    peak = 0
    stop = None
    with (HERE / "solver.stdout.txt").open("x") as out, \
         (HERE / "solver.stderr.txt").open("x") as err:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(formula_path)],
                                 stdout=out, stderr=err, start_new_session=True)
        proc = psutil.Process(child.pid)
        parent = psutil.Process()
        while child.poll() is None:
            try:
                peak = max(peak, proc.memory_info().rss + parent.memory_info().rss)
                cpu = proc.cpu_times()
                child_cpu = max(child_cpu, cpu.user + cpu.system)
            except psutil.NoSuchProcess:
                pass
            if peak >= RSS_CAP:
                stop = "RSS_CAP"
            elif (time.monotonic_ns() - setup_done) / 1e9 >= CAP - 5:
                stop = "SAFE_WALL_STOP"
            if stop:
                child.terminate()
                break
            time.sleep(.1)
        try:
            child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            stop = (stop or "DRAIN_TIMEOUT") + "_KILLED"
    searched = time.monotonic_ns()
    output = (HERE / "solver.stdout.txt").read_text(errors="replace")
    statuses = [line for line in output.splitlines() if line.startswith("s ")]
    model_lines = sum(line.startswith("v ") for line in output.splitlines())
    selected = None
    group_status = None
    model_check = None
    if statuses == ["s SATISFIABLE"] and model_lines:
        model = joint.old.experiment.run.base.read_model(output, formula["variables"])
        model_check = joint.old.experiment.run.base.check_xcnf(formula_path, model)
        choices = [i for i, wire in enumerate(meta["flags"]) if model[wire]]
        assert len(choices) == 1
        selected = choices[0]
        prefix = prefixes[selected // 4]
        masks = [sum(1 << bit for bit, wire in enumerate(row) if model[wire])
                 for row in meta["masks"]]
        middle = [sum(1 << bit for bit, wire in enumerate(row) if model[wire])
                  for row in meta["middle"]]
        lifted = joint.old.lift.lift(masks, middle, tuple(prefix["residual_q"]),
                                     selected % 4, prefix["columns"])
        save(HERE / "group_lift.json", lifted)
        group_status = lifted["status"]
        if group_status == "GROUP_LIFT_FOUND":
            assert any(curve.add(tuple(prefix["projected_sum"]),
                                 tuple(sol["projected_sum"])) == q
                       for sol in lifted["solutions"])
            status = "GROUP_RELATION_FOUND"
        else:
            status = "SAT_NO_GROUP_LIFT"
    elif stop == "RSS_CAP":
        status = "OOM"
    elif stop == "SAFE_WALL_STOP" or "s INDETERMINATE" in statuses:
        status = "CENSORED_TIME"
    elif statuses == ["s UNSATISFIABLE"]:
        status = "UNSAT_COMPLETE"
    else:
        status = "PRODUCER_OR_SOLVER_FAILURE"
    finished = time.monotonic_ns()
    phases = {"target_query_ns": target_query_done - setup_done,
              "target_PDP_build_ns": built - target_query_done,
              "target_PDP_write_ns": written - built,
              "target_PDP_search_ns": searched - written,
              "target_relation_check_ns": finished - searched,
              "total_online_ns": finished - setup_done}
    assert sum(value for key, value in phases.items() if key != "total_online_ns") == phases["total_online_ns"]
    record = {"status": status, "candidate_id": None, "target_q": list(q),
              "formula": formula, "selected_choice": selected,
              "solver_status_lines": statuses, "model_lines": model_lines,
              "model_check": model_check, "group_lift_status": group_status,
              "stop_reason": stop, "solver_exit_code": child.returncode,
              "phase_ns": phases, "sampled_solver_cpu_seconds": child_cpu,
              "sampled_peak_combined_rss_bytes": peak,
              "source_sha256": p["source_sha256"],
              "output_sha256": {"stdout": sha(HERE / "solver.stdout.txt"),
                                "stderr": sha(HERE / "solver.stderr.txt")}}
    save(HERE / "result.json", record)
    print(json.dumps({"status": status, "online_seconds": phases["total_online_ns"] / 1e9,
                      "solver_cpu_seconds": child_cpu, "peak_rss": peak}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "run"))
    {"freeze": freeze, "run": run}[parser.parse_args().mode]()
