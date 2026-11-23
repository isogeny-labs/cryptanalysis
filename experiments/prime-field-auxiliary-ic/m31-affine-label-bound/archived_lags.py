"""Exact short-lag overlap for the public archived M31 walk step tables."""
from collections import Counter
from fractions import Fraction
from itertools import combinations_with_replacement
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from archived_loops import read

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_five_sum_coverage import P, add, add_many


def multiple(k, point):
    result = None
    while k:
        if k & 1:
            result = add(result, point)
        point = add(point, point)
        k //= 2
    return result


def archived_coefficients():
    source = """
#include <iostream>
#include <random>
int main() {
    for (int seed = 0; seed < 3; ++seed) {
        std::mt19937_64 rng(20261115 + seed);
        for (int j = 0; j < 32; ++j) {
            auto a = rng() % 2147505293ULL;
            auto b = rng() % 2147505293ULL;
            std::cout << a << ' ' << b << '\\n';
        }
    }
}
"""
    with TemporaryDirectory() as directory:
        exe = Path(directory) / "coefficients"
        subprocess.run(["c++", "-std=c++17", "-x", "c++", "-", "-o", exe],
                       input=source, text=True, check=True)
        lines = subprocess.check_output([exe], text=True).splitlines()
    assert len(lines) == 96
    return [tuple(map(int, line.split())) for line in lines]


def main():
    manifest = json.loads(read("public", "json"))
    pub = manifest["public"]
    signed = [(x, v) for x, y in manifest["factor_base"] for v in (y, (-y) % P)]
    accepted = {add(a, b) for a,b in combinations_with_replacement(signed, 2)} - {None}
    assert len(accepted) == 578
    # The accepted set is closed under negation, so its difference histogram
    # equals its ordered sum histogram. Infinity counts all diagonal pairs.
    overlap = Counter(point for step in accepted for point in add_many(accepted, step))
    assert overlap[None] == 578 and sum(overlap.values()) == 578**2
    coefficients = archived_coefficients()
    print("seed,lag,ordered_paths,paths_with_overlap,ordered_hit_pairs,conditional_return")
    for seed in range(3):
        steps = [add(multiple(a, tuple(pub["P"])), multiple(b, tuple(pub["Q"])))
                 for a,b in coefficients[32*seed:32*(seed+1)]]
        paths = Counter({None: 1})
        for lag in range(1, 5):
            extended = Counter()
            for offset, count in paths.items():
                for step in steps:
                    extended[add(offset, step)] += count
            paths = extended
            assert sum(paths.values()) == 32**lag
            possible = sum(n for offset,n in paths.items() if overlap[offset])
            hits = sum(n*overlap[offset] for offset,n in paths.items())
            probability = Fraction(hits, 578*32**lag)
            print(seed,lag,32**lag,possible,hits,probability,sep=",")


if __name__ == "__main__":
    main()
