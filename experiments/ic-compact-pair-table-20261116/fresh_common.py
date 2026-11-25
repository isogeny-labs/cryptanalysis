"""Prospective seven-method Williams orders, repeated three times per field."""
from collections import Counter
MODES=['anchor-vector16-const','direct-vector16-const','direct-vector16-inverse','coefficient-vector16-const','coefficient-vector16-inverse','compact-vector16-const','compact-vector16-inverse']
INVERSE={MODES[2],MODES[4],MODES[6]}
ACTUAL={m:('mitm-walk16-vector-inverse' if m in INVERSE else 'mitm-walk16-vector-const') for m in MODES}
TAGS={MODES[0]:'anchor',MODES[1]:'current',MODES[2]:'current',MODES[3]:'coefficient',MODES[4]:'coefficient',MODES[5]:'optimized',MODES[6]:'optimized'}
STORAGE_COUNTERS={'mitm_compact_map32_backend','mitm_map_entry_payload_bytes'}
CONTRASTS=[('vs_anchor',MODES[0],MODES[6]),('storage_ordinary',MODES[3],MODES[5]),('storage_inverse',MODES[4],MODES[6]),('combined_ordinary',MODES[1],MODES[5]),('combined_inverse',MODES[2],MODES[6]),('compact_kernel',MODES[5],MODES[6]),('coefficient_kernel',MODES[3],MODES[4]),('direct_kernel',MODES[1],MODES[2]),('coefficient_vs_direct_ordinary',MODES[1],MODES[3]),('coefficient_vs_direct_inverse',MODES[2],MODES[4]),('compact_ordinary_vs_anchor',MODES[0],MODES[5]),('coefficient_ordinary_vs_anchor',MODES[0],MODES[3]),('direct_ordinary_vs_anchor',MODES[0],MODES[1])]
base=[0,1,6,2,5,3,4]
ORDERS=[[(x+k)%7 for x in base] for k in range(7)]
ORDERS += [list(reversed(row)) for row in ORDERS]
assert len(set(map(tuple,ORDERS)))==14
assert set(Counter((i,m) for row in ORDERS for i,m in enumerate(row)).values())=={2}
assert len(Counter((row[i],row[i+1]) for row in ORDERS for i in range(6)))==42
assert set(Counter((row[i],row[i+1]) for row in ORDERS for i in range(6)).values())=={2}
FIXTURES=range(540,582)
