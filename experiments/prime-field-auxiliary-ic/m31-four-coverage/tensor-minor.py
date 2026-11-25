"""Print a public 128-row M31 lift minor and its inverse over GF(2)."""
p = 2**31 - 1
n = 128


def row_bits(h):
    row = 0
    for s in range(n):
        x = 65536*h + s
        side = pow((x**3 + 2*x + 14) % p, (p-1)//2, p)
        row |= int(side != p-1) << s
    return row


def inverse(rows):
    work = [r | (1 << (n+i)) for i, r in enumerate(rows)]
    for j in range(n):
        pivot = next((k for k in range(j,n) if (work[k] >> j) & 1), None)
        if pivot is None:
            return None
        work[j], work[pivot] = work[pivot], work[j]
        for k in range(n):
            if k != j and (work[k] >> j) & 1:
                work[k] ^= work[j]
    return [r >> n for r in work]


if __name__ == "__main__":
    for start in range(0,32768,n):
        rows = [row_bits(h) for h in range(start,start+n)]
        inv = inverse(rows)
        if inv is not None:
            print("prefix,label_bits,inverse_bits")
            for i in range(n):
                print(start+i,rows[i],inv[i],sep=",")
            break
    else:
        raise ValueError("no full-rank minor")
