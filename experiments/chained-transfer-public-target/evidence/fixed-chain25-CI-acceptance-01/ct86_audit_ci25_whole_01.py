"""Audit complete CI custody and execute its actual I/O-only Rust auditors."""
from pathlib import Path
import hashlib,json,re,subprocess,os
out=Path('/workspace/scratch/ct86-fixed-chain25-CI-acceptance-01');p=out/'whole-artifact';r=Path('/workspace/cryptanalysis');study=r/'experiments/chained-transfer-public-target'
assert(p/'original.exit').read_text().strip()=='0'and(p/'final-source-guards.exit').read_text().strip()=='0'
assert(p/'consumer-head.txt').read_text().strip()=='77a26ca643847f32b746c8de98812073f71535d0';assert(p/'producer-head.txt').read_text().strip()=='3d49af7f3d0a28e76b79e4825c9d2324e85853d2'
phases=[dict(zip(['name','expected','original'],line.split()))for line in(p/'phases.txt').read_text().splitlines()];assert len(phases)==58 and all(v['expected']==v['original']for v in phases)
assert(p/'original-reference.sha256').read_bytes()==(study/'ci_fixed_chain/reference-02.sha256').read_bytes();ref=(p/'original-reference.sha256').read_text().splitlines();assert len(ref)==1141
for line in ref:
 h,n=line.split('  ',1);assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
for label in ['geometry','chain']:
 for a,b in [(label+'-original-compiled-test.bin',label+'-actual-runtime-test.bin'),('actual-compiled-'+label+'-auditor.bin','actual-runtime-'+label+'-auditor.bin')]:assert(p/a).read_bytes()==(p/b).read_bytes()
 test=json.loads((p/(label+'-compiled-binary.json')).read_text());assert hashlib.sha256((p/(label+'-original-compiled-test.bin')).read_bytes()).hexdigest()==test['sha256']
 for mode in ['compiled','runtime']:
  v=json.loads((p/(label+'-auditor-'+mode+'-custody.json')).read_text());b=(p/('actual-'+mode+'-'+label+'-auditor.bin')).read_bytes();assert len(b)==v['bytes']and hashlib.sha256(b).hexdigest()==v['sha256']
 prepared=json.loads((p/'engine-prepared.json').read_text());reuse=json.loads((p/('engine-reused-'+label+'.json')).read_text());assert reuse['actual_reuse']is True and reuse['Cargo_artifact']['fresh']is True
 for row in prepared['files']:
  f=p/'actual-prepared-original-engine'/Path(row['copy']).name;b=f.read_bytes();assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']
 for row in reuse['actual_aliases']:
  original=next(v for v in prepared['files']if Path(v['actual_path']).suffix==Path(row['dependency_path']).suffix);assert row['bytes']==original['bytes']and row['sha256']==original['sha256']and row['whole_before_and_after_bytes_equal']is True
 for suffix in ['consumer-proofs','producer-proofs']:
  statuses=list((p/suffix).rglob('status'));assert len(statuses)==7 and all(v.read_text().strip()=='PASS'for v in statuses)
  declarations=[]
  for log in(p/suffix).rglob('audit.log'):
   t=log.read_text();assert '0 failing, 0 trusted (native_decide)'in t;declarations+=re.findall(r'^ok\s+([^\s]+)',t,re.M)
  assert len(declarations)==33 and len(set(declarations))==33
bindings=list(p.glob('binding-*.txt'));assert len(bindings)==33
for f in bindings:
 a=json.loads(f.read_text());assert a['verdict']=='pass'and a['commit']=='77a26ca643847f32b746c8de98812073f71535d0';assert all(v['verdict']=='pass'for v in a['proofs'])
source_members=[]
for name,current in [('fixed-jacobian-chain-01',study/'fixed-jacobian-chain-01'),('fixed-jacobian-chain-evaluator-01',study/'fixed-jacobian-chain-evaluator-01'),('paired-fourth-preflight',study/'paired-fourth-preflight'),('geometry-auditor',study/'ci_fixed_chain/audit')]:
 for f in(p/'actual-compiled-source'/name).rglob('*'):
  if f.is_file()and f.suffix in ['.rs','.toml','.lock','.py','.sh','.sha256','.md']:
   target=current/f.relative_to(p/'actual-compiled-source'/name);assert f.read_bytes()==target.read_bytes(),str(f);source_members.append(str(f.relative_to(p)))
host=out/'actual-downloaded-Rust-auditor-controls';host.mkdir();results=[];links=[]
for label,tags in [('geometry',['N4_CHAIN_OLD_LITERAL_PARITY','N4_CHAIN_FIXED_GEOMETRY']),('chain',['N4_FIXED_CHAIN_EXCEPTIONAL_CASE','N4_FIXED_CHAIN_ALL_EXCEPTIONALS','N4_FIXED_CHAIN_ALL_PUBLIC','N4_FIXED_CHAIN_SELECTED_CALL_VECTORS'])]:
 exe=host/(label+'-actual-CI-auditor.bin');exe.write_bytes((p/('actual-compiled-'+label+'-auditor.bin')).read_bytes());exe.chmod(0o700)
 cases=[('whole-positive',p/(label+'-native.txt'),0)]+[(tag,p/(tag+'-entire-actual-records-omitted.txt'),101)for tag in tags]
 for name,native,want in cases:
  target=host/(label+'-'+name+'-accepted.json');cmd=['timeout','120',str(exe),'--compare',str(p/'old-sixteen.json'),str(p/(label+'-expected.json')),str(native),str(target)];q=subprocess.run(cmd,capture_output=True)
  (host/(label+'-'+name+'.txt')).write_bytes(q.stdout+q.stderr);(host/(label+'-'+name+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==want,(label,name,q.returncode)
  if want:
   assert not target.exists()
  else:
   original=p/(label+'-all-whole-records.json');assert target.read_bytes()==original.read_bytes();before=dict(path=str(target),existing_actual_CI_positive=str(original),bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),whole_independent_before_and_after_bytes_equal=True)
   tmp=target.with_name(target.name+'.closed-link');os.link(original,tmp);os.replace(tmp,target);links.append(before)
  results.append(dict(label=label,case=name,original_exit=q.returncode,accepted_output=target.exists()));print(label,name,q.returncode,flush=True)
 assert exe.read_bytes()==(p/('actual-compiled-'+label+'-auditor.bin')).read_bytes()
(out/'host-control-results.json').write_text(json.dumps(results,indent=2)+'\n');(out/'host-positive-exact-byte-links.json').write_text(json.dumps(links,indent=2)+'\n')
logs=json.loads((out/'all-unfiltered-runlog-members.json').read_text());whole=max(logs,key=lambda x:x['bytes']);text=(out/'whole-runlogs'/whole['name']).read_text();assert text.count('test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;')==2
(out/'acceptance.json').write_text(json.dumps(dict(source='77a26ca643847f32b746c8de98812073f71535d0',run=43674526503,job=132691640180,artifact=14146271228,artifact_bytes=44978600,artifact_sha256='4ba6c96eac32a6fb8884bdd7a6270e42e5e48992461b63245fc6d1d9771b2558',all_unfiltered_members=294,expected_phase_exits=58,whole_geometry_records=13,whole_chain_records=695,original_source_guards=1141,both_original_proof_roots=33,all_local_binding_verdicts=33,whole_compiled_source_members_checked=source_members,whole_log=whole,all_runlog_members=len(logs),actual_CI_auditor_controls=results,actual_test_and_auditor_bytes_equal=True,whole_prepared_library_copies_and_actual_reuse=True,scope='unsigned independent whole-custody/actual Rust I-O replay acceptance of original geometry+chain only; no all-current-CI or candidate norm-reuse/prime-chain native inference, calibrated/cold/ECDLP/signing promotion'),indent=2)+'\n');print('Whole CI25 acceptance recorded',flush=True)
