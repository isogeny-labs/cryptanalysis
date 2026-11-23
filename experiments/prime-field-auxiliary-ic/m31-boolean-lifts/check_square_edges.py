"""Independent replay using descending square divisibility and FLINT Jacobi labels."""
import csv
import re
from pathlib import Path

import numpy as np
from flint import fmpz

P = 2**31 - 1
PRIMES = [q for q in range(2, 90) if fmpz(q).is_prime()]


def main():
    x = np.array([1], dtype=np.uint64)
    for q in PRIMES:
        powers = [x]
        current = x
        while current.size:
            current = current[current <= (P-1)//q] * q
            powers.append(current)
        x = np.concatenate(powers)
    x.sort()
    assert len(x) == 3846525 and np.all(x[1:] > x[:-1])
    rhs = ((x*x % P)*x + 2*x + 14) % P
    label = np.fromiter((fmpz(int(v)).jacobi(P) >= 0 for v in rhs), np.uint8, len(x))
    assert label.sum() == 1924024
    rows = []
    has_parent = np.zeros(len(x), dtype=bool)
    for q in PRIMES:
        has_src = x % (q*q) == 0
        has_parent |= has_src
        source = x[has_src] // (q*q)
        indices = np.searchsorted(x, source)
        assert np.array_equal(x[indices], source)
        counts = np.bincount(2*label[indices] + label[has_src], minlength=4)
        rows.append([q, *map(int, counts)])
    assert (~has_parent).sum() == 266975
    with Path(__file__).with_name("square_edges.csv").open() as f:
        recorded = csv.reader(f)
        next(recorded)
        assert rows == [list(map(int, row)) for row in recorded]
    lean = Path(__file__).with_name("SquareEdges.lean").read_text()
    cells = re.findall(r"^  ⟨(\d+), (\d+), (\d+), (\d+)⟩", lean, flags=re.M)
    assert [row[1:] for row in rows] == [list(map(int, c)) for c in cells]
    print("Matched all 96 cells; squarefree roots:", int((~has_parent).sum()))


if __name__ == "__main__":
    main()
