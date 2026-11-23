"""Count odd smooth positive integers strictly below the M31 modulus."""
from bisect import bisect_right
from math import isqrt

p = 2**31-1
for bound in (89, 211, 331, 811, 1423, 2789):
    primes = [q for q in range(3,bound+1,2) if all(q%d for d in range(3,isqrt(q)+1,2))]

    def count(limit, first):
        end = bisect_right(primes, limit, lo=first)
        # The empty product and the one-factor products.
        total = 1 + end-first
        for i in range(first, end):
            q = primes[i]
            if q*q > limit:
                break
            # Removing the smallest factor leaves a nonempty smooth product.
            total += count(limit//q, i)-1
        return total

    print(bound, count(p-1, 0))
