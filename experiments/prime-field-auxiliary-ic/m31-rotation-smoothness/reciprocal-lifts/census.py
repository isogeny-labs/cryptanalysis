import csv
import sys

P = 2**31-1
PRIMES = (3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89)
PERIOD = 31
MASK = (1 << PERIOD)-1


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


def lift_masks(start, step, auxiliary_mask=None):
    masks = [0 if auxiliary_mask is None else auxiliary_mask, 0, 0]
    x = start
    for i in range(PERIOD):
        cube = pow(x,3,P)
        if auxiliary_mask is None and pow(cube+x, (P-1)//2, P) != P-1:
            masks[0] |= 1 << i
        for j, rhs in enumerate((cube+2*x+14,cube+2*x-14), start=1):
            if pow(rhs,(P-1)//2,P) != P-1:
                masks[j] |= 1 << i
        x = x*step % P
    assert x == start
    return masks


def rotate(m, j):
    return ((m << j) & MASK) | (m >> (PERIOD-j))


def main():
    groups = representatives()
    totals = [[0]*5 for _ in range(PERIOD)]
    pairs = 0
    for key, x in groups.items():
        inverse = pow(key,-1,P)
        if key >= inverse or inverse not in groups:
            continue
        pairs += 1
        a = lift_masks(x,2)
        # Transport.lean proves that inverse coordinates have the same auxiliary lift.
        # The inverse orbit uses the inverse step, so the bit positions agree.
        b = lift_masks(pow(x,-1,P), (P+1)//2, auxiliary_mask=a[0])
        for j,row in enumerate(totals):
            aux,curve,twist = (m & rotate(n,j) for m,n in zip(a,b))
            for i,bits in enumerate((aux,curve,twist,aux & curve,aux & twist)):
                row[i] += bits.bit_count()
    assert pairs == 3302
    writer = csv.writer(sys.stdout,lineterminator='\n')
    writer.writerow(('phase','coordinates','aux_joint','curve_joint','twist_joint',
                     'aux_curve_joint','aux_twist_joint'))
    for j,row in enumerate(totals):
        writer.writerow((j,PERIOD*pairs,*row))


if __name__ == '__main__':
    main()
