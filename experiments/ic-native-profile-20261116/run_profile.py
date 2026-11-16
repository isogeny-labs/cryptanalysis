#!/usr/bin/env python3
"""Bounded whole-guest instruction attribution with immutable prepared bytes."""
import hashlib,json,os,platform,resource,signal,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=HERE/'profile-001';OUT.mkdir(exist_ok=False);START=time.monotonic();arms=[]
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

host=dict(platform=platform.platform(),cpuinfo=read('/proc/cpuinfo'),initial=snap(),allowed_cpus=sorted(os.sched_getaffinity(0)),
          physical_memory_technology='unknown',physical_memory_speed='unknown',physical_memory_channels='unknown',qualified=None)
summary=dict(status='started',qualified=None,scope='whole-guest instruction attribution; instrumented clock is not native performance')
try:
 doc=json.loads((HERE/'profile-input.json').read_text());prepared=doc['prepared']
 assert sha(HERE/'instances.json')==doc['instances_sha256']
 for filename,pin in doc['candidates'].items():assert sha(ROOT/'experiments/ic-bench/candidates'/filename)==pin
 job=prepared['source_job'];metadata=(Path('/jobs')/job/'job.json').read_bytes()
 assert hashlib.sha256(metadata).hexdigest()==prepared['job_metadata_sha256']
 meta=json.loads(metadata);assert meta['git']['commit']==prepared['source_commit'] and not meta['git']['dirty']
 receipt=extracted(job,'experiments/ic-packed-square-20261116/build-001/','receipt.json')
 assert hashlib.sha256(receipt).hexdigest()==prepared['receipt_sha256']
 receipt_doc=json.loads(receipt);assert receipt_doc['status']=='prepared' and receipt_doc['source_commit']==prepared['source_commit']
 data=extracted(job,'experiments/ic-packed-square-20261116/build-001/','probe');assert hashlib.sha256(data).hexdigest()==prepared['binary_sha256']
 binary=OUT/'probe';binary.write_bytes(data);binary.chmod(0o755);(OUT/'preparation-receipt.json').write_bytes(receipt)
 calibration=extracted(doc['timing_job'],'experiments/ic-packed-square-20261116/timing-001/','calibration-4.json')
 assert hashlib.sha256(calibration).hexdigest()==doc['calibration_sha256'];(OUT/'calibration.json').write_bytes(calibration)
 timingmeta=(Path('/jobs')/doc['timing_job']/'job.json').read_bytes();assert hashlib.sha256(timingmeta).hexdigest()==doc['timing_metadata_sha256']
 (OUT/'timing-job-metadata.json').write_bytes(timingmeta)
 host.update(binary_sha256=prepared['binary_sha256'],binary_source_commit=prepared['source_commit'],source_sha256={str(f.relative_to(ROOT)):sha(f) for f in [HERE/'PROTOCOL.md',HERE/'run_profile.py',HERE/'profile-input.json',HERE/'workload.json',HERE/'instances.json']})
 os.sched_setaffinity(0,{host['allowed_cpus'][0]});host['selected_cpu']=host['allowed_cpus'][0]
 for label,argv in [('valgrind-version',['valgrind','--version']),('annotate-version',['callgrind_annotate','--version']),('objdump-version',['objdump','--version']),('lscpu',['lscpu']),('uname',['uname','-a'])]:
  code,_,_=command(argv,20,label);assert code==0,label
 pre=['valgrind','--tool=none','--log-file='+str(OUT/'preflight.valgrind.log'),str(binary),str(HERE/'instances.json'),'4','verify-table']
 code,out,_=timed(pre,'preflight',90);assert code==0,'instrumented capability preflight failed'
 check=json.loads(out);assert check['status']=='pass' and check['complete_map_comparisons']==25 and check['vector_backend']=='avx2-pclmul128'
 assert check['vector_packed_square_pairs']>0 and check['vector_pairs']==2*check['vector_packed_square_pairs']
 workload=json.loads((HERE/'workload.json').read_text());target=workload['targets'][0];results=[]
 for index,mode in enumerate(['mitm-vector','mitm-vector-packed','mitm-vector-packed','mitm-vector','rho-plain','rho-negation']):
  label=f'arm-{index:02d}-{mode}';capture=OUT/(label+'.callgrind')
  args=[str(binary),str(HERE/'instances.json'),'4',mode,'0',str(OUT/'calibration.json')]
  argv=['valgrind','--tool=callgrind','--dump-instr=yes','--collect-jumps=yes','--callgrind-out-file='+str(capture),'--log-file='+str(OUT/(label+'.valgrind.log')),*args]
  code,out,_=timed(argv,label,60 if mode.startswith('rho-') else 120)
  assert code==0 and capture.is_file(),label+' incomplete capture'
  result=json.loads(out);assert result['curve_id']==workload['curve_id'] and result['target']==target[1:] and result['target_seed']==workload['walk_seed'] and result['planted']==target[0]
  assert result['calibration']==json.loads(calibration)['calibration'] and not result['euclidean_inverse']
  if mode.startswith('rho-'):report=result['solver']
  else:
   report=result['report']['Ok'];native=report['decomposition']['setup']['native']
   assert native['mitm_vector_pairs']>0 and native['mitm_vector_pclmul128_pairs']==native['mitm_vector_pairs'] and native['mitm_vector_vpclmul_pairs']==0
   assert native['mitm_vector_packed_square_pairs']==(native['mitm_vector_pairs'] if 'packed' in mode else 0)
  assert report['verified'] and report['recovered']==target[0]
  results.append(dict(mode=mode,label=label,result=result,capture_sha256=sha(capture),capture_bytes=capture.stat().st_size))
  (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
  for kind in ['no','yes']:
   annotation=['callgrind_annotate','--auto=no','--threshold=100','--inclusive='+kind,str(capture)]
   annotation_code,_,_=command(annotation,20,label+'-inclusive-'+kind);assert annotation_code==0,'annotation failed'
 code,_,_=command(['objdump','-d','-C','--no-show-raw-insn',str(binary)],20,'disassembly');assert code==0
 # Full deterministic work check excludes elapsed nanoseconds and setup arithmetic counters.
 def signature(result):
  r=result['report']['Ok'];keys=[('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')]
  phases=[r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]
  return [r[s][k] for s,k in keys],[(p['group_ops'],{k:v for k,v in p.get('native',{}).items() if not k.endswith('_ns')}) for p in phases]
 assert all(signature(x['result'])==signature(results[0]['result']) for x in results[:4])
 summary.update(status='completed_unqualified',profiled_ic=4,profiled_rho=2,preflight=check,binary_sha256=prepared['binary_sha256'])
except Exception as error:summary.update(status='failed_or_capped',error=repr(error))
finally:
 host['final']=snap();(OUT/'host.json').write_text(json.dumps(host,indent=2)+'\n');(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if summary['status']!='completed_unqualified':raise SystemExit(1)
