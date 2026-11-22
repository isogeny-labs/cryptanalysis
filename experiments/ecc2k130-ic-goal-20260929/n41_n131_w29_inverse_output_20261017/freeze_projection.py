"""Freeze exact binary product-map ranks and decoder coordinates."""
import hashlib
import json
from pathlib import Path

import inverse_output as design

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


rows = []
for name, source in (('n41', design.n41), ('n131', design.n131)):
    projection = design.projection(source.PB, source.N)
    d = len(source.PB)
    assert projection['basis_rank'] == d
    decode = projection['decode']
    assert all(decode(source.PB[i]) == 1 << i for i in range(d))
    rows.append({'field': name, 'field_degree': source.N,
                 'seed_mask': source.SEED_MASK,
                 'canonical_source_bits': d,
                 'product_map_rank': projection['basis_rank'],
                 'independent_coordinate_rows': projection['pivots'],
                 'basis_vectors_sha256': hashlib.sha256(json.dumps(source.PB).encode()).hexdigest()})
result = {'status': 'PASS_EXACT_PRODUCT_MAP_RANK_AND_BASIS_INVERSE',
          'rows': rows,
          'source_sha256': {'script': sha(Path(__file__)),
                            'circuit': sha(HERE / 'inverse_output.py'),
                            'n41': sha(design.N41_PRIOR),
                            'n131': sha(design.N131_PRIOR)}}
with (HERE / 'projection_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'], 'rows': rows}))
