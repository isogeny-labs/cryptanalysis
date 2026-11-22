"""Bounded exact branch enumeration with eight source masks fixed."""

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
BASE = HERE / "all_pair.xcnf"
FLAGS = ("--threads=1", "--maxtime=4", "--zero-exit-status", "--verb=0", "--printsol=1")
PER_SLICE_NS = 5 * 10**9
GLOBAL_NS = 120 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write("\n")


def freeze():
    paths = (Path(__file__), BASE, HERE / "build_result.json", PARENT / "chart.json",
             HERE / "full_pin_audit.json", SOLVER)
    save(HERE / "slice_protocol.json", {
        "status": "FROZEN_BEFORE_ALL_PAIR_BRANCH_SLICES", "candidate_id": None,
        "workers": 1, "branch_patterns": 128, "positive_first": True,
        "per_slice_cap_ns": PER_SLICE_NS, "global_cap_ns": GLOBAL_NS,
        "rss_cap_bytes": RSS_CAP, "flags": FLAGS,
        "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "slice_protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    chart = json.loads((PARENT / "chart.json").read_text())
    build = json.loads((HERE / "build_result.json").read_text())
    wires = build["variants"]["all_pair"]["wire_map"]["root_branches"]
    positive = sum(bit << i for i, bit in enumerate(chart["root_branch_bits"]))
    order = [positive, *(index for index in range(128) if index != positive)]
    temp = HERE / "slice_current.xcnf"
    journal = HERE / "slice_results.jsonl"
    parent = psutil.Process()
    start_all = time.monotonic_ns()
    completed = 0
    with journal.open("x") as log:
        for index in order:
            if time.monotonic_ns() - start_all >= GLOBAL_NS:
                break
            start_write = time.monotonic_ns()
            with BASE.open() as inp, temp.open("x") as out:
                head = inp.readline().split()
                assert head[:2] == ["p", "cnf"]
                variables, rows = map(int, head[2:])
                out.write(f"p cnf {variables} {rows + 7}\n")
                for line in inp:
                    out.write(line)
                for bit, wire in enumerate(wires):
                    out.write(f"{wire if index >> bit & 1 else -wire} 0\n")
            write_ns = time.monotonic_ns() - start_write
            input_sha = sha(temp)
            stdout, stderr = HERE / f"slice_{index:03}.stdout", HERE / f"slice_{index:03}.stderr"
            peak, stop = 0, None
            start = time.monotonic_ns()
            with stdout.open("x") as out, stderr.open("x") as err:
                child = subprocess.Popen([str(SOLVER), *FLAGS, str(temp)], stdout=out, stderr=err)
                proc = psutil.Process(child.pid)
                while child.poll() is None:
                    try:
                        rss = parent.memory_info().rss + proc.memory_info().rss
                        peak = max(peak, rss)
                        if rss > RSS_CAP:
                            stop = "RSS_CAP"
                    except psutil.NoSuchProcess:
                        pass
                    if time.monotonic_ns() - start > PER_SLICE_NS:
                        stop = "SLICE_WALL_CAP"
                    if time.monotonic_ns() - start_all > GLOBAL_NS:
                        stop = "GLOBAL_WALL_CAP"
                    if stop:
                        child.kill()
                        break
                    time.sleep(.025)
                code = child.wait()
            wall_ns = time.monotonic_ns() - start
            lines = stdout.read_text(errors="replace").splitlines()
            terminals = [line for line in lines if line.startswith("s ")]
            terminal = terminals[-1] if terminals else None
            status = ("SAT_PENDING_REPLAY" if terminal == "s SATISFIABLE" else
                      "UNSAT" if terminal == "s UNSATISFIABLE" else "BOUNDED_UNKNOWN")
            row = {"index": index, "status": status, "terminal": terminal,
                   "stop_reason": stop, "exit_code": code,
                   "write_ns": write_ns, "solver_wall_ns": wall_ns,
                   "peak_combined_rss_bytes": peak, "input_sha256": input_sha,
                   "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}
            log.write(json.dumps(row, sort_keys=True) + "\n")
            log.flush()
            temp.unlink()
            completed += 1
            if completed == 1 or completed % 16 == 0:
                print("SLICE", completed, index, status, flush=True)
            if stop == "GLOBAL_WALL_CAP":
                break
    save(HERE / "slice_result.json", {
        "status": "COMPLETE" if completed == 128 else "BOUNDED_PARTIAL",
        "completed": completed, "total": 128, "positive_index": positive,
        "total_wall_ns": time.monotonic_ns() - start_all,
        "journal_sha256": sha(journal),
        "protocol_sha256": sha(HERE / "slice_protocol.json")})
    print("SLICES", completed, flush=True)


def audit():
    protocol = json.loads((HERE / "slice_protocol.json").read_text())
    result = json.loads((HERE / "slice_result.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert result["protocol_sha256"] == sha(HERE / "slice_protocol.json")
    journal = HERE / "slice_results.jsonl"
    assert result["journal_sha256"] == sha(journal)
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    assert len(rows) == result["completed"]
    assert len({row["index"] for row in rows}) == len(rows)
    assert rows[0]["index"] == result["positive_index"]
    counts = {}
    for row in rows:
        index = row["index"]
        assert row["stdout_sha256"] == sha(HERE / f"slice_{index:03}.stdout")
        assert row["stderr_sha256"] == sha(HERE / f"slice_{index:03}.stderr")
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    save(HERE / "slice_audit.json", {
        "status": "PASS_FROZEN_BRANCH_SLICE_RECEIPT_AUDIT",
        "completed": len(rows), "status_counts": counts,
        "result_sha256": sha(HERE / "slice_result.json")})
    print("AUDITED SLICES", len(rows), counts)


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "audit": audit}[sys.argv[1]]()
