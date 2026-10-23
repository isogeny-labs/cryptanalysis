#!/usr/bin/env python3
"""Exploratory (untiered) paired timing on the authoring VM: the frozen binaries and panels,
alternating reference/candidate, pinned to one CPU with taskset; records steal time from
/proc/stat around every run. Fails the Tier 1 preflight (cgroup v1), so no tier is claimed.

    exploratory_local.py REF CAND PANEL_DIR OUT.jsonl [--pairs 15] [--cpu 3]"""
import argparse, json, re, subprocess, time

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("cand"); ap.add_argument("panels"); ap.add_argument("out")
ap.add_argument("--pairs", type=int, default=15); ap.add_argument("--cpu", type=int, default=3)
a = ap.parse_args()
EXPECT = {"j1728": "1b2f48914f323ea1", "j0": "13edb0311980828c"}

def steal():
    f = open("/proc/stat").readline().split()
    return int(f[8])

with open(a.out, "w") as fh:
    for fam, want in EXPECT.items():
        for i in range(a.pairs):
            order = [("reference", a.ref), ("candidate", a.cand)] if i % 2 == 0 else [("candidate", a.cand), ("reference", a.ref)]
            for arm, binary in order:
                s0 = steal(); t0 = time.time()
                out = subprocess.run(["taskset", "-c", str(a.cpu), binary, f"{a.panels}/panel_{fam}.txt", "7"],
                                     capture_output=True, text=True, check=True).stdout
                kv = dict(re.findall(r"(\w+)=(\S+)", out))
                assert kv["verified"] == "1" and kv["result"] == want, out
                fh.write(json.dumps({"family": fam, "pair": i, "arm": arm, "online_ms": float(kv["online_ms"]),
                                     "cpu_ms": float(kv["cpu_ms"]), "ops": int(kv["ops"]), "steal_ticks": steal() - s0,
                                     "outer_s": time.time() - t0}) + "\n")
            print(fam, i, flush=True)
