"""Original proof bindings and whole known-identity development evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,lzma,os,shutil,subprocess,sys
r=Path('/workspace/cryptanalysis');p=r/'experiments/chained-transfer-lp-presentation-01';raw=Path('/workspace/scratch/ct134-LP-foundation-development-01');e=p/'evidence/foundation-proof-and-identity-01';e.mkdir()
names=['even_four_cycle','odd_triangle','two_odd_triangles','half_ground_edge','dot_zero','dot_add','dot_scale','combine_kernel','combine_full_kernel','projected_kernel_iff_of_finite_spans'];expected={'LPProjection.'+n for n in names}
assert (p/'lean/LPProjection.lean').read_bytes()==(raw/'LPProjection.first-source.lean').read_bytes()
for side in ['original-Lean434-gate','original-Root-Lean435-gate']:
 assert(raw/(side+'.exit')).read_text().strip()=='0'
 logs=list((raw/side).rglob('audit.log'));assert len(logs)==1;body=logs[0].read_text();decl={line.split()[1]for line in body.splitlines()if line.startswith('ok    ')}
 assert expected<=decl and decl-expected=={'LPProjection.dot.eq_1','LPProjection.dot.eq_2','LPProjection.dot.eq_def'}and'0 failing, 0 trusted'in body
 shutil.copytree(raw/side,e/side)
 for suffix in ['.log','.exit']:shutil.copyfile(raw/(side+suffix),e/(side+suffix))
for n in ['second-native-unit-build.log','second-native-unit-build.exit','native-binary-build.log','native-binary-build.exit','native-identities.log','native-identities.exit']:
 shutil.copyfile(raw/n,e/n)
 if n.endswith('.exit'):assert(raw/n).read_text().strip()=='0'
shutil.copytree(raw/'entire-native-identities',e/'entire-native-identities')
shutil.copyfile('/workspace/scratch/ct134-foundation-conductor.txt',e/'conductor.txt');shutil.copyfile('/workspace/scratch/ct134-foundation-conductor.exit',e/'conductor.exit');assert(e/'conductor.exit').read_text().strip()=='127'
for f in (e/'entire-native-identities').glob('*.certificate.json'):
 cert=json.loads(f.read_text());assert cert['proof']['sha256']==hashlib.sha256((p/'lean/LPProjection.lean').read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
scope='Known ring cancellations and finite homogeneous linear-kernel projection under explicit full-projection-span, constraint-span, annihilation and valid-full-lift hypotheses. Both unchanged original gates audit13declarations: ten named substantive theorems and three generated dot equations, standard foundations only,0trusted. No new identity or novelty, no concrete numerical basis-completeness theorem, no q223 population, Picard character or solver/program bridge, solve/cost/complexity claim. Original native identity checker and SHA included unchanged; deterministic extra-point diagnostics are not signed independent execution proofs. Unsigned local theorem binding.'
bindings=[];env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.34.1/bin:'+os.environ['PATH'])
for short in names:
 name='LPProjection.'+short;_,statement=m.lean_find_declaration([p/'lean/LPProjection.lean'],name)
 proof=dict(path=(p/'lean/LPProjection.lean').relative_to(r).as_posix(),theorem=name,decl_sha256=hashlib.sha256(statement.encode()).hexdigest())
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope',scope,'--proof','lean:'+json.dumps(proof)]
 claim=subprocess.check_output(cmd,cwd=r,text=True).strip();q=subprocess.run(['python3','tools/pcc/pcc.py','verify',claim,'--json'],cwd=r,env=env,capture_output=True,timeout=120)
 (e/(short+'-binding.json')).write_bytes(q.stdout);(e/(short+'-binding.stderr.txt')).write_bytes(q.stderr);(e/(short+'-binding.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0 and json.loads(q.stdout)['verdict']=='pass'
 bindings.append(dict(claim=claim,theorem=name,statement=statement));print(name,claim,'local-binding0 unsigned',flush=True)
(e/'all-ten-bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
binary=Path('/dev/shm/ct134-lp-foundation-target-01/release/lp-foundation-identities')
dep=Path('/dev/shm/ct134-lp-foundation-target-01/release/lp-foundation-identities.d');shutil.copyfile(dep,e/'actual-native-dependency-closure.d')
guard=subprocess.run(['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'],cwd=r,capture_output=True);(e/'whole1605-original-source-guards.txt.xz').write_bytes(lzma.compress(guard.stdout+guard.stderr));(e/'whole1605-original-source-guards.exit').write_text(str(guard.returncode)+'\n');assert guard.returncode==0
hashes={str(f):dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())for f in [binary,p/'lean/LPProjection.lean',p/'native/Cargo.toml',p/'native/Cargo.lock',p/'native/src/lib.rs',p/'native/src/bin/identities.rs',Path('/workspace/crypto/src/cryptanalysis/identity_certificate.rs'),Path('/workspace/crypto/src/hash/sha256.rs'),r/'tools/lean/proof-gate.sh',r/'tools/lean/AuditAxioms.lean',Path('/workspace/crypto/tools/lean/proof-gate.sh'),Path('/workspace/crypto/tools/lean/AuditAxioms.lean')]}
(e/'complete-source-and-runtime-custody.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),parent_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),exact_files=hashes,all1605_old_source_guards=0,ten_named_theorems_plus_three_generated_equations=True,both_original_gate_0_trusted=True,native_unit_tests=24,all_four_whole_positive_certificates_and_false_identity_counterexamples_retained=True,issuer_points=32,extra_checker_points=32,checker_field='2^61-1',native_field_curve_engine_dependency=False,fixed_population_run=False,paid_build_or_job=False,conductor_unavailable=127,scope='unsigned known-identity and generic proof development; all actual failed attempts retained separately; no numerical/global/signed or performance promotion'),indent=2)+'\n');shutil.copyfile(__file__,e/'original-custody-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','PublishedLPprotocolfoundation: bothunchangedoriginalConsumer4.34/Root4.35gates0,13auditeddeclarations=tennamedsubstantivetheorems+threedotgeneratedequations,0trusted; alltenexactoriginalPCCstatementbindingslocalpass, unsignedstanding. Knownfourcycle/triangle/twooddcycles/halfgroundcancellations, finitekernelclosureandconditionalprojectioniff underexplicitcomplete-span/annihilation/valid-lift hypotheses. Originalnativechecker/SHAbyteexact, release24unitspass, fourfullidentitycertificates32issuer+32extracheckerpointseach andfourwholefalseidentitycounterexamplesretained; originalmodulesactualdependencyclosure/noengine andcompiledbinaryhashcustody. All1605oldsourceguards0, firsthexbuild69d18dandwrongversiongatef05c67 preserved. No fixed60callcomputation, paidbuild/job, novelty/numericbasis/globalcharacter/solve/calibratedcost/complexity orsignedverificationclaim.']
for f in sorted(e.rglob('*')):
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
cmd+=['--proof','attestation:'+(p/'lean/LPProjection.lean').relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();(raw/'foundation-claim-id.txt').write_text(claim+'\n')
entry=f'''# Complete known-identity and generic LP projection foundation

## What was done
{claim}: both original proof gates0,13 audited declarations and0 trusted; all ten substantive statement bindings pass locally. Native release units24/24, four full identity certificates with32 original plus32 extra checker points each, and four whole false controls rejected with original counterexamples. Entire outputs/source/runtime closure retained; all1605 old guards0. [pcc:unverified]

## Decisions made
Keep these as known generic mathematics and development checks. Numerical matrix/basis completeness, finite character and actual program bridges remain independent obligations. Next implement complete native finite projection certificates and independent replay, exercising all frozen synthetic graph classes before the EKS population admission. [pcc:unverified]

## Open threads
Foundation source/report publication, graph units/matrix certificates/lifts/replayer, complete-source CI03, Root4366 actual immutable-tag transport, full NEW28 and original merge/cost/reference/global bridges. [pcc:unverified]

## Errors
Both first failures remain69d18d andf05c67. Extra checker points are deterministic diagnostics, not signed independent execution proofs; no target answers or historical trace entered this foundation. [pcc:unverified]
'''
with(r/'docs/session-logs/2026-11-15.md').open('a')as out:out.write('\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+entry+'\n---\n')
f=r/'.resume/RESUME.md';f.write_text(entry+'\n---\n'+f.read_text());print('foundation',claim,flush=True)
