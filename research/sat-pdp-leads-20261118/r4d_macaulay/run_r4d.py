#!/usr/bin/env python3
"""Run every frozen cell of PROTOCOL.md (3 worker processes); one JSON row per matrix."""
import json, sys
from multiprocessing import Pool
import macaulay_r4d as M

CELLS = []
for (n, l) in [(13, 4), (17, 5)]:
    for seed in (0, 1, 2):
        CELLS.append((n, l, seed, "real", ((1, 1), (1, 2), (2, 1), (2, 2))))
        CELLS.append((n, l, seed, "null", ((1, 1), (1, 2), (2, 1), (2, 2))))
    CELLS.append((n, l, 0, "planted", ((1, 1), (1, 2), (2, 1), (2, 2)) if n == 13 else ((1, 1), (1, 2), (2, 1))))

def job(c):
    n, l, seed, kind, bd = c
    try:
        return M.run_cell(n, l, seed, kind, bd, cap=900)
    except AssertionError as e:
        return [{"n": n, "l": l, "seed": seed, "kind": kind, "error": str(e)}]

if __name__ == "__main__":
    out = sys.argv[1]
    with Pool(3) as pool, open(out, "w") as fo:
        for rows in pool.imap_unordered(job, sorted(CELLS, key=lambda c: -c[0])):
            for r in rows:
                fo.write(json.dumps(r, separators=(",", ":")) + "\n")
            fo.flush()
