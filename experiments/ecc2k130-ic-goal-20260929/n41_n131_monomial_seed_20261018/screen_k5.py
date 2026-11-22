"""Check full exact W29 k5 circuit on the independently built group witness."""
import hashlib,importlib.util,json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((HERE/'screen_k5_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_SCREEN'
for label,item in cfg['sources'].items():assert sha(item['path'])==item['sha256'],label
sys.path.insert(0,str(ROOT/'n131_w20_selector_elimination_v2_20261013'))
import selector
path=ROOT/'n41_n131_fivepair_w9_w29_20261017/circuit_n131_3p2.py'
spec=importlib.util.spec_from_file_location('k5_control_design',path)
design=importlib.util.module_from_spec(spec);sys.modules[spec.name]=design;spec.loader.exec_module(design)
mask=528;design.SEED_MASK=mask;design.SEED=mask<<1
h=design.previous.halftrace(design.SEED)
assert h==1<<5 and design.previous.trace(h)==0
design.H=design.F.square(h);design.C=1^design.H
design.BITS=[i for i in range(design.WIDTH) if i!=mask.bit_length()-1]
design.BASE=[1<<(i+1) for i in design.BITS]
design.PB=[design.F.square(v)^design.F.mul(design.SEED,v) for v in design.BASE]
control=json.loads((HERE/'control_k5.json').read_text())
start=time.monotonic();circuit,wires,counts=design.build(control['target_reciprocal'])
assignment={}
def bind(bits,word):assignment.update({v:(word>>j)&1 for j,v in enumerate(bits)})
for slot,row in enumerate(control['pairs']):
    code=sum(((row['masks'][0]>>bit)&1)<<j for j,bit in enumerate(design.BITS))
    bind(wires['mask'][slot],code)
    bind(wires['out'][slot],row['output_reciprocal'])
    bind(wires['source_inverse'][slot],row['source_inverse_product'])
for bits,word in zip(wires['middle'],control['middle_reciprocals']):bind(bits,word)
full=selector.old.complete_assignment(circuit,assignment)
check=selector.old.check_assignment(circuit,full)
assert check['clauses']==len(circuit.clauses) and check['native_xor_rows']==len(circuit.xors)
result={'status':'PASS_EXACT_K5_CONSTRUCTED_CIRCUIT','candidate_id':None,'counts':counts,
        'check':check,'bound_inputs':len(assignment),'completed_variables':len(full),
        'wall_seconds':time.monotonic()-start,'protocol_sha256':sha(HERE/'screen_k5_protocol.json'),
        'script_sha256':sha(Path(__file__))}
(HERE/'screen_k5_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True),flush=True)
