"""Prospective eight-path routing and balanced40fixture design; no observations."""
from collections import Counter
MODES=['anchor-vector16-const','compact-vector16-inverse','indexed-vector16-inverse',
       'setup-staged','setup-indexed','setup-observed','setup-reserved','setup-gathered']
INVERSE=set(MODES[1:]);INDEXED={MODES[2],*MODES[4:]}
ACTUAL=dict(zip(MODES,['mitm-walk16-vector-const','mitm-walk16-vector-inverse','mitm-walk16-vector-inverse',
                      'mitm-counterfactual-sp','mitm-counterfactual-ip','mitm-setup-observed','mitm-setup-reserved','mitm-setup-gathered']))
TAGS={MODES[0]:'anchor',MODES[1]:'current',MODES[2]:'indexed',**{m:'optimized' for m in MODES[3:]}}
STRATEGIES=dict(zip(MODES[3:],[5,3,6,7,8]))
CONTRASTS=[('staged_vs_indexed',MODES[3],MODES[4]),('opaque_observation',MODES[4],MODES[5]),
 ('reservation',MODES[5],MODES[6]),('gather',MODES[6],MODES[7]),
 ('rebuilt_indexed',MODES[2],MODES[4]),('reserved_vs_frozen',MODES[2],MODES[6]),
 ('gathered_vs_frozen',MODES[2],MODES[7]),('vs_anchor',MODES[0],MODES[4]),('vs_compact',MODES[1],MODES[4])]
base=[0,1,7,2,6,3,5,4];ORDERS=[[(v+k)%8 for v in base] for k in range(8)]
FIXTURES=range(768,808)
assert len(set(map(tuple,ORDERS)))==8
assert set(Counter((i,m) for row in ORDERS*5 for i,m in enumerate(row)).values())=={5}
a=Counter((row[i],row[i+1]) for row in ORDERS*5 for i in range(7));assert len(a)==56 and set(a.values())=={5}
assert set(Counter((j,(f+j)%5) for f in range(40) for j in range(5)).values())=={8}
STORAGE_COUNTERS={'mitm_compact_map32_backend','mitm_map_entry_payload_bytes','mitm_vector_packed_square_pairs',
 'mitm_vector_const_packed_square_pairs','mitm_vector_const_validated_pairs','mitm_indexed_prepare_pairs'}
