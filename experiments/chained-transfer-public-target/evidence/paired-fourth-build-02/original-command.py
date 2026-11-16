"""Compile remaining wrappers after preserved disk failure; no native research."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');pkg=r/'experiments/chained-transfer-public-target/paired-fourth-preflight';old=Path('/workspace/scratch/ct81-paired-fourth-build-01');out=old.with_name('ct81-paired-fourth-build-02');out.mkdir();shutil.copyfile(__file__,out/'original-command.py')
assert(old/'fourth-compile.exit').read_text().strip()=='0'and(old/'audit-paired-fourth-compile.exit').read_text().strip()=='101'
errors=[json.loads(x)for x in(old/'audit-paired-fourth-compile.txt').read_text().splitlines()if x.startswith('{')];errors=[x for x in errors if x.get('reason')=='compiler-message'and x['message']['level']=='error'];assert len(errors)==1 and 'No space left on device'in errors[0]['message']['rendered']
for p in(old/'actual-source').rglob('*'):
 if p.is_file():assert p.read_bytes()==(pkg/p.relative_to(old/'actual-source')).read_bytes(),str(p)
test=json.loads((old/'fourth-compiled-binary.json').read_text());assert Path(test['actual_path']).read_bytes()==(old/'fourth-original-compiled-test.bin').read_bytes()
env=os.environ.copy();env['PATH']='/home/agent/.cargo/bin:/home/agent/.elan/bin:'+env['PATH'];env['RUSTUP_TOOLCHAIN']='1.99.1';env['CARGO_TARGET_DIR']='/workspace/scratch/ct80-twisted-pair-build-01-cache'
(out/'start.txt').write_text(datetime.now(timezone.utc).isoformat()+'\n');(out/'retained-passing-test-source.json').write_text(json.dumps(dict(original_build=str(old),original_test_compile=0,whole_actual_source_unchanged=True,actual_test_compiler_path=test['actual_path'],whole_compiler_and_retained_bytes_equal=True,prior_auditor_compile=101,prior_error=errors[0]['message']['rendered'],scope='Only remaining two bins compiled; prior passing test/engine not rebuilt or run'),indent=2)+'\n')
try:
 for name in ['audit-paired-fourth','paired-fourth-old-dual-control']:
  q=subprocess.run(['timeout','120','cargo','build','--release','--locked','--offline','--manifest-path',str(pkg/'Cargo.toml'),'--bin',name,'--message-format=json'],cwd=r,env=env,capture_output=True);(out/(name+'-compile.txt')).write_bytes(q.stdout);(out/(name+'-compile.stderr.txt')).write_bytes(q.stderr);(out/(name+'-compile.exit')).write_text(str(q.returncode)+'\n');print(name,q.returncode,flush=True);assert q.returncode==0
  rows=[json.loads(x)for x in q.stdout.decode().splitlines()if x.startswith('{')];bins=[x for x in rows if x.get('reason')=='compiler-artifact'and x.get('target',{}).get('name')==name];assert len(bins)==1
  artifact=bins[0];p=Path(artifact['executable']);copy=out/(name+'.actual-compiled.bin');shutil.copy2(p,copy);(out/(name+'-executable.json')).write_text(json.dumps(dict(actual_Cargo_artifact=artifact,actual_path=str(p),actual_copy=str(copy),bytes=copy.stat().st_size,sha256=hashlib.sha256(copy.read_bytes()).hexdigest(),scope='compiled only; not executed'),indent=2)+'\n')
  engine=[x for x in rows if x.get('reason')=='compiler-artifact'and x.get('target',{}).get('name')=='isogeny_algos'];assert len(engine)==1 and engine[0]['fresh']is True
  before=json.loads((old/'engine-prepared.json').read_text());e=engine[0]
  for k in ['package_id','manifest_path','target','profile','features','executable']:assert e[k]==before['Cargo_artifact'][k]
  prior={Path(x['actual_path']).suffix:x for x in before['files']};seen=set()
  for filename in e['filenames']:
   p=Path(filename);suffix=p.suffix;assert suffix not in seen;seen.add(suffix);ref=prior[suffix];assert p.read_bytes()==Path(ref['copy']).read_bytes()==Path(ref['actual_path']).read_bytes();assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256']
  assert seen=={'.rlib','.rmeta'}
  (out/(name+'-engine-reuse.json')).write_text(json.dumps(dict(Cargo_artifact=e,all_prepared_full_library_alias_bytes_equal=True,actually_fresh=True),indent=2)+'\n')
 for p in(old/'actual-source').rglob('*'):
  if p.is_file():assert p.read_bytes()==(pkg/p.relative_to(old/'actual-source')).read_bytes()
 (out/'original.exit').write_text('0\n')
finally:(out/'finish.txt').write_text(datetime.now(timezone.utc).isoformat()+'\n')
