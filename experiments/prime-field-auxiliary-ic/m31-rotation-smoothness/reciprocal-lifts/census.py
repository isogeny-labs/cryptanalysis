import argparse
import csv
import sys
import subprocess

P = 2**31-1
PRIMES = (3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89)
PERIOD = 31
EXPECTED_PAIRS = 3302
DIGIT_BITS = (EXPECTED_PAIRS * PERIOD).bit_length()
DIGIT_MASK = (1 << DIGIT_BITS) - 1


def byte_table(reverse):
    positions = range(7, -1, -1) if reverse else range(8)
    return tuple(sum(((byte >> bit) & 1) << (digit * DIGIT_BITS)
                     for digit, bit in enumerate(positions))
                 for byte in range(256))


FORWARD = byte_table(False)
BACKWARD = byte_table(True)


def representatives():
    # Store chi(v) * v. Multiplicativity lets every power of q inherit
    # its character using just one Euler-criterion evaluation per prime.
    values = [1]
    for q in PRIMES:
        signed_q = -q if pow(q, (P-1)//2, P) == P-1 else q
        extra = []
        for v in values:
            product = v * signed_q
            while -P < product < P:
                extra.append(product)
                product *= signed_q
        values.extend(extra)
    return {pow(-v, 31, P): -v for v in values if v < 0}


def euler_lift(rhs):
    return pow(rhs, (P-1)//2, P) != P-1


def lift_masks(start, step, auxiliary_mask=None, lifts=euler_lift):
    masks = [0 if auxiliary_mask is None else auxiliary_mask, 0, 0]
    x = start
    for i in range(PERIOD):
        cube = pow(x,3,P)
        if auxiliary_mask is None and lifts(cube+x):
            masks[0] |= 1 << i
        for j, rhs in enumerate((cube+2*x+14,cube+2*x-14), start=1):
            if lifts(rhs):
                masks[j] |= 1 << i
        x = x*step % P
    assert x == start
    return masks


def packed(mask, table, byteorder):
    value = 0
    for byte in mask.to_bytes(4, byteorder):
        value = (value << (8 * DIGIT_BITS)) + table[byte]
    return value


def phase_count(product, phase):
    # A left bit i and a right bit k land at coefficient i + 31 - k.
    low = (product >> (phase * DIGIT_BITS)) & DIGIT_MASK
    high = (product >> ((phase + PERIOD) * DIGIT_BITS)) & DIGIT_MASK
    return low + high


def reciprocal(x):
    return pow(x, -1, P)


def pair_representatives(invert_word):
    groups = representatives()
    for key, x in groups.items():
        inverse = invert_word(key)
        if key < inverse and inverse in groups:
            yield x


def main(lifts=euler_lift, invert_word=reciprocal, pair_generator=None):
    if pair_generator is None:
        selected = pair_representatives(invert_word)
    else:
        output = subprocess.check_output([pair_generator], text=True)
        selected = map(int, output.splitlines())
    products = [0] * 5
    pairs = 0
    for x in selected:
        pairs += 1
        a = lift_masks(x, 2, lifts=lifts)
        # Transport.lean proves that inverse coordinates have the same auxiliary lift.
        # The inverse orbit uses the inverse step, so the bit positions agree.
        b = lift_masks(invert_word(x), (P+1)//2, auxiliary_mask=a[0], lifts=lifts)
        left = (*a, a[0] & a[1], a[0] & a[2])
        right = (*b, b[0] & b[1], b[0] & b[2])
        for column, (u, v) in enumerate(zip(left, right)):
            products[column] += packed(u, FORWARD, "big") * packed(v, BACKWARD, "little")
    if pairs != EXPECTED_PAIRS:
        raise ValueError(f"expected {EXPECTED_PAIRS} orbit pairs, found {pairs}")
    writer = csv.writer(sys.stdout,lineterminator='\n')
    writer.writerow(('phase','coordinates','aux_joint','curve_joint','twist_joint',
                     'aux_curve_joint','aux_twist_joint'))
    for j in range(PERIOD):
        writer.writerow((j, PERIOD*pairs, *(phase_count(v, j) for v in products)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Count affine lifts over M31.")
    parser.add_argument("--gmp", action="store_true",
                        help="use gmpy2 for lift tests and field inversion")
    parser.add_argument("--pair-generator", help="path to the compiled native-pairs/pairs.cpp helper")
    args = parser.parse_args()
    if args.gmp:
        try:
            from gmpy2 import invert, jacobi
        except ImportError as error:
            parser.exit(2, f"--gmp requires gmpy2: {error}\n")

        def gmp_lift(rhs):
            return jacobi(rhs, P) >= 0

        def gmp_reciprocal(x):
            return int(invert(x, P))

        main(gmp_lift, gmp_reciprocal, args.pair_generator)
    else:
        main(pair_generator=args.pair_generator)
