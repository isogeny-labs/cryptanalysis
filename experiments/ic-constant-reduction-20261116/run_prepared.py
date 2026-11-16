#!/usr/bin/env python3
"""Frozen registered-field scaling comparison with fresh rho processes."""
import hashlib,itertools,json,os,platform,resource,signal,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=HERE/'timing-001';OUT.mkdir(exist_ok=False);START=time.monotonic()
MODES=['mitm-walk16-vector-narrow','mitm-walk16-vector-const']
ids=json.loads((HERE/'identities.json').read_text());pairs=[];references=[];arms=[]
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
def child_limits():
 resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
def command(argv,limit=12):
 remaining=780-(time.monotonic()-START)
 if remaining<=0:raise TimeoutError('timing controller budget')
 started=time.monotonic();p=subprocess.Popen(argv,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,preexec_fn=child_limits)
 try:out,err=p.communicate(timeout=min(limit,remaining))
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate();return 124,out,err+'\nprocess group killed at cap\n',time.monotonic()-started
 return p.returncode,out,err,time.monotonic()-started
host={'platform':platform.platform(),'cpuinfo':read('/proc/cpuinfo'),'initial':snap(),'allowed_cpus':sorted(os.sched_getaffinity(0)),
 'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'PROTOCOL.md',HERE/'run_prepared.py',HERE/'instances.json',HERE/'identities.json',HERE/'prepared-input-amended.json']},
 'qualification':'frozen exploratory protocol; CPU work on one L4 allocation',
 'physical_memory_technology':'unknown','physical_memory_speed':'unknown','physical_memory_channels':'unknown'}
def arm(index,mode,fixture,role):
 argv=[str(OUT/'probe'),str(HERE/'instances.json'),str(index),mode,str(fixture)]
 if mode!='calibration' and (OUT/f'calibration-{index}.json').exists():argv.append(str(OUT/f'calibration-{index}.json'))
 before=snap();usage=resource.getrusage(resource.RUSAGE_CHILDREN)
 rusage_path=OUT/f'rusage-{len(arms):04d}.json'
 wrapped=['/usr/bin/time','-q','-o',str(rusage_path),'-f','{"max_rss_kib":%M,"user_s":%U,"system_s":%S,"involuntary":%c,"voluntary":%w,"major_faults":%F,"minor_faults":%R}','--',*argv]
 code,out,err,wall=command(wrapped,30 if role in ['native-host-capability','native-walker-capability'] else 12);after=resource.getrusage(resource.RUSAGE_CHILDREN)
 row={'index':index,'mode':mode,'fixture':fixture,'role':role,'argv':argv,'exit_code':code,'stdout':out,'stderr':err,
  'process_wall_s':wall,'cpu_s':after.ru_utime+after.ru_stime-usage.ru_utime-usage.ru_stime,
  'gnu_time_argv':wrapped,'child_rusage_raw':read(rusage_path),'involuntary':after.ru_nivcsw-usage.ru_nivcsw,'before':before,'after':snap(),'qualified':None}
 if not code:
  try:row['result']=json.loads(out);row['child_rusage']=json.loads(read(rusage_path));row['peak_rss_kib']=row['child_rusage']['max_rss_kib'] or None
  except (ValueError,TypeError):row['parse_error']=True
 arms.append(row)
 with (OUT/'arms.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 return row
def report(row):return row.get('result',{}).get('report',{}).get('Ok')
def online(row):
 r=report(row);return None if r is None else r['collector_wall_seconds']
def save():
 (OUT/'pairs.json').write_text(json.dumps(pairs,indent=2)+'\n')
 (OUT/'references.json').write_text(json.dumps(references,indent=2)+'\n')
def reference_block(index,fixture):
 modes=['rho-plain','rho-negation']
 if fixture%2:modes.reverse()
 runs={mode:arm(index,mode,fixture,'same-target-reference') for mode in modes}
 row={'index':index,'fixture':fixture,'runs':runs}
 plain,neg=runs['rho-plain'],runs['rho-negation']
 if plain.get('result') and neg.get('result'):
  a,b=plain['result'],neg['result']
  assert all(a[k]==b[k] for k in ['curve_id','planted','target','target_seed','calibration'])
  assert not a['euclidean_inverse'] and not b['euclidean_inverse']
  row['result']={**b,'plain':a['solver'],'matched':b['solver'],'plain_context_ns':a['context_ns']}
 references.append(row);save()
try:
 assert Path('/usr/bin/time').is_file(),'GNU time required by frozen protocol'
 prepared=json.loads((HERE/'prepared-input-amended.json').read_text())
 with tarfile.open(Path('/jobs')/prepared['source_job']/'shards/0/out.tar.gz','r:gz') as tar:
  prefix='experiments/ic-constant-reduction-20261116/build-002/'
  def member(name):
   m=tar.getmember(prefix+name);assert m.isfile();return tar.extractfile(m).read()
  receipt_bytes=member('receipt.json');assert hashlib.sha256(receipt_bytes).hexdigest()==prepared['receipt_sha256']
  receipt=json.loads(receipt_bytes);assert receipt['status']=='prepared' and receipt['source_commit']==prepared['receipt_source_commit']
  metadata_bytes=(Path('/jobs')/prepared['source_job']/'job.json').read_bytes()
  assert hashlib.sha256(metadata_bytes).hexdigest()==prepared['job_metadata_sha256']
  metadata=json.loads(metadata_bytes)
  assert metadata['git']['commit']==prepared['source_commit'] and not metadata['git']['dirty']
  candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/(ids['0']['mitm-walk16-vector-narrow']+'.json')).read_text())
  assert receipt['source_sha256']==candidate['implementation']['sources_sha256']
  data=member('probe');assert hashlib.sha256(data).hexdigest()==prepared['binary_sha256']==receipt['binary_sha256']
  (OUT/'probe').write_bytes(data);(OUT/'probe').chmod(0o755);(OUT/'preparation-receipt.json').write_bytes(receipt_bytes)
 host.update(binary_sha256=prepared['binary_sha256'],binary_source_commit=prepared['source_commit'],receipt_source_commit=receipt['source_commit'],binary_toolchain=receipt['rustc'])
 os.sched_setaffinity(0,{host['allowed_cpus'][0]});host['selected_cpu']=host['allowed_cpus'][0]
 for index in range(5):
  preflight=arm(index,'verify-table',0,'native-host-capability')
  check=preflight.get('result',{})
  assert preflight['exit_code']==0 and check.get('status')=='pass' and check.get('vector_pairs',0)>0 and check.get('has_clmul') and check.get('vector_backend') in ['avx2-vpclmul','avx2-pclmul128'], 'timing host capability admission failed'
  assert check['complete_map_comparisons']==35 and check['vector_packed_square_pairs']>0 and check['vector_pairs']==4*check['vector_packed_square_pairs'] and check['vector_const_pairs']==check['vector_packed_square_pairs'], 'packed square admission failed'
  (OUT/f'preflight-{index}.json').write_text(json.dumps(check,indent=2)+'\n')
  walker=arm(index,'verify-walkbatch',0,'native-walker-capability');walk=walker.get('result',{})
  assert walker['exit_code']==0 and walk.get('status')=='pass' and walk.get('has_clmul') and walk.get('checks')==512 and walk.get('complete_stream_comparisons')==3, 'walker capability admission failed'
  assert walk['native_counters']['walk_batch_native_backend']==1 and walk['scalar_counters']['walk_batch_native_backend']==0 and walk['native_counters']['walk_batch_pair_adds']>0
  assert walk['vector_counters']['walk_batch_vector_requested']==1 and walk['vector_counters']['walk_batch_vector_backend']==1 and walk['vector_counters']['walk_batch_vector_pairs']>0
  (OUT/f'walk-smoke-{index}.json').write_text(json.dumps(walk,indent=2)+'\n')
 for index in range(5):
  calibration=arm(index,'calibration',0,'frozen-model-units');assert calibration['exit_code']==0
  (OUT/f'calibration-{index}.json').write_text(json.dumps(calibration['result'],indent=2)+'\n')
 for fixture in range(432,456):
  for index in range(5):
   if fixture%2==0:reference_block(index,fixture)
   pre=arm(index,MODES[0],0,'calibration')
   order=MODES if (fixture-432)%2==0 else list(reversed(MODES))
   runs={mode:arm(index,mode,fixture,'complete-pipeline') for mode in order}
   post=arm(index,MODES[0],0,'calibration')
   if fixture%2:reference_block(index,fixture)
   pair={'index':index,'fixture':fixture,'order':order,'runs':runs,'pre':pre,'post':post,
    'candidate_ids':{m:ids[str(index)][m] for m in MODES},'workload':ids[str(index)]['workloads'][str(fixture)],'qualified':None}
   frozen=json.loads((OUT/f'calibration-{index}.json').read_text())['calibration']
   results=[runs[m].get('result') for m in MODES]
   pair['all_completed']=all(report(runs[m]) is not None for m in MODES)
   if pair['all_completed']:
    pair['same_input']=all(all(r[k]==results[0][k] for k in ['curve_id','planted','target','target_seed']) for r in results)
    pair['all_verified']=all(report(runs[m])['verified'] for m in MODES)
    pair['same_calibration']=all(r['calibration']==frozen for r in results) and references[-1].get('result',{}).get('calibration')==frozen
    a,b=(report(runs[m]) for m in MODES)
    signature=lambda r:[(p['group_ops'],{k:v for k,v in p['native'].items() if not k.endswith('_ns')}) for p in [r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]]
    pair['same_schedule_counts']=signature(a)==signature(b) and all(a[s][k]==b[s][k] for s,k in [('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')])
   if online(pre) is not None and online(post) is not None:
    aa=online(pre)/online(post);pair.update(calibration_ratio=aa,calibration_within_bound=.85<=aa<=1.15 and all(report(q)['verified'] and q['result']['calibration']==frozen for q in [pre,post]))
   pairs.append(pair);save()
 summary={'status':'matrix_completed_unqualified','pairs':len(pairs),'references':len(references),'qualified':None}
except Exception as e:summary={'status':'failed_or_capped','error':repr(e),'pairs':len(pairs),'references':len(references),'qualified':None}
finally:
 save();host['final']=snap();(OUT/'host.json').write_text(json.dumps(host,indent=2)+'\n')
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if summary['status']!='matrix_completed_unqualified':raise SystemExit(1)
