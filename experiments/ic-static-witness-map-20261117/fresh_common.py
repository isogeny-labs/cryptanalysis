"""Frozen seven-path routing and balanced Williams orders."""
from collections import Counter
MODES=['anchor-vector16-const','compact-vector16-const','compact-vector16-inverse','indexed-vector16-const','indexed-vector16-inverse','static-vector16-const','static-vector16-inverse']
INVERSE={MODES[2],MODES[4],MODES[6]}
ACTUAL={m:('mitm-walk16-vector-inverse' if m in INVERSE else 'mitm-walk16-vector-const') for m in MODES}
TAGS={MODES[0]:'anchor',MODES[1]:'current',MODES[2]:'current',MODES[3]:'indexed',MODES[4]:'indexed',MODES[5]:'optimized',MODES[6]:'optimized'}
CONTRASTS=[('vs_anchor',MODES[0],MODES[6]),('compact_static_ordinary',MODES[1],MODES[5]),('compact_static_inverse',MODES[2],MODES[6]),('indexed_static_ordinary',MODES[3],MODES[5]),('indexed_static_inverse',MODES[4],MODES[6]),('static_kernel',MODES[5],MODES[6]),('indexed_kernel',MODES[3],MODES[4]),('compact_kernel',MODES[1],MODES[2]),('static_ordinary_vs_anchor',MODES[0],MODES[5])]
base=[0,1,6,2,5,3,4]
ORDERS=[[(x+k)%7 for x in base] for k in range(7)]
ORDERS += [list(reversed(row)) for row in ORDERS]
assert len(set(map(tuple,ORDERS)))==14
assert set(Counter((i,m) for row in ORDERS for i,m in enumerate(row)).values())=={2}
assert len(Counter((row[i],row[i+1]) for row in ORDERS for i in range(6)))==42
assert set(Counter((row[i],row[i+1]) for row in ORDERS for i in range(6)).values())=={2}
FIXTURES=range(684,726)
STORAGE_COUNTERS={'mitm_compact_map32_backend','mitm_map_entry_payload_bytes','mitm_vector_packed_square_pairs','mitm_vector_const_packed_square_pairs','mitm_vector_const_validated_pairs','mitm_indexed_prepare_pairs','mitm_static_map32_backend'}
