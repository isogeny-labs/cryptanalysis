"""Replay depth-12 coverage from the pinned archive with the standard library."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import subprocess

revision = "67a393a4d5169647498f50ad5a0df113742eb659"
folder = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/structure_results/field31_s12"
p = 2**31 - 1
finite_points = 2147505293 - 1


def read(name):
    path = f"{revision}:{folder}/{name}.json"
    return json.loads(subprocess.check_output(["git", "show", path], cwd=Path(__file__).parent))


models = read("models")
assert models["curve"] == {"p": p, "a": 2, "b": 14}
for base in ("structured_roots", "random_roots"):
    roots = read(base)
    assert roots == models[base] and len(set(roots)) == len(roots) == 4096
    symbols = Counter(pow((x**3 + 2*x + 14) % p, (p-1)//2, p) for x in roots)
    assert symbols == {1: 2025, p-1: 2071}

queries = {}
for arm in ("chain", "expanded", "random"):
    rows = [r for r in read("runs") if r["encoding"] == arm]
    assert len(rows) == 16 and all(r["status"] == "solved" and r["relations"] == [] for r in rows)
    queries[arm] = {(r["seed"], tuple(r["target"])) for r in rows}
assert len(queries["chain"]) == 16 and queries["chain"] == queries["expanded"] == queries["random"]

# All unordered signed pairs, including repeats, less one inverse pair per x.
signed = 4050
finite_pairs = signed*(signed+1)//2 - 2025
hit_bound = Fraction(finite_pairs, finite_points)
for bases in (1, 2):
    miss_floor = 1 - 16*bases*hit_bound
    print(f"{bases} base(s): probability of zero hits >= {float(miss_floor):.9f}")
