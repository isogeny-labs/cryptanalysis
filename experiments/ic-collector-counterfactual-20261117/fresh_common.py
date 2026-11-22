"""Prospectively frozen routing, fixtures and contrasts; no observations."""
from collections import Counter

MODES = ['anchor-vector16-const', 'compact-vector16-inverse', 'indexed-vector16-inverse',
         'counterfactual-sp', 'counterfactual-sa', 'counterfactual-ip', 'counterfactual-ia']
INVERSE = set(MODES[1:])
ACTUAL = {MODES[0]: 'mitm-walk16-vector-const', MODES[1]: 'mitm-walk16-vector-inverse',
          MODES[2]: 'mitm-walk16-vector-inverse',
          **{m: 'mitm-'+m for m in MODES[3:]}}
TAGS = {MODES[0]: 'anchor', MODES[1]: 'current', MODES[2]: 'indexed',
        **{m: 'optimized' for m in MODES[3:]}}
CONTRASTS = [('indexing_present', MODES[3], MODES[5]),
             ('indexing_absent', MODES[4], MODES[6]),
             ('counter_staged', MODES[3], MODES[4]),
             ('counter_indexed', MODES[5], MODES[6]),
             ('vs_anchor', MODES[0], MODES[5]),
             ('vs_compact', MODES[1], MODES[5]),
             ('rebuilt_indexed', MODES[2], MODES[5]),
             ('remedy_vs_indexed', MODES[2], MODES[6])]
# The ninth contrast is a within-block interaction. It must never be computed
# by multiplying separately aggregated effects or observations from panels.
INTERACTION = ('setup_interaction', (MODES[3], MODES[6]), (MODES[5], MODES[4]))
base = [0, 1, 6, 2, 5, 3, 4]
ORDERS = [[(x+k) % 7 for x in base] for k in range(7)]
ORDERS += [list(reversed(row)) for row in ORDERS]
assert len(set(map(tuple, ORDERS))) == 14
assert set(Counter((i, m) for row in ORDERS for i, m in enumerate(row)).values()) == {2}
assert len(Counter((row[i], row[i+1]) for row in ORDERS for i in range(6))) == 42
assert set(Counter((row[i], row[i+1]) for row in ORDERS for i in range(6)).values()) == {2}
FIXTURES = range(726, 768)
STORAGE_COUNTERS = {'mitm_compact_map32_backend', 'mitm_map_entry_payload_bytes',
                    'mitm_vector_packed_square_pairs', 'mitm_vector_const_packed_square_pairs',
                    'mitm_vector_const_validated_pairs', 'mitm_indexed_prepare_pairs'}
