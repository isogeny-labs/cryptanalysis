"""Read-only source, arithmetic, and receipt audit of the paired build."""
import hashlib,json
from pathlib import Path
import circuit
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def s3(a,b,z):
    F=circuit.F;ab=F.mul(a,b);abz=F.mul(ab,z)
    return F.square(abz)^abz^F.square(a^b)^F.square(z)
proto=json.loads((HERE/'protocol_v3.json').read_text())
result=json.loads((HERE/'result_v3.json').read_text())
fixture=json.loads((HERE/'fixture.json').read_text())
public=json.loads((ROOT/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json').read_text())['preimages'][0]
paths={'circuit':HERE/'circuit.py','run_v3':HERE/'run_v3.py','assignment':HERE/'run.py',
       'fixture':HERE/'fixture.json',
       'public':ROOT/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json',
       'runtime':HERE/'sage_runtime_info.json'}
assert all(sha(p)==proto['source_sha256'][k] for k,p in paths.items())
assert sha(HERE/'protocol_v3.json')==result['protocol_sha256']
assert fixture['source_audit_sha256']==sha(ROOT/'n131_w23_sixpair_density_20261016/sage_audit_result.json')
assert circuit.F.inverse(public['point'][0])==result['target_public_standard_reciprocal']
assert public['reciprocal_x_z']==result['target_public_archived_shifted_reciprocal']
assert circuit.F.inverse(public['point'][0]^1)==public['reciprocal_x_z']
assert circuit.F.inverse(fixture['target_raw_point'][0])==fixture['target_reciprocal']
assert len(fixture['pairs'])==6 and len(fixture['middle_reciprocals'])==4
cols=[];nodes=[]
for slot,row in enumerate(fixture['pairs']):
    a,b=row['masks'];cols.extend(row['columns'])
    assert a^b==circuit.SEED_MASK
    av,bv=a<<1,b<<1
    p=circuit.F.mul(av,bv)
    assert p==row['source_product']
    assert circuit.F.mul(p,row['source_inverse_product'])==1
    assert circuit.trace(av)==circuit.trace(bv)==0
    assert circuit.trace(circuit.F.inverse(av))==circuit.trace(circuit.F.inverse(bv))==0
    z=row['output_reciprocal']
    assert circuit.F.mul(z,row['output_inv'])==1
    assert (circuit.F.mul(circuit.C,circuit.F.square(z))^circuit.F.mul(p,z)^circuit.H)==0
    nodes.append(circuit.F.frob(z,circuit.ROTATIONS[slot]))
assert len(set(cols))==12
nodes+=fixture['middle_reciprocals']+[fixture['target_reciprocal']]
assert all(s3(nodes[i],nodes[j],nodes[k])==0 for i,j,k in circuit.LINKS)
rows=result['rows'];assert len(rows)==4
for row in rows:
    assert row['control_check'] is None or row['control_check']=={
        'clauses':row['clauses'],'native_xor_rows':row['xor_rows']}
    assert row['and_gates']>0 and row['clauses']>0 and row['build_ns']>0
for target in ('control','public'):
    sh=next(x for x in rows if x['target']==target and x['variant']=='shared')
    two=next(x for x in rows if x['target']==target and x['variant']=='two')
    assert sh['and_gates']<two['and_gates'] and sh['clauses']<two['clauses']
    assert sh['and_gates']==86937 and two['and_gates']==100881
assert result['candidate_id'] is None
out={'status':'PASS','source_hashes':len(paths),'pair_equations':6,'s3_links':5,
     'distinct_folded_columns':len(set(cols)),'checked_circuit_rows':4,
     'control_clauses_checked':sum(r['clauses'] for r in rows if r['target']=='control'),
     'control_xor_rows_checked':sum(r['xor_rows'] for r in rows if r['target']=='control')}
(HERE/'verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True))
