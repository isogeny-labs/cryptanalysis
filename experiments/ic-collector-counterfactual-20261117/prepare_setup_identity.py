#!/usr/bin/env python3
"""Build and pin a separate ARM identity probe before generating any targets."""
import hashlib,json,os,platform,shutil,signal,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1];F=Path('/tmp/ic-canonical-frozen-source-001')
r=json.loads((P/'setup-build-001/receipt.json').read_text());assert r['status']=='prepared'
hashes=r['source_sha256'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert {n:sha(F/n) for n in hashes}==hashes
D=P/'setup-identity-arm';D.mkdir(exist_ok=False)
argv=['cargo','build','--locked','-j2','--manifest-path',str(F/'suite/Cargo.toml'),'--example','ic_affine_pipeline_probe']
env=dict(os.environ,TMPDIR=str(P/'local-tmp'),CARGO_TARGET_DIR=str(ROOT/'suite/target'),CARGO_INCREMENTAL='0')
with (D/'build.log').open('w') as log:
 proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=proc.wait(timeout=180)
 except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait();code=124
assert code==0,'identity build failed/capped; retain logs'
assert {n:sha(F/n) for n in hashes}==hashes
binary=D/'probe';shutil.copy2(ROOT/'suite/target/debug/examples/ic_affine_pipeline_probe',binary)
receipt=dict(status='built_before_generation',created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_sha256=hashes,argv=argv,binary_sha256=sha(binary),binary_bytes=binary.stat().st_size,build_log_sha256=sha(D/'build.log'),platform=platform.platform(),rustc=subprocess.check_output(['rustc','-Vv'],text=True),purpose='ARM identity generation only; not native timing binary')
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status='built_before_generation',binary_sha256=receipt['binary_sha256'])))
