"""Preserve the failed import build and corrected compiled source boundary."""
from pathlib import Path
import hashlib,json,lzma,os,stat,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';old=Path('/workspace/scratch/ct86-original-prime-build-01');new=Path('/workspace/scratch/ct86-original-prime-build-02');e=s/'evidence/original-prime-chain-compiled-02';e.mkdir()
assert(old/'chain-compile.exit').read_text().strip()=='101'and(old/'original.exit').read_text().strip()=='1';errors=[]
for line in(old/'chain-compile.txt').read_text().splitlines():
 try:a=json.loads(line)
 except json.JSONDecodeError:continue
 if a.get('reason')=='compiler-message'and a['message']['level']=='error':errors.append(a['message'])
assert len(errors)==2 and all(a['code']['code']=='E0433'and'curve'in a['message']for a in errors)
assert(new/'original.exit').read_text().strip()=='0'
for n in ['prior-inputs','metadata','inherited-preparation','chain-compile','auditor-compile','final-prior-inputs']:assert(new/(n+'.exit')).read_text().strip()=='0'
diff=[]
for p in(old/'actual-source').rglob('*'):
 if p.is_file()and p.read_bytes()!=(new/'actual-source'/p.relative_to(old/'actual-source')).read_bytes():diff.append(p.relative_to(old/'actual-source').as_posix())
assert diff==['src/rational.rs'],diff
before=(old/'actual-source/src/rational.rs').read_text();after=(new/'actual-source/src/rational.rs').read_text();assert before.replace('curve::{Curve, Pt, RatIsogeny}','curve::{self, Curve, Pt, RatIsogeny}')==after
# The complete failed-preparation and corrected-inherited copies remain intact;
# deduplicate only exact closed copies after comparison with the actual cache.
baseline=json.loads(Path('/workspace/scratch/ct82-fixed-chain-evaluator-build-02/engine-prepared.json').read_text());by_suffix={Path(v['copy']).suffix:Path(v['copy'])for v in baseline['files']};links=[]
for raw in [old,new]:
 for row in json.loads((raw/'engine-prepared.json').read_text())['files']:
  p=Path(row['copy']);q=by_suffix[p.suffix]
  if p.read_bytes()==q.read_bytes()==Path(row['actual_path']).read_bytes():
   assert stat.S_IMODE(p.stat().st_mode)==stat.S_IMODE(q.stat().st_mode);h=hashlib.sha256(p.read_bytes()).hexdigest();tmp=p.with_name(p.name+'.closed-identical');os.link(q,tmp);os.replace(tmp,p);assert p.read_bytes()==q.read_bytes();links.append(dict(path=str(p),existing_closed_raw=str(q),bytes=p.stat().st_size,sha256=h,whole_independent_before_after_comparison=True))
(e/'closed-prepared-byte-links.json').write_text(json.dumps(links,indent=2)+'\n')
for label,raw in [('failed01',old),('corrected02',new)]:
 d=e/label;d.mkdir()
 for p in sorted(raw.iterdir()):
  if p.is_file()and p.suffix!='.bin':
   b=p.read_bytes();v=lzma.compress(b)if len(b)>60000 else b;name=p.name+'.xz'if len(b)>60000 else p.name
   assert len(v)<65536,(name,len(v));(d/name).write_bytes(v)
 inv={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()};(d/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_files=inv,future_custody='NEW23; all failed/corrected sources/compiler logs/binaries/full prepared bytes retained'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py');(e/'outcome.json').write_text(json.dumps(dict(protocol='38b827 publishedbd603d0 before code',failed01=dict(compiler=101,worker=1,errors='two E0433 missing curve module imports; before mathematical native'),repair='one nominal curve::self import; every original source member otherwise exact',corrected02=dict(all_recorded_phases=0,prior_guards=1131,engine='original preparation inherited under exact Cargo/resolve/full actual library custody; no second engine preparation',compiler_test=0,compiler_auditor=0),proof='6d8c42 both original7root gates0trusted/all7 bindings',native='NOT RUN',full_population='entire declared original-prime protocol;1,077 ordered records/four whole-class omissions mandatory',scope='unsigned compiled-source boundary only, no runtime/cost/geometric/signed promotion'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Original-prime chain38b827 compiled-source boundary: actual failed01 testcompile101/worker1 has exactlytwo E0433 missing curve imports, full source/compiler/preparedcopies retained. Corrected02 changes only nominal curve::self import among every original member; original1131guards/lockedoffline metadata/inherited full original preparation/testno-run/auditor/finalguards all0. Exact Cargo manifests/resolveddependencygraph/full actual before-after library bytes pin original preparation; NO second enginebuild. Entire tests implement frozen18oldrows/3sourcebackends/672projectedexceptionals-twoways/384public/all228cofactor attempts-fourclasses-strictrejection/64additions-perpair/15oldpublictransfers/12vectors-fiveactualroutes/whole1077auditor+fourwholeomission criteria. Both7root Lean gates/all7 bindings6d8c42 separate. NativeNOTRUN; publish compiledsource/exactoriginalcheckpoint before one900s2GiB attempt. All actualsource/binaries/fullpreparedcopies/failures retainedforNEW23. Unsigned compilation only/no actualfullprimechain/primitivecost/geometric/ECDLP/signed promotion.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+str(p.relative_to(r))]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct86-original-prime-compiled.claim.txt').write_text(claim+'\n');print(claim)
state='''# Original-prime reprojection compiled; publish and exact checkpoint next

'''+claim+''': prospective38b827 was publishedbd603d0 BEFORE code. Corrected02 build all1131 guards/metadata/inherited exact original preparation/test no-run/auditor/finalguards0. Failed01 two E0433 missing imports/source/raw retained; only curve::self nominal import changed. No second engine build. Seven conditional proof roots/both original gates/all7 bindings6d8c42 remain exact. Native NOT RUN. [pcc:unverified]

## What was done
Original-prime runtime implements strict class/norm prime admission and cofactor rejection, norm-assisted reprojection, explicit recovery and five matched opaque/retained/known-point expanded/factored routes. Tests require all18 oldrows/3models/672 projected exceptionals bothways/384public/all228 cofactor attempts-domain/all4classes/64 additions perpair/15 original public endpoint transfers/12vectors and all1077 whole records with four actual class omissions101. Extra correctness preflights are exposed, not minimal setup or a price. [pcc:unverified]

## Decisions made
Publish compiled source and import its exact ORIGINAL checkpoint before original-prime-chain-01/run-native-01.sh EXACTHEAD /workspace/scratch/ct86-original-prime-native-01 /workspace/scratch/ct86-original-prime-build-02. One900s2GiB unfiltered test, whole1077 freeze/compare and four omissions required; preserve any failure without model/population reselection. [pcc:unverified]

## Open threads
Exact strict25 acceptance0f3ea8 is now complete: 43674526503/job132691640180/art14146271228/44978600B/all294members/all58phases/whole13+695/sixwholeomissions/both33rootgates/all33bindings/all1141guards; actualCIauditor positives0/sixomissions101 and full15runlog members retained. Original-prime native; complete primitive/minimal setup/known-point baseline and calibratedrefs; genuineNEW23 of whole new roots before canonical fixtures/replay. [pcc:unverified]

## Errors
All D12/D24/D67, oldtwistprime, fullcold120/root124/clock101/CIpath/staging/authoring/import/legacycleanup failures retained. Source/math contexts remain unsigned/conditional; no paidlaunch/force/rebase/waiver/novelty/signedpromotion. Vault unchanged, KB127. [pcc:unverified]

---

'''
for p in [s/'RESEARCH_QUEUE.md',s/'CHECKPOINT.md',r/'.resume/RESUME.md',r/'docs/session-logs/2026-11-15.md']:p.write_text(state+p.read_text())
