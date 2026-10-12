"""Construct and measure the exact public-target N131 formula without solving."""
import hashlib,json,time
from pathlib import Path
from fourpair import build, field_config
h=Path(__file__).resolve().parent
p=json.loads((h/'projection_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'script':h/'project_n131.py','builder':h/'fourpair.py',
       'support':h.parent/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv',
       'target':h.parent/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
assert not (h/'n131_projection_result.json').exists()
target=json.loads(paths['target'].read_text())
assert target['workload_id']=='cc09e7eb202a' and target['curve_id']=='EC1N131Ckb1heb5f1998f20b'
field,_,_=field_config('n131')
raw_x=int(target['preimages'][0]['point'][0])
z=field.inverse(raw_x)
assert field.mul(raw_x,z)==1
start=time.monotonic_ns();c,wires,meta=build('n131',z);built=time.monotonic_ns()
path=h/'n131_projection.xcnf'
assert not path.exists();c.write(path);end=time.monotonic_ns()
result={'status':'PASS_N131_ALLSEED_FOURPAIR_FORMULA_PROJECTION','candidate_id':None,
        'curve_id':target['curve_id'],'workload_id':target['workload_id'],
        'raw_preimage_index':0,'target_reciprocal':z,
        'variables':c.next_var-1,'and_gates':c.and_count,'clauses':len(c.clauses),
        'xor_rows':len(c.xors),'formula_bytes':path.stat().st_size,
        'formula_sha256':sha(path),'build_ns':built-start,'write_ns':end-built,
        'metadata':meta,'projection_protocol_sha256':sha(h/'projection_protocol.json')}
(h/'n131_projection_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result),flush=True)
