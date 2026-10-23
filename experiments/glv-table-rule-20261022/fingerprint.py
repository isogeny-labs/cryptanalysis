#!/usr/bin/env python3
"""Operation-count fingerprint of curve_solve: 4 curves x 10 targets per family at 28 bits.

    CRYPTANALYSIS_LIB=build/libcryptanalysis.so ML_CRYPTANALYSIS=../ml-cryptanalysis \
        python3 experiments/glv-table-size-20261022/fingerprint.py j1728,j0

Prints the 40 (or 80) group_ops values as JSON. Two builds walk identically on these
inputs exactly when their fingerprints are equal. Curves come from the sampler of
ml-cryptanalysis's frozen experiments/glv-j1728-controlled/run.py (seed 20261017)."""
import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bindings" / "python"))
ml = Path(os.environ.get("ML_CRYPTANALYSIS", ROOT.parent / "ml-cryptanalysis"))
sys.path.insert(0, str(ml / "experiments" / "glv-j1728-controlled"))
import cryptanalysis as ca  # noqa: E402
from run import sample_curve  # noqa: E402

out = []
for fam in sys.argv[1].split(","):
    rng = random.Random(f"20261017:{fam}:28")
    for ci in range(4):
        p, a, b, N, r = sample_curve(ca, rng, fam, 28)
        G = ca.Group.ec(p, a, b, N)
        G.set_order(r, N // r)
        g = G.find_generator(1)
        for s in range(10):
            k = random.Random(f"20261017:{p}:{a}:{b}:{s}").randrange(1, r)
            x, _, st = G.curve_solve(g, G.mul(g, k), s + 1)
            assert x == k
            out.append(st.group_ops)
print(json.dumps(out))
