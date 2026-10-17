"""Freeze independent curve-sum replay of the three-code survivor."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
files={'audit_sage':HERE/'audit_sage.py','sweep_result':HERE/'sweep_result.json',
       'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','audit':'independent N41 group sum of all 64 signed states in each retained code triple',
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}}
with (HERE/'audit_protocol.json').open('x') as output:json.dump(proto,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'audit_protocol.json').read_bytes()).hexdigest()}))
