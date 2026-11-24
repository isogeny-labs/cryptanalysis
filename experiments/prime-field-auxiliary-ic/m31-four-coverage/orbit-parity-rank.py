"""Select affine bases within each parity class and emit left-inverse certificates."""
import csv
import sys

P = 2**31 - 1
KX, KY = 1965083199, 1854403464

def inverse(rows):
    n = len(rows)
    masks = [row | (1 << (n+i)) for i,row in enumerate(rows)]
    for col in range(n):
        pivot = next(i for i in range(col,n) if masks[i] >> col & 1)
        masks[col], masks[pivot] = masks[pivot], masks[col]
        for i in range(n):
            if i != col and masks[i] >> col & 1:
                masks[i] ^= masks[col]
    assert [r % (1<<n) for r in masks] == [1<<i for i in range(n)]
    return [r >> n for r in masks]

writer = csv.writer(sys.stdout, lineterminator="\n")
writer.writerow(["seed","parity","orbit","labels","inverse"] +
                [f"x{i}" for i in range(32)] + [f"y{i}" for i in range(32)] + ["rotation_inverse"])
for seed,path in zip((291163,291164),sys.argv[1:],strict=True):
    with open(path) as f:
        entries = [tuple(map(int,line.split())) for line in f]
    assert len(entries) == 32768
    rows = [entries[i:i+32] for i in range(0,len(entries),32)]
    labels = [sum(bit<<j for j,(_,bit) in enumerate(row)) for row in rows]
    for parity in (0,1):
        anchor = next(i for i,w in enumerate(labels) if w.bit_count()%2 == parity)
        selected, pivots = [anchor], {}
        for i,w in enumerate(labels):
            if w.bit_count()%2 != parity:
                continue
            diff = (w ^ labels[anchor]) % (1<<31)
            while diff:
                pivot = diff.bit_length()-1
                if pivot not in pivots:
                    pivots[pivot] = diff
                    selected.append(i)
                    break
                diff ^= pivots[pivot]
            if len(selected)==32:
                break
        assert len(selected)==32
        inv = [0]+inverse([(labels[i]^labels[anchor]) % (1<<31) for i in selected[1:]])
        rotation_inv = [0]*32
        if parity:
            w = labels[anchor]
            rotations = [((w>>k)|(w<<(32-k))) & (2**32-1) for k in range(1,32)]
            rotation_inv = [0]+inverse([(r^w)%(1<<31) for r in rotations])
        for i,coeff,rot in zip(selected,inv,rotation_inv):
            xs = [x for x,_ in rows[i]]
            ys = [((x**3+x+KY**2-(x-KX)**2*(z+x+KX))*pow(2*KY,-1,P))%P
                  for x,z in zip(xs,xs[1:]+xs[:1])]
            writer.writerow([seed,parity,i,labels[i],coeff,*xs,*ys,rot])
