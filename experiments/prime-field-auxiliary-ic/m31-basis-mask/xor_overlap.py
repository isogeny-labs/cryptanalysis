"""Exact translation-overlap census in the 31-bit Boolean cube."""
from collections import Counter
from itertools import combinations
from pathlib import Path


def main():
    coords = [int(x) for x in Path(__file__).with_name("coordinates.txt").read_text().splitlines()]
    basis = set(coords)
    assert len(coords) == len(basis) == 195 and all(0 <= x < 2**31 for x in basis)
    differences = Counter(a ^ b for a, b in combinations(coords, 2))

    # Each unordered pair at difference d supplies both x and x XOR d.
    # Conversely, every intersection point at nonzero d belongs to one such pair.
    overlaps = Counter(2 * multiplicity for multiplicity in differences.values())
    overlaps[0] = 2**31 - 1 - len(differences)
    assert overlaps == {2: 18_915, 0: 2_147_464_732}
    for delta, multiplicity in differences.items():
        assert sum((x ^ delta) in basis for x in coords) == 2 * multiplicity

    distance = min(d.bit_count() for d in differences)
    witness = min(d for d in differences if d.bit_count() == distance)
    print("nonzero shifts by overlap size:", sorted(overlaps.items()))
    print("minimum Hamming distance:", distance)
    print("witness:", hex(witness), sorted(x for x in basis if x ^ witness in basis))


if __name__ == "__main__":
    main()
