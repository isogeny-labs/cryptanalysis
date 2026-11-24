"""Count four distinct nonzero classes, modulo sign, admitting a signed zero sum."""
from fractions import Fraction
from itertools import combinations
from math import comb, factorial


def oriented_count(q):
    # Scale the first entry to 1. For b outside {0,1,-1}, d=-1-b-c.
    # Exclude c that is zero, repeats a class, or makes d zero or a repeated class.
    half = -pow(2, -1, q) % q
    forbidden = [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0),
                 (-1, -1), (-1, -2), (-2, -1), (half, half)]
    crossings = set()
    for (m, k), (n, t) in combinations(forbidden, 2):
        if (m-n) % q:
            crossings.add((t-k) * pow(m-n, -1, q) % q)
    generic_count = (q-3)*(q-len(forbidden))
    correction = sum(len(forbidden)-len({(m*b+k) % q for m, k in forbidden})
                     for b in crossings - {0, 1, q-1})
    return (q-1)*(generic_count+correction)


def direct_supports(q):
    # Independent check counting sign classes and sign patterns directly.
    from itertools import product
    total = 0
    for a, b, c, d in combinations(range(1, (q+1)//2), 4):
        solutions = sum((a+i*b+j*c+k*d) % q == 0 for i, j, k in product((-1, 1), repeat=3))
        assert solutions <= 1
        total += solutions
    return total


if __name__ == "__main__":
    factor = 2*factorial(4)
    for prime in (11, 13, 17, 19, 23, 31, 53):
        assert oriented_count(prime) == factor*direct_supports(prime)
    q = 2147505293
    # The two orientations differ by global sign (UniqueSigns.lean).
    rate = Fraction(oriented_count(q), factor*comb((q-1)//2, 4))
    assert rate == Fraction(8, q-3)
    print("probability per four classes", rate)
    for width in (34, 68, 136, 272, 544):
        expectation = rate*comb(width, 4)
        print(width, float(expectation), float(16*expectation))
