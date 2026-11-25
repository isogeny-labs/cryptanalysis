#!/usr/bin/env python3
"""GT-02 optimal-base driver. usage: driver.py <stage> ; writes JSON reports under OUT."""
import sys, json, itertools, math, os
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/user/workspace/tools")
import lead_sweep as L
B = "/home/user/wt/gt02-optimal-base/suite/target/release/ca-ic"
OUT = os.environ["OUT"]
def cell(name, args):
    p = f"{OUT}/{name}.json"
    if os.path.exists(p): return name, "cached"
    cmd = [B, "bench", *args, "--max-cofactor", "8", "--json", "--out", p]
    st = L.watched_run(cmd, f"{OUT}/{name}.log", 3.0, 600)
    json.dump(st, open(f"{OUT}/{name}.watch", "w"))
    return name, st["status"]
def char2_args(n, d, arm, m, seed, reps, rho):
    orc = "mitm" if arm == "base" else f"mitm:coset_filter=1,m={m}"
    if arm == "base" and m == 3: orc = "mitm:m=3"
    return ["--char2-degree", str(n), "--factor-base", f"binary-subspace:dimension={d}", "--oracle", orc,
            "--repeats", str(reps), "--seed", str(seed), "--max-trials", "20000000", "--rho-runs", str(rho)]
def prime_args(bits, k, arm, m, seed, reps, rho):
    orc = ("mitm" if m == 2 else "mitm:m=3") if arm == "base" else f"mitm:coset_filter=1,m={m}"
    return ["--bits", str(bits), "--factor-base", f"prime-abscissa:size={k}", "--oracle", orc,
            "--repeats", str(reps), "--seed", str(seed), "--max-trials", "20000000", "--rho-runs", str(rho)]
if __name__ == "__main__":
    stage = sys.argv[1]; jobs = []
    os.makedirs(OUT, exist_ok=True)
    if stage == "A":
        for n in [17,19,21,23,25,27,29,31,33]:
            for m in (2, 3):
                if m == 3 and n > 29: continue
                for d in range(4, math.ceil(n/3) + (2 if m == 2 else 3) + 1):
                    for arm in ("base", "lead"):
                        jobs.append((f"A_c2_n{n}_m{m}_d{d}_{arm}", char2_args(n, d, arm, m, 20261123, 12, 0)))
    elif stage == "B":
        for spec in json.load(open(sys.argv[2])):   # [{n,m,d}]
            for arm in ("base", "lead"):
                jobs.append((f"B_c2_n{spec['n']}_m{spec['m']}_d{spec['d']}_{arm}",
                             char2_args(spec['n'], spec['d'], arm, spec['m'], 20261124, 12, 12 if arm == "base" else 0)))
    elif stage == "P":
        reg = {16:(123145648762,[40,23,31]),18:(123145648762,[63,30,50]),20:(20261102,[100,47,79]),22:(20261102,[160,58,119]),24:(20261104,[256,96])}
        for bits,(seed,ks) in reg.items():
            for k in ks:
                for m in (2, 3):
                    if m == 3 and bits == 24: continue
                    for arm in ("base", "lead"):
                        jobs.append((f"P_n{bits}_k{k}_m{m}_{arm}", prime_args(bits, k, arm, m, seed, 12, 12 if arm == "base" else 0)))
    with ThreadPoolExecutor(2) as ex:
        for name, st in ex.map(lambda j: cell(*j), jobs):
            print(name, st, flush=True)
