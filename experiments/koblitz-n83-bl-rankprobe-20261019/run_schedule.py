#!/usr/bin/env python3
"""Execute one phase of the frozen schedule, one pinned process at a time, and keep every row.

`koblitz-n83-rankprobe-20261019`'s `run_schedule.py` (the same counters, noise
gate, time guard, ledger, fsync and per-serial stdout/stderr files), with two
changes:

* the schedule has two phases (`schedule.json` segment `phase`). `--phase
  budget` runs K1 (one kP rank-stage process) and writes
  `--budget-out/precompute_receipt.json` with P_IC_ms = timing_ms.rank_stage +
  timing_ms.setup_total of that process (the BL-arm experiment's budget, which
  its `bl_table.py precompute --ic-receipt` reads). `--phase panel` runs every
  other segment, after the BL table has been built and checked;
* each arm is launched through the frozen wrapper of the experiment it comes
  from, unchanged: IC and rho arms through
  `../koblitz-n83-rankprobe-20261019/arm.py` (its arm ids cP, kP, rT, so its
  own protocol's layout, fold, index and counter checks apply), BL arms
  through `../koblitz-n83-bl-arm-20261014/arm.py` (kinds `bl_sg`,
  `bl_plain_sg`, with the table, its BLAKE3 and entry count from the
  precompute receipt).

Rows go to `runs.jsonl` (the panel phase appends to the budget phase's file).
Nothing is re-run. `--segments`, `--one-per-arm` and `--max-runs-per-segment`
are for the local smoke only; the workflow passes none of them.
"""

import argparse
import base64
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
RP = HERE.parent / "koblitz-n83-rankprobe-20261019"
BL = HERE.parent / "koblitz-n83-bl-arm-20261014"
sys.path.insert(0, str(REPO / "scripts"))
import host_cpu_record  # noqa: E402  (M5 host record)
import isolated_bench as ib  # noqa: E402  (Tier 1 counters and noise gate)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def fields_of(stdout):
    for line in reversed(stdout.splitlines()):
        if "online_ms=" in line and "verified=" in line:
            return dict(word.split("=", 1) for word in line.split() if "=" in word)
    return {}


def raw_of(stdout):
    for line in stdout.splitlines():
        if line.startswith("raw_b64="):
            return json.loads(base64.b64decode(line[len("raw_b64="):]))
    return None


def binary_of(arm, args):
    return (args.ic_bin_dir if arm["bin_dir"] == "ic" else args.bl_bin_dir) / arm["binary"]


def command(protocol, run, args, table):
    arm = protocol["arms"][run["arm"]]
    point = "%s,%s" % tuple(run["point"])
    if arm["runner"] == "rankprobe":
        rp_online = json.loads((RP / "protocol.json").read_text())["online"]
        argv = [str(args.python), str(RP / "arm.py"), "--arm", arm["wrapper_arm"], "--kind", arm["kind"],
                "--panel", run["point_id"], "--binary", str(binary_of(arm, args)), "--seed", str(run["seed"]),
                "--point", point]
        if arm["kind"] == "rho_tuned":
            argv += ["--config", str(RP / rp_online["tuned_rho_config"])]
        else:
            argv += ["--base", str(RP / rp_online["base"]), "--log-table", str(args.log_table)]
        return argv
    bl = json.loads((BL / "protocol.json").read_text())["bl"]
    argv = [str(args.python), str(BL / "arm.py"), "--arm", run["arm"], "--kind", arm["kind"],
            "--panel", run["point_id"], "--point", point, "--seed", str(run["seed"]),
            "--binary", str(binary_of(arm, args)), "--lanes", str(arm["lanes"]),
            "--reference-dp-bits", str(arm["reference_dp_bits"]), "--field", arm["field"]]
    if arm["uses_table"]:
        argv += ["--dp-bits", str(bl["dp_bits"]), "--bl-jump-seed", str(bl["bl_jump_seed"]),
                 "--table", str(table["path"]), "--table-blake3", table["blake3"],
                 "--table-entries", str(table["entries"])]
    return argv


def timeout_for(protocol, run):
    return protocol["design"]["timeout_s"][protocol["arms"][run["arm"]]["kind"]]


def one(protocol, run, args, receipt_dir, cgroup, table):
    argv = command(protocol, run, args, table)
    binary = Path(argv[argv.index("--binary") + 1])
    binary_before = sha256(binary)
    cpus = {args.cpu}
    before = ib.counters(cpus, cgroup)
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic_ns()

    def child_setup():
        os.sched_setaffinity(0, {args.cpu})

    wrapper_dir = Path(argv[1]).parent
    proc = subprocess.Popen(argv, cwd=str(wrapper_dir), env=ib.benchmark_env(), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True, preexec_fn=child_setup)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout_for(protocol, run))
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
    wall_ms = (time.monotonic_ns() - started) / 1e6
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    after = ib.counters(cpus, cgroup)
    stdout, stderr = stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace")
    stem = "%05d" % run["serial"]
    (receipt_dir / "runs" / (stem + ".stdout.txt")).write_text(stdout)
    (receipt_dir / "runs" / (stem + ".stderr.txt")).write_text(stderr)
    fields = fields_of(stdout)
    noise = ib.noise(before, after, usage_before, usage_after, "tier1")
    memory_events = [item for item in noise if item.startswith("memory event")]
    contention = [item for item in noise if item not in memory_events]
    issues = []
    if proc.returncode != 0:
        issues.append("nonzero exit %d" % proc.returncode)
    if timed_out:
        issues.append("timeout")
    if fields.get("verified") != "1":
        issues.append("missing verified=1")
    if sha256(binary) != binary_before:
        issues.append("binary changed during the run")
    issues += memory_events
    try:
        online = float(fields.get("online_ms", "nan"))
        if not online > 0 or online > wall_ms:
            issues.append("online_ms missing, nonpositive or above process wall")
    except ValueError:
        issues.append("online_ms unparsable")
    return {
        "serial": run["serial"], "arm": run["arm"], "point_id": run["point_id"], "seed": run["seed"],
        "status": "valid" if not issues else "invalid",
        "issues": issues, "contention_flags": contention, "command": argv,
        "binary_sha256": binary_before, "returncode": proc.returncode, "timed_out": timed_out,
        "process_wall_ms": wall_ms,
        "child_cpu_user_ms": (usage_after.ru_utime - usage_before.ru_utime) * 1000,
        "child_cpu_system_ms": (usage_after.ru_stime - usage_before.ru_stime) * 1000,
        "child_peak_rss_kb_cumulative": usage_after.ru_maxrss,
        "child_involuntary_switches": usage_after.ru_nivcsw - usage_before.ru_nivcsw,
        "child_major_faults": usage_after.ru_majflt - usage_before.ru_majflt,
        "fields": fields, "counters_before": before, "counters_after": after,
        "stdout_file": "runs/" + stem + ".stdout.txt", "stderr_file": "runs/" + stem + ".stderr.txt",
        "finished_unix_s": time.time(),
    }


def table_of(bl_receipt_dir):
    receipt = json.loads((bl_receipt_dir / "precompute_receipt.json").read_text())
    checks = json.loads((bl_receipt_dir / "table_checks.json").read_text())
    if receipt.get("status") != "PASS" or checks.get("status") != "PASS":
        raise SystemExit("the BL table's precompute receipt or table checks did not pass; no BL arm runs")
    path = bl_receipt_dir / "table.bin"
    if sha256(path) != receipt["table_sha256"]:
        raise SystemExit("table.bin differs from its precompute receipt")
    return {"path": path.resolve(), "blake3": receipt["producer"]["table_blake3"],
            "entries": receipt["producer"]["table_entries"], "sha256": receipt["table_sha256"]}


def write_budget(row, receipt_dir, out_dir):
    out_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"source": "run_schedule.py --phase budget: K1's kP process (serial %d)" % row["serial"],
               "definition": "P_IC_ms = timing_ms.rank_stage + timing_ms.setup_total",
               "row_status": row["status"]}
    raw = raw_of((receipt_dir / row["stdout_file"]).read_text()) if row.get("stdout_file") else None
    summary = next((r for r in (raw or {}).get("records", []) if r.get("kind") == "compact_orbit_dlp_summary"), {})
    timing = summary.get("timing_ms") or {}
    if row["status"] == "valid" and "rank_stage" in timing and "setup_total" in timing:
        receipt.update(status="PASS", P_IC_ms=timing["rank_stage"] + timing["setup_total"], timing_ms=timing,
                       cold_in_process_ms=summary.get("cold_in_process_ms"),
                       setup_complete_ms=summary.get("setup_complete_ns", 0) / 1e6)
    else:
        receipt.update(status="FAIL", P_IC_ms=None)
    (out_dir / "precompute_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"budget_status": receipt["status"], "P_IC_ms": receipt["P_IC_ms"]}), flush=True)
    return receipt["status"] == "PASS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("budget", "panel"))
    parser.add_argument("--ic-bin-dir", required=True, type=Path)
    parser.add_argument("--bl-bin-dir", required=True, type=Path)
    parser.add_argument("--log-table", required=True, type=Path)
    parser.add_argument("--receipt-dir", required=True, type=Path)
    parser.add_argument("--budget-out", type=Path, help="budget phase: folder of the P_IC receipt")
    parser.add_argument("--bl-receipt-dir", type=Path, help="panel phase: bl_table.py's receipt folder")
    parser.add_argument("--cpu", required=True, type=int)
    parser.add_argument("--job-start-epoch", type=float, default=time.time())
    parser.add_argument("--deadline-min", type=float, default=300.0)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--segments", help="smoke only: comma-separated segment ids")
    parser.add_argument("--one-per-arm", action="store_true", help="smoke only: first run of each arm")
    parser.add_argument("--max-runs-per-segment", type=int, help="smoke only: first k runs of each segment")
    args = parser.parse_args()
    args.ic_bin_dir = args.ic_bin_dir.resolve(strict=True)
    args.bl_bin_dir = args.bl_bin_dir.resolve(strict=True)
    args.log_table = args.log_table.resolve(strict=True)
    protocol = json.loads((HERE / "protocol.json").read_text())
    schedule = json.loads((HERE / "schedule.json").read_text())
    if sha256(args.log_table) != protocol["sources"]["sibling_sha256"]["b:factor_logs_n83_K600.json"]:
        raise SystemExit("factor-log table differs from the protocol's")
    if args.phase == "budget" and args.budget_out is None:
        raise SystemExit("--phase budget needs --budget-out")
    table = table_of(args.bl_receipt_dir.resolve()) if args.phase == "panel" else None
    receipt_dir = args.receipt_dir.resolve()
    (receipt_dir / "runs").mkdir(parents=True, exist_ok=args.phase == "panel")
    cgroup = ib.current_cgroup()
    estimates = protocol["design"]["segment_upper_estimate_s"]
    binaries = sorted({str(binary_of(arm, args)) for arm in protocol["arms"].values()})
    start = {"phase": args.phase, "job_start_epoch": args.job_start_epoch, "runner_started_epoch": time.time(),
             "execution_cpu": args.cpu, "cgroup": str(cgroup), "host": ib.host_probe(),
             "host_cpu_record": host_cpu_record.record(args.cpu),
             "protocol_sha256": sha256(HERE / "protocol.json"),
             "schedule_sha256": sha256(HERE / "schedule.json"), "runner_sha256": sha256(Path(__file__)),
             "wrappers_sha256": {"rankprobe": sha256(RP / "arm.py"), "bl": sha256(BL / "arm.py")},
             "isolated_bench_sha256": sha256(REPO / "scripts/isolated_bench.py"),
             "log_table_sha256": sha256(args.log_table), "table": {k: str(v) for k, v in (table or {}).items()},
             "binaries_sha256": {name: sha256(name) for name in binaries},
             "smoke_subset": {"segments": args.segments, "one_per_arm": args.one_per_arm,
                              "max_runs_per_segment": args.max_runs_per_segment}}
    (receipt_dir / ("runner_start_%s.json" % args.phase)).write_text(json.dumps(start, indent=2, sort_keys=True) + "\n")
    wanted = set(args.segments.split(",")) if args.segments else None
    guard_tripped = False
    observed = {}
    counts = {"valid": 0, "invalid": 0, "skipped_time_guard": 0}
    last_row = None
    with (receipt_dir / "runs.jsonl").open("a") as ledger:
        def write(row):
            ledger.write(json.dumps(row, sort_keys=True) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())
            counts[row["status"]] = counts.get(row["status"], 0) + 1

        for segment in schedule["segments"]:
            if segment["phase"] != args.phase or (wanted is not None and segment["id"] not in wanted):
                continue
            elapsed = time.time() - args.job_start_epoch
            projected = max(estimates[segment["panel"]], 1.1 * observed.get(segment["panel"], 0.0))
            if guard_tripped or elapsed + projected > args.deadline_min * 60:
                guard_tripped = True
                for run in segment["runs"]:
                    last_row = {"serial": run["serial"], "arm": run["arm"], "point_id": run["point_id"],
                                "seed": run["seed"], "segment": segment["id"], "status": "skipped_time_guard",
                                "elapsed_s_at_guard": elapsed}
                    write(last_row)
                continue
            runs = segment["runs"]
            if args.one_per_arm:
                firsts = {}
                for run in runs:
                    firsts.setdefault(run["arm"], run)
                runs = sorted(firsts.values(), key=lambda run: run["serial"])
            if args.max_runs_per_segment:
                runs = runs[:args.max_runs_per_segment]
            segment_started = time.time()
            for run in runs:
                row = one(protocol, run, args, receipt_dir, cgroup, table)
                row["segment"] = segment["id"]
                write(row)
                last_row = row
                print(json.dumps({"serial": row["serial"], "arm": row["arm"], "point": row["point_id"],
                                  "status": row["status"], "issues": row["issues"]}), flush=True)
            observed[segment["panel"]] = max(observed.get(segment["panel"], 0.0), time.time() - segment_started)
    end = {"phase": args.phase, "finished_epoch": time.time(), "counts": counts, "guard_tripped": guard_tripped,
           "binaries_sha256_after": {name: sha256(name) for name in binaries}}
    (receipt_dir / ("runner_end_%s.json" % args.phase)).write_text(json.dumps(end, indent=2, sort_keys=True) + "\n")
    print(json.dumps(end, sort_keys=True))
    if args.phase == "budget":
        ok = last_row is not None and write_budget(last_row, receipt_dir, args.budget_out)
        if not ok:
            raise SystemExit(3)


if __name__ == "__main__":
    main()
