import csv
import sys

P = 2**31-1
PRIMES = (3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89)
PERIOD = 31
MASK = (1 << PERIOD)-1


def representatives():
    values = [1]
    for q in PRIMES:
        extra = []
        for v in values:
            v *= q
            while v < P:
                extra.append(v)
                v *= q
        values.extend(extra)
    return {pow(x,31,P): x for x in values if pow(x,(P-1)//2,P) == P-1}


def lift_masks(start, step):
    masks = [0,0,0]
    x = start
    for i in range(PERIOD):
        cube = pow(x,3,P)
        for j, rhs in enumerate((cube+x,cube+2*x+14,cube+2*x-14)):
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
        b = lift_masks(pow(x,-1,P),(P+1)//2)
        assert a[0] == b[0]
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
