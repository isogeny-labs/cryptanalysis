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
sources=['suite/examples/ic_affine_pipeline_probe.rs','suite/Cargo.toml','suite/Cargo.lock',
 'suite/src/cryptanalysis/s3_affine_projection.rs','suite/src/cryptanalysis/ic_framework/affine.rs',
 'suite/src/cryptanalysis/ic_framework/batch_mitm.rs','suite/src/cryptanalysis/ic_framework/mod.rs','suite/src/cryptanalysis/ic_framework/plugins.rs',
 'suite/src/cryptanalysis/ic_framework/u32_reciprocal.rs','suite/src/cryptanalysis/ic_framework/linalg.rs','suite/src/cryptanalysis/ic_boundary.rs',
 'suite/src/cryptanalysis/koblitz_fast.rs','suite/src/cryptanalysis/semaev_decomp.rs']
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
identities={}
for index,record in enumerate(json.loads((HERE/'instances.json').read_text())):
 n=record['field']['degree'];cid=record['curve_id'];curve=dict(record['curve'],curve_id=cid)
 row=json.loads((HERE/f'archive-n{n}.json').read_text())
 doc=json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/row['path']).read_bytes()))
 assert doc['field']==record['field'] and doc['curve']==curve
 fb=doc['factor_base'];case={'workloads':{},'archive':row}
 for mode,family in [('mitm-prefix','prefixchain'),('mitm-prefix-u32','prefixchainu32'),('mitm-euclid','prefixeuclid'),('mitm-euclid-u32','prefixeuclidu32')]:
  params=dict(m=2,batch_size=1024,x_only=1,prefix_inverse_cache=1)
  candidate={'schema':'ic-bench-candidate/1','field':record['field'],'curve':curve,'factor_base':fb,
   'point_decomposition':{'summands':2,'solver_family':family,'stage_code':'PDP2'+family,
    'oracle':'mitm-batched','params':params,
    'projection_cap_policy':'complete subtraction fallback','zero_target_policy':'complete subtraction fallback',
    'setup_policy':'cold target-independent setup charged once per single target'},
   'relation_collection':{'stage_code':'RCwalk','targets':'walk','max_trials':record['max_trials']},
   'relation_linear_algebra':{'stage_code':'LAgaussu32' if mode.endswith('u32') else 'LAgauss','implementation':'incremental-gauss-u32' if mode.endswith('u32') else 'incremental-gauss'},
   'target_descent':{'stage_code':'TDdirect','rule':'one target column in relation matrix'},'isogeny':'none',
   'implementation':{'entry_point':'suite/examples/ic_affine_pipeline_probe.rs -> run_pipeline',
    'sources_sha256':hashes,'cargo_features':[],'field_inverse':'euclidean-u32' if 'euclid' in mode else 'itoh-tsujii'}}
  prefix=cid.split('h')[0].replace('EC1','IC1',1)
  candidate_id=f"{prefix}fb{fb['actual_usable_point_count']}PDP2{family}RCwalkLAgaussTDdirectISO0h{digest(candidate)[:12]}"
  write(ROOT/'experiments/ic-bench/candidates'/f'{candidate_id}.json',candidate);case[mode]=candidate_id
 for fixture in range(256,280):
  native=json.loads(subprocess.check_output([str(args.probe.resolve()),str(HERE/'instances.json'),str(index),'workload',str(fixture)],text=True))
  assert native['curve_id']==cid
  workload={'schema':'ic-bench-workload/1','curve_id':cid,'subgroup_order':record['curve']['subgroup_order'],
   'target_count':1,'cache_state':'cold','fixture':fixture,'prng':'StdRng rand pinned in suite/Cargo.lock',
   'target_law':'public fixed seed law in ic_affine_pipeline_probe.rs; scalar uniform on [1,r-1]',
   'targets':[[native['planted'],*native['target']]],'walk_seed':native['target_seed'],
   'rho_reference':'separate fresh plain/negation processes with both original and Euclidean backends on this exact point and walk seed'}
  wid=digest(workload)[:12];write(ROOT/'experiments/ic-bench/workloads'/f'{wid}.json',workload)
  case['workloads'][str(fixture)]=wid
 identities[str(index)]=case
write(HERE/'identities.json',identities)
print(json.dumps({'curves':5,'candidates':20,'one_target_workloads':120}))
