#!/usr/bin/env python3
"""Rebuild and replay the smoothness-stage comparison on this checkout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def command(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def summarize():
    rows = [json.loads(x) for x in (HERE / "samples.jsonl").read_text().splitlines()]
    output = []
    for metadata in (r for r in rows if "kind" in r):
        samples = [r for r in rows if r["workload"] == metadata["workload"] and "repeat" in r]
        result = dict(metadata)
        for metric in ("seconds", "cpu_seconds"):
            ratios = []
            for repeat in sorted({r["repeat"] for r in samples}):
                pair = {r["optimized"]: r for r in samples if r["repeat"] == repeat}
                ratios.append(pair[0][metric] / pair[1][metric])
            result[metric] = {
                "paired_ratios": ratios,
                "median_reference_over_optimized": statistics.median(ratios),
                "min": min(ratios), "max": max(ratios),
                "reference_median": statistics.median(r[metric] for r in samples if not r["optimized"]),
                "optimized_median": statistics.median(r[metric] for r in samples if r["optimized"]),
            }
        output.append(result)
    (HERE / "summary.json").write_text(json.dumps({
        "classification": "exploratory shared-host stage diagnostic",
        "tier_0_or_1_gate": "not established",
        "promoted_wall_speedup": None,
        "workloads": output,
    }, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=Path("/tmp/cryptanalysis-ic-native-20261115"))
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    if args.summarize_only:
        summarize()
        return
    build = args.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cmake", "-S", str(ROOT), "-B", str(build), "-DCA_CUPQC=OFF",
                    "-DCA_WERROR=ON", "-DCA_BUILD_SHARED=OFF", "-DCA_BUILD_TOOLS=OFF"], check=True)
    subprocess.run(["cmake", "--build", str(build), "-j", "3", "--target", "cryptanalysis_static"], check=True)
    cc = os.environ.get("CC", "cc")
    compile_args = [cc, "-O3", "-std=c11", "-I" + str(ROOT / "include"), "-I" + str(ROOT / "src"),
                    str(HERE / "bench.c"), str(build / "libcryptanalysis.a"), "-lm", "-lpthread",
                    "-o", str(build / "bench")]
    subprocess.run(compile_args, check=True)
    sources = list((ROOT / "src").glob("*.[ch]")) + list((ROOT / "include/cryptanalysis").glob("*.h"))
    sources += [HERE / name for name in ("bench.c", "reference.h", "run.py")]
    receipt = {
        "started_unix": time.time(), "platform": platform.platform(), "machine": platform.machine(),
        "compiler": command([cc, "--version"]), "compile_args": compile_args,
        "checkout_head": command(["git", "rev-parse", "HEAD"]),
        "reference_commit": "9f47ea93e0",
        "reference_scope": "trial_factor body from src/indexcalc.c before optimization",
        "load_average_start": os.getloadavg(), "logical_cpus": os.cpu_count(),
        "isolation": "shared local host; no affinity, frequency, IRQ or memory isolation",
        "backend": "physical Apple ARM64 CPU" if platform.system() == "Darwin" and platform.machine() == "arm64" else platform.machine(),
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "binary_sha256": hashlib.sha256((build / "bench").read_bytes()).hexdigest(),
        "seed": "0x1c20261115", "inputs_per_workload": 65536, "repeats": 9,
        "batches_per_sample": 4,
        "timing_boundary": "complete trial_factor calls with relation writes and checksum; descriptor/input construction and correctness checks excluded",
    }
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    with (HERE / "samples.jsonl").open("w") as f:
        subprocess.run([str(build / "bench")], stdout=f, check=True)
    receipt.update(finished_unix=time.time(), load_average_end=os.getloadavg())
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    summarize()


if __name__ == "__main__":
    main()
