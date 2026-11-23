"""Exact GF(2) witnesses for degree-at-most-three one-sided M31 classifiers."""
from itertools import combinations
from math import comb
import json

P = (1 << 31) - 1
WIDTH = sum(comb(31, k) for k in range(4))


def feature_masks():
    # Bit j is the j-th square-free monomial, in degree/lexicographic order.
    blocks = [bytearray((WIDTH + 7) // 8) for _ in range(31)]
    index = 0
    for degree in range(4):
        for term in combinations(range(31), degree):
            for bit in term:
                blocks[bit][index // 8] |= 1 << (index % 8)
            index += 1
    assert index == WIDTH
    return [int.from_bytes(block, "little") for block in blocks]


def insert(basis, word):
    while word:
        pivot = word.bit_length() - 1
        if basis[pivot] == 0:
            basis[pivot] = word
            return 1
        word ^= basis[pivot]
    return 0


def main():
    contains = feature_masks()
    bases = [[0] * WIDTH for _ in range(2)]
    ranks = [0, 0]
    completion = [None, None]
    state = 1
    # This affine recurrence has period 2^31. Skip the noncanonical word P.
    for step in range(1, 20001):
        state = (1103515245 * state + 12345) & P
        if state == P:
            continue
        rhs = (state**3 + 2*state + 14) % P
        y = pow(rhs, (P + 1)//4, P)
        label = int(y*y % P == rhs)
        # A failed positive test supplies a witness for the opposite square class.
        assert y*y % P == (rhs if label else -rhs) % P
        if ranks[label] == WIDTH:
            continue
        row = (1 << WIDTH) - 1
        missing = P ^ state
        while missing:
            low = missing & -missing
            row &= ~contains[low.bit_length() - 1]
            missing ^= low
        ranks[label] += insert(bases[label], row)
        if ranks[label] == WIDTH:
            completion[label] = step
        if all(completion):
            break
    assert ranks == [WIDTH, WIDTH]
    print(json.dumps(dict(columns=WIDTH, ranks_nonlift_lift=ranks,
                          first_full_rank_steps_nonlift_lift=completion), indent=2))


if __name__ == "__main__":
    main()
