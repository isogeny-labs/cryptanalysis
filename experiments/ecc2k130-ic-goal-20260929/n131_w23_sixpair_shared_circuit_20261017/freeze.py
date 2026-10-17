"""Freeze source and fixture identities before the paired circuit build."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
paths={'circuit':HERE/'circuit.py','run':HERE/'run.py','fixture':HERE/'fixture.json',
       'public':ROOT/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json',
       'runtime':HERE/'sage_runtime_info.json'}
proto={'curve_id':'EC1N131Ckb1heb5f1998f20b','source':'W23 canonical fixed seed 898618',
       'rotations':[0,18,36,54,72,90],'variant_order':['shared','two'],
       'targets':['constructed six-pair control','frozen ordinary public raw preimage 0'],
       'measurement':'full circuit build and constructed assignment, ordinary host, one process',
       'source_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()}}
path=HERE/'protocol.json'
with path.open('x') as output:json.dump(proto,output,sort_keys=True,indent=2);output.write('\n')
print(json.dumps({'protocol_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
