"""Frozen constructed-target oracle-hint profile for the ten-pair circuit.

The hints are true internal point-sum reciprocals. They measure how much
joint partial-sum information would have to be produced by a future gate;
they are deliberately not available to an ordinary public-point query.
"""

import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_tenpair_binary_frob_20261012"
sys.path.insert(0, str(SOURCE))
import ten  # noqa: E402

ARMS = (0, 1, 2, 4)
CAP_SECONDS = 90
RSS_CAP = 4 * 1024**3
RAW_HASH = "68d25f14df34ff8eff90b759e99e77321276e4face1d3b8c58fd54230da6f401"
SOLVER_FLAGS = ("--threads=1", "--maxtime=85", "--zero-exit-status", "--verb=1", "--printsol=1")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def freeze():
    assert ten.base.SOLVER.is_file()
    fixture = json.loads((SOURCE / "control_fixture.json").read_text())
    assert len(fixture["selected"]) == 10
    parent = json.loads((SOURCE / "archive_receipt.json").read_text())
    assert parent["formulas"]["control"]["raw_sha256"] == RAW_HASH
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_HINT_PROFILE", "candidate_id": None,
        "curve_id": "EC1N131Ckb1heb5f1998f20b",
        "target_law": "constructed ten-pair control point, not ordinary public point",
        "arms_bottom_node_count": ARMS, "bottom_tree_nodes": list(ten.TREE[:4]),
        "hint_law": "exact reciprocal bits of the first k disjoint bottom point sums",
        "cap_seconds_per_arm": CAP_SECONDS, "rss_cap_bytes": RSS_CAP,
        "worker_count": 1, "solver_flags": SOLVER_FLAGS,
        "source_hashes": {name: sha(SOURCE / name) for name in
                          ("ten.py", "control_fixture.json", "control_result.json",
                           "control.xcnf.gz", "archive_receipt.json")},
        "solver_sha256": sha(ten.base.SOLVER),
        "runner_sha256": sha(__file__), "source_raw_hash": RAW_HASH,
    })


def build_hints():
    fixture = json.loads((SOURCE / "control_fixture.json").read_text())
    prior = json.loads((ten.NINE / "control_fixture.json").read_text())
    points = ten.witness_points(prior) + [tuple(fixture["last_pair_point"])]
    assert len(points) == 10
    reciprocals = []
    for left, right in ten.TREE[:4]:
        point = ten.independent.point_add(points[left], points[right])
        assert point is not None and point[0] != 0
        reciprocals.append(ten.independent.inverse(point[0]))
    rows = ten.orbit9.orbit_rows(ten.orbit9.constructed_preimages(fixture["raw_target"]))
    _, root, nodes = ten.base.source_domain()
    circuit, wires = ten.build([row["standard_reciprocal"] for row in rows], root, nodes)
    assert len(wires["intermediates"]) == 8
    return circuit, wires, reciprocals


def write_variant(raw, wires, reciprocals, count, path):
    header, tail = raw.split(b"\n", 1)
    parts = header.split()
    assert parts[:2] == [b"p", b"cnf"]
    units = []
    for bits, value in zip(wires["intermediates"][:count], reciprocals[:count]):
        for bit, wire in enumerate(bits):
            units.append(f"{wire if value >> bit & 1 else -wire} 0\n".encode())
    new_header = f"p cnf {int(parts[2])} {int(parts[3]) + len(units)}\n".encode()
    payload = new_header + tail + b"".join(units)
    path.write_bytes(payload)
    return {"unit_clauses": len(units), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert protocol["status"] == "FROZEN_BEFORE_HINT_PROFILE"
    assert protocol["runner_sha256"] == sha(__file__)
    assert protocol["solver_sha256"] == sha(ten.base.SOLVER)
    assert all(sha(SOURCE / name) == digest for name, digest in
               protocol["source_hashes"].items())
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as inp:
        raw = inp.read()
    assert hashlib.sha256(raw).hexdigest() == RAW_HASH
    circuit, wires, reciprocals = build_hints()
    regenerated = HERE / "regenerated.xcnf"
    circuit.write(regenerated)
    assert sha(regenerated) == RAW_HASH
    regenerated.unlink()
    results = []
    for count in ARMS:
        path = HERE / f"hint_{count}.xcnf"
        formula = write_variant(raw, wires, reciprocals, count, path)
        stdout_path, stderr_path = HERE / f"hint_{count}.stdout", HERE / f"hint_{count}.stderr"
        parent = psutil.Process()
        peak, stop = 0, None
        start = time.monotonic_ns()
        with stdout_path.open("x") as stdout, stderr_path.open("x") as stderr:
            proc = subprocess.Popen([str(ten.base.SOLVER), *SOLVER_FLAGS, str(path)],
                                    stdout=stdout, stderr=stderr)
            child = psutil.Process(proc.pid)
            while proc.poll() is None:
                try:
                    rss = parent.memory_info().rss + child.memory_info().rss
                    peak = max(peak, rss)
                    if rss > RSS_CAP:
                        stop = "RSS_CAP"
                except psutil.NoSuchProcess:
                    pass
                if (time.monotonic_ns() - start) / 1e9 > CAP_SECONDS:
                    stop = "WALL_CAP"
                if stop:
                    proc.kill()
                    break
                time.sleep(0.025)
            exit_code = proc.wait()
        elapsed = time.monotonic_ns() - start
        lines = stdout_path.read_text(errors="replace").splitlines()
        terminal = [line for line in lines if line.startswith("s ")]
        status = ("SAT" if terminal and terminal[-1] == "s SATISFIABLE" else
                  "UNSAT" if terminal and terminal[-1] == "s UNSATISFIABLE" else
                  "BOUNDED_UNKNOWN")
        # Preserve the exact query input as deterministic gzip; free raw space.
        archive = path.with_suffix(".xcnf.gz")
        with archive.open("xb") as out:
            with gzip.GzipFile(fileobj=out, mode="wb", filename="", mtime=0, compresslevel=6) as gz:
                gz.write(path.read_bytes())
        path.unlink()
        row = {"bottom_nodes_fixed": count, "status": status,
               "solver_terminal": terminal[-1] if terminal else None,
               "stop_reason": stop, "exit_code": exit_code,
               "solver_wall_ns": elapsed, "peak_combined_rss_bytes": peak,
               "formula": formula, "formula_gzip_sha256": sha(archive),
               "stdout_sha256": sha(stdout_path), "stderr_sha256": sha(stderr_path),
               "restart_rows": sum(line.startswith("c rst") for line in lines)}
        results.append(row)
        print(json.dumps({k: row[k] for k in ("bottom_nodes_fixed", "status", "solver_wall_ns", "restart_rows")}), flush=True)
    save(HERE / "result.json", {"status": "COMPLETE_CONSTRUCTED_HINT_PROFILE",
                                "protocol_sha256": sha(HERE / "protocol.json"),
                                "raw_parent_sha256": RAW_HASH,
                                "bottom_reciprocals": reciprocals,
                                "arms": results})


def verify():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert sha(HERE / "protocol.json") == result["protocol_sha256"]
    assert result["raw_parent_sha256"] == RAW_HASH
    assert protocol["runner_sha256"] == sha(__file__)
    with gzip.open(SOURCE / "control.xcnf.gz", "rb") as inp:
        raw = inp.read()
    assert hashlib.sha256(raw).hexdigest() == RAW_HASH
    circuit, wires, reciprocals = build_hints()
    assert result["bottom_reciprocals"] == reciprocals
    for count, row in zip(ARMS, result["arms"]):
        assert row["bottom_nodes_fixed"] == count
        path = HERE / f"hint_{count}.xcnf"
        details = write_variant(raw, wires, reciprocals, count, path)
        assert details == row["formula"]
        with gzip.open(HERE / f"hint_{count}.xcnf.gz", "rb") as inp:
            assert hashlib.sha256(inp.read()).hexdigest() == details["sha256"]
        path.unlink()
        assert sha(HERE / f"hint_{count}.stdout") == row["stdout_sha256"]
        assert sha(HERE / f"hint_{count}.stderr") == row["stderr_sha256"]
        lines = (HERE / f"hint_{count}.stdout").read_text(errors="replace").splitlines()
        assert sum(line.startswith("c rst") for line in lines) == row["restart_rows"]
        assert row["peak_combined_rss_bytes"] < RSS_CAP
        assert row["status"] in ("SAT", "BOUNDED_UNKNOWN")
    print("PASS_N131_TENPAIR_CONSTRUCTED_HINT_PROFILE", len(result["arms"]))


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "verify": verify}[sys.argv[1]]()
