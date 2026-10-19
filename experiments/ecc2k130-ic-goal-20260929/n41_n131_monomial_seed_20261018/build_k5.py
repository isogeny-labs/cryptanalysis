"""Build exact W29 k=5 N131 public XCNF from frozen circuit sources."""
import hashlib, importlib.util, json, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'build_k5_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_BUILD'
for label,item in cfg['sources'].items():
    assert sha(item['path'])==item['sha256'],label
path=ROOT/'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
spec=importlib.util.spec_from_file_location('k5_design',path)
design=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=design
spec.loader.exec_module(design)
k=5
mask=(1<<(k-1))|(1<<(2*k-1))
assert mask==528
design.SEED_MASK=mask; design.SEED=mask<<1
h=design.previous.halftrace(design.SEED)
assert h==1<<k and design.previous.trace(h)==0
design.H=design.F.square(h); design.C=1^design.H
design.BITS=[i for i in range(design.WIDTH) if i!=mask.bit_length()-1]
design.BASE=[1<<(i+1) for i in design.BITS]
design.PB=[design.F.square(v)^design.F.mul(design.SEED,v) for v in design.BASE]
target=design.F.inverse(cfg['public_raw_x'])
assert target==cfg['public_reciprocal']
start=time.monotonic()
circuit,wires,counts=design.build(target)
assert {k:counts[k] for k in cfg['expected_counts']}==cfg['expected_counts']
built=time.monotonic()
formula=HERE/'n131_k5_public.xcnf'
assert not formula.exists()
circuit.write(formula)
written=time.monotonic()
result={'status':'COMPLETE_EXACT_K5_FORMULA','candidate_id':None,'counts':counts,
        'public_reciprocal':target,'formula_sha256':sha(formula),'formula_bytes':formula.stat().st_size,
        'build_wall_seconds':built-start,'serialize_wall_seconds':written-built,
        'protocol_sha256':sha(HERE/'build_k5_protocol.json'),'builder_sha256':sha(Path(__file__))}
(HERE/'build_k5_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True),flush=True)
