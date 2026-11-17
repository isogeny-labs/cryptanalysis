#!/usr/bin/env python3
"""Bounded local correctness/lint/build checks with source immutability receipts."""
import hashlib,json,os,platform,shutil,signal,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]; FROZEN=Path('/tmp/ic-canonical-frozen-source-001')
expected=json.loads((P/'local-source-manifest.json').read_text())['source_sha256']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def unchanged(): assert {n:sha(FROZEN/n) for n in expected}==expected
env=dict(os.environ,TMPDIR=str(P/'local-tmp'),CARGO_TARGET_DIR=str(ROOT/'suite/target'))
base=['cargo']; manifest=['--locked','-j2','--manifest-path',str(FROZEN/'suite/Cargo.toml')]
checks=[('local-counterfactual-v2.log',base+['test',*manifest,'--lib','counterfactual','--','--nocapture'],240,'3 passed; 0 failed'),('local-framework-v2.log',base+['test',*manifest,'--lib','ic_framework','--','--nocapture'],120,'29 passed; 0 failed'),('local-clippy.log',base+['clippy',*manifest,'--lib','--example','ic_affine_pipeline_probe','--','-D','warnings'],240,None),('local-identity-build.log',base+['build',*manifest,'--example','ic_affine_pipeline_probe'],240,None)]
receipt=dict(status='started',purpose='local ARM correctness and identity generation only; no native performance evidence',source_sha256=expected,checks=[])
try:
    for filename,argv,cap,marker in checks:
        unchanged(); path=P/filename; assert not path.exists()
        with path.open('w') as log:
            proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try: code=proc.wait(timeout=cap)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL); proc.wait(); code=124
        row=dict(argv=argv,cap_seconds=cap,exit_code=code,log=filename,sha256=sha(path)); receipt['checks'].append(row)
        assert code==0 and (marker is None or marker in path.read_text()),filename
        unchanged()
    identity=P/'identity-arm'; identity.mkdir(exist_ok=False)
    binary=identity/'probe'; shutil.copy2(ROOT/'suite/target/debug/examples/ic_affine_pipeline_probe',binary)
    pin=dict(status='built_before_generation',source_sha256=expected,argv=checks[-1][1],binary_sha256=sha(binary),binary_bytes=binary.stat().st_size,rustc=subprocess.check_output(['rustc','-Vv'],text=True),platform=platform.platform(),purpose='identity generation and correctness only; not x86 timing binary')
    (identity/'receipt.json').write_text(json.dumps(pin,indent=2)+'\n')
    receipt['status']='pass'
except Exception as e:receipt.update(status='failed_or_capped',error=repr(e)); raise
finally:(P/'local-checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],checks=len(receipt['checks']),identity_binary_sha256=pin['binary_sha256'])))
