#!/usr/bin/env python3
"""Frozen driver: run the sweep prime by prime, ascending, under a wall-clock gate."""
import math, os, subprocess, sys, time
BIN, OUT = sys.argv[1], sys.argv[2]
PRIMES = (31, 67, 127, 251, 509, 1021, 2039, 4093, 8191, 16381, 32749, 65521)
START_GATE_S = 3000
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
for p in PRIMES:
    T = round(300 * math.sqrt(p / 67))
    el = time.time() - t0
    if el > START_GATE_S:
        print(f"CENSORED p={p}: stage not started, elapsed {el:.0f}s > {START_GATE_S}s", flush=True)
        continue
    print(f"START p={p} trials_per_cell={T} elapsed={el:.0f}s", flush=True)
    subprocess.run([sys.executable, os.path.join(here, "sweep.py"), "--binary", BIN, "--primes", str(p),
                    "--trials", str(T), "--out", os.path.join(OUT, f"rows-p{p}.jsonl")], check=True)
print(f"END elapsed={time.time()-t0:.0f}s", flush=True)
