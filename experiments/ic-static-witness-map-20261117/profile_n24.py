#!/usr/bin/env python3
"""Pre-generation N24 instruction diagnostic with explicit synthetic units."""
import argparse,hashlib,json,os,resource,signal,subprocess,tarfile,time
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];D=P/'profile-n24-001';D.mkdir(exist_ok=False)
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);a=p.parse_args()
START=time.monotonic();commands=[];rows=[];summary={'status':'started','qualification':None,'purpose':'synthetic-unit instruction diagnostic only; no native timing inference'}
sha=lambda b:hashlib.sha256(b).hexdigest()
PHYSICAL={'mitm_compact_map32_backend','mitm_map_entry_payload_bytes','mitm_vector_packed_square_pairs','mitm_vector_const_packed_square_pairs','mitm_vector_const_validated_pairs','mitm_indexed_prepare_pairs','mitm_static_map32_backend'}
def signature(raw):
 r=raw['report']['Ok']
 return [(v['group_ops'],{k:n for k,n in v['native'].items() if not k.endswith('_ns') and not k.startswith('walk_batch_inverse_vector_') and k not in PHYSICAL}) for v in [r['decomposition']['setup'],r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]]
def limits():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
def run(argv,cap,label):
 remaining=210-(time.monotonic()-START)
 if remaining<=0:raise TimeoutError('N24 diagnostic controller cap')
 proc=subprocess.Popen(argv,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits)
 try:out,err=proc.communicate(timeout=min(cap,remaining));code=proc.returncode
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate();code=124;err+='\nchild group killed at declared cap\n'
 (D/(label+'.stdout')).write_text(out);(D/(label+'.stderr')).write_text(err)
 commands.append(dict(argv=argv,exit_code=code,label=label));(D/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
 if code:raise RuntimeError(label+' exit'+str(code))
 return out
try:
 pin=json.loads((P/'profile-result-input.json').read_text())
 with tarfile.open(Path('/jobs')/pin['job']/'shards/0/out.tar.gz','r:gz') as tar:
  b=tar.extractfile('experiments/ic-inverse-regression-20261116/profile-001/host.json').read();assert sha(b)==pin['host_sha256'];tools=json.loads(b)['tool_sha256']
 import shutil
 for name in ['valgrind','callgrind_annotate','objdump']:assert sha(Path(shutil.which(name)).read_bytes())==tools[name]
 allowed=sorted(os.sched_getaffinity(0));os.sched_setaffinity(0,{allowed[0]})
 (D/'environment.json').write_text(json.dumps(dict(allowed_cpus=allowed,selected_cpu=allowed[0],tool_sha256=tools,job_id=os.environ['JOB_ID'],source_commit=json.loads((Path('/jobs')/os.environ['JOB_ID']/'job.json').read_text())['git']['commit'],controller_sha256=sha(Path(__file__).read_bytes()),instruction_only=True),indent=2)+'\n')
 inst=json.loads((P/'instances.json').read_text())[3]
 units={k:1.0 for k in ['ns_per_add','ns_per_double','ns_per_lookup','ns_per_row_op']}
 units.update({k:None for k in ['ns_per_sqrt','ns_per_as_solve','ns_per_s4_pair','ns_per_word_xor','ns_per_legendre','ns_per_inversion','ns_per_frobenius','ns_per_canon']});units['pinned_units']=[]
 cal=D/'synthetic-units.json';cal.write_text(json.dumps(dict(curve_id=inst['curve_id'],calibration=units),indent=2)+'\n')
 controls=[]
 for tag,binding,prefix in [('compact','prepared-input.json','experiments/ic-compact-pair-table-20261116/build-001/'),('packed','packed-input.json','experiments/ic-packed-const-square-20261116/build-002/'),('indexed','indexed-input.json','experiments/ic-pair-index-gather-20261117/build-001/')]:
  pin=json.loads((P/binding).read_text());meta=(Path('/jobs')/pin['source_job']/'job.json').read_bytes();assert sha(meta)==pin['job_metadata_sha256'] and not json.loads(meta)['git']['dirty']
  with tarfile.open(Path('/jobs')/pin['source_job']/'shards/0/out.tar.gz','r:gz') as tar:
   rb=tar.extractfile(prefix+'receipt.json').read();data=tar.extractfile(prefix+'probe').read()
  assert sha(rb)==pin['receipt_sha256'] and sha(data)==pin['binary_sha256'];receipt=json.loads(rb);assert receipt['status']=='prepared'
  path=D/('probe-'+tag);path.write_bytes(data);path.chmod(0o755);(D/(tag+'-receipt.json')).write_bytes(rb);controls.append((tag,path,receipt,pin))
 receipt=json.loads((P/'build-001/receipt.json').read_text());assert receipt['status']=='correctness_prepared' and sha(a.binary.read_bytes())==receipt['binary_sha256'];controls.append(('static',a.binary.resolve(),receipt,None))
 assert all(r['rustc']==receipt['rustc'] and r['environment']==receipt['environment'] for _,_,r,_ in controls)
 first=None
 for tag,binary,receipt,binding in controls:
  label=tag+'-inverse';capture=D/(label+'.callgrind')
  argv=['valgrind','--tool=callgrind','--dump-instr=yes','--collect-jumps=yes','--callgrind-out-file='+str(capture),'--log-file='+str(D/(label+'.valgrind.log')),str(binary),str(P/'instances.json'),'3','mitm-walk16-vector-inverse','0',str(cal)]
  raw=json.loads(run(argv,120,label));r=raw['report']['Ok'];assert r['verified'] and r['recovered']==raw['planted'] and raw['curve_id']==inst['curve_id'] and raw['calibration']==units
  assert r['decomposition']['cost']['native']['walk_batch_inverse_vector_elements']>0
  setup=r['decomposition']['setup']['native'];assert setup['mitm_compact_map32_backend']==1 and setup['mitm_map_entry_payload_bytes']==8
  assert (setup.get('mitm_static_map32_backend',0)==1)==(tag=='static')
  assert (setup.get('mitm_indexed_prepare_pairs',0)>0)==(tag in ['indexed','static'])
  if first is None:first=raw
  else:
   assert all(raw[k]==first[k] for k in ['curve_id','planted','target','target_seed','calibration']) and signature(raw)==signature(first)
   assert all(r[s][k]==first['report']['Ok'][s][k] for s,k in [('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')])
  rows.append(dict(tag=tag,result=raw,binary_sha256=receipt['binary_sha256'],binding=binding,capture_sha256=sha(capture.read_bytes()),synthetic_units=True));(D/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
  for inclusive in ['no','yes']:run(['callgrind_annotate','--auto=no','--threshold=100','--inclusive='+inclusive,str(capture)],20,label+'-inclusive-'+inclusive)
  run(['objdump','-d','-C','--no-show-raw-insn',str(binary)],20,tag+'-disassembly')
 summary.update(status='completed_unqualified',captures=4)
except Exception as e:summary.update(status='failed_or_capped',error=repr(e))
finally:(D/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if summary['status']!='completed_unqualified':raise SystemExit(1)
