#!/usr/bin/env python3
"""CT322 live exact-prime31 public-only Rust BSGS controls.

Real native child DLP work and Linux wait4 memory; not strongest BSGS,
not candidate/retained/IC comparison, not independent PCC. [pcc:unverified]
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

import ct317_group_replay as group
import ct321_blind_challenge as blind

PRIME31 = {
    "schema": blind.CURVE, "curve_id": "crypto-prime31-exact-ordinary-20261115",
    "p": 2147483647, "a": 847514846, "b": 2087444724,
    "generator": [625037715, 2100627251], "subgroup_prime": 2147446831,
}
MAX_WALL_S = 20.0
MAX_RSS_KIB = 256 * 1024
RESPONSE = {"schema", "result_scalar", "baby_table_entries",
            "baby_iterations", "giant_iterations", "affine_adds",
            "field_inversions", "inside_ns", "original_jacobian_calls", "pcc"}


def refuse(message):
    raise ValueError("CT322: " + message)


def digest(v):
    return hashlib.sha256(v).hexdigest()


def check_response(raw, q, curve):
    out = group.strict(raw)
    if type(out) is not dict or set(out) != RESPONSE or (
            out["schema"] != "ct322-native-bsgs/v1" or
            out["original_jacobian_calls"] != 0 or
            out["pcc"] != "unverified"):
        refuse("native response schema")
    for f in ("result_scalar", "baby_table_entries", "baby_iterations",
              "giant_iterations", "affine_adds", "field_inversions", "inside_ns"):
        if type(out[f]) is not int or out[f] < 1:
            refuse("missing positive native count " + f)
    n = curve["subgroup_prime"]
    m = __import__("math").isqrt(n - 1) + 1
    if (out["result_scalar"] >= n or out["baby_iterations"] != m or
            out["baby_table_entries"] != m or
            out["giant_iterations"] > n // m + 2):
        refuse("native bounds or recovered scalar")
    p, a = curve["p"], curve["a"]
    P = tuple(curve["generator"])
    if group.mul(out["result_scalar"], P, p, a) != tuple(q):
        refuse("independent source group equation failed")
    return out


def native_child(binary, fields, workdir):
    if not hasattr(os, "wait4") or not hasattr(os, "sched_getaffinity"):
        refuse("requires Linux wait4 and CPU affinity")
    b = Path(binary).resolve(strict=True)
    argv = [str(b)] + [str(v) for v in fields]
    public_only = all(type(v) is int and v >= 0 for v in fields)
    if not public_only or len(fields) != 8:
        refuse("native argv must contain eight public integers")
    cpus = os.sched_getaffinity(0)
    if not cpus:
        refuse("no allowed CPU")
    cpu = min(cpus)
    stdout_path = Path(workdir) / "native.stdout"
    stderr_path = Path(workdir) / "native.stderr"
    env = {"PATH": "/usr/bin:/bin", "LANG": "C", "HOME": str(workdir)}
    started = time.perf_counter_ns()
    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        proc = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            env=env, cwd=workdir, close_fds=True,
            preexec_fn=lambda: os.sched_setaffinity(0, {cpu}))
        deadline = time.monotonic() + MAX_WALL_S
        timed_out = False
        while True:
            pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
            if pid == proc.pid:
                break
            if time.monotonic() >= deadline:
                timed_out = True
                try:
                    os.kill(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                pid, status, usage = os.wait4(proc.pid, 0)
                break
            time.sleep(0.005)
        ended = time.perf_counter_ns()
        proc.returncode = os.waitstatus_to_exitcode(status)
    stdout = stdout_path.read_bytes()
    stderr = stderr_path.read_bytes()
    rss = int(usage.ru_maxrss)  # Linux wait4 reports child ru_maxrss in KiB
    if timed_out or proc.returncode != 0:
        refuse("native child failed/timeout, status=%d stderr_sha=%s" %
               (proc.returncode, digest(stderr)))
    if not (0 < rss <= MAX_RSS_KIB and 0 < ended-started and stdout and
            stderr == b""):
        refuse("invalid native memory/wall/output capture")
    return {
        "argv_sha256": digest(blind.canonical(argv)),
        "binary_sha256": digest(b.read_bytes()),
        "stdout_sha256": digest(stdout),
        "stderr_sha256": digest(stderr),
        "external_wall_ns": ended-started, "peak_rss_kib": rss,
        "cpu_affinity": [cpu], "exit_code": proc.returncode,
        "native": stdout,
    }


def benchmark(binary):
    toy = (97, 2, 3, 5, 3, 6, 80, 10)
    with tempfile.TemporaryDirectory(prefix="ct322-native-") as td:
        root = Path(td)
        for title, fields, valid in (
                ("toy-ok", toy, True),
                ("toy-off-curve", (97,2,3,5,3,6,80,11), False),
                ("toy-composite-prime", (95,2,3,5,3,6,80,10), False),
                ("toy-composite-order", (97,2,3,4,3,6,80,10), False)):
            d = root / title
            d.mkdir()
            if not valid:
                try:
                    native_child(binary, fields, d)
                except ValueError:
                    pass
                else:
                    refuse("native accepted invalid " + title)
                continue
            cap = native_child(binary, fields, d)
            answer = check_response(
                cap["native"], [80, 10],
                {"subgroup_prime": 5, "p": 97, "a": 2,
                 "generator": [3, 6]})
            if answer["result_scalar"] != 2:
                refuse("toy BSGS returned wrong source logarithm")
        public_path, private_path = root / "public.json", root / "private.json"
        issued = blind.publish(PRIME31, 4, public_path, private_path)
        public_raw = public_path.read_bytes()
        public = group.strict(public_raw)
        curve = public["witness"]
        results = []
        # At this point ONLY the public bytes are opened by the supervisor.
        # Private manifest is deliberately read after every child has exited.
        for i, t in enumerate(curve["targets"]):
            d = root / ("child-%d" % i)
            d.mkdir()
            q = t["Q"]
            fields = (
                curve["p"], curve["a"], curve["b"],
                curve["subgroup_prime"], *curve["generator"], *q)
            cap = native_child(binary, fields, d)
            rec = check_response(cap.pop("native"), q, curve)
            results.append((t["target_id"], q, rec, cap))
        private_raw = private_path.read_bytes()
        admitted = blind.audit(public_raw, private_raw)
        reveal = group.strict(private_raw)
        truths = {s["target_id"]:s["scalar"] for s in reveal["reveals"]}
        for tid, q, rec, cap in results:
            if rec["result_scalar"] != truths[tid]:
                refuse("post-reveal scalar differs from independent native solve")
            forged = dict(rec)
            forged["result_scalar"] = (
                rec["result_scalar"] % (curve["subgroup_prime"]-1)) + 1
            if forged["result_scalar"] == rec["result_scalar"]:
                forged["result_scalar"] = (
                    (rec["result_scalar"]+1) % (curve["subgroup_prime"]-1)) + 1
            try:
                check_response(blind.canonical(forged), q, curve)
            except ValueError:
                pass
            else:
                refuse("accepted tampered recovered scalar")
        return {
            "schema": "ct322-native-prime31-live-control/v1",
            "source": "existing ordinary crypto prime31 cofactor-one fixture",
            "p": curve["p"], "subgroup_order": curve["subgroup_prime"],
            "public_sha256": issued["public_sha256"],
            "public_challenge": public,
            "native_processes": len(results),
            "correct_full_prime31_discrete_logs": len(results),
            "post_reveal_commitments_replayed": admitted["target_count"],
            "child_external_wall_ns": [r[3]["external_wall_ns"] for r in results],
            "child_peak_rss_kib": [r[3]["peak_rss_kib"] for r in results],
            "child_affine_adds": [r[2]["affine_adds"] for r in results],
            "child_field_inversions": [r[2]["field_inversions"] for r in results],
            "binary_sha256": results[0][3]["binary_sha256"],
            "argv_sha256": [r[3]["argv_sha256"] for r in results],
            "stdout_sha256": [r[3]["stdout_sha256"] for r in results],
            "result_scalar_or_salt_printed": False,
            "supervisor_and_solver_independently_isolated": False,
            "candidate_transfer_runs": 0,
            "original_native_jacobian_executions": 0,
            "strongest_baseline_or_speedup_established": False,
            "independent_execution_authenticated": False,
            "pcc": "unverified",
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native", required=True, type=Path)
    args = ap.parse_args()
    out = benchmark(args.native)
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
