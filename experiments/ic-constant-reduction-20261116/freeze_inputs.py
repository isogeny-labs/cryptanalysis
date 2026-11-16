#!/usr/bin/env python3
"""Exact fixed-base method and fresh one-target workload manifests."""
import argparse,gzip,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
p=argparse.ArgumentParser();p.add_argument('probe',type=Path);args=p.parse_args()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def write(path,v):
 if path.exists() and json.loads(path.read_text())!=v:raise ValueError('immutable input differs: '+str(path))
 path.write_text(json.dumps(v,indent=2)+'\n')
from source_manifest import hashes as source_hashes
hashes=source_hashes()
identities={}
for index,record in enumerate(json.loads((HERE/'instances.json').read_text())):
 n=record['field']['degree'];cid=record['curve_id'];curve=dict(record['curve'],curve_id=cid)
 row=json.loads((HERE/f'archive-n{n}.json').read_text())
 doc=json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/row['path']).read_bytes()))
 assert doc['field']==record['field'] and doc['curve']==curve
 fb=doc['factor_base'];case={'workloads':{},'archive':row}
 for mode,rc,targets in [('mitm-walk16-vector-narrow','walk16vector','walk-batch16-vector'),('mitm-walk16-vector-const','walk16vector','walk-batch16-vector')]:
  family='vector64' if n<=21 else 'vector1024'
  params=dict(m=2,batch_size=64 if n<=21 else 1024,x_only=1,prefix_inverse_cache=1,vector_prepare=3 if mode.endswith("-const") else 4)
  candidate={'schema':'ic-bench-candidate/1','field':record['field'],'curve':curve,'factor_base':fb,
   'point_decomposition':{'summands':2,'solver_family':family,'stage_code':'PDP2'+family,
    'oracle':'mitm-batched','params':params,
    'projection_cap_policy':'complete subtraction fallback','zero_target_policy':'complete subtraction fallback',
    'setup_policy':'cold target-independent setup charged once per single target'},
   'relation_collection':{'stage_code':'RC'+rc,'targets':targets,'lanes':1 if rc=='walk' else 16,'native_pairwise':rc in ['walk16native','walk16vector'],'vector_point_formulas':rc=='walk16vector','generated_point_cap':record['max_trials'],'max_trials':record['max_trials']},
   'relation_linear_algebra':{'stage_code':'LAgauss','implementation':'incremental-gauss'},
   'target_descent':{'stage_code':'TDdirect','rule':'one target column in relation matrix'},'isogeny':'none',
   'implementation':{'entry_point':'suite/examples/ic_affine_pipeline_probe.rs -> run_pipeline',
    'sources_sha256':hashes,'cargo_features':[],'vector_policy':'ordinary-pclmul128-for-table; runtime-full-point-query', 'reduction_policy':'exact-constant-polynomial' if mode.endswith('-const') else 'dynamic-polynomial', 'square_policy':'product','query_arithmetic':'shared-inverse-vector-full-point' if rc=='walk16vector' else 'native-pairwise-batch' if rc=='walk16native' else 'scalar-pair-additions'}}
  prefix=cid.split('h')[0].replace('EC1','IC1',1)
  candidate_id=f"{prefix}fb{fb['actual_usable_point_count']}PDP2{family}RC{rc}LAgaussTDdirectISO0h{digest(candidate)[:12]}"
  write(ROOT/'experiments/ic-bench/candidates'/f'{candidate_id}.json',candidate);case[mode]=candidate_id
 for fixture in range(432,456):
  native=json.loads(subprocess.check_output([str(args.probe.resolve()),str(HERE/'instances.json'),str(index),'workload',str(fixture)],text=True))
  assert native['curve_id']==cid
  workload={'schema':'ic-bench-workload/1','curve_id':cid,'subgroup_order':record['curve']['subgroup_order'],
   'target_count':1,'cache_state':'cold','fixture':fixture,'prng':'StdRng rand pinned in suite/Cargo.lock',
   'target_law':'public fixed seed law in ic_affine_pipeline_probe.rs; scalar uniform on [1,r-1]',
   'targets':[[native['planted'],*native['target']]],'walk_seed':native['target_seed'],
   'rho_reference':'separate fresh plain and negation processes on this exact point and walk seed'}
  wid=digest(workload)[:12];write(ROOT/'experiments/ic-bench/workloads'/f'{wid}.json',workload)
  case['workloads'][str(fixture)]=wid
 identities[str(index)]=case
write(HERE/'identities.json',identities)
print(json.dumps({'curves':5,'candidates':10,'one_target_workloads':120}))
