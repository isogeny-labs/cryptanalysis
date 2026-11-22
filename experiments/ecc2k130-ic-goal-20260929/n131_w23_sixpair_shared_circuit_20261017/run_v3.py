"""Matched six-pair build with public point converted to standard reciprocal 1/x."""
import hashlib,json,resource,time
from pathlib import Path
import circuit
import importlib.util
_spec=importlib.util.spec_from_file_location('w23_assignment',Path(__file__).resolve().parent/'run.py')
_module=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_module)
assignment=_module.assignment
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
FIX=HERE/'fixture.json'
PUBLIC=ROOT/'n131_fixed_seed_eight_pair_circuit_20261010/target_preimages.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    protocol=json.loads((HERE/'protocol_v3.json').read_text())
    paths={'circuit':HERE/'circuit.py','run_v3':HERE/'run_v3.py','assignment':HERE/'run.py',
           'fixture':FIX,'public':PUBLIC,'runtime':HERE/'sage_runtime_info.json'}
    assert all(sha(path)==protocol['source_sha256'][name] for name,path in paths.items())
    fix=json.loads(FIX.read_text())
    public=json.loads(PUBLIC.read_text())['preimages'][0]
    public_standard=circuit.F.inverse(public['point'][0])
    assert public_standard!=public['reciprocal_x_z']
    rows=[]
    for name,target in (('control',fix['target_reciprocal']),('public',public_standard)):
        for variant in protocol['variant_order']:
            start=time.monotonic_ns()
            machine,wires,counts=circuit.build(target,variant)
            built=time.monotonic_ns(); checks=None
            if name=='control':
                import sys
                sys.path.insert(0,str(ROOT/'n131_w20_selector_elimination_v2_20261013'))
                import selector as old
                full=old.old.complete_assignment(machine,assignment(wires,fix,variant))
                checks=old.old.check_assignment(machine,full)
            checked=time.monotonic_ns()
            rows.append({'target':name,'variant':variant,**counts,
                         'build_ns':built-start,'check_ns':checked-built,
                         'control_check':checks,
                         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
            print(json.dumps({'target':name,'variant':variant,'counts':counts,'control_check':checks}),flush=True)
    out={'status':'COMPLETE','candidate_id':None,'curve_id':fix['curve_id'],
         'target_public_point':public['point'],'target_public_standard_reciprocal':public_standard,
         'target_public_archived_shifted_reciprocal':public['reciprocal_x_z'],
         'control_raw_point':fix['target_raw_point'],'control_subgroup_point':fix['subgroup_point'],
         'rows':rows,'source_sha256':protocol['source_sha256'],
         'protocol_sha256':sha(HERE/'protocol_v3.json'),
         'source_semantics':'Exact fixed-seed eligible endpoints and six-pair S3 target links; distinct folded columns checked on constructed control only.'}
    with (HERE/'result_v3.json').open('x') as file:json.dump(out,file,sort_keys=True,indent=2);file.write('\n')
if __name__=='__main__':main()
