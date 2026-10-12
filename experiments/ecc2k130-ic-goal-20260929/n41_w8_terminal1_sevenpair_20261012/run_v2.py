"""Freeze and bound the N41 seven-pair first-edge four-sign public join."""

import hashlib
import json
import math
import psutil
import resource
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "n41_w8_sixpair_mitm_20261011"
CAP = 240
RSS = 4 * 1024**3
HITS = 1
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")


def sources():
    return {"runner": Path(__file__), "native_source": HERE / "join7_v2.cpp",
            "native_binary": HERE / "join7_v2", "input": BASE / "join_input.tsv",
            "input_preparer": BASE / "prepare_sage.py",
            "input_protocol": BASE / "prepare_protocol.json",
            "input_receipt": BASE / "prepare_result.json",
            "sage_runtime": BASE / "sage_runtime_info.json",
            "geometry": BASE.parent / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
            "fixture": BASE.parent / "n41_w7_entropy_cubic_20261011/w8/fixture.json"}


def freeze():
    original = json.loads((BASE / "protocol.json").read_text())
    assert original["source_sha256"]["input"] == sha(BASE / "join_input.tsv")
    assert original["eligible_pair_edges"] == 35
    assert original["signed_pair_states_per_slot"] == 140
    assert (HERE / "join7_v2").is_file()
    source_count = 4 * math.perm(34, 6) * 4**6
    mean = Fraction(source_count, 4 * R)
    save("protocol_v2.json", {"status": "FROZEN_N41_SEVEN_PAIR_TERMINAL4",
                           "candidate_id": None,
                           "curve_id": original["curve_id"],
                           "public_target_transported": original["public_target_transported"],
                           "raw_target_preimage": original["raw_target_preimages"][0],
                           "input_rotations": original["rotations"],
                           "seven_pair_rotations": original["rotations"] + [original["rotations"][0]],
                           "terminal_source_law": "slot 6 reuses slot 0 rotation and signed state IDs 0..3, all four signs of the first source edge",
                           "terminal_signed_states": 4,
                           "source_pair_edges": 35,
                           "effective_folded_columns": 70,
                           "source_count_distinct_column_ordered_tuples": str(source_count),
                           "uniform_raw_point_mean_upper_exact": f"{mean.numerator}/{mean.denominator}",
                           "uniform_raw_point_mean_upper_decimal": format(float(mean), ".12g"),
                           "worker_count": 1, "raw_preimage_index": 0,
                           "target_hit_stop": HITS,
                           "parent_wall_cap_seconds": CAP,
                           "combined_rss_cap_bytes": RSS,
                           "compiler": subprocess.check_output(["/usr/bin/clang++", "--version"], text=True).splitlines()[0],
                           "compile_command": "/usr/bin/clang++ -O3 -std=c++17 -Wall -Wextra -pedantic join7_v2.cpp -o join7_v2",
                           "source_sha256": {name: sha(path) for name, path in sources().items()}})
    print("FROZEN_N41_SEVEN_PAIR_TERMINAL4", format(float(mean), ".9g"))


def query():
    protocol = json.loads((HERE / "protocol_v2.json").read_text())
    assert protocol["status"] == "FROZEN_N41_SEVEN_PAIR_TERMINAL4"
    assert protocol["source_sha256"] == {name: sha(path) for name, path in sources().items()}
    outpath, errpath = HERE / "join_v2.stdout.txt", HERE / "join_v2.stderr.txt"
    parent = psutil.Process()
    start = time.monotonic_ns()
    peak, stop = 0, None
    with outpath.open("x") as stdout, errpath.open("x") as stderr:
        child = subprocess.Popen([str(HERE / "join7_v2"), str(BASE / "join_input.tsv")],
                                 stdout=stdout, stderr=stderr)
        process = psutil.Process(child.pid)
        while child.poll() is None:
            try:
                combined = parent.memory_info().rss + process.memory_info().rss
            except psutil.NoSuchProcess:
                combined = parent.memory_info().rss
            peak = max(peak, combined)
            if combined > RSS:
                stop = "RSS_CAP"
                child.kill()
                break
            if time.monotonic_ns() - start > CAP * 10**9:
                stop = "WALL_CAP"
                child.kill()
                break
            time.sleep(0.05)
        code = child.wait()
    end = time.monotonic_ns()
    lines = outpath.read_text().splitlines()
    hits = [line for line in lines if line.startswith("HIT ")]
    complete = [line for line in lines if line.startswith("COMPLETE_HITS ")]
    if stop:
        status = "CENSORED_RSS" if stop == "RSS_CAP" else "CENSORED_TIME"
    elif code == 0 and len(hits) == HITS and len(complete) == 1:
        status = "HITS_PENDING_SAGE_REPLAY"
    elif code == 0 and any(line.startswith("MISS_COMPLETE ") for line in lines):
        status = "COMPLETE_RESTRICTED_SOURCE_SCAN"
    else:
        status = "PRODUCER_FAILURE"
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save("query_result_v2.json", {"status": status, "candidate_id": None,
                               "curve_id": protocol["curve_id"],
                               "public_target_transported": protocol["public_target_transported"],
                               "raw_preimage_index": 0,
                               "source_count_mean_upper": protocol["uniform_raw_point_mean_upper_decimal"],
                               "target_count": 1, "worker_count": 1,
                               "wall_ns_exploratory": end-start,
                               "parent_wall_cap_seconds": CAP,
                               "peak_combined_rss_bytes_sampled": peak,
                               "parent_peak_rss_bytes": rss if sys.platform == "darwin" else rss*1024,
                               "stop_reason": stop, "exit_code": code,
                               "preflight_group_checks_passed": bool(lines and lines[0].startswith("CHECK_PASS 128 ")),
                               "phase_lines": [line for line in lines if line.startswith(("CHECK_PASS ", "LEFT_DONE ", "COMPLETE_HITS ", "MISS_COMPLETE "))],
                               "hit_lines": hits, "stdout_sha256": sha(outpath),
                               "stderr_sha256": sha(errpath),
                               "protocol_sha256": sha(HERE / "protocol_v2.json")})
    print(json.dumps({"status": status, "hits": len(hits),
                      "wall_seconds": (end-start)/1e9, "peak_rss": peak}), flush=True)


if __name__ == "__main__":
    assert len(sys.argv) == 2 and sys.argv[1] in ("freeze", "query")
    {"freeze": freeze, "query": query}[sys.argv[1]]()
