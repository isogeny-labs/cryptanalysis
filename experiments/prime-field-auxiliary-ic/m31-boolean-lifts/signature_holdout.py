"""Read the signature-holdout census histogram on stdin."""
import csv
import math
import sys
from collections import Counter


def votes(own, other):
    """Twice the expected correct score of a label held out from this group."""
    if own == 0:
        return 0
    return own * (int(own - 1 >= other) + int(own - 1 > other))


def main():
    sizes = Counter()
    fitted = held_twice = lifts = coordinates = ties = 0
    pairs = agreements = 0
    for row in csv.DictReader(sys.stdin):
        a, b, freq = (int(row[key]) for key in ("nonlifts", "lifts", "signatures"))
        assert a + b > 0 and freq > 0
        sizes[a+b] += freq
        coordinates += (a+b)*freq
        pairs += math.comb(a+b, 2)*freq
        agreements += (math.comb(a, 2) + math.comb(b, 2))*freq
        lifts += b*freq
        fitted += max(a,b)*freq
        held_twice += (votes(a,b) + votes(b,a))*freq
        ties += (a*(a == b+1) + b*(b == a+1))*freq
    assert (coordinates, lifts, sum(sizes.values())) == (3846525, 1924024, 266975)

    # For n independent fair signs, E|S_(n+1)| - E|S_n| = Pr(S_n=0).
    # The probability at n=2k is choose(2k,k)/4**k. E(S_n**2)=n.
    abs_mean = 0.
    central = 1.
    null_sum = null_var = 0.
    for n in range(1, max(sizes)+1):
        if n % 2:
            abs_mean += central
            central *= n/(n+1)
        null_sum += sizes[n] * (n + abs_mean)/2
        null_var += sizes[n] * (n - abs_mean**2)/4
    print("coordinates", coordinates, "singleton groups", sizes[1])
    print("fitted correct", fitted, "fraction", fitted/coordinates)
    print("fair iid fitted mean and sd", null_sum, math.sqrt(null_var))
    print("held-out correct x2", held_twice, "fraction", held_twice/(2*coordinates))
    print("tied withheld votes", ties, "always-lift fraction", lifts/coordinates)
    print("same-signature pairs", pairs, "agreements", agreements,
          "fraction", agreements/pairs)


if __name__ == "__main__":
    main()
