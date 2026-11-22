"""Distinct residual functions, witnessed on the same 64 suffixes for each cut."""
import numpy as np
import hashlib

P = 2**31 - 1

def scatter(indices, bits):
    value = np.zeros_like(indices)
    for i, bit in enumerate(bits):
        value |= ((indices >> i) & 1) << bit
    return value

def curve_signs(x):
    # Canonical cubic values and Euler's criterion using ordinary modular products.
    f = (((x*x % P)*x % P) + 2*x + 14) % P
    power = f.copy()
    for _ in range(30):
        power = power*power % P
    assert np.all((power == f) | (power == P-f))
    return power != f

for name,order in [('ascending',list(range(31))),('descending',list(reversed(range(31)))),
                   ('parity',list(range(0,31,2))+list(range(1,31,2)))]:
    for k in [15,19]:
        columns = scatter(np.arange(64,dtype=np.uint64), order[k:k+6])
        chunks=[]
        for i in range(0,1<<k,512):
            rows=scatter(np.arange(i,i+512,dtype=np.uint64),order[:k])
            cells=curve_signs(rows[:,None] | columns)
            # Independently check a complete suffix signature per prefix block.
            row = int(rows[0])
            expected = [pow(((row | int(c))**3 + 2*(row | int(c)) + 14) % P,
                            (P-1)//2, P) == P-1 for c in columns]
            assert np.array_equal(cells[0], expected)
            chunks.append(np.packbits(cells,axis=1,bitorder='little').ravel().view('<u8'))
        signatures=np.concatenate(chunks)
        # Normalize a suffix function and its complement to the same representative.
        normalized=np.minimum(signatures,np.bitwise_not(signatures))
        classes=len(np.unique(normalized))
        assert classes==len(signatures)
        print(name,k,classes,hashlib.sha256(signatures.astype('<u8').tobytes()).hexdigest(),flush=True)
