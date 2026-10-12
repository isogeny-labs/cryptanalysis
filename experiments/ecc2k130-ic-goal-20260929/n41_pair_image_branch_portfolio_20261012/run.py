"""Eight exact root slices of the N41 pair-output BDD public formula."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_pair_image_bdd_20261012"
BASE = PARENT / "public.xcnf"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=18", "--zero-exit-status", "--verb=1", "--printsol=1")
PER_SLICE_NS = 20 * 10**9
GLOBAL_NS = 190 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def freeze():
    build = json.loads((PARENT / "build_result.json").read_text())
    assert sha(BASE) == build["formula_sha256"]
    wires = build["root_branch_wires"]
    assert len(wires) == 3
    paths = (Path(__file__), BASE, PARENT / "build_result.json",
             PARENT / "output_values.json", PARENT / "census_result.json",
             PARENT / "control_audit.json", SOLVER)
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_N41_OUTPUT_BDD_BRANCH_PORTFOLIO",
        "candidate_id": None, "workers": 1,
        "pair_outputs_pinned": 0, "root_branch_wires": wires,
        "branch_order": list(range(8)), "flags": FLAGS,
        "per_slice_wall_cap_ns": PER_SLICE_NS, "total_wall_cap_ns": GLOBAL_NS,
        "rss_cap_bytes": RSS_CAP,
        "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    wires = protocol["root_branch_wires"]
    temp, journal = HERE / "current_slice.xcnf", HERE / "slices.jsonl"
    parent = psutil.Process()
    start_all = time.monotonic_ns()
    completed, hit = 0, None
    with journal.open("x") as log:
        for index in protocol["branch_order"]:
            if time.monotonic_ns() - start_all >= GLOBAL_NS:
                break
            start_write = time.monotonic_ns()
            with BASE.open() as inp, temp.open("x") as out:
                head = inp.readline().split()
                assert head[:2] == ["p", "cnf"]
                variables, rows = map(int, head[2:])
                out.write(f"p cnf {variables} {rows + 3}\n")
                for line in inp:
                    out.write(line)
                for bit, wire in enumerate(wires):
                    out.write(f"{wire if index >> bit & 1 else -wire} 0\n")
            write_ns = time.monotonic_ns() - start_write
            input_sha = sha(temp)
            stdout, stderr = HERE / f"slice_{index}.stdout", HERE / f"slice_{index}.stderr"
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
                      "UNSAT" if terminal == "s UNSATISFIABLE" else
                      "BOUNDED_UNKNOWN" if stop or terminal in (None, "s INDETERMINATE") else
                      "PRODUCER_FAILURE")
            row = {"index": index, "status": status, "terminal": terminal,
                   "stop_reason": stop, "exit_code": code,
                   "write_ns": write_ns, "solver_wall_ns": wall_ns,
                   "peak_combined_rss_bytes": peak, "input_sha256": input_sha,
                   "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
                   "restart_rows": sum(line.startswith("c rst") for line in lines)}
            log.write(json.dumps(row, sort_keys=True) + "\n")
            log.flush()
            temp.unlink()
            completed += 1
            print("SLICE", index, status, round(wall_ns / 1e9, 3), flush=True)
            if status == "SAT_PENDING_REPLAY":
                hit = index
                break
            if stop == "GLOBAL_WALL_CAP":
                break
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    status = ("SAT_PENDING_REPLAY" if hit is not None else
              "COMPLETE_UNSAT" if completed == 8 and all(row["status"] == "UNSAT" for row in rows) else
              "BOUNDED_UNKNOWN")
    save(HERE / "result.json", {
        "status": status, "completed": completed, "total": 8, "hit_index": hit,
        "total_wall_ns": time.monotonic_ns() - start_all,
        "journal_sha256": sha(journal), "protocol_sha256": sha(HERE / "protocol.json")})
    print("PORTFOLIO", completed, status, flush=True)


def audit():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["journal_sha256"] == sha(HERE / "slices.jsonl")
    rows = [json.loads(line) for line in (HERE / "slices.jsonl").read_text().splitlines()]
    assert len(rows) == result["completed"]
    assert [row["index"] for row in rows] == list(range(len(rows)))
    counts = {}
    for row in rows:
        index = row["index"]
        stdout, stderr = HERE / f"slice_{index}.stdout", HERE / f"slice_{index}.stderr"
        assert row["stdout_sha256"] == sha(stdout)
        assert row["stderr_sha256"] == sha(stderr)
        lines = stdout.read_text(errors="replace").splitlines()
        terminals = [line for line in lines if line.startswith("s ")]
        assert (terminals[-1] if terminals else None) == row["terminal"]
        assert sum(line.startswith("c rst") for line in lines) == row["restart_rows"]
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    save(HERE / "audit.json", {
        "status": "PASS_FROZEN_N41_OUTPUT_BDD_BRANCH_RECEIPT_AUDIT",
        "portfolio_status": result["status"], "completed": len(rows),
        "status_counts": counts, "result_sha256": sha(HERE / "result.json")})
    print("AUDITED", len(rows), counts)


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "audit": audit}[sys.argv[1]]()
