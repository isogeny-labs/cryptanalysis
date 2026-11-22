"""Freeze isolated-process interpolation with identical selection and panels."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
prior=json.loads((HERE/'protocol.json').read_text())
files={'parent_v2':HERE/'parent_v2.py','sample_sage':HERE/'sample_sage.py',
       'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'prior':ROOT/'n41_w8_three_pair_resultant_20261013/result.json',
       'witness_archived':OLD/'result.json','negative_archived':OLD/'control_result.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={k:prior[k] for k in ('curve_id','method','sample_first_products','holdout_first_products','panel_order','worker_count','rss_boundary_bytes')}
proto['method']='same degree-16 interpolation with sequential isolated checked-Sage specializations'
proto['alarm_s_per_panel']=300
proto['child_timeout_s']=45
proto['source_sha256']={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}
with (HERE/'protocol_v2.json').open('x') as out:json.dump(proto,out,indent=2,sort_keys=True);out.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'protocol_v2.json').read_bytes()).hexdigest()}))
