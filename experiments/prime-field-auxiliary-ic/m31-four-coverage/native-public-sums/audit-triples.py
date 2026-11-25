"""Replay the archived relation triples. Reads pinned git objects, without running a collector."""
import json
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path
import re
import subprocess

COMMIT = "f94834307158ff36d7440c86bf0bfef0df75f261"
BASE = "experiments/prime-field-auxiliary-ic/snapshot/algebraic"
FIXTURE = "field31_s5_base0"
Q = 2147505293


def read(path):
    return subprocess.check_output(["git", "-C", Path(__file__).resolve().parent,
                                    "show", f"{COMMIT}:{BASE}/{path}"])


def canonical(entry, size):
    row = [0] * size
    for key, sign in [("i", "si"), ("j", "sj")]:
        idx, value = entry[key], entry[sign]
        assert 0 <= idx < size and value in (-1, 1)
        row[idx] += value
    assert sum(map(abs, row)) == 2
    orientation = next(x for x in row if x)
    return tuple(row if orientation > 0 else [-x for x in row])


def dependent(a, b, c):
    occupied = [i for i in range(len(a)) if a[i] or b[i] or c[i]]
    for i, j, k in combinations(occupied, 3):
        det = (a[i]*(b[j]*c[k]-b[k]*c[j]) - a[j]*(b[i]*c[k]-b[k]*c[i])
               + a[k]*(b[i]*c[j]-b[j]*c[i]))
        if det % Q:
            return False
    return True


def main():
    controls = [("end_to_end", name) for name in ("chain", "same_base", "random")]
    controls.append(("optimized/results", "v2_batch"))
    histories = {}
    for seed in range(3):
        for folder, arm in controls:
            prefix = f"{folder}/{FIXTURE}/{arm}_seed{seed}"
            data = json.loads(read(prefix + ".audited.json"))
            public = json.loads(read(f"{folder}/{FIXTURE}/public.json"))
            basis = tuple(map(tuple, public["random_factor_base" if arm == "random" else "factor_base"]))
            raw = read(prefix + ".relations.jsonl")
            rows = tuple(canonical(json.loads(line), len(basis)) for line in raw.splitlines())
            assert data["audit"]["certified_full_group_order"] == Q and len(basis) == 17
            assert data["relations"] == data["audit"]["verified_relations"] == len(set(rows)) == len(rows)
            assert data["seed"] == seed and data["audit"]["verified_factor_base_cancellation"]
            log = read(prefix + ".log").decode()
            first, = re.findall(r"^queries 1000000, relations (\d+), seconds ", log, re.M)
            first = int(first)
            key = basis, rows
            triples = [ids for ids in combinations(range(len(rows)), 3)
                       if dependent(*(rows[i] for i in ids))]
            if key in histories:
                print(arm, seed, "identical basis and row sequence to", histories[key])
                continue
            histories[key] = (arm, seed)
            support = data["audit"]["dependency_relations"]
            print(arm, seed, "queries", data["queries"], "rows", len(rows),
                  "rows before query 1M", first, "triples before query 1M",
                  sum(k < first for _, _, k in triples),
                  "terminal support", support, "dependent triples", len(triples),
                  "earliest ending row", min((k+1 for _, _, k in triples), default=None))
    prefix = min(len(rows) for _, rows in histories)
    observed = sum(dependent(a, b, c) for _, rows in histories for a, b, c in combinations(rows[:prefix], 3))
    mean = Fraction(comb(prefix, 3)*3264, comb(289, 3))
    print("common prefix", prefix, "distinct histories", len(histories), "observed triples", observed,
          "iid uniform distinct-label expected triples per history", float(mean))


if __name__ == "__main__":
    main()
