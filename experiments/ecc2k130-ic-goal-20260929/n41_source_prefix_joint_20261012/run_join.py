"""Freeze and run exhaustive N41 prefix-family labels under a local cap."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv"
BINARY = HERE / "join_prefix"
CAP_NS = 30_000_000_000
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open("x") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def freeze():
    panel = json.loads((HERE / "panel.json").read_text())
    cases = [row for row in panel["rows"] if row["depth"] in (3, 4)]
    paths = [Path(__file__), HERE / "join_prefix.cpp", BINARY,
             HERE.parent / "n41_w8_ninepair_join_control_20261012/join9.cpp",
             HERE / "panel.json", HERE / "analysis.json", SOURCE,
             HERE / "compiler.txt"]
    save(HERE / "join_protocol.json", {
        "status": "FROZEN_BEFORE_N41_PREFIX_EXHAUSTIVE_LABELS", "candidate_id": None,
        "cases": [{"label": row["label"], "depth": row["depth"],
                   "prefixes": row["prefixes"]} for row in cases],
        "raw_target_preimage_index": 1, "one_worker": True,
        "per_case_parent_cap_ns": CAP_NS, "combined_rss_cap_bytes": RSS_CAP,
        "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "join_protocol.json").read_text())
    for path, digest in protocol["sources"].items():
        assert sha(path) == digest, path
    parent = psutil.Process()
    receipts = []
    for case in protocol["cases"]:
        label = case["label"]
        stdout = HERE / f"{label}.join.stdout"
        stderr = HERE / f"{label}.join.stderr"
        peak = 0
        stop = None
        start = time.monotonic_ns()
        cmd = [str(BINARY), str(SOURCE), str(case["depth"])] + [str(p) for p in case["prefixes"]]
        with stdout.open("x") as out, stderr.open("x") as err:
            child = subprocess.Popen(cmd, stdout=out, stderr=err)
            process = psutil.Process(child.pid)
            while child.poll() is None:
                try:
                    peak = max(peak, parent.memory_info().rss + process.memory_info().rss)
                    if peak > RSS_CAP:
                        stop = "RSS_CAP"
                except psutil.NoSuchProcess:
                    pass
                if time.monotonic_ns() - start > CAP_NS:
                    stop = "WALL_CAP"
                if stop:
                    child.kill()
                    break
                time.sleep(0.01)
            code = child.wait()
        wall = time.monotonic_ns() - start
        lines = stdout.read_text(errors="replace").splitlines()
        hits = [line for line in lines if line.startswith("HIT ")]
        exhausted = [line for line in lines if line.startswith("EXHAUSTED ")]
        status = ("HIT_PENDING_SAGE" if code == 0 and len(hits) == 1 else
                  "EXACT_MISS" if code == 0 and len(exhausted) == 1 else
                  "BOUNDED_UNKNOWN" if stop else "ERROR")
        receipt = {"label": label, "status": status, "stop_reason": stop,
                   "exit_code": code, "wall_ns": wall, "peak_combined_rss_bytes": peak,
                   "hit": hits[0] if hits else None,
                   "exhausted": exhausted[0] if exhausted else None,
                   "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr)}
        save(HERE / f"{label}.join.receipt.json", receipt)
        receipts.append(receipt)
        print(label, status, round(wall / 1e9, 3), flush=True)
    save(HERE / "join_summary.json", {
        "status": "COMPLETE_N41_PREFIX_EXHAUSTIVE_LABELS", "candidate_id": None,
        "join_protocol_sha256": sha(HERE / "join_protocol.json"),
        "receipts": receipts})


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
