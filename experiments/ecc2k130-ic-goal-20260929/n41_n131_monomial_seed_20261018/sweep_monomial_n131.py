"""Exact W29 monomial-seed circuit sweep on one frozen N131 public point."""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'sweep_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_SWEEP'
for label,item in cfg['sources'].items():
    assert sha(item['path'])==item['sha256'],label
path=ROOT/'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
spec=importlib.util.spec_from_file_location('sweep_design',path)
design=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=design
spec.loader.exec_module(design)
target=design.F.inverse(cfg['public_raw_x'])
assert target==cfg['public_reciprocal']
rows=[]
for k in cfg['k_values']:
    mask=(1<<(k-1))|(1<<(2*k-1))
    seed=mask<<1
    h=design.previous.halftrace(seed)
    assert h==(1<<k) and design.previous.trace(h)==0
    bits=[i for i in range(design.WIDTH) if i!=mask.bit_length()-1]
    base=[1<<(i+1) for i in bits]
    assert len(bits)==28 and all(design.previous.trace(v)==0 for v in base)
    design.SEED_MASK=mask
    design.SEED=seed
    design.H=design.F.square(h)
    design.C=1^design.H
    design.BITS=bits
    design.BASE=base
    design.PB=[design.F.square(v)^design.F.mul(seed,v) for v in base]
    start=time.monotonic()
    circuit,_,counts=design.build(target)
    row={'k':k,'seed_mask':mask,'H':design.H,'C':design.C,
         'build_wall_seconds':time.monotonic()-start,**counts}
    rows.append(row)
    print(json.dumps(row,sort_keys=True),flush=True)
    del circuit
(HERE/'sweep_result.json').write_text(json.dumps({'status':'COMPLETE_EXACT_N131_MONOMIAL_SWEEP',
    'candidate_id':None,'public_reciprocal':target,
    'protocol_sha256':sha(HERE/'sweep_protocol.json'),'script_sha256':sha(Path(__file__)),
    'rows':rows},indent=2,sort_keys=True)+'\n')
