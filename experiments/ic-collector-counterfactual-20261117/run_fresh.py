#!/usr/bin/env python3
"""Frozen registered-field scaling comparison with fresh rho processes."""
import hashlib,itertools,json,os,platform,resource,signal,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=HERE/'timing-optimized-001';OUT.mkdir(exist_ok=False);START=time.monotonic()
from fresh_common import MODES,ACTUAL,TAGS,INVERSE,ORDERS,FIXTURES,STORAGE_COUNTERS
from counterfactual_checks import check as check_cell,equal as equal_cells
ids=json.loads((HERE/'fresh-identities.json').read_text());triples=[];references=[];arms=[]
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
 'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'FRESH_PROTOCOL.md',HERE/'run_fresh.py',HERE/'analyze_fresh.py',HERE/'replay_fresh_answers.py',HERE/'replay_fresh_states.py',HERE/'fresh_common.py',HERE/'profile_n24.py',HERE/'counterfactual_checks.py',HERE/'profile-result-input.json',HERE/'instances.json',HERE/'fresh-identities.json',HERE/'prepared-input.json',HERE/'indexed-input.json',HERE/'anchor-input.json',HERE/'optimized-input.json']},
 'qualification':'frozen exploratory protocol; CPU work on one L4 allocation',
 'physical_memory_technology':'unknown','physical_memory_speed':'unknown','physical_memory_channels':'unknown'}
def arm(index,mode,fixture,role,binary_tag=None):
 tag=binary_tag or TAGS.get(mode,'current')
 argv=[str(OUT/('probe-'+tag)),str(HERE/'instances.json'),str(index),ACTUAL.get(mode,mode),str(fixture)]
 if mode!='calibration' and (OUT/f'calibration-{index}.json').exists():argv.append(str(OUT/f'calibration-{index}.json'))
 before=snap();usage=resource.getrusage(resource.RUSAGE_CHILDREN)
 rusage_path=OUT/f'rusage-{len(arms):04d}.json'
 wrapped=['/usr/bin/time','-q','-o',str(rusage_path),'-f','{"max_rss_kib":%M,"user_s":%U,"system_s":%S,"involuntary":%c,"voluntary":%w,"major_faults":%F,"minor_faults":%R}','--',*argv]
 code,out,err,wall=command(wrapped,30 if role in ['native-host-capability','native-walker-capability','anchor-host-capability','anchor-walker-capability'] else 12);after=resource.getrusage(resource.RUSAGE_CHILDREN)
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
 (OUT/'triples.json').write_text(json.dumps(triples,indent=2)+'\n')
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
 assert Path('/usr/bin/time').is_file()
 for label,filename,binding,prefix,candidate_mode in [
  ('current','probe-current','prepared-input.json','experiments/ic-compact-pair-table-20261116/build-001/',MODES[1]),
  ('anchor','probe-anchor','anchor-input.json','experiments/ic-constant-reduction-20261116/build-002/',MODES[0]),
  ('indexed','probe-indexed','indexed-input.json','experiments/ic-pair-index-gather-20261117/build-001/',MODES[2]),
  ('optimized','probe-optimized','optimized-input.json','experiments/ic-collector-counterfactual-20261117/build-001/',MODES[5])]:
  prepared=json.loads((HERE/binding).read_text())
  with tarfile.open(Path('/jobs')/prepared['source_job']/'shards/0/out.tar.gz','r:gz') as tar:
   def member(name):
    item=tar.getmember(prefix+name);assert item.isfile();return tar.extractfile(item).read()
   rb=member('receipt.json');assert hashlib.sha256(rb).hexdigest()==prepared['receipt_sha256'];receipt=json.loads(rb)
   assert receipt['status']=='prepared' and receipt['source_commit']==prepared['receipt_source_commit']
   metadata=(Path('/jobs')/prepared['source_job']/'job.json').read_bytes();assert hashlib.sha256(metadata).hexdigest()==prepared['job_metadata_sha256']
   md=json.loads(metadata);assert md['git']['commit']==prepared['source_commit'] and not md['git']['dirty']
   if label=='optimized':
    snapshot=(Path('/jobs')/prepared['source_job']/'src.tar.gz').read_bytes();assert hashlib.sha256(snapshot).hexdigest()==prepared['snapshot_sha256']
   candidate=json.loads((ROOT/'experiments/ic-bench/candidates'/(ids['0'][candidate_mode]+'.json')).read_text());assert candidate['implementation']['sources_sha256']==receipt['source_sha256']
   data=member('probe');assert hashlib.sha256(data).hexdigest()==prepared['binary_sha256']==receipt['binary_sha256']
   (OUT/filename).write_bytes(data);(OUT/filename).chmod(0o755);(OUT/(label+'-receipt.json')).write_bytes(rb)
   host[label+'_binary']=dict(binary_sha256=prepared['binary_sha256'],source_commit=prepared['source_commit'],rustc=receipt['rustc'],environment=receipt['environment'])
 assert all(host[tag+'_binary']['rustc']==host['current_binary']['rustc'] and host[tag+'_binary']['environment']==host['current_binary']['environment'] for tag in ['anchor','indexed','optimized'])
 os.sched_setaffinity(0,{host['allowed_cpus'][0]});host['selected_cpu']=host['allowed_cpus'][0]
 for index in range(5):
  firstwalk=None
  for tag in ['anchor','current','indexed','optimized']:
   raw=arm(index,'verify-table',0,'native-host-capability',tag);check=raw.get('result',{})
   assert raw['exit_code']==0 and check.get('status')=='pass' and check.get('has_clmul') and check.get('complete_map_comparisons')==(40 if tag=='optimized' else 35)
   if tag in ['indexed','optimized']:
    assert check['vector_pairs']==2*check['vector_packed_square_pairs'] and check['vector_const_pairs']*2==check['vector_packed_square_pairs'] and check['vector_const_validated_pairs']==check['vector_const_packed_square_pairs']==check['vector_const_pairs']>0
   else:assert check['vector_pairs']==4*check['vector_packed_square_pairs'] and check['vector_const_pairs']==check['vector_packed_square_pairs']>0
   assert (check.get('indexed_prepare_pairs',0)>0)==(tag in ['indexed','optimized'])
   if tag in ['indexed','optimized']:assert check['indexed_prepare_pairs']>=check['vector_const_pairs']
   assert check.get('static_map_comparisons',0)==0
   if tag=='optimized':assert check['staged_map_comparisons']==check['staged_compact_map_comparisons']==5 and check['staged_const_pairs']==check['vector_const_pairs']>0
   assert check['vector_backend'] in ['avx2-pclmul128','avx2-vpclmul']
   if tag in ['current','indexed','optimized']:assert check['compact_map_comparisons']==5 and check['compact_entry_payload_bytes']==8
   else:assert check.get('compact_map_comparisons',0)==0
   (OUT/f'{tag}-preflight-{index}.json').write_text(json.dumps(check,indent=2)+'\n')
   raw=arm(index,'verify-walkbatch',0,'native-walker-capability',tag);walk=raw.get('result',{})
   assert raw['exit_code']==0 and walk.get('status')=='pass' and walk.get('checks')==512 and walk.get('complete_stream_comparisons')==(3 if tag=='anchor' else 4)
   assert walk['vector_counters']['walk_batch_vector_pairs']>0
   if tag!='anchor':assert walk['inverse_vector_counters']['walk_batch_inverse_vector_backend']==1 and walk['inverse_vector_counters']['walk_batch_inverse_vector_elements']>0
   if firstwalk is None:firstwalk=walk
   else:assert all(walk[k]==firstwalk[k] for k in ['frames','group_ops','curve_id','planted','target','target_seed'])
   (OUT/f'{tag}-walk-smoke-{index}.json').write_text(json.dumps(walk,indent=2)+'\n')
 for index in range(5):
  raw=arm(index,'calibration',0,'frozen-model-units');assert raw['exit_code']==0
  (OUT/f'calibration-{index}.json').write_text(json.dumps(raw['result'],indent=2)+'\n')
 for fixture in FIXTURES:
  for index in range(5):
   if fixture%2==0:reference_block(index,fixture)
   pre=arm(index,'mitm-counterfactual-ip-ordinary',0,'calibration','optimized')
   order=[MODES[i] for i in ORDERS[(fixture-726)%len(ORDERS)]]
   runs={mode:arm(index,mode,fixture,'complete-pipeline') for mode in order}
   post=arm(index,'mitm-counterfactual-ip-ordinary',0,'calibration','optimized')
   if fixture%2:reference_block(index,fixture)
   triple={'index':index,'fixture':fixture,'order':order,'runs':runs,'pre':pre,'post':post,'candidate_ids':{m:ids[str(index)][m] for m in MODES},'workload':ids[str(index)]['workloads'][str(fixture)],'qualified':None}
   frozen=json.loads((OUT/f'calibration-{index}.json').read_text())['calibration']
   results=[runs[m].get('result') for m in MODES];triple['all_completed']=all(report(runs[m]) is not None for m in MODES)
   if triple['all_completed']:
    triple['same_input']=all(all(r[k]==results[0][k] for k in ['curve_id','planted','target','target_seed']) for r in results)
    triple['all_verified']=all(report(runs[m])['verified'] for m in MODES)
    triple['same_calibration']=all(r['calibration']==frozen for r in results) and references[-1].get('result',{}).get('calibration')==frozen
    signature=lambda r:[(p['group_ops'],{k:v for k,v in p['native'].items() if not k.endswith('_ns') and not k.startswith('walk_batch_inverse_vector_') and k not in STORAGE_COUNTERS}) for p in [r['decomposition']['setup'],r['decomposition']['cost'],r['linear_algebra']['cost'],r['verify']]]
    reports=[report(runs[m]) for m in MODES]
    assert all((report(runs[m])['decomposition']['cost']['native'].get('walk_batch_inverse_vector_elements',0)>0)==(m in INVERSE) for m in MODES)
    assert all(report(runs[m])['decomposition']['setup']['native'].get('mitm_compact_map32_backend',0)==int(m in MODES[1:]) for m in MODES)
    assert all(report(runs[m])['decomposition']['setup']['native'].get('mitm_map_entry_payload_bytes')==8 for m in MODES[1:])
    assert all(report(runs[m])['decomposition']['setup']['native'].get('mitm_vector_const_validated_pairs',0)==(report(runs[m])['decomposition']['setup']['native']['mitm_vector_pairs'] if m in MODES[2:] else 0) for m in MODES)
    assert all(report(runs[m])['decomposition']['setup']['native'].get('mitm_vector_const_packed_square_pairs',0)==(report(runs[m])['decomposition']['setup']['native']['mitm_vector_pairs'] if m in MODES[2:] else 0) for m in MODES)
    assert all(report(runs[m])['decomposition']['setup']['native']['mitm_vector_packed_square_pairs']==(report(runs[m])['decomposition']['setup']['native']['mitm_vector_pairs'] if m in MODES[2:] else 0) for m in MODES)
    assert all((report(runs[m])['decomposition']['setup']['native'].get('mitm_indexed_prepare_pairs',0)>0)==(m in [MODES[2],MODES[5]]) for m in MODES)
    assert all(report(runs[m])['decomposition']['setup']['native']['mitm_indexed_prepare_pairs']>=report(runs[m])['decomposition']['setup']['native']['mitm_vector_pairs']>0 for m in [MODES[2],MODES[5]])
    for m in MODES[3:]:
     check_cell(runs[m]['result'],m.rsplit('-',1)[1]);equal_cells(runs[MODES[3]]['result'],runs[m]['result'])
    assert all(report(runs[m])['decomposition']['setup']['native'].get('mitm_static_map32_backend',0)==0 for m in MODES)
    triple['same_schedule_counts']=all(signature(r)==signature(reports[0]) and all(r[s][k]==reports[0][s][k] for s,k in [('decomposition','targets_tried'),('decomposition','relations_found'),('linear_algebra','rank'),('linear_algebra','rows'),('linear_algebra','dependent'),('linear_algebra','work')]) for r in reports[1:])
   if online(pre) is not None and online(post) is not None:
    aa=online(pre)/online(post);triple.update(calibration_ratio=aa,calibration_within_bound=.85<=aa<=1.15 and all(report(r)['verified'] and r['result']['calibration']==frozen for r in [pre,post]))
   triples.append(triple);save()
 summary={'status':'matrix_completed_unqualified','triples':len(triples),'references':len(references),'qualified':None}
except Exception as e:summary={'status':'failed_or_capped','error':repr(e),'triples':len(triples),'references':len(references),'qualified':None}
finally:
 save();host['final']=snap();(OUT/'host.json').write_text(json.dumps(host,indent=2)+'\n');(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
if summary['status']!='matrix_completed_unqualified':raise SystemExit(1)
