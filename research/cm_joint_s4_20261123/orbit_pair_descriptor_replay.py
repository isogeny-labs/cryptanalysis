#!/usr/bin/env python3
"""Exact coefficient replay of signed-orbit pair descriptors on the r=61 control."""

from collections import Counter

R, L, LAM = 61, 3, 7
CATEGORIES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def add(*vectors):
    return tuple(sum(v[k] for v in vectors) % R for k in (0, 1))


def scale(a, vector):
    return tuple(a * v % R for v in vector)


def indexed_base():
    # Match the existing Sage runner's seed, exponent, sign index order.
    return [scale(pow(LAM, j, R), (s, 0)) for j in range(L) for s in (1, -1)] + [
        scale(pow(LAM, j, R), (0, s)) for j in range(L) for s in (1, -1)
    ]


def descriptor_pairs():
    for j in range(L):
        for i, low in enumerate(CATEGORIES):
            for high in CATEGORIES[i:]:
                yield add(scale(pow(LAM, j, R), low), scale(pow(LAM, j, R), high))
    for gap in range(1, L):
        for low in CATEGORIES:
            for high in CATEGORIES:
                seed = add(low, scale(pow(LAM, gap, R), high))
                for j in range(L - gap):
                    yield scale(pow(LAM, j, R), seed)


def main():
    base = indexed_base()
    direct = Counter(add(base[i], base[j]) for i in range(len(base))
                     for j in range(i, len(base)))
    encoded = Counter(descriptor_pairs())
    assert direct == encoded
    assert sum(direct.values()) == 78
    descriptors = len(CATEGORIES) * (len(CATEGORIES) + 1) // 2
    descriptors += (L - 1) * len(CATEGORIES) ** 2
    assert descriptors == 42

    # First frozen d=3 query: witness pair [0,2], third point [9].
    assert add(base[0], base[2]) == (8, 0)
    assert base[9] == (0, 54)
    assert add(base[0], base[2], base[9]) == (8, 54)
    query = (54, 59)
    relation = ((8 - query[0]) % R, (54 - query[1]) % R)
    assert relation == (15, 56)
    assert (relation[0] + 3 * relation[1]) % R == 0

    print("PASS: 42 descriptors encode all 78 indexed pairs with multiplicity")
    print("PASS: first frozen query gives 15G+56Q=O at d=3")


if __name__ == "__main__":
    main()
