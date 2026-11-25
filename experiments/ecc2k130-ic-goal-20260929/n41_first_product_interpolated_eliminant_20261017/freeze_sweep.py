"""Freeze both interpolated tensors and the full N41 source-code cube."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
files={'sweep':HERE/'sweep.py','geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'prior':ROOT/'n41_w8_three_pair_resultant_20261013/result.json',
       'witness_tensor':HERE/'witness_result_v2.json','negative_tensor':HERE/'negative_result_v2.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','panels':['witness','negative'],
       'source':'all 40 admissible products in each of first three pair slots, four fixed suffix states',
       'code_triples_per_panel':64000,'worker_count':1,'alarm_s':180,
       'rss_boundary_bytes':4294967296,
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}}
with (HERE/'sweep_protocol.json').open('x') as output:json.dump(proto,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'sweep_protocol.json').read_bytes()).hexdigest()}))
