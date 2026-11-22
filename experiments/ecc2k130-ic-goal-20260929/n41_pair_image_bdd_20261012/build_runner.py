"""Frozen one-worker 4-GiB bound for the output-first BDD construction."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
WALL_NS = 180 * 10**9
RSS_CAP = 4 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    with path.open("x") as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write("\n")


def freeze():
    paths = (Path(__file__), HERE / "build.py", HERE / "census_result.json",
             HERE / "output_values.json",
             GOAL / "n131_w18_allseed_fourpair_20261012/fourpair_v2.py",
             GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/pairs.tsv",
             GOAL / "n41_w8_tenpair_functional_20261012/build.py",
             GOAL / "n41_w8_tenpair_functional_20261012/run.py",
             GOAL / "n41_allseed_fourpair_forward_20261012/chart.json")
    save(HERE / "build_protocol.json", {
        "status": "FROZEN_BEFORE_EXACT_PAIR_BDD_BUILD", "candidate_id": None,
        "workers": 1, "wall_cap_ns": WALL_NS, "rss_cap_bytes": RSS_CAP,
        "command": [sys.executable, str(HERE / "build.py"), "construct"],
        "sources": {str(path): sha(path) for path in paths}})


def run():
    protocol = json.loads((HERE / "build_protocol.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    stdout, stderr = HERE / "build.stdout", HERE / "build.stderr"
    parent, peak, stop = psutil.Process(), 0, None
    start = time.monotonic_ns()
    with stdout.open("x") as out, stderr.open("x") as err:
        child = subprocess.Popen(protocol["command"], stdout=out, stderr=err)
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
    status = ("PASS_BUILT" if code == 0 and (HERE / "build_result.json").exists() else
              "BOUNDED_RESOURCE" if stop else "PRODUCER_FAILURE")
    save(HERE / "build_receipt.json", {
        "status": status, "stop_reason": stop, "exit_code": code,
        "wall_ns": time.monotonic_ns() - start,
        "peak_combined_rss_bytes": peak,
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "formula_sha256": sha(HERE / "public.xcnf") if (HERE / "public.xcnf").exists() else None,
        "build_result_sha256": sha(HERE / "build_result.json") if (HERE / "build_result.json").exists() else None,
        "protocol_sha256": sha(HERE / "build_protocol.json")})
    print(status, peak, flush=True)


def audit():
    protocol = json.loads((HERE / "build_protocol.json").read_text())
    receipt = json.loads((HERE / "build_receipt.json").read_text())
    assert all(sha(path) == digest for path, digest in protocol["sources"].items())
    assert receipt["protocol_sha256"] == sha(HERE / "build_protocol.json")
    assert receipt["stdout_sha256"] == sha(HERE / "build.stdout")
    assert receipt["stderr_sha256"] == sha(HERE / "build.stderr")
    if receipt["status"] == "PASS_BUILT":
        result = json.loads((HERE / "build_result.json").read_text())
        assert result["status"] == "PASS_N41_OUTPUT_BDD_CONSTRUCTED_ASSIGNMENT"
        assert receipt["formula_sha256"] == result["formula_sha256"]
        assert receipt["build_result_sha256"] == sha(HERE / "build_result.json")
    save(HERE / "build_audit.json", {
        "status": "PASS_FROZEN_PAIR_BDD_BUILD_RECEIPT_AUDIT",
        "build_status": receipt["status"], "receipt_sha256": sha(HERE / "build_receipt.json")})
    print("AUDITED", receipt["status"])


if __name__ == "__main__":
    {"freeze": freeze, "run": run, "audit": audit}[sys.argv[1]]()
