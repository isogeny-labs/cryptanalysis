"""Check compatible sibling pairs on one archived M31 fiber."""
import argparse
import json
from math import isqrt, prod
from pathlib import Path
import subprocess

P = 2**31 - 1


def make_smooth_test(bound, method):
    primes = [q for q in range(2, bound+1)
              if all(q % d for d in range(2, isqrt(q)+1))]

    if method == "trial":
        def smooth(n):
            for q in primes:
                while n % q == 0:
                    n //= q
            return n == 1
        return smooth

    def maximal_power(q):
        value = q
        while value*q < P:
            value *= q
        return value

    multiple = prod(maximal_power(q) for q in primes)
    return lambda n: multiple % n == 0


def orbit_hits(x, smooth):
    for _ in range(31):
        if smooth(x):
            return True
        x = ((x << 1) & P) | (x >> 30)
    return False


def odd_orbit_hits(x, smooth):
    # A set bit at position i becomes the low bit of the i-th right rotation.
    doubled = (x << 31) | x
    remaining = x
    while remaining:
        bit = remaining & -remaining
        shift = bit.bit_length() - 1
        if smooth((doubled >> shift) & P):
            return True
        remaining ^= bit
    return False


def coverage(fixture, bound, method, helper=None):
    if fixture["auxiliary"]["p"] != P:
        raise ValueError("requires an M31 fiber")
    if method == "index":
        values = subprocess.check_output([str(Path(helper).resolve())]).splitlines()
        keys = {k for word in values for k in (pow(int(word),31,P), pow(int(word),-31,P))}

        def covered(x, y):
            return pow(x,31,P) in keys and pow(y,31,P) in keys
    else:
        smooth = make_smooth_test(bound, method)
        hits_orbit = odd_orbit_hits if method == "odd" else orbit_hits

        def covered(x, y):
            return (pow(x,(P-1)//2,P) == P-1 and pow(x,62,P) != 1
                    and hits_orbit(x,smooth) and hits_orbit(y,smooth))

    xs = fixture["structured_roots"]
    rows = []
    for step in fixture["auxiliary"]["maps"]:
        b = step["B"]
        shifted = {(x-step["r"]) % P for x in xs}
        siblings = [(u,v) for u in sorted(shifted) if u < (v := b*pow(u,-1,P) % P)]
        if {x for pair in siblings for x in pair} != shifted:
            raise ValueError("incomplete or ramified fiber")
        hits = []
        s0 = pow(pow(b,-1,P),(P+1)//4,P)
        if s0*s0*b % P == 1:
            for s in (s0, P-s0):
                for u,v in siblings:
                    if covered(s*u % P,s*v % P):
                        hits.append([s,u,v])
        rows.append(dict(sibling_pairs=len(siblings), hits_up_to_rotation=hits))
        xs = [(u+v+step["A"]) % P for u,v in siblings]
    if xs != [fixture["auxiliary"]["terminal_c"]]:
        raise ValueError("terminal coordinate mismatch")
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("bound", type=int, choices=(89,211))
    parser.add_argument("--method", choices=("index","trial","multiple","odd"), default="multiple")
    parser.add_argument("--helper", help="native generator compiled at the selected bound")
    args = parser.parse_args()
    if args.method == "index" and not args.helper:
        parser.error("--method index requires --helper")
    print(json.dumps(coverage(json.loads(args.fixture.read_bytes()), args.bound,
                              args.method, args.helper)))
