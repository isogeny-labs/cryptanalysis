#!/usr/bin/env python3
"""Run the frozen native public-point join with an auditable resource cap."""

import hashlib
import json
import resource
import subprocess
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "n41_w8_sixpair_mitm_20261011" / "join_input.tsv"
EXPECTED = {
    "join9.cpp": "b0a74e93f5daf4f66c22e866c6594b7e6e3e4df024cba2989e4df7e1ac5129db",
    "join9": "b13c1d0cadbffe19a11131f1107af68260bcbb12247d4f542d5e31c61e494902",
    "input": "1f99b78210c3ec6c30945f3a9d261c1fd58cbb3a509e3a050fb5bdd4a75f06dd",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    paths = {"join9.cpp": HERE / "join9.cpp", "join9": HERE / "join9", "input": INPUT}
    for name, path in paths.items():
        actual = digest(path)
        if actual != EXPECTED[name]:
            raise RuntimeError(f"{name} SHA-256 mismatch: {actual}")
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic_ns()
    forced_status = None
    peak_sampled_rss = 0
    with (HERE / "stdout.log").open("wb") as out, (HERE / "stderr.log").open("wb") as err:
        proc = subprocess.Popen([str(HERE / "join9"), str(INPUT)],
                                cwd=HERE, stdout=out, stderr=err)
        while proc.poll() is None:
            if (time.monotonic_ns() - start) / 1e9 >= 180:
                forced_status = "TIMEOUT"
                proc.kill()
                break
            sampled = subprocess.run(["ps", "-o", "rss=", "-p", str(proc.pid)],
                                     text=True, capture_output=True, check=False)
            if sampled.returncode == 0 and sampled.stdout.strip():
                rss_bytes = int(sampled.stdout.strip()) * 1024
                peak_sampled_rss = max(peak_sampled_rss, rss_bytes)
                if rss_bytes > 4 * 1024**3:
                    forced_status = "RSS_LIMIT_SAMPLED"
                    proc.kill()
                    break
            time.sleep(0.2)
        exit_code = proc.wait()
    end = time.monotonic_ns()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    stdout = (HERE / "stdout.log").read_text()
    status = forced_status or (
        "HIT" if "COMPLETE_HITS 1 " in stdout and exit_code == 0 else
        "MISS_COMPLETE" if "MISS_COMPLETE " in stdout and exit_code == 0 else "ERROR")
    receipt = {
        "status": status, "exit_code": exit_code, "wall_seconds": (end - start) / 1e9,
        "child_user_seconds": after.ru_utime - before.ru_utime,
        "child_system_seconds": after.ru_stime - before.ru_stime,
        "child_maxrss_raw": after.ru_maxrss,
        "peak_sampled_rss_bytes": peak_sampled_rss,
        "resource_cap": {"workers": 1, "wall_seconds": 180,
                         "sampled_rss_limit_bytes": 4 * 1024**3,
                         "rss_sample_period_seconds": 0.2},
        "sha256": EXPECTED,
    }
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
