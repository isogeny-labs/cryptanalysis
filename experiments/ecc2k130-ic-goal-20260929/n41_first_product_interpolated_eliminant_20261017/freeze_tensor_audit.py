"""Freeze reverse-order full-cube arithmetic audit."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
files={'audit_tensor_sage':HERE/'audit_tensor_sage.py',
       'sweep_result':HERE/'sweep_result.json','geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'witness_tensor':HERE/'witness_result_v2.json','negative_tensor':HERE/'negative_result_v2.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','audit':'reverse-order p-polynomial evaluation over all 40 cubed product triples per panel',
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}}
with (HERE/'tensor_audit_protocol.json').open('x') as output:json.dump(proto,output,indent=2,sort_keys=True);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'tensor_audit_protocol.json').read_bytes()).hexdigest()}))
