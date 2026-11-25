"""Emit paired counts for held-out seeds 1024 through 5119."""
import csv
from pathlib import Path
import runpy
import sys

source = runpy.run_path(str(Path(__file__).with_name("twist53-labels.py")))
P = source["P"]


def cross_count(fixed, partners):
    hits = 0
    for x, y in fixed:
        for u, v in partners:
            inverse = pow(u - x, -1, P)
            for ordinate in (v, -v):
                slope = (ordinate - y) * inverse % P
                z = (slope * slope - x - u) % P
                hits += pow(z**3 + 2*z - 14, (P-1)//2, P) == 1
    return hits


def main():
    auxiliary = source["archived"]("same_base")
    control = source["archived"]("random")
    forbidden = {x for x, _ in auxiliary + control}
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(("seed", "auxiliary_hits", "control_hits"))
    for seed in range(1024, 5120):
        points = source["control"]["public_basis"](seed)
        partners = [point for point in points if point[0] not in forbidden][:17]
        assert len(partners) == len(auxiliary) == len(control) == 17
        writer.writerow((seed, cross_count(auxiliary, partners), cross_count(control, partners)))


if __name__ == "__main__":
    main()
