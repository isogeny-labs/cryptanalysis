import csv
import sys

P = 2**31-1
PRIMES = (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89)
SHIFTS = (0,1,101,65537)


def cubic(x):
    return (x**3+2*x+14) % P


def duplicate(x):
    return ((3*x*x+2)**2 * pow(4*cubic(x),-1,P) - 2*x) % P


def census(values):
    members = set(values)
    assert len(members) == len(values)
    parents = {}

    def root(x):
        while x in parents:
            x = parents[x]
        return x

    hits = [0]*len(SHIFTS)
    for x in values:
        out = duplicate(x)
        for i,s in enumerate(SHIFTS):
            hits[i] += (out+s) % P in members
        if out in members:
            assert pow(cubic(x),(P-1)//2,P) == pow(cubic(out),(P-1)//2,P)
            a,b = root(x),root(out)
            if a != b:
                parents[a] = b
    return [len(values),*hits,len(parents)]


def main():
    w = csv.writer(sys.stdout,lineterminator='\n')
    w.writerow(['bound','smooth',*[f'shift_{s}' for s in SHIFTS],'component_merges'])
    values = [1]
    for q in PRIMES:
        extra = []
        for x in values:
            x *= q
            while x < P:
                extra.append(x)
                x *= q
        values.extend(extra)
        if q in (47,67,89):
            w.writerow([q,*census(values)])
            sys.stdout.flush()


if __name__ == '__main__':
    main()
