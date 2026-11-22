"""Freeze corrected ordinary public target for the curve-sum audit."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
files={'audit_sage_v2':HERE/'audit_sage_v2.py','sweep_result':HERE/'sweep_result.json',
       'geometry':ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json',
       'public':ROOT/'n41_w8_fixedseed_ordinary_join_20261013/protocol.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','audit':'independent N41 group sum of all 64 signed states in each retained code triple',
       'public_target_source':'n41_w8_fixedseed_ordinary_join_20261013/protocol.json',
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in files.items()}}
with (HERE/'audit_protocol_v2.json').open('x') as output:json.dump(proto,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256((HERE/'audit_protocol_v2.json').read_bytes()).hexdigest()}))
