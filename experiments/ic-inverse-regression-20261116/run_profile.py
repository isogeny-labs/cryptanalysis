#!/usr/bin/env python3
"""Bounded whole-guest instruction attribution with immutable prepared bytes."""
import argparse,hashlib,json,os,platform,resource,shutil,signal,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args()
assert args.run_id.replace('-','').isalnum()
OUT=HERE/args.run_id;OUT.mkdir(exist_ok=False);START=time.monotonic();arms=[]
def read(p):
 try:return Path(p).read_text()
 except OSError:return None
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cgroup_paths(cgroup_text,mount_text):
 groups={}
 for line in cgroup_text.splitlines():
  _,controllers,relative=line.split(':',2)
  for controller in controllers.split(','):groups[controller]=relative
 paths=[]
 names={'cpu':['cpu.stat','cpu.cfs_quota_us','cpu.cfs_period_us'],
  'cpuacct':['cpuacct.usage','cpuacct.stat'],
  'memory':['memory.limit_in_bytes','memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control'],
  'cpuset':['cpuset.cpus','cpuset.mems','cpuset.effective_cpus','cpuset.effective_mems']}
 for line in mount_text.splitlines():
  before,after=line.split(' - ',1);left=before.split();right=after.split()
  if right[0] not in ['cgroup','cgroup2']:continue
  root,mount=left[3:5]
  if right[0]=='cgroup2':
   relative=groups.get('','/')
   suffix=relative[len(root):] if relative==root or relative.startswith(root.rstrip('/')+'/') else relative
   for name in ['cpu.stat','cpu.max','cpuset.cpus.effective','cpuset.mems.effective','memory.events','memory.max','memory.current','memory.peak']:
    paths.append(mount.rstrip('/')+'/'+suffix.strip('/')+'/'+name)
  else:
   for controller,files in names.items():
    if controller not in right[2].split(',') or controller not in groups:continue
    relative=groups[controller]
    suffix=relative[len(root):] if relative==root or relative.startswith(root.rstrip('/')+'/') else relative
    for name in files:paths.append(mount.rstrip('/')+'/'+suffix.strip('/')+'/'+name)
 return [str(Path(p)) for p in paths]
def snap():
 cg=read('/proc/self/cgroup') or '';mount=read('/proc/self/mountinfo') or ''
 paths=['/proc/self/status','/proc/self/cgroup','/proc/self/mountinfo','/proc/stat','/proc/interrupts','/proc/softirqs','/proc/self/numa_maps']+cgroup_paths(cg,mount)
 return {p:read(p) for p in paths}

def limits():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
def command(argv,cap,label):
 remaining=780-(time.monotonic()-START)
 if remaining<=0:raise TimeoutError('profile controller780s cap')
 started=time.monotonic();proc=subprocess.Popen(argv,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=limits)
 try:out,err=proc.communicate(timeout=min(cap,remaining));code=proc.returncode
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate();code=124
 (OUT/(label+'.stdout')).write_text(out);(OUT/(label+'.stderr')).write_text(err)
 row=dict(label=label,argv=argv,exit_code=code,process_wall_s=time.monotonic()-started,qualified=None)
 arms.append(row);(OUT/'commands.json').write_text(json.dumps(arms,indent=2)+'\n')
 return code,out,err

def extracted(job,prefix,name):
 with tarfile.open(Path('/jobs')/job/'shards/0/out.tar.gz','r:gz') as tar:
  entry=tar.getmember(prefix+name);assert entry.isfile();return tar.extractfile(entry).read()

def timed(argv,label,cap):
 rusage=OUT/(label+'.rusage.json')
 wrapper=['/usr/bin/time','-q','-o',str(rusage),'-f','{"max_rss_kib":%M,"user_s":%U,"system_s":%S,"involuntary":%c,"voluntary":%w,"major_faults":%F,"minor_faults":%R}','--',*argv]
 return command(wrapper,cap,label)

host=dict(platform=platform.platform(),cpuinfo=read('/proc/cpuinfo'),initial=snap(),allowed_cpus=sorted(os.sched_getaffinity(0)),qualified=None)
summary=dict(status='started',qualified=None,scope='whole-guest Ir attribution; not native wall or collector-only cost')
try:
 doc=json.loads((HERE/'profile-input.json').read_text())
 assert sha(HERE/'instances.json')==doc['instances_sha256'] and sha(HERE/'workload.json')==doc['workload_sha256']
 binaries={};walks={}
 for tag,key,prefix in [('anchor','anchor','experiments/ic-constant-reduction-20261116/build-002/'),('current','prepared','experiments/ic-vector-inverse-20261116/build-001/')]:
  pin=doc[key];job=pin['source_job'];metadata=(Path('/jobs')/job/'job.json').read_bytes()
  assert hashlib.sha256(metadata).hexdigest()==pin['job_metadata_sha256']
  meta=json.loads(metadata);assert meta['git']['commit']==pin['source_commit'] and not meta['git']['dirty']
  receipt=extracted(job,prefix,'receipt.json');assert hashlib.sha256(receipt).hexdigest()==pin['receipt_sha256']
  rd=json.loads(receipt);assert rd['status']=='prepared' and rd['source_commit']==pin['source_commit']
  data=extracted(job,prefix,'probe');assert hashlib.sha256(data).hexdigest()==pin['binary_sha256']
  binary=OUT/('probe-'+tag);binary.write_bytes(data);binary.chmod(0o755);binaries[tag]=binary
  (OUT/(tag+'-receipt.json')).write_bytes(receipt);(OUT/(tag+'-job.json')).write_bytes(metadata)
 calibration=extracted(doc['timing_job'],'experiments/ic-vector-inverse-20261116/timing-001/','calibration-4.json')
 assert hashlib.sha256(calibration).hexdigest()==doc['calibration_sha256'];(OUT/'calibration.json').write_bytes(calibration)
 prior=extracted(doc['timing_job'],'experiments/ic-vector-inverse-20261116/timing-001/','walk-smoke-4.json')
 assert hashlib.sha256(prior).hexdigest()==doc['development_state_sha256']
 host['source_sha256']={str(f.relative_to(ROOT)):sha(f) for f in [HERE/'PROTOCOL.md',HERE/'run_profile.py',HERE/'profile-input.json',HERE/'instances.json',HERE/'workload.json']}
 os.sched_setaffinity(0,{host['allowed_cpus'][0]});host['selected_cpu']=host['allowed_cpus'][0]
 for label,argv in [('valgrind-version',['valgrind','--version']),('objdump-version',['objdump','--version']),('lscpu',['lscpu']),('uname',['uname','-a'])]:
  code,_,_=command(argv,20,label);assert code==0,label
 host['tool_sha256']={name:sha(shutil.which(name)) for name in ['valgrind','callgrind_annotate','objdump']}
 for tag,binary in binaries.items():
  argv=['valgrind','--tool=none','--log-file='+str(OUT/(tag+'-preflight.valgrind.log')),str(binary),str(HERE/'instances.json'),'4','verify-table']
  code,out,_=timed(argv,tag+'-preflight',90);assert code==0,'table preflight '+tag
  check=json.loads(out);assert check['status']=='pass' and check['complete_map_comparisons']==35 and check['vector_backend']=='avx2-pclmul128'
  assert check['vector_const_pairs']==check['vector_packed_square_pairs']>0
  argv=['valgrind','--tool=none','--log-file='+str(OUT/(tag+'-walk.valgrind.log')),str(binary),str(HERE/'instances.json'),'4','verify-walkbatch','0']
  code,out,_=timed(argv,tag+'-walk',90);assert code==0,'walk preflight '+tag
  walk=json.loads(out);assert walk['status']=='pass' and walk['checks']==512 and walk['complete_stream_comparisons']==(3 if tag=='anchor' else 4)
  assert walk['vector_counters']['walk_batch_vector_pairs']>0 and walk['vector_counters']['walk_batch_vector_backend']==1
  if tag=='current':assert walk['inverse_vector_counters']['walk_batch_inverse_vector_elements']>0
  assert all(walk[k]==json.loads(prior)[k] for k in ['frames','group_ops','curve_id','planted','target','target_seed'])
  walks[tag]=walk;(OUT/(tag+'-walk.json')).write_text(json.dumps(walk,indent=2)+'\n')
 workload=json.loads((HERE/'workload.json').read_text());target=workload['targets'][0];results=[]
 methods={'anchor':('anchor','mitm-walk16-vector-const'),'current':('current','mitm-walk16-vector-const'),'inverse':('current','mitm-walk16-vector-inverse'),'rho-plain':('current','rho-plain'),'rho-negation':('current','rho-negation')}
 for index,method in enumerate(['anchor','current','inverse','inverse','current','anchor','rho-plain','rho-negation']):
  tag,mode=methods[method];binary=binaries[tag];label=f'arm-{index:02d}-{method}';capture=OUT/(label+'.callgrind')
  argv=['valgrind','--tool=callgrind','--dump-instr=yes','--collect-jumps=yes','--callgrind-out-file='+str(capture),'--log-file='+str(OUT/(label+'.valgrind.log')),str(binary),str(HERE/'instances.json'),'4',mode,'0',str(OUT/'calibration.json')]
  code,out,_=timed(argv,label,60 if method.startswith('rho-') else 120);assert code==0 and capture.is_file(),label
  result=json.loads(out);assert result['curve_id']==workload['curve_id'] and result['target']==target[1:] and result['target_seed']==workload['walk_seed'] and result['planted']==target[0]
  assert result['calibration']==json.loads(calibration)['calibration'] and not result['euclidean_inverse']
  report=result['solver'] if method.startswith('rho-') else result['report']['Ok']
  assert report['verified'] and report['recovered']==target[0]
  if not method.startswith('rho-'):
   assert int(report['spec']['oracle_params']['vector_prepare'])==3 and int(report['spec']['oracle_params']['batch_size'])==1024
   setup=report['decomposition']['setup']['native'];assert setup['mitm_vector_const_pairs']>0 and setup['mitm_vector_vpclmul_pairs']==0
   query=report['decomposition']['cost']['native'];assert query['walk_batch_vector_pairs']>0 and query['walk_batch_vector_backend']==1
   assert query.get('walk_batch_inverse_vector_elements',0)>0 if method=='inverse' else query.get('walk_batch_inverse_vector_elements',0)==0
  results.append(dict(method=method,mode=mode,binary_sha256=sha(binary),label=label,result=result,capture_sha256=sha(capture),capture_bytes=capture.stat().st_size))
  (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
  for kind in ['no','yes']:
   code,_,_=command(['callgrind_annotate','--auto=no','--threshold=100','--inclusive='+kind,str(capture)],20,label+'-inclusive-'+kind);assert code==0
 for tag,binary in binaries.items():
  code,_,_=command(['objdump','-d','-C','--no-show-raw-insn',str(binary)],20,tag+'-disassembly');assert code==0
 def signature(result):
  r=result['report']['Ok'];keys=[('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')]
  phases=[r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]
  return [r[s][k] for s,k in keys],[(p['group_ops'],{k:v for k,v in p.get('native',{}).items() if not k.endswith('_ns') and not k.startswith('walk_batch_inverse_vector_')}) for p in phases]
 assert all(signature(x['result'])==signature(results[0]['result']) for x in results[:6])
 summary.update(status='completed_unqualified',profiled_ic=6,profiled_rho=2)
except Exception as error:summary.update(status='failed_or_capped',error=repr(error))
finally:
 host['final']=snap();(OUT/'host.json').write_text(json.dumps(host,indent=2)+'\n');(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if summary['status']!='completed_unqualified':raise SystemExit(1)

