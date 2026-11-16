#!/usr/bin/env python3
"""Freeze one public development point and pinned profiling prerequisites."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('probe',type=Path);args=parser.parse_args()
sys.path.insert(0,str(ROOT/'cloud'));import modal_run as modal
sys.path.insert(0,str(ROOT/'experiments/fb-archive'));from purepy import PyField;from external import _smul
old=ROOT/'experiments/ic-packed-square-20261116'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def write(p,data):
 if p.exists():assert p.read_bytes()==data,'immutable profile input differs: '+str(p)
 p.write_bytes(data)
def write_json(p,v):write(p,(json.dumps(v,indent=2)+'\n').encode())
write(P/'instances.json',(old/'instances.json').read_bytes());inst=json.loads((P/'instances.json').read_text())[4]
ids=json.loads((old/'identities.json').read_text())['4'];candidatepins={}
for mode in ['mitm-vector','mitm-vector-packed']:
 path=ROOT/'experiments/ic-bench/candidates'/(ids[mode]+'.json');candidate=json.loads(path.read_text());candidatepins[path.name]=sha(path)
 assert hashlib.sha256(canonical(candidate)).hexdigest().startswith(ids[mode].rsplit('h',1)[1])
 for name,pin in candidate['implementation']['sources_sha256'].items():assert sha(ROOT/name)==pin
native=json.loads(subprocess.check_output([str(args.probe.resolve()),str(P/'instances.json'),'4','workload','0'],text=True))
assert native['curve_id']==inst['curve_id']
integer=lambda v:int(v,0) if isinstance(v,str) and v.startswith('0x') else int(v)
f=inst['field'];c=inst['curve'];K=PyField(f['degree'],sum(1<<e for e in f['modulus_exponents']))
assert _smul(K,integer(c['coefficients'][1]),tuple(map(integer,c['generator'])),native['planted'])==tuple(native['target'])
workload={'schema':'ic-bench-workload/1','curve_id':inst['curve_id'],'subgroup_order':c['subgroup_order'],'target_count':1,'cache_state':'cold','fixture':0,'prng':'StdRng rand pinned in suite/Cargo.lock','target_law':'public fixed seed law in ic_affine_pipeline_probe.rs; scalar uniform on [1,r-1]','targets':[[native['planted'],*native['target']]],'walk_seed':native['target_seed'],'rho_reference':'separate fresh plain and negation processes on this exact point and walk seed'}
write_json(P/'workload.json',workload);wid=hashlib.sha256(canonical(workload)).hexdigest()[:12]
registered=ROOT/'experiments/ic-bench/workloads'/(wid+'.json')
if registered.exists():assert json.loads(registered.read_text())==workload
else:write_json(registered,workload)
job='20261116-112736-c9d0';metadata=modal.read_bytes(modal.volume(),job+'/job.json');assert metadata
write(P/'timing-job-metadata.json',metadata)
cal=json.loads((old/'timing-001/calibration-4.json').read_text());assert cal['curve_id']==inst['curve_id']
assert all(cal['calibration'][k]>0 for k in ['ns_per_add','ns_per_double','ns_per_lookup','ns_per_row_op'])
doc=dict(schema='ic-native-profile-input/1',prepared=json.loads((old/'prepared-input.json').read_text()),timing_job=job,timing_metadata_sha256=hashlib.sha256(metadata).hexdigest(),calibration_sha256=sha(old/'timing-001/calibration-4.json'),instances_sha256=sha(P/'instances.json'),workload_id=wid,workload_sha256=sha(P/'workload.json'),candidates=candidatepins,profile_modes=['mitm-vector','mitm-vector-packed','mitm-vector-packed','mitm-vector','rho-plain','rho-negation'])
write_json(P/'profile-input.json',doc)
print(json.dumps(dict(status='frozen',workload_id=wid,candidates=len(candidatepins),target_count=1,fixture=0,independent_point_construction_check='pass',standing='unsigned producer invocation of existing independent arithmetic')))
