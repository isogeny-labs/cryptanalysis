"""Repository governance and normal publication; no scientific calculations."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess,sys
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
label,message=sys.argv[1:3];base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
g=s/'evidence'/('beta-'+label+'-governance-01');g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scopes=['problems/chained-transfer-original-FB30-character-extension.md','.github/workflows/chained-transfer-original-fixed-ic.yml','docs/research-artifacts/chained-transfer/original-IC-sampler-26','.github/workflows/chained-transfer-induced-proof.yml',str(s.relative_to(r)),'.github/workflows/chained-transfer-beta-rational-lift.yml','.github/workflows/chained-transfer-beta-complete.yml','.github/workflows/chained-transfer-norm-halving.yml','.gitattributes','docs/research-artifacts/chained-transfer/beta-complete-rational-01','docs/research-artifacts/chained-transfer/beta-complete-PCC-failure-01','docs/research-artifacts/chained-transfer/norm-halving-01','docs/research-artifacts/chained-transfer/nondual13-phaseA-01','docs/research-artifacts/chained-transfer/nondual-models-18','docs/research-artifacts/chained-transfer/fixed-twisted-pair-20','docs/research-artifacts/chained-transfer/paired-fourth-21','docs/research-artifacts/chained-transfer/complete-chain-22','docs/research-artifacts/chained-transfer/norm-point-original-prime-23','docs/research-artifacts/chained-transfer/original-prime-kernel-geometry-24','docs/research-artifacts/chained-transfer/original-full-group-25','.github/workflows/chained-transfer-nondual-preflight.yml','.github/workflows/chained-transfer-twisted-pair.yml','.github/workflows/chained-transfer-paired-fourth.yml','.github/workflows/chained-transfer-fixed-chain.yml','.github/workflows/chained-transfer-original-full.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','docs/session-logs/2026-11-15.md','.resume/RESUME.md','problems/chained-transfer-odd-product-kernel-and-odd-factor.md','problems/README.md','problems/chained-transfer-cold-preflight-build-budget.md','problems/chained-transfer-cold-preflight-build-budget-update-20261114.md','problems/chained-transfer-census-process-lifetime.md','problems/chained-transfer-incomplete-cold-arithmetic-census.md']
new23aliases=[s/'fixed-jacobian-chain-evaluator-02/expected-native-01.json.xz',s/'evidence/fixed-chain-norm-point-native-01/whole-positive-native.txt.xz',s/'evidence/original-prime-native-failure-01/completed-whole-records.json']
new23manifest=json.loads((r/'docs/research-artifacts/chained-transfer/norm-point-original-prime-23/.artifacts.json').read_text())
new23names=['norm-point-reuse-expected-native-01.json.xz','norm-point-reuse-whole-native-01.txt.xz','original-prime-native01-completed-records.json']
new23paths=set()
for p,name in zip(new23aliases,new23names):
 assert p.is_symlink() and len(__import__('os').readlink(p))<500
 target=r/'docs/research-artifacts/chained-transfer/norm-point-original-prime-23'/name
 assert p.resolve()==target.resolve() and p.read_bytes()==target.read_bytes()
 assert new23manifest['files'][name]==dict(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
 new23paths.add(p.relative_to(r).as_posix().encode())
new24names=['original-prime-native02-whole1077.json','original-kernel-native01-whole311.json','original-full-geometry-native01-whole16.json','original-full-geometry-all-three-whole-records.json.xz']
new24aliases=[s/'original-prime-chain-01/expected-native-02.json',s/'original-kernel-census-01/expected-native-01.json',s/'original-full-geometry-01/expected-native-01.json',s/'evidence/original-full-geometry-native-01/literal-all-three-whole-geometries.json.xz']
new24manifest=json.loads((r/'docs/research-artifacts/chained-transfer/original-prime-kernel-geometry-24/.artifacts.json').read_text());new24paths=set();new24unparented=set()
for p,name in zip(new24aliases,new24names):
 assert p.is_symlink()and len(__import__('os').readlink(p))<500
 target=r/'docs/research-artifacts/chained-transfer/original-prime-kernel-geometry-24'/name
 assert p.resolve()==target.resolve()and p.read_bytes()==target.read_bytes()
 assert new24manifest['files'][name]==dict(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
 n=p.relative_to(r).as_posix().encode();new24paths.add(n)
 if subprocess.run(['git','cat-file','-e',base+':'+n.decode()],cwd=r,capture_output=True).returncode!=0:new24unparented.add(n)
new25name='original-full-evaluator-native02-whole701.json.xz';new25alias=s/'original-full-evaluator-01/expected-native-02.json.xz';new25target=r/'docs/research-artifacts/chained-transfer/original-full-group-25'/new25name
new25manifest=json.loads((new25target.parent/'.artifacts.json').read_text());assert new25alias.is_symlink()and len(__import__('os').readlink(new25alias))<500 and new25alias.resolve()==new25target.resolve()and new25alias.read_bytes()==new25target.read_bytes();assert new25manifest['files'][new25name]==dict(bytes=new25target.stat().st_size,sha256=hashlib.sha256(new25target.read_bytes()).hexdigest())
new25paths={new25alias.relative_to(r).as_posix().encode()};new25unparented={n for n in new25paths if subprocess.run(['git','cat-file','-e',base+':'+n.decode()],cwd=r,capture_output=True).returncode!=0}
new26manifest=json.loads((r/'docs/research-artifacts/chained-transfer/original-IC-sampler-26/.artifacts.json').read_text());new26original=json.loads(Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-original-IC-sampler-handoff-26/.artifacts.json').read_text());new26paths=set();new26unparented=set()
for name,package in [('original-fixed-model-IC-whole100.json.xz','original-fixed-model-ic-01'),('original-fixed-model-sampler-whole101.json.xz','original-fixed-model-sampler-01')]:
 p=s/package/'expected-native-01.json.xz';target=r/'docs/research-artifacts/chained-transfer/original-IC-sampler-26'/name
 assert p.is_symlink()and len(__import__('os').readlink(p))<500 and p.resolve()==target.resolve()and p.read_bytes()==target.read_bytes()
 assert new26manifest['files'][name]==new26original['files'][name]==dict(bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
 n=p.relative_to(r).as_posix().encode();new26paths.add(n)
 if subprocess.run(['git','cat-file','-e',base+':'+n.decode()],cwd=r,capture_output=True).returncode!=0:new26unparented.add(n)
def paths():return sorted(((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--no-renames','--name-only','-z'],cwd=r).split(b'\0')))-{b''})|new24unparented|new25unparented|new26unparented)
def run(n,c):
 q=subprocess.run(c,cwd=r,capture_output=True);raw=q.stdout+q.stderr;(g/(n+'.txt.xz'if len(raw)>60000 else n+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw);(g/(n+'.exit')).write_text(str(q.returncode)+'\n');print(n,q.returncode,flush=True);assert q.returncode==0,raw[:2000]
for n,p in [('norm784','ci_norm_sampling/reference-01.sha256'),('arithmetic22','arithmetic-audit/reference-03.sha256')]:run(n,['sha256sum','--check',str(s/p)])
ref=s/'ci_beta_lift'/('reference-02.sha256'if(s/'ci_beta_lift/reference-02.sha256').exists()else'reference-01.sha256')
run('beta-reference',['sha256sum','--check',str(ref)])
run('complete-reference',['sha256sum','--check',str(s/'ci_beta_complete/reference-01.sha256')])
run('complete-shell',['bash','-n',str(s/'ci_beta_complete/check.sh')])
run('complete-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-beta-complete.yml'])
run('complete-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'beta-complete-evaluator/src').rglob('*.rs'))]])
run('norm-halving-reference',['sha256sum','--check',str(s/'ci_norm_halving/reference-01.sha256')])
run('norm-halving-shell',['bash','-n',str(s/'ci_norm_halving/check.sh')])
run('norm-halving-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-norm-halving.yml'])
run('norm-halving-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'norm-halving-evaluator/src').rglob('*.rs'))]])
run('new-audit-shell',['bash','-n',str(s/'norm-arithmetic-audit/quadratic-canary.sh'),str(s/'norm-arithmetic-audit/run-panels.sh')])
run('new-audit-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'norm-arithmetic-audit').rglob('*.rs'))]])
run('nondual-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'nondual13-preflight/src').rglob('*.rs'))]])
run('model-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'nondual13-preflight/models/src').rglob('*.rs'))]])
run('next-prior-inputs',['sha256sum','--check',str(s/'nondual13-next-preflight/frozen-prior-inputs-01.sha256')])
run('next-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for root in [s/'nondual13-next-preflight/src',s/'nondual13-next-preflight/models/src']for p in sorted(root.rglob('*.rs'))]])
run('observer-prior24',['sha256sum','--check',str(s/'observer-storage-prior-inputs-02.sha256')])
run('partial-diagnostic-shell',['bash','-n',str(s/'norm-arithmetic-storage-02/diagnose-partial-04.sh')])
run('twist-prior981',['sha256sum','--check',str(s/'twisted-pair-preflight/frozen-prior-inputs-01.sha256')])
run('twist-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(x) for x in sorted((s/'twisted-pair-preflight/src').rglob('*.rs'))]])
run('twist-new-shell',['bash','-n',str(s/'twisted-pair-preflight/run-native-01.sh'),str(s/'twisted-pair-preflight/run-native-02.sh'),str(s/'norm-arithmetic-storage-02/panel-after-interruption-04.sh')])
run('observer-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p) for p in sorted((s/'norm-arithmetic-storage-02').rglob('*.rs'))]])
run('observer-new-shell',['bash','-n',str(s/'norm-arithmetic-storage-02/quadratic-canary.sh'),str(s/'norm-arithmetic-storage-02/run-panels.sh'),str(s/'norm-arithmetic-storage-02/continue-validation-03.sh')])
run('nondual22-shell',['bash','-n',str(s/'ci_nondual_preflight/check.sh')])
run('nondual22-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-nondual-preflight.yml'])
run('nondual22-reference',['sha256sum','--check',str(s/'ci_nondual_preflight/reference-04.sha256')])
run('twisted20-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/fixed-twisted-pair-20'])
run('fourth-prior1028',['sha256sum','--check',str(s/'paired-fourth-preflight/frozen-prior-inputs-01.sha256')])
run('fourth-new-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'paired-fourth-preflight/src').rglob('*.rs'))]])
run('fourth-shell',['bash','-n',str(s/'paired-fourth-preflight/build-only-01.sh'),str(s/'paired-fourth-preflight/run-native-01.sh')])
run('chain-prior1060',['sha256sum','--check',str(s/'fixed-jacobian-chain-01/frozen-prior-inputs-01.sha256')])
run('chain-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(x)for x in sorted((s/'fixed-jacobian-chain-01/src').rglob('*.rs'))]])
run('chain-shell',['bash','-n',str(s/'fixed-jacobian-chain-01/build-only-01.sh'),str(s/'fixed-jacobian-chain-01/run-native-01.sh')])
run('fourth24-reference',['sha256sum','--check',str(s/'ci_paired_fourth/reference-01.sha256')])
run('fourth24-shell',['bash','-n',str(s/'ci_paired_fourth/check.sh')])
run('fourth24-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-paired-fourth.yml'])
run('chain-evaluator-prior1080',['sha256sum','--check',str(s/'fixed-jacobian-chain-evaluator-01/frozen-prior-inputs-01.sha256')])
run('chain-evaluator-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(x)for x in sorted((s/'fixed-jacobian-chain-evaluator-01/src').rglob('*.rs'))]])
run('chain-evaluator-shell',['bash','-n',str(s/'fixed-jacobian-chain-evaluator-01/build-only-01.sh'),str(s/'fixed-jacobian-chain-evaluator-01/run-native-01.sh')])
run('fixedchain25-reference',['sha256sum','--check',str(s/'ci_fixed_chain/reference-02.sha256')])
run('fixedchain25-shell',['bash','-n',str(s/'ci_fixed_chain/check-02.sh')])
run('fixedchain25-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-fixed-chain.yml'])
run('fixedchain25-audit-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--check',str(s/'ci_fixed_chain/audit/src/main.rs')])
run('norm-reuse-original1099',['sha256sum','--check',str(s/'fixed-jacobian-chain-evaluator-02/frozen-prior-inputs-01.sha256')])
run('norm-reuse-shell',['bash','-n',str(s/'fixed-jacobian-chain-evaluator-02/build-only-01.sh'),str(s/'fixed-jacobian-chain-evaluator-02/run-native-01.sh')])
run('norm-reuse-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for root in [s/'fixed-jacobian-chain-evaluator-02/src',s/'fixed-jacobian-chain-evaluator-02/derived']for p in sorted(root.rglob('*.rs'))]])
run('original-prime-prior1131',['sha256sum','--check',str(s/'original-prime-chain-01/frozen-prior-inputs-01.sha256')])
run('original-prime-shell',['bash','-n',str(s/'original-prime-chain-01/build-only-01.sh'),str(s/'original-prime-chain-01/build-only-02.sh'),str(s/'original-prime-chain-01/run-native-01.sh')])
run('original-prime-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-prime-chain-01/src').rglob('*.rs'))]])
run('kernel-census-prior1172',['sha256sum','--check',str(s/'original-kernel-census-01/frozen-prior-inputs-01.sha256')])
run('kernel-census-shell',['bash','-n',str(s/'original-kernel-census-01/build-only-01.sh'),str(s/'original-kernel-census-01/run-native-01.sh')])
run('kernel-census-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-kernel-census-01/src').rglob('*.rs'))]])
run('original-full-geometry-prior1206',['sha256sum','--check',str(s/'original-full-geometry-01/frozen-prior-inputs-01.sha256')])
run('original-full-geometry-shell',['bash','-n',str(s/'original-full-geometry-01/build-only-01.sh'),str(s/'original-full-geometry-01/run-native-01.sh')])
run('original-full-geometry-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-full-geometry-01/src').rglob('*.rs'))]])
run('original-full-evaluator-prior',['sha256sum','--check',str(s/'original-full-evaluator-01/frozen-prior-inputs-01.sha256')])
run('original-full-evaluator-shell',['bash','-n',str(s/'original-full-evaluator-01/build-only-01.sh'),str(s/'original-full-evaluator-01/run-native-01.sh')])
run('original-full-evaluator-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-full-evaluator-01/src').rglob('*.rs'))]])
run('additive-original-full03-reference',['sha256sum','--check',str(s/'ci_fixed_chain/reference-03.sha256')])
run('additive-original-full03-shell',['bash','-n',str(s/'ci_fixed_chain/check-03.sh')])
run('additive-original-full03-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-original-full.yml'])
run('induced-proof73-reference',['sha256sum','--check',str(s/'ci_induced_transfer/reference-01.sha256')])
run('induced-proof-shell',['bash','-n',str(s/'ci_induced_transfer/check-01.sh')])
run('induced-proof-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-induced-proof.yml'])
run('original-model-IC-prior1465',['sha256sum','--check',str(s/'original-fixed-model-ic-01/frozen-prior-inputs-01.sha256')])
run('original-model-IC-build-native-shell',['bash','-n',str(s/'original-fixed-model-ic-01/build-only-01.sh'),str(s/'original-fixed-model-ic-01/run-native-01.sh')])
run('original-model-IC-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-fixed-model-ic-01/src').rglob('*.rs'))]])
run('original-model-IC-literal-solver',['cmp',str(s/'original-fixed-model-ic-01/derived/class_solver.rs'),str(s/'new-target-ic/derived/class_solver.rs')])
run('original-sampler-prior',['sha256sum','--check',str(s/'original-fixed-model-sampler-01/frozen-prior-inputs-01.sha256')])
run('original-sampler-shell',['bash','-n',str(s/'original-fixed-model-sampler-01/build-only-01.sh'),str(s/'original-fixed-model-sampler-01/run-native-01.sh')])
run('original-sampler-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-fixed-model-sampler-01/src').rglob('*.rs'))]])
run('original-sampler-literal-classbody',['cmp',str(s/'original-fixed-model-sampler-01/derived/class_solver.rs'),str(s/'norm-assisted-ic/derived/class_solver.rs')])
run('new-fixed-IC1503-reference',['sha256sum','--check',str(s/'ci_original_fixed_ic/reference-01.sha256')])
run('new-fixed-IC-shell',['bash','-n',str(s/'ci_original_fixed_ic/check-01.sh')])
run('new-fixed-IC-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-original-fixed-ic.yml'])
run('new-fixed-IC-historical-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(s/'ci_original_fixed_ic/audit/src/main.rs')])
run('relation1503-prior',['sha256sum','--check',str(s/'original-relation-kernel-01/frozen-prior-inputs-01.sha256')])
run('relation17-current',['sha256sum','--check',str(s/'original-relation-kernel-01/frozen-current-inputs-01.sha256')])
run('relation-two-native-driver',['sha256sum','--check',str(s/'original-relation-kernel-01/frozen-native-driver-01.sha256')])
run('relation-build-native-shell',['bash','-n',str(s/'original-relation-kernel-01/build-only-01.sh'),str(s/'original-relation-kernel-01/run-native-01.sh')])
run('relation-wrapper-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(p)for p in sorted((s/'original-relation-kernel-01/src').rglob('*.rs'))]])
run('rank10-current',['sha256sum','--check',str(s/'original-relation-rank-01/frozen-current-inputs-01.sha256')])
run('rank-shell',['bash','-n',str(s/'original-relation-rank-01/run-native-01.sh')])
run('rank-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--check',*[str(q)for q in sorted((s/'original-relation-rank-01/src').rglob('*.rs'))]])
run('character1532-prior',['sha256sum','--check',str(s/'original-relation-character-01/frozen-prior-inputs-01.sha256')])
run('character11-current',['sha256sum','--check',str(s/'original-relation-character-01/frozen-current-inputs-01.sha256')])
run('character2-native-driver',['sha256sum','--check',str(s/'original-relation-character-01/frozen-native-driver-01.sha256')])
run('character-shell',['bash','-n',str(s/'original-relation-character-01/build-only-01.sh'),str(s/'original-relation-character-01/run-native-01.sh')])
run('character-rustfmt',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--check',*[str(q)for q in sorted((s/'original-relation-character-01/src').rglob('*.rs'))]])
run('twisted23-reference',['sha256sum','--check',str(s/'ci_twisted_pair/reference-01.sha256')])
run('twisted23-shell',['bash','-n',str(s/'ci_twisted_pair/check.sh')])
run('twisted23-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-twisted-pair.yml'])
run('native-models18-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/nondual-models-18'])
run('nativeA-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/nondual13-phaseA-01','docs/research-artifacts/chained-transfer/nondual-models-18','docs/research-artifacts/chained-transfer/fixed-twisted-pair-20','.github/workflows/chained-transfer-nondual-preflight.yml'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scopes]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-beta-rational-lift.yml']);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate']);run('reportPython',['python3','tools/ci/check_report_graph_python.py'])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite'],cwd=r)
def stage():
 ps=paths();indexed=set(subprocess.check_output(['git','ls-files','-z'],cwd=r).split(b'\0'))
 prefix=b'experiments/chained-transfer-public-target/evidence/fixed-chain25-source-controls-01/build/'
 explicit=[x for x in ps if x.startswith(prefix)]
 allowed=set()
 for proof in json.loads((r/'pcc/claims/PCC-20261115-65dc1f.json').read_text())['proofs']:
  if proof.get('kind')=='attestation':
   v=proof['subject'];name=v['path'].encode()
   if name.startswith(prefix):
    q=r/v['path'];assert q.is_file()and q.stat().st_size<65536 and q.suffix in ['.txt','.exit','.json'];assert hashlib.sha256(q.read_bytes()).hexdigest()==v['sha256'];allowed.add(name)
 assert set(explicit)<=allowed
 for suffix,selected_paths,force in [('normal',[x for x in ps if x!=b'.resume/RESUME.md'and x not in allowed and x not in new23paths and x not in new24paths and x not in new25paths and x not in new26paths],False),('exact-small-attestations',explicit,True),('exact-three-canonical-symlinks',sorted(new23paths&set(ps)),True),('exact-four24-canonical-symlinks',sorted(new24paths&set(ps)),True),('exact-one25-canonical-symlink',sorted(new25paths&set(ps)),True),('exact-two26-canonical-symlinks',sorted(new26paths&set(ps)),True)]:
  if not selected_paths:continue
  file=Path('/workspace/scratch/ct89-'+label+'-'+suffix+'.paths0');file.write_bytes(b'\0'.join(x for x in selected_paths if (r/x.decode()).exists()or(r/x.decode()).is_symlink()or x in indexed)+b'\0')
  command=['git','add','--sparse']+(['--force']if force else[])+['--pathspec-from-file='+str(file),'--pathspec-file-nul'];subprocess.run(command,cwd=r,check=True)
 subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--no-renames','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for name in selected:
  if name.startswith(b'pcc/claims/'):
   for proof in json.loads((r/name.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     v=proof['subject'];assert hashlib.sha256((r/v['path']).read_bytes()).hexdigest()==v['sha256']
     if v['path'].encode()not in selected and subprocess.run(['git','cat-file','-e',base+':'+v['path']],cwd=r,capture_output=True).returncode!=0:
      allowed='experiments/chained-transfer-public-target/reports/beta-complete-rational-01/complete-diagram.png';assert v['path']==allowed,v['path']
      png=r/allowed;manifest=png.parent/'.artifacts.json';ignore=png.parent/'.gitignore';actual=Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-beta-png-handoff-01/.artifacts.json')
      entry=json.loads(manifest.read_text())['files'][png.name];assert entry==json.loads(actual.read_text())['files'][png.name];assert entry==dict(bytes=png.stat().st_size,sha256=v['sha256'])
      assert manifest.relative_to(r).as_posix().encode()in selected and ignore.relative_to(r).as_posix().encode()in selected
      assert subprocess.run(['git','check-ignore','-q',allowed],cwd=r).returncode==0
      assert json.loads((r/'experiments/chained-transfer-public-target/evidence/genuine-complete-beta-PNG-publication-01/publication.json').read_text())['bot']=='e149ba385fd3539a58fada68f279e9f1b30f898e'
 return selected
stage();run('original-IC-sampler26-staged-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/original-IC-sampler-26']);run('original-full-group25-staged-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/original-full-group-25']);run('original-prime-kernel-geometry24-staged-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/original-prime-kernel-geometry-24']);run('norm-point-original-prime23-staged-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/norm-point-original-prime-23']);run('complete22-staged-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/complete-chain-22']);run('fourth21-staged-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/paired-fourth-21']);run('twisted20-staged-original-artifact-verify',['python3','tools/artifacts/artifacts.py','verify','docs/research-artifacts/chained-transfer/fixed-twisted-pair-20']);run('cached-whitespace',['git','diff','--cached','--check']);assert subprocess.check_output(['git','show',':experiments/chained-transfer-public-target/reports/original-relation-kernel-proposal-01/report.pdf'],cwd=r)==(s/'reports/original-relation-kernel-proposal-01/report.pdf').read_bytes();tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),base=base,label=label,all_recorded_governance_exits=0,reference=ref.relative_to(r).as_posix(),exact_subject_hash_and_staging_checked=True,only_external_subject="none; all report/data subjects are tracked links to original genuinely published canonical docs",original_tools_scripts_suite_unchanged=True,scope='unsigned governance; no mathematical or execution signed standing'),indent=2)+'\n')
cmd=['python3', 'tools/pcc/pcc.py', 'claim', 'new', '--kind', 'statement', '--claim-type', 'data', '--statement', 'Complete relation-character result-report checkpoint governance: alloriginal science/workflows/oldguards/passive observer/rank10/character1532prior11compiled2driver unchanged; originalRustfmt-shell-ledger-prose-workingcachedwhitespace-wiring-benchrec-reportPython-canonicalartifactverify-artifact0 and exactnewsubjects stagedorparented. Report2fd6b0 full53962B/twoactualopenedpages/sourceMarkdown-Typst-vectorplot-evidenceflow/wholeRust60reportdata; allthreewhole drafts/PDFs/rasters and citation-spacing corrections retained, no scientific data change. Named finite FB30 character-extension problem records true limited obstruction and unassisted prospective-repair/matched-cost exit criteria. Published3a7d56/693 native13200actualnormBSGSdirectwitnesses15125relation occurrences/whole60population confirms finitefunctional mismatch before descent/all180canonical-characterdecompositions hold; no globalcharacter-causal-numericLean-calibrated promotion. Current693requiredPCCsuccess/GitHubqueueupdated/Root4cea mirrorsacceptedCI-capture-rank-proof. NextRootcharacter mirror/genuineNEW27 with everywhole raw-source-runtime-fullprepared-control-failure-GitHubartifact-log-report root, thenprospective diagnosticCI/successor review.']
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(f.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();print(cl,flush=True);selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m',message],cwd=r,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print(head,len(selected),flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-public-target-20261113','/workspace/scratch/ct89-'+label+'-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct89-'+label+'-publication-caller.txt').write_bytes(q.stdout+q.stderr);print('normalpub',q.returncode,flush=True);assert q.returncode==0
