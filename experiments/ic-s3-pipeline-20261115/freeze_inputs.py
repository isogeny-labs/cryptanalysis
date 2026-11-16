#!/usr/bin/env python3
"""Materialize frozen public targets and exact immutable method identities."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('probe',type=Path)
args=parser.parse_args()


def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def write(path,v):
    if path.exists() and json.loads(path.read_text())!=v:raise ValueError('immutable input differs: '+str(path))
    path.write_text(json.dumps(v,indent=2)+'\n')


sources=['suite/examples/ic_s3_pipeline_probe.rs','suite/Cargo.toml','suite/Cargo.lock',
         'suite/src/cryptanalysis/pq_descent_symbolic.rs','suite/src/cryptanalysis/ic_framework/mod.rs',
         'suite/src/cryptanalysis/ic_framework/plugins.rs','suite/src/cryptanalysis/ic_framework/solvers.rs',
         'suite/src/cryptanalysis/ic_framework/linalg.rs','suite/src/cryptanalysis/ic_boundary.rs',
         'suite/src/cryptanalysis/koblitz_fast.rs','suite/src/cryptanalysis/semaev_decomp.rs']
source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}
identities={}
for index,record in enumerate(json.loads((HERE/'instances.json').read_text())):
 n=record['field']['degree'];cid=record['curve_id'];curve=dict(record['curve'],curve_id=cid)
 row=json.loads((HERE/f'archive-n{n}.json').read_text())
 doc=json.loads(gzip.decompress((ROOT/'experiments/fb-archive'/row['path']).read_bytes()))
 assert doc['field']==record['field'] and doc['curve']==curve
 fb=doc['factor_base'];case={'workloads':{}}
 for method,family in [('buchberger-f2','buchbergerf2'),('f4-f2','f4f2'),('fes-f2-wide','feswide'),('mitm','mitm')]:
  case[method]={}
  for variant in ['reference','direct']:
   candidate={'schema':'ic-bench-candidate/1','field':record['field'],'curve':curve,'factor_base':fb,
     'point_decomposition':{'summands':2,'solver_family':family,'stage_code':'PDP2'+family,
       'oracle':'mitm' if method=='mitm' else 'descent-algebraic','solver':None if method=='mitm' else method,
       'solver_budget_seconds':1,'constructor':'direct S3 coefficients' if variant=='direct' else 'generic symbolic S3',
       'negation_folded':True},
     'relation_collection':{'stage_code':'RCwalk','targets':'walk','max_trials':50000},
     'relation_linear_algebra':{'stage_code':'LAgauss','implementation':'incremental-gauss'},
     'target_descent':{'stage_code':'TDdirect','rule':'single target column in relation matrix'},
     'isogeny':'none','implementation':{'entry_point':'suite/examples/ic_s3_pipeline_probe.rs -> run_pipeline',
       'sources_sha256':source_hashes,'cargo_features':[] if variant=='reference' else ['s3-direct-coefficients']}}
   prefix=cid.split('h')[0].replace('EC1','IC1',1)
   candidate_id=f"{prefix}fb{fb['actual_usable_point_count']}PDP2{family}RCwalkLAgaussTDdirectISO0h{digest(candidate)[:12]}"
   write(ROOT/'experiments/ic-bench/candidates'/f'{candidate_id}.json',candidate)
   case[method][variant]=candidate_id
 for fixture in range(100,106):
  native=json.loads(subprocess.check_output([str(args.probe.resolve()),str(HERE/'instances.json'),str(index),'workload',str(fixture)],text=True))
  assert native['curve_id']==cid
  workload={'schema':'ic-bench-workload/1','curve_id':cid,'subgroup_order':record['curve']['subgroup_order'],
    'target_count':1,'cache_state':'cold','fixture':fixture,'prng':'StdRng rand pinned in suite/Cargo.lock',
    'target_law':'public fixed seed law in ic_s3_pipeline_probe.rs; scalar uniform on [1,r-1]',
    'targets':[[native['planted'],*native['target']]],'walk_seed':native['target_seed'],
    'rho_reference':'plain and negation-map repository walks on this exact target and seed'}
  wid=digest(workload)[:12]
  write(ROOT/'experiments/ic-bench/workloads'/f'{wid}.json',workload)
  case['workloads'][str(fixture)]=wid
 identities[str(index)]=case
write(HERE/'identities.json',identities)
print(json.dumps({'curves':len(identities),'candidates':16,'single_target_workloads':12}))
