"""One-worker branch-first portfolio for an unpinned N41 public point."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
PARENT = GOAL / "n41_allseed_fourpair_forward_20261012"
LADDER = GOAL / "n41_allseed_fourpair_pin_ladder_20261012"
BASE = PARENT / "n41_public.xcnf"
SOLVER = Path("/opt/homebrew/bin/cryptominisat5")
FLAGS = ("--threads=1", "--maxtime=1", "--zero-exit-status", "--verb=0", "--printsol=1")
PER_SLICE_NS = 1_250_000_000
GLOBAL_NS = 190_000_000_000
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write("\n")


def validate_wire_map():
    parent = json.loads((PARENT / "build_result.json").read_text())
    ladder = json.loads((LADDER / "build_result.json").read_text())
    wires = ladder["variants"]["all_pair"]["wire_map"]["root_branches"]
    mask_wires = ladder["variants"]["all_pair"]["wire_map"]["mask_bits"]
    assert len(wires) == 7
    assert sha(BASE) == parent["formula_sha256"]
    with BASE.open() as original, (LADDER / "all_pair.xcnf").open() as pinned:
        head0, head1 = original.readline().split(), pinned.readline().split()
        assert head0[:2] == head1[:2] == ["p", "cnf"]
        variables, rows = map(int, head0[2:])
        pinned_variables, pinned_rows = map(int, head1[2:])
        assert pinned_variables == variables == parent["variables"]
        assert pinned_rows == rows + 64
        for _ in range(parent["cnf_clauses"]):
            assert original.readline() == pinned.readline()
        chart = json.loads((PARENT / "chart.json").read_text())
        expected_pins = [f"{wire if mask >> bit & 1 else -wire} 0\n"
                         for bits, mask in zip(mask_wires, chart["masks"])
                         for bit, wire in enumerate(bits)]
        assert [pinned.readline() for _ in range(64)] == expected_pins
        for _ in range(parent["native_xor_rows"]):
            assert original.readline() == pinned.readline()
        assert not original.readline() and not pinned.readline()
    return wires, variables, rows


def freeze():
    wires, variables, rows = validate_wire_map()
    fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json").read_text())
    assert fixture["target_reciprocal"] == json.loads((PARENT / "build_result.json").read_text())["metadata"]["target_reciprocal"]
    paths = (Path(__file__), BASE, PARENT / "build_result.json", LADDER / "build_result.json",
             LADDER / "all_pair.xcnf", SOLVER,
             GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/control_fixture.json")
    save(HERE / "protocol.json", {
        "status": "FROZEN_BEFORE_UNPINNED_N41_BRANCH_PORTFOLIO",
        "candidate_id": None, "workers": 1, "target": fixture["public_target"],
        "target_reciprocal": fixture["target_reciprocal"],
        "source_masks_pinned": 0, "root_branches_pinned_per_slice": 7,
        "branch_order": list(range(128)), "root_branch_wires": wires,
        "base_variables": variables, "base_rows": rows,
        "per_slice_wall_cap_ns": PER_SLICE_NS, "total_wall_cap_ns": GLOBAL_NS,
        "rss_cap_bytes": RSS_CAP, "flags": FLAGS,
        "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    wires = protocol["root_branch_wires"]
    temp = HERE / "current_slice.xcnf"
    journal = HERE / "slices.jsonl"
    parent = psutil.Process()
    start_all = time.monotonic_ns()
    completed = 0
    hit = None
    with journal.open("x") as log:
        for index in protocol["branch_order"]:
            if time.monotonic_ns() - start_all >= GLOBAL_NS:
                break
            start_write = time.monotonic_ns()
            with BASE.open() as inp, temp.open("x") as out:
                head = inp.readline().split()
                variables, rows = map(int, head[2:])
                assert variables == protocol["base_variables"] and rows == protocol["base_rows"]
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
            if completed == 1 or completed % 16 == 0 or status == "SAT_PENDING_REPLAY":
                print("SLICE", completed, index, status, flush=True)
            if status == "SAT_PENDING_REPLAY":
                hit = index
                break
            if stop == "GLOBAL_WALL_CAP":
                break
    save(HERE / "result.json", {
        "status": "SAT_PENDING_REPLAY" if hit is not None else
                  "COMPLETE_UNSAT" if completed == 128 and
                  all(json.loads(line)["status"] == "UNSAT" for line in journal.read_text().splitlines()) else
                  "BOUNDED_UNKNOWN",
        "completed": completed, "total": 128, "hit_index": hit,
        "total_wall_ns": time.monotonic_ns() - start_all,
        "journal_sha256": sha(journal), "protocol_sha256": sha(HERE / "protocol.json")})
    print("PORTFOLIO", completed, hit, flush=True)


def audit():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert result["journal_sha256"] == sha(HERE / "slices.jsonl")
    rows = [json.loads(line) for line in (HERE / "slices.jsonl").read_text().splitlines()]
    assert len(rows) == result["completed"]
    assert [row["index"] for row in rows] == protocol["branch_order"][:len(rows)]
    counts = {}
    for row in rows:
        index = row["index"]
        stdout, stderr = HERE / f"slice_{index:03}.stdout", HERE / f"slice_{index:03}.stderr"
        assert row["stdout_sha256"] == sha(stdout)
        assert row["stderr_sha256"] == sha(stderr)
        terminals = [line for line in stdout.read_text(errors="replace").splitlines() if line.startswith("s ")]
        assert (terminals[-1] if terminals else None) == row["terminal"]
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    save(HERE / "audit.json", {
        "status": "PASS_FROZEN_UNPINNED_PORTFOLIO_RECEIPT_AUDIT",
        "portfolio_status": result["status"], "completed": len(rows), "status_counts": counts,
        "result_sha256": sha(HERE / "result.json")})
    print("AUDITED", len(rows), counts)


if __name__ == "__main__":
    action = sys.argv[1]
    {"freeze": freeze, "run": run, "audit": audit}[action]()
