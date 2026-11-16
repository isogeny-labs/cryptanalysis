"""Independent complete CI custody audit and downloaded Rust auditor replay; no Python math."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,shutil,stat,subprocess,zipfile
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
out=Path('/workspace/scratch/ct94-additive-original-full-CI-acceptance-01');p=out/'whole-artifact'
source='25801fe6aaba49674ef010e814dc7c9a58c28247';producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
shutil.copyfile(__file__,out/'actual-acceptance-command-01.py')
def digest(f):
 with f.open('rb') as q:return hashlib.file_digest(q,'sha256').hexdigest()
def equal(a,b):
 if a.stat().st_size!=b.stat().st_size:return False
 with a.open('rb') as x,b.open('rb') as y:
  while True:
   u,v=x.read(1048576),y.read(1048576)
   if u!=v:return False
   if not u:return True
def guards():
 rows=(p/'original-reference.sha256').read_text().splitlines();assert len(rows)==1440
 assert equal(p/'original-reference.sha256',s/'ci_fixed_chain/reference-03.sha256')
 for line in rows:
  h,n=line.split('  ',1);assert digest(r/n)==h,n
 return len(rows)
assert (p/'original.exit').read_text().strip()=='0'
assert (p/'final-source-guards.exit').read_text().strip()=='0'
assert (p/'consumer-head.txt').read_text().strip()==source
assert (p/'producer-head.txt').read_text().strip()==producer
assert equal(p/'original-command.sh',s/'ci_fixed_chain/check-03.sh')
guards(); print('all1440 actual original source guards verified',flush=True)
phases=[dict(zip(['name','expected','actual'],line.split()))for line in(p/'phases.txt').read_text().splitlines()]
assert len(phases)==153 and len({v['name']for v in phases})==153
assert all(v['expected']==v['actual']for v in phases)
for v in phases:assert (p/(v['name']+'.pipe-exits')).read_text().split()==[v['actual'],'0']
assert len([v for v in phases if v['expected']=='101'])==24
native_labels=['geometry','chain','norm-point','original-prime','original-kernel','original-geometry','original-full']
counts=[13,695,695,1077,311,16,701]
binary_rows=[]
for label,count in zip(native_labels,counts):
 text=(p/(label+'-native.txt')).read_text()
 assert len(re.findall(r'^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',text,re.M))==1,label
 assert len(json.load((p/(label+'-all-whole-records.json')).open()))==count
 for a,b in [(label+'-original-compiled-test.bin',label+'-actual-runtime-test.bin'),('actual-compiled-'+label+'-auditor.bin','actual-runtime-'+label+'-auditor.bin')]:
  assert equal(p/a,p/b),a
  binary_rows.append(dict(compiled=a,runtime=b,bytes=(p/a).stat().st_size,sha256=digest(p/a),whole_bytes_equal=True))
 for mode in ['compiled','runtime']:
  record=json.loads((p/(label+'-'+mode+'-binary.json')).read_text())
  f=p/(label+('-original-compiled-test.bin'if mode=='compiled'else'-actual-runtime-test.bin'))
  assert f.stat().st_size==record['bytes'] and digest(f)==record['sha256']
  if mode=='runtime':assert record['compiled_runtime_equal']is True
  record=json.loads((p/(label+'-auditor-'+mode+'-custody.json')).read_text())
  f=p/('actual-'+mode+'-'+label+'-auditor.bin')
  assert f.stat().st_size==record['bytes'] and digest(f)==record['sha256']
prepared=json.loads((p/'engine-prepared.json').read_text())
for row in prepared['files']:
 f=p/'actual-prepared-original-engine'/Path(row['copy']).name
 assert f.stat().st_size==row['bytes'] and digest(f)==row['sha256']
for label in [v for v in native_labels if v!='original-kernel']:
 for suffix in ['.json']+(['-before-native.json']if label not in ['geometry','chain']else[]):
  reuse=json.loads((p/('engine-reused-'+label+suffix)).read_text())
  assert reuse['actual_reuse']is True and reuse['actual_prepared_bytes_unchanged']is True and reuse['Cargo_artifact']['fresh']is True
  assert reuse['Cargo_artifact']['features']==prepared['Cargo_artifact']['features']
  for row in reuse['actual_aliases']:
   original=next(v for v in prepared['files']if Path(v['actual_path']).suffix==Path(row['dependency_path']).suffix)
   assert row['bytes']==original['bytes'] and row['sha256']==original['sha256'] and row['whole_before_and_after_bytes_equal']is True
def closure(name):
 data=json.loads((p/(name+'-metadata.txt')).read_text());packages={v['id']:v for v in data['packages']};nodes={v['id']:v for v in data['resolve']['nodes']}
 roots=[k for k,v in packages.items() if v['manifest_path']==prepared['Cargo_artifact']['manifest_path']]
 if name=='original-kernel':assert not roots;return None
 assert len(roots)==1
 seen=set();pending=roots[:]
 while pending:
  k=pending.pop()
  if k in seen:continue
  seen.add(k);pending.extend(v['pkg']for v in nodes[k]['deps'])
 return {k:dict(node=nodes[k],package={n:packages[k][n]for n in ['id','manifest_path','dependencies','features','targets']})for k in sorted(seen)}
baseline=closure('chain')
for label in native_labels[2:]:
 actual=closure(label);record=json.loads((p/('engine-closure-'+label+'.json')).read_text())
 assert record['exact_complete_closure']==actual
 assert actual is None if label=='original-kernel' else actual==baseline
proof_rows=[]
for gate in ['consumer-proofs','producer-proofs']:
 statuses=list((p/gate).rglob('status'));assert len(statuses)==12 and all(q.read_text().strip()=='PASS'for q in statuses)
 roots=[]
 for log in(p/gate).rglob('audit.log'):
  text=log.read_text();assert '0 failing, 0 trusted (native_decide)'in text
  roots.extend(re.findall(r'^ok\s+(\S+)',text,re.M))
 assert len(roots)==len(set(roots))==70
 proof_rows.append(dict(gate=gate,modules=12,declarations=roots,failing=0,trusted_native_decide=0))
bindings=(s/'ci_fixed_chain/statement-bindings-03.txt').read_text().splitlines()
assert len(bindings)==70 and {q.name for q in p.glob('binding-*.txt')}=={'binding-'+n+'.txt'for n in bindings}
for claim in bindings:
 row=json.loads((p/('binding-'+claim+'.txt')).read_text())
 assert row['verdict']=='pass' and row['commit']==source and all(v['verdict']=='pass'for v in row['proofs'])
 assert row['claim_sha256']==digest(r/'pcc/claims'/(claim+'.json'))
source_rows=[]
for directory in sorted((p/'actual-compiled-source').iterdir()):
 current=s/'ci_fixed_chain/audit'if directory.name=='geometry-auditor'else s/directory.name
 for f in sorted(directory.rglob('*')):
  if not f.is_file():continue
  target=current/f.relative_to(directory)
  assert target.is_file(),('missing-local-source',str(f),str(target))
  assert equal(f,target),('source-mismatch',str(f),str(target))
  source_rows.append(dict(path=f.relative_to(p).as_posix(),bytes=f.stat().st_size,sha256=digest(f)))
for f in(p/'actual-proof-stage').glob('*.lean'):
 matches=list(s.glob('*/lean/'+f.name));assert len(matches)==1 and equal(f,matches[0]),str(f)
installed=json.loads((p/'installed-literal-successor-sources.json').read_text())
assert len(installed)==21
assert installed==json.loads((s/'ci_fixed_chain/successor-sources-03.json').read_text())['files']
for row in installed:
 rel=row['relative_to_study'];f=p/'actual-compiled-source'/rel
 assert equal(f,s/'ci_fixed_chain/successor-sources-03'/rel) and f.stat().st_size==row['bytes'] and digest(f)==row['sha256']
fixtures=json.loads((p/'whole-successor-fixture-custody.json').read_text())
for row in fixtures:
 path=row['destination'];prefix='/home/runner/work/_temp/n4-original-full-output/'
 assert path.startswith(prefix)
 f=p/path[len(prefix):];assert f.stat().st_size==row['bytes'] and digest(f)==row['sha256']
 if 'source_pin'in row:
  pin=row['source_pin'];local=s/pin['source'];assert local.stat().st_size==pin['bytes'] and digest(local)==pin['sha256']
with zipfile.ZipFile(out/'whole-original-runlogs.zip')as z:
 log_counts=[]
 for info in z.infolist():
  n=0;h=hashlib.sha256();footers=0
  with z.open(info)as f:
   for line in f:
    n+=len(line);h.update(line)
    if b'test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;'in line:footers+=1
  log_counts.append(dict(path=info.filename,bytes=n,sha256=h.hexdigest(),unfiltered_test_footers=footers))
 assert sum(v['unfiltered_test_footers']for v in log_counts)==7
(out/'independent-custody-checks.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),phases=phases,binaries=binary_rows,proof_gates=proof_rows,bindings=bindings,all_compiled_source_files=source_rows,literal_installed_sources=installed,whole_runlogs=log_counts,source_guards=1440,all_checks_above_pass=True),indent=2)+'\n')
print('static complete custody passes:',len(phases),'phases,',len(source_rows),'source files, both70 declarations/all70 bindings',flush=True)
host=out/'actual-downloaded-Rust-auditor-controls-01';host.mkdir();results=[];links=[]
tag_sets=[['N4_CHAIN_OLD_LITERAL_PARITY','N4_CHAIN_FIXED_GEOMETRY'],['N4_FIXED_CHAIN_EXCEPTIONAL_CASE','N4_FIXED_CHAIN_ALL_EXCEPTIONALS','N4_FIXED_CHAIN_ALL_PUBLIC','N4_FIXED_CHAIN_SELECTED_CALL_VECTORS'],['N4_FIXED_CHAIN_EXCEPTIONAL_CASE','N4_FIXED_CHAIN_ALL_EXCEPTIONALS','N4_FIXED_CHAIN_ALL_PUBLIC','N4_FIXED_CHAIN_SELECTED_CALL_VECTORS'],['N4_ORIGINAL_PRIME_EXCEPTIONAL_CASE','N4_ORIGINAL_PRIME_PUBLIC_CASE','N4_ORIGINAL_PRIME_SOURCE_MODEL','N4_ORIGINAL_PRIME_SELECTED_VECTORS'],['N4_ORIGINAL_KERNEL_TRANSPORT','N4_ORIGINAL_KERNEL_VERTEX','N4_ORIGINAL_KERNEL_PAIR','N4_ORIGINAL_KERNEL_TRIPLE'],['N4_CHAIN_FIXED_GEOMETRY'],['N4_FIXED_CHAIN_EXCEPTIONAL_CASE','N4_FIXED_CHAIN_ALL_EXCEPTIONALS','N4_FIXED_CHAIN_ALL_PUBLIC','N4_FIXED_CHAIN_SELECTED_CALL_VECTORS','N4_ORIGINAL_FULL_KNOWN_POINT_VECTORS']]
for label,tags in zip(native_labels,tag_sets):
 exe=p/('actual-compiled-'+label+'-auditor.bin');before=digest(exe)
 prefix=[]if label=='original-kernel'else[p/'old-sixteen.json']
 if label=='original-geometry':prefix.append(p/'geometry-expected.json')
 cases=[('whole-positive',p/(label+'-native.txt'),0)]
 for tag in tags:
  stem=tag if label in ['geometry','chain']else label+'-'+tag
  cases.append((tag,p/(stem+'-entire-actual-records-omitted.txt'),101))
 for name,native,want in cases:
  target=host/(label+'-'+name+'-accepted.json');assert not target.exists()
  cmd=['timeout','120',str(exe),'--compare',*[str(v)for v in prefix],str(p/(label+'-expected.json')),str(native),str(target)]
  with(host/(label+'-'+name+'.txt')).open('xb')as log:q=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  (host/(label+'-'+name+'.exit')).write_text(str(q.returncode)+'\n')
  assert q.returncode==want,(label,name,q.returncode)
  if want:assert not target.exists()
  else:
   original=p/(label+'-all-whole-records.json');assert equal(target,original)
   row=dict(path=str(target),original=str(original),bytes=target.stat().st_size,sha256=digest(target),whole_independently_generated_bytes_compared_before_link=True)
   assert stat.S_IMODE(target.stat().st_mode)==stat.S_IMODE(original.stat().st_mode),('positive-mode-difference',label)
   temporary=target.with_name(target.name+'.closed-link');os.link(original,temporary);os.replace(temporary,target)
   links.append(row)
  results.append(dict(label=label,case=name,command=cmd,actual_exit=q.returncode,accepted_output=target.exists()))
  (out/'host-controls-progress.json').write_text(json.dumps(results,indent=2)+'\n')
  print(label,name,q.returncode,flush=True)
 assert digest(exe)==before
assert len(results)==31 and len([v for v in results if v['actual_exit']==101])==24
guards()
(out/'host-positive-exact-byte-links.json').write_text(json.dumps(links,indent=2)+'\n')
acceptance=dict(at=datetime.now(timezone.utc).isoformat(),source=source,producer_pin=producer,run=43700115169,job=132769186550,artifact=14156900587,artifact_bytes=99483928,artifact_sha256='06104f175a79f38aa22961cabb6467e33838724e9e87f9b037e3477defa970fb',all_unfiltered_artifact_members=749,expected_phase_exits=153,whole_record_counts=dict(zip(native_labels,counts)),whole_class_omissions=24,original_source_guards=1440,both_original_proof_modules=12,both_original_proof_declarations=70,all_exact_local_binding_verdicts=70,all_compiled_source_files=len(source_rows),downloaded_actual_Rust_auditor_controls=results,whole_original_job_log_retained=True,actual_compiled_runtime_test_and_auditor_bytes_equal=True,full_prepared_RLIB_RMETA_and_complete_Cargo_closure_and_actual_reuse_checked=True,scope='unsigned bounded exact CI03 replay and independent downloaded Rust auditor acceptance only; no induced-transfer proof CI, all-current/global CI, calibrated cost, cold120 acceptance, ECDLP advantage, or signed standing')
(out/'acceptance.json').write_text(json.dumps(acceptance,indent=2)+'\n')
print('Complete exact CI03 acceptance',json.dumps({k:v for k,v in acceptance.items()if k!='downloaded_actual_Rust_auditor_controls'}),flush=True)
