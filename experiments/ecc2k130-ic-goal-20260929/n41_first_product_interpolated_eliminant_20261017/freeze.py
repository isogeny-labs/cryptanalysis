"""Freeze 17 source products and two held-out products before interpolation."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
PRIOR=ROOT/'n41_w8_three_pair_resultant_20261013/result.json'
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
geo=json.loads(GEO.read_text());prior=json.loads(PRIOR.read_text())
def product(mask):
    value=0
    for i,basis in enumerate(geo['blocks'][0]['product_basis']):
        if mask>>i&1:value^=basis
    return value
source=sorted({product(m) for m in geo['permitted_canonical_a']})
witness=prior['witness_pair_products'][0]
assert len(source)==40 and witness in source
sample=[value for value in source if value!=witness][:17]
holdouts=[witness,next(value for value in reversed(source) if value not in sample and value!=witness)]
assert len(sample)==17 and len(set(sample+holdouts))==19
paths={'worker':HERE/'worker.py','geometry':GEO,'prior':PRIOR,
       'witness_archived':OLD/'result.json','negative_archived':OLD/'control_result.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','method':'degree-16 first-product interpolation of two-free-product resultant',
       'sample_first_products':sample,'holdout_first_products':holdouts,
       'panel_order':['witness','negative'],'worker_count':1,'alarm_s_per_panel':300,
       'rss_boundary_bytes':4294967296,
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}}
with (HERE/'protocol.json').open('x') as output:json.dump(proto,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
                  'sample_count':len(sample),'holdouts':holdouts}))
