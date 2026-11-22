"""Build paired source-gate variants and check the full constructed target."""
import hashlib,json,resource,time
from pathlib import Path
import circuit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
FIX=HERE/'fixture.json'
PUBLIC=ROOT/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(values,wires,value):
    values.update({w:(value>>i)&1 for i,w in enumerate(wires)})

def assignment(wires,fixture,variant):
    values={}
    for slot,row in enumerate(fixture['pairs']):
        a,b=row['masks'];assert a^b==circuit.SEED_MASK
        code=sum(((a>>bit)&1)<<j for j,bit in enumerate(circuit.BITS))
        bind(values,wires['mask'][slot],code)
        bind(values,wires['out'][slot],row['output_reciprocal'])
        if variant=='shared':
            bind(values,wires['source_inverse'][slot][0],row['source_inverse_product'])
        else:
            bind(values,wires['source_inverse'][slot][0],circuit.F.inverse(a<<1))
            bind(values,wires['source_inverse'][slot][1],circuit.F.inverse(b<<1))
    for bits,value in zip(wires['middle'],fixture['middle_reciprocals']):bind(values,bits,value)
    return values

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for name,path in {'circuit':HERE/'circuit.py','run':HERE/'run.py',
                      'fixture':FIX,'public':PUBLIC,'runtime':HERE/'sage_runtime_info.json'}.items():
        assert sha(path)==protocol['source_sha256'][name],name
    fix=json.loads(FIX.read_text())
    public=json.loads(PUBLIC.read_text())['preimages'][0]
    assert fix['curve_id']==public.get('curve_id',fix['curve_id'])
    targets=[('control',fix['target_reciprocal']),('public',public['reciprocal_x_z'])]
    rows=[]
    for name,target in targets:
        for variant in protocol['variant_order']:
            start=time.monotonic_ns()
            machine,wires,counts=circuit.build(target,variant)
            built=time.monotonic_ns()
            checks=None
            if name=='control':
                initial=assignment(wires,fix,variant)
                # The assignment logic comes from a separately authored circuit checker.
                import sys
                sys.path.insert(0,str(ROOT/'n131_w20_selector_elimination_v2_20261013'))
                import selector as old
                full=old.old.complete_assignment(machine,initial)
                checks=old.old.check_assignment(machine,full)
            checked=time.monotonic_ns()
            rows.append({'target':name,'variant':variant,**counts,
                         'build_ns':built-start,'check_ns':checked-built,
                         'control_check':checks,
                         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
            print(json.dumps({'target':name,'variant':variant,'counts':counts,'control_check':checks}),flush=True)
    out={'status':'COMPLETE','candidate_id':None,'curve_id':fix['curve_id'],
         'target_public_point':public['point'],'target_public_reciprocal':public['reciprocal_x_z'],
         'control_raw_point':fix['target_raw_point'],'control_subgroup_point':fix['subgroup_point'],
         'rows':rows,'source_sha256':protocol['source_sha256'],
         'protocol_sha256':sha(HERE/'protocol.json'),
         'source_semantics':'Exact fixed-seed eligible endpoints and six-pair S3 target links; distinct folded columns checked on constructed control only.'}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
