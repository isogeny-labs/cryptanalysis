"""Freeze corrected tuple/list receipt comparison before the rerun."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
paths={'worker_v2':HERE/'worker_v2.py','geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'witness':OLD/'result.json','negative':OLD/'control_result.json',
       'joint':OLD/'joint_result.json','negative_joint':OLD/'control_joint_result.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','method':'per-right degree-16 GCD against left product-span annihilator',
       'panels':['witness','negative'],'domain':'all 128 right-span values, with 40 valid codes marked',
       'worker_count':1,'worker_alarm_s':120,'rss_boundary_bytes':4294967296,
       'correction':'Convert archived JSON pair lists to tuples before equality comparison.',
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}}
with (HERE/'protocol_v2.json').open('x') as output:json.dump(proto,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'protocol_v2.json').read_bytes()).hexdigest()}))
