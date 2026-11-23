"""Exact Hamming error of a row bit XOR a column bit on balanced eight-bit cuts."""
import hashlib
import json
import subprocess
from itertools import combinations
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
FIXTURE = "experiments/prime-field-auxiliary-ic/snapshot/algebraic/end_to_end/field31_s8_base0/public.json"
SHA256 = "d9b37ebd239714b43c5495ab1d0fc9178f5d0362b4c9ffe775257f18b0b653ca"
P = 2**31 - 1
BITS = 1 << np.arange(16)
# Simultaneously complementing both functions leaves their XOR unchanged.
PATTERNS = np.arange(2**15, dtype=np.int32)
ROW_ERRORS = np.array([min(i.bit_count(), 16 - i.bit_count()) for i in range(2**16)],
                      dtype=np.uint8)


def optimum(matrix):
    rows = matrix @ BITS
    # For each column function choose the better row bit independently.
    errors = ROW_ERRORS[PATTERNS[:, None] ^ rows].sum(axis=1)
    pattern = int(errors.argmin())
    column_bits = (pattern & BITS) != 0
    row_bits = (matrix != column_bits).sum(axis=1) > 8
    mismatch = np.count_nonzero(matrix != (row_bits[:, None] ^ column_bits))
    assert mismatch == errors[pattern]
    return int(mismatch)


def offsets(axes):
    return [sum(((i >> j) & 1) << axis for j, axis in enumerate(axes)) for i in range(16)]


def main():
    data = subprocess.check_output(["git", "show", f"HEAD:{FIXTURE}"], cwd=HERE)
    assert hashlib.sha256(data).hexdigest() == SHA256
    roots = json.loads(data)["structured_roots"]
    assert len(roots) == len(set(roots)) == 256
    print("curve_b,mask,errors")
    for b in (14, 36):
        labels = np.array([pow((x**3 + 2*x + b) % P, (P-1)//2, P) == 1 for x in roots])
        for other in combinations(range(1, 8), 3):
            axes = (0, *other)
            complement = [i for i in range(8) if i not in axes]
            row, col = offsets(axes), offsets(complement)
            matrix = labels[np.bitwise_or.outer(row, col)]
            errors = optimum(matrix)
            assert errors == optimum(matrix.T)
            print(b, sum(1 << i for i in axes), errors, sep=",")


if __name__ == "__main__":
    main()
