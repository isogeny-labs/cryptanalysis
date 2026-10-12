"""Build exact folded-column-shield four-pair controls and public projection."""
import hashlib,json,sys,time
from pathlib import Path
from fourpair_v2 import build,check_assignment,field_config
h=Path(__file__).resolve().parent
mode=sys.argv[1]
assert mode in ('n41_control','n131_control','n131_public')
p=json.loads((h/'v2_protocol.json').read_text())
def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
paths={'script':h/'v2_build.py','builder':h/'fourpair_v2.py',
       'n41_fixture':h/'n41_diagonal/control_fixture.json',
       'n131_fixture':h/'n131_control_fixture.json',
       'n41_support':h.parent/'n41_w7_entropy_cubic_20261011/w8/geometry.json',
       'n131_support':h.parent/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv',
       'public_target':h.parent/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'}
assert {k:sha(v) for k,v in paths.items()}==p['sha256']
name='n41' if mode=='n41_control' else 'n131'
fixture=None
if mode=='n41_control':fixture=json.loads(paths['n41_fixture'].read_text());z=int(fixture['target_reciprocal'])
elif mode=='n131_control':fixture=json.loads(paths['n131_fixture'].read_text());z=int(fixture['target_reciprocal'])
else:
    target=json.loads(paths['public_target'].read_text())
    assert target['curve_id']=='EC1N131Ckb1heb5f1998f20b' and target['workload_id']=='cc09e7eb202a'
    field,_,_=field_config('n131');x=int(target['preimages'][0]['point'][0]);z=field.inverse(x)
    assert field.mul(x,z)==1
start=time.monotonic_ns();c,wires,meta=build(name,z);built=time.monotonic_ns()
check=None
if fixture is not None:
    field,_,rotations=field_config(name)
    check=check_assignment(c,wires,fixture,field,rotations)
checked=time.monotonic_ns()
formula=h/('v2_'+mode+'.xcnf');assert not formula.exists();c.write(formula)
end=time.monotonic_ns()
result={'status':'PASS_EXACT_FOLDED_COLUMN_CONTROL' if check else 'PASS_EXACT_FOLDED_COLUMN_FORMULA_PROJECTION',
        'mode':mode,'candidate_id':None,'variables':c.next_var-1,'and_gates':c.and_count,
        'clauses':len(c.clauses),'xor_rows':len(c.xors),'formula_bytes':formula.stat().st_size,
        'formula_sha256':sha(formula),'build_ns':built-start,'check_ns':checked-built,
        'write_ns':end-checked,'metadata':meta,'control_check':check,
        'protocol_sha256':sha(h/'v2_protocol.json')}
path=h/('v2_'+mode+'.json');assert not path.exists();path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(result['status'],mode,result['variables'],flush=True)
