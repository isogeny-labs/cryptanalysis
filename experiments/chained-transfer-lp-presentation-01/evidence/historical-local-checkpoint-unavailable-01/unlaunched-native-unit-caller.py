"""Build/run native unit tests only; Python handles process and byte custody."""
from pathlib import Path
import hashlib,json,lzma,os,resource,shutil,subprocess

r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01/historical-01'
out=Path('/dev/shm/ct167-lp-historical-development-01');out.mkdir()
shutil.copyfile(__file__,out/'actual-caller.py')
shutil.copyfile('/workspace/scratch/ct167-historical-development-checkpoint-gate01.txt',out/'original-checkpoint-gate.txt')
shutil.copyfile(r/'.resume/.last-push',out/'original-checkpoint-last-push.txt')
for label,source in [('entire-historical-source',p),('entire-unchanged-matrix-source',p.parent/'matrix-01')]:
 shutil.copytree(source,out/label,ignore=shutil.ignore_patterns('target','__pycache__'))
env=os.environ.copy();env.update(CARGO_TARGET_DIR='/dev/shm/ct167-lp-historical-target-01',CARGO_BUILD_JOBS='1',RUSTUP_TOOLCHAIN='1.99.1',LP_HISTORICAL_DEVELOPMENT_OUT=str(out/'all14-entire-native-fixtures'))
def bound():resource.setrlimit(resource.RLIMIT_AS,(2097152*1024,2097152*1024))
def run(label,args):
 q=subprocess.run(['timeout','120',*args],cwd=r,env=env,capture_output=True,preexec_fn=bound)
 (out/(label+'.stdout.xz')).write_bytes(lzma.compress(q.stdout));(out/(label+'.stderr.xz')).write_bytes(lzma.compress(q.stderr));(out/(label+'.exit')).write_text(str(q.returncode)+'\n')
 print(label,q.returncode,flush=True)
 return q
cargo='/home/agent/.cargo/bin/cargo';manifest=str(p/'Cargo.toml')
q=run('cold-compile-all-native-targets',[cargo,'test','--release','--locked','--offline','--manifest-path',manifest,'--all-targets','--no-run','--message-format=json'])
assert q.returncode==0
executables=[]
for line in q.stdout.splitlines():
 row=json.loads(line)
 if row.get('reason')=='compiler-artifact' and row.get('executable') and row.get('profile',{}).get('test'):
  executables.append(Path(row['executable']))
assert len(executables)==3
custody=[]
for i,exe in enumerate(executables):
 whole=exe.read_bytes();digest=hashlib.sha256(whole).hexdigest();binary=out/('actual-native-executable-'+str(i)+'.bin');shutil.copyfile(exe,binary)
 result=run('actual-native-tests-'+str(i),[str(binary),'--nocapture','--test-threads=1'])
 custody.append(dict(executable=str(exe),held_entire_binary=str(binary),sha256=digest,bytes=len(whole),actual_exit=result.returncode))
 assert result.returncode==0
(out/'entire-actual-native-binary-custody.json').write_text(json.dumps(custody,indent=2)+'\n')
q=run('strict-all-target-Clippy',[cargo,'clippy','--release','--locked','--offline','--manifest-path',manifest,'--all-targets','--','-D','warnings'])
assert q.returncode==0
q=run('no-field-engine-Cargo-metadata',[cargo,'metadata','--locked','--offline','--manifest-path',manifest,'--format-version=1'])
assert q.returncode==0
meta=json.loads(q.stdout);allowed={'chained-transfer-lp-historical-01','chained-transfer-lp-finite-projection-01','serde','serde_core','serde_derive','serde_json','proc-macro2','quote','syn','unicode-ident','itoa','ryu','memchr'}
assert {pkg['name']for pkg in meta['packages']}<=allowed
(out/'complete-development-receipt.json').write_text(json.dumps(dict(scope='14 synthetic F101 raw graph fixtures only; no historical source extraction/population',all_native_exits=[x['actual_exit']for x in custody],strict_Clippy_exit=0,no_field_engine_dependency_names=sorted(pkg['name']for pkg in meta['packages']),original_literal_source_checked_by_native_build=True,whole_original_feedback_control_and_fixed60_pending=True),indent=2)+'\n')
