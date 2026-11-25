"""Freeze and execute a public, deterministic N41 target-orientation SAT schedule."""
import gzip
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n41_w11_fourpair_orbit_sat_20261019"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
SOURCE = ROOT / "n41_w11_fourpair_public_20261019/join4_input.tsv"
FORMULA = OLD / "orbit41.xcnf"
sys.path.insert(0, str(OLD))
import circuit_orbit as circuit


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def deterministic_setup():
    fields = SOURCE.read_text().splitlines()[1].split()
    assert fields[:2] == ["T", "0"]
    x = int(fields[2])
    reciprocals = [circuit.F.frob(circuit.F.inverse(x), k) for k in range(41)]
    machine, wires, counts = circuit.build(reciprocals, SOURCE)
    assert counts == json.loads((OLD / "orbit_build_result.json").read_text())["counts"]
    with tempfile.TemporaryDirectory() as dirname:
        rebuilt = Path(dirname) / "rebuilt.xcnf"
        machine.write(rebuilt)
        assert sha(rebuilt) == sha(FORMULA)
    return wires["selector"], counts


def freeze():
    assert not (HERE / "protocol.json").exists()
    selector, counts = deterministic_setup()
    protocol = {
        "status": "FROZEN_BEFORE_N41_W11_ORIENTATION_SCHEDULE",
        "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
        "candidate_id": None,
        "public_target": [1936680952394, 910597499030],
        "orientation_order": list(range(41)),
        "selector_wires": selector,
        "circuit_counts": counts,
        "seconds_per_orientation": 13,
        "global_wall_cap_seconds": 590,
        "rss_cap_bytes": 4294967296,
        "worker_count": 1,
        "solver_flags": ["--threads=1", "--maxtime=13", "--zero-exit-status", "--verb=0", "--printsol=1"],
        "sources": {name: {"path": str(path), "sha256": sha(path)} for name, path in {
            "script": Path(__file__), "circuit": OLD / "circuit_orbit.py",
            "formula": FORMULA, "source_input": SOURCE, "solver": SOLVER,
        }.items()},
    }
    (HERE / "protocol.json").write_text(json.dumps(protocol, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": protocol["status"], "selector_wires": selector,
                      "formula_sha256": sha(FORMULA)}, sort_keys=True), flush=True)


def run():
    cfg = json.loads((HERE / "protocol.json").read_text())
    assert cfg["status"] == "FROZEN_BEFORE_N41_W11_ORIENTATION_SCHEDULE"
    assert cfg["worker_count"] == 1 and cfg["orientation_order"] == list(range(41))
    assert not (HERE / "result.json").exists()
    for item in cfg["sources"].values():
        assert sha(item["path"]) == item["sha256"]
    selector, counts = deterministic_setup()
    assert selector == cfg["selector_wires"] and counts == cfg["circuit_counts"]
    header, rest = FORMULA.read_bytes().split(b"\n", 1)
    tag, fmt, vars_, rows = header.split()
    assert (tag, fmt) == (b"p", b"cnf")
    assert int(vars_) == counts["variables"]
    assert int(rows) == counts["clauses"] + counts["xor_rows"]
    protocol_hash = sha(HERE / "protocol.json")
    start = time.monotonic()
    results = []
    status = "SCHEDULE_EXHAUSTED"
    for k in cfg["orientation_order"]:
        if time.monotonic() - start >= cfg["global_wall_cap_seconds"]:
            status = "GLOBAL_WALL_CAP"
            break
        literals = [wire if (k >> bit) & 1 else -wire for bit, wire in enumerate(selector)]
        suffix = b"".join(f"{literal} 0\n".encode() for literal in literals)
        formula_path = HERE / f"orientation_{k:02d}.xcnf"
        formula_path.write_bytes(b" ".join([tag, fmt, vars_, str(int(rows) + 6).encode()]) + b"\n" + rest + suffix)
        output_path = HERE / f"orientation_{k:02d}.stdout.gz"
        error_path = HERE / f"orientation_{k:02d}.stderr.gz"
        cmd = [str(SOLVER), *cfg["solver_flags"], str(formula_path)]
        t0 = time.monotonic()
        peak = 0
        stop = None
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            child = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, cwd=HERE, start_new_session=True)
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak = max(peak, process.memory_info().rss + psutil.Process(os.getpid()).memory_info().rss)
                except psutil.NoSuchProcess:
                    if child.poll() is None:
                        stop = "MONITOR_FAILURE"
                    break
                if peak > cfg["rss_cap_bytes"]:
                    stop = "RSS_CAP"
                    break
                if time.monotonic() - t0 > cfg["seconds_per_orientation"] + 0.5:
                    stop = "ORIENTATION_WALL_CAP"
                    break
                if time.monotonic() - start > cfg["global_wall_cap_seconds"]:
                    stop = "GLOBAL_WALL_CAP"
                    break
                time.sleep(0.02)
            if stop and child.poll() is None:
                child.terminate()
            code = child.wait()
            stdout.seek(0)
            data = stdout.read()
            stderr.seek(0)
            errors = stderr.read()
        with gzip.open(output_path, "wb", compresslevel=9) as stream:
            stream.write(data)
        with gzip.open(error_path, "wb", compresslevel=9) as stream:
            stream.write(errors)
        lines = data.decode(errors="replace").splitlines()
        sat = any(line.strip() == "s SATISFIABLE" for line in lines)
        unsat = any(line.strip() == "s UNSATISFIABLE" for line in lines)
        assert not (sat and unsat)
        result = {"orientation": k, "status": "SAT_MODEL_PENDING_AUDIT" if sat else
                  "UNSAT_SOLVER_STATUS" if unsat else stop or "BOUNDED_UNKNOWN",
                  "wall_seconds": time.monotonic() - t0, "exit_code": code,
                  "peak_combined_rss_bytes": peak, "formula_sha256": sha(formula_path),
                  "stdout_sha256": hashlib.sha256(data).hexdigest(),
                  "stderr_sha256": hashlib.sha256(errors).hexdigest(),
                  "terminal_sat_line": sat, "terminal_unsat_line": unsat}
        results.append(result)
        (HERE / "progress.json").write_text(json.dumps({"protocol_sha256": protocol_hash,
            "orientations": results}, sort_keys=True, indent=2) + "\n")
        print(json.dumps({"orientation": k, "status": result["status"],
                          "wall_seconds": result["wall_seconds"]}, sort_keys=True), flush=True)
        formula_path.unlink()
        if sat:
            status = "SAT_MODEL_PENDING_AUDIT"
            break
        if stop in ("RSS_CAP", "MONITOR_FAILURE", "GLOBAL_WALL_CAP"):
            status = stop
            break
    receipt = {"status": status, "candidate_id": None, "curve_id": cfg["curve_id"],
               "protocol_sha256": protocol_hash, "orientations": results,
               "total_wall_seconds": time.monotonic() - start,
               "solver_sha256": sha(SOLVER), "script_sha256": sha(__file__)}
    (HERE / "result.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": status, "attempts": len(results),
                      "total_wall_seconds": receipt["total_wall_seconds"]}, sort_keys=True), flush=True)


if __name__ == "__main__":
    assert sys.argv[1:] in (["freeze"], ["run"])
    (freeze if sys.argv[1] == "freeze" else run)()
