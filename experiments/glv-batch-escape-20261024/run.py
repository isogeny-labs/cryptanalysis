#!/usr/bin/env python3
"""Field-operation counts of glv_rho_solve by walk phase (PROTOCOL.md).

    CRYPTANALYSIS_LIB=<build>/libcryptanalysis.so python3 run.py --arm main --out rows_main.jsonl

The library must be built with -DCA_GLV_FIELD_COUNT=ON; the batch-escape arm
adds -DCA_GLV_BATCH_ESCAPE=ON.  Every arm samples the same curves, targets and
solver seeds (the sampler of experiments/glv-table-rule-20261022/run.py); one
JSON line per (family, bits, curve, target) with the counts of each phase."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bindings" / "python"))
sys.path.insert(0, str(ROOT / "experiments" / "glv-table-rule-20261022"))
import cryptanalysis as ca  # noqa: E402
from run import sample_curve  # noqa: E402

PHASES = ["outside", "setup", "batch", "post", "escape", "restart"]
KINDS = ["mul", "sqr", "inv", "euclid"]  # euclid: division steps inside the inversions
EVENTS = ["batches", "batch_walks", "esc2", "esc4", "restarts", "retries"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--families", default="j1728,j0")
    ap.add_argument("--sizes", default="26,28,30,32,34,36")
    ap.add_argument("--curves", type=int, default=200)
    ap.add_argument("--targets", type=int, default=10)
    ap.add_argument("--seed", type=int, default=20261025)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    lib = ctypes.CDLL(os.environ["CRYPTANALYSIS_LIB"])
    buf = (ctypes.c_uint64 * (len(PHASES) * len(KINDS) + len(EVENTS)))()
    with open(a.out, "w") as fh:
        for bits in map(int, a.sizes.split(",")):
            for fam in a.families.split(","):
                rng = random.Random(f"{a.seed}:{fam}:{bits}")
                for ci in range(a.curves):
                    p, a_, b_, N, r = sample_curve(rng, fam, bits)
                    G = ca.Group.ec(p, a_, b_, N)
                    G.set_order(r, N // r)
                    g = G.find_generator(1)
                    for s in range(a.targets):
                        k = random.Random(f"{a.seed}:{p}:{a_}:{b_}:{s}").randrange(1, r)
                        Q = G.mul(g, k)
                        lib.ca_fc_reset()
                        x, _, st = G.curve_solve(g, Q, s + 1)
                        lib.ca_fc_read(buf)
                        row = {"arm": a.arm, "family": fam, "bits": bits, "curve": ci, "target": s,
                               "p": p, "a": a_, "b": b_, "N": N, "r": r, "k": k,
                               "ops": st.group_ops, "correct": x == k}
                        for i, ph in enumerate(PHASES):
                            for j, kd in enumerate(KINDS):
                                row[f"{ph}_{kd}"] = buf[i * len(KINDS) + j]
                        for i, ev in enumerate(EVENTS):
                            row[ev] = buf[len(PHASES) * len(KINDS) + i]
                        fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
