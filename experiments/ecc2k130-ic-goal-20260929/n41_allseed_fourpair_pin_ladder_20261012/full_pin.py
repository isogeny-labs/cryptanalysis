"""Fully pinned source and root diagnostic derived from the frozen all-pair XCNF."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "n41_allseed_fourpair_forward_20261012"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=30", "--zero-exit-status", "--verb=1", "--printsol=1")
WALL_NS = 35 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, sort_keys=True, indent=2)
        stream.write("\n")


def construct():
    build = json.loads((HERE / "build_result.json").read_text())
    chart = json.loads((PARENT / "chart.json").read_text())
    wires = build["variants"]["all_pair"]["wire_map"]["root_branches"]
    bits = chart["root_branch_bits"]
    assert len(wires) == len(bits) == 7
    source, output = HERE / "all_pair.xcnf", HERE / "all_pair_branch.xcnf"
    with source.open() as inp, output.open("x") as out:
        head = inp.readline().split()
        assert head[:2] == ["p", "cnf"]
        variables, rows = map(int, head[2:])
        out.write(f"p cnf {variables} {rows + 7}\n")
        for line in inp:
            out.write(line)
        for wire, bit in zip(wires, bits):
            out.write(f"{wire if bit else -wire} 0\n")
    save(HERE / "full_pin_build.json", {
        "status": "PASS_FULL_PRIMARY_PIN_CONSTRUCTED",
        "pinned_source_masks": 8, "pinned_root_bits": 7,
        "formula_sha256": sha(output), "source_formula_sha256": sha(source),
        "variables": variables, "rows": rows + 7})


def freeze():
    paths = (Path(__file__), HERE / "all_pair.xcnf", HERE / "all_pair_branch.xcnf",
             HERE / "build_result.json", HERE / "full_pin_build.json",
             PARENT / "chart.json", PARENT / "audit_result.json", SOLVER)
    save(HERE / "full_pin_protocol.json", {
        "status": "FROZEN_BEFORE_FULL_PRIMARY_PIN_CONTROL", "candidate_id": None,
        "workers": 1, "wall_cap_ns": WALL_NS, "rss_cap_bytes": RSS_CAP,
        "flags": FLAGS, "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "full_pin_protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    stdout, stderr = HERE / "full_pin.stdout", HERE / "full_pin.stderr"
    parent, peak, stop = psutil.Process(), 0, None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen([str(SOLVER), *FLAGS, str(HERE / "all_pair_branch.xcnf")],
                                 stdout=out, stderr=err)
        proc = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                rss = parent.memory_info().rss + proc.memory_info().rss
                peak = max(peak, rss)
                if rss > RSS_CAP:
                    stop = "RSS_CAP"
            except psutil.NoSuchProcess:
                pass
            if time.monotonic_ns() - start > WALL_NS:
                stop = "WALL_CAP"
            if stop:
                child.kill()
                break
            time.sleep(.025)
        code = child.wait()
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    terminal = terminals[-1] if terminals else None
    status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
              "UNSAT" if terminal == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
    save(HERE / "full_pin_result.json", {
        "status": status, "terminal": terminal, "stop_reason": stop,
        "exit_code": code, "wall_ns": time.monotonic_ns() - start,
        "peak_combined_rss_bytes": peak,
        "restart_rows": sum(line.startswith("c rst") for line in lines),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "protocol_sha256": sha(HERE / "full_pin_protocol.json")})
    print("full_pin", status, flush=True)


def audit():
    protocol = json.loads((HERE / "full_pin_protocol.json").read_text())
    result = json.loads((HERE / "full_pin_result.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert result["protocol_sha256"] == sha(HERE / "full_pin_protocol.json")
    stdout, stderr = HERE / "full_pin.stdout", HERE / "full_pin.stderr"
    assert result["stdout_sha256"] == sha(stdout)
    assert result["stderr_sha256"] == sha(stderr)
    lines = stdout.read_text(errors="replace").splitlines()
    terminals = [line for line in lines if line.startswith("s ")]
    assert (terminals[-1] if terminals else None) == result["terminal"]
    checked = None
    if result["status"] == "SAT_PENDING_REPLAY":
        assignment = {}
        for line in lines:
            if line.startswith("v "):
                for word in line.split()[1:]:
                    literal = int(word)
                    if literal:
                        assert abs(literal) not in assignment
                        assignment[abs(literal)] = literal > 0
        with (HERE / "all_pair_branch.xcnf").open() as stream:
            head = stream.readline().split()
            variables, rows = map(int, head[2:])
            assert set(assignment) == set(range(1, variables + 1))
            count = 0
            for line in stream:
                parts = line.split()
                is_xor = parts[0] == "x"
                lits = list(map(int, parts[1 if is_xor else 0:-1]))
                assert parts[-1] == "0" and lits
                values = [assignment[abs(lit)] == (lit > 0) for lit in lits]
                assert (sum(values) & 1) if is_xor else any(values)
                count += 1
            assert count == rows
        checked = {"variables": variables, "rows": count}
    save(HERE / "full_pin_audit.json", {
        "status": "PASS_FULL_PRIMARY_PIN_RECEIPT_AUDIT",
        "recorded_status": result["status"], "model_check": checked,
        "result_sha256": sha(HERE / "full_pin_result.json")})
    print("full_pin AUDITED", result["status"])


if __name__ == "__main__":
    {"construct": construct, "freeze": freeze, "run": run, "audit": audit}[sys.argv[1]]()
