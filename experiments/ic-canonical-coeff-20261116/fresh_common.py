"""Frozen logical routing and balanced five-method order matrix."""
from collections import Counter
MODES=['anchor-vector16-const','baseline-vector16-const','baseline-vector16-inverse','patched-vector16-const','patched-vector16-inverse']
ACTUAL={m:('mitm-walk16-vector-inverse' if m in [MODES[2],MODES[4]] else 'mitm-walk16-vector-const') for m in MODES}
TAGS={MODES[0]:'anchor',MODES[1]:'current',MODES[2]:'current',MODES[3]:'optimized',MODES[4]:'optimized'}
INVERSE={MODES[2],MODES[4]}
CONTRASTS=[('vs_anchor',MODES[0],MODES[4]),('coefficient_ordinary',MODES[1],MODES[3]),('coefficient_inverse',MODES[2],MODES[4]),('patched_kernel',MODES[3],MODES[4]),('old_kernel',MODES[1],MODES[2]),('patched_ordinary_vs_anchor',MODES[0],MODES[3]),('old_ordinary_vs_anchor',MODES[0],MODES[1])]
base=[0,1,4,2,3]
ORDERS=[[(x+k)%5 for x in base] for k in range(5)]
ORDERS+= [list(reversed(row)) for row in ORDERS]
assert len(set(map(tuple,ORDERS)))==10
assert set(Counter((i,m) for row in ORDERS for i,m in enumerate(row)).values())=={2}
assert len(Counter((row[i],row[i+1]) for row in ORDERS for i in range(4)))==20
assert set(Counter((row[i],row[i+1]) for row in ORDERS for i in range(4)).values())=={2}
FIXTURES=range(510,540)
