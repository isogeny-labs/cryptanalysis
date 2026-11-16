"""I/O custody of the actual native result; performs no research arithmetic."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
e=s/'evidence/nondual13-model-native-01';e.mkdir()
n=Path('/workspace/scratch/ct77-nondual-model-native-01');a=Path('/workspace/scratch/ct77-nondual-model-audit-01');o=Path('/workspace/scratch/ct77-nondual-model-obstruction-02')
for name in ['native.exit','source-guard.exit','source-head.txt','original-command.sh','actual-Cargo.lock','literal-source-custody.json','frozen-source.sha256','final-source-guards.txt','actual-binary-custody.json']:
 shutil.copyfile(n/name,e/name)
for name in ['freeze.txt','freeze.exit','compare.txt','compare.exit','omission.txt','omission.exit','omission-custody.json','projection.txt','projection.exit','actual-projection-auditor.rs']:
 shutil.copyfile(a/name,e/name)
for name in ['compile.txt','compile.exit','native.txt','native.exit','actual-auditor.rs','report-data.json']:
 shutil.copyfile(o/name,e/('obstruction02-'+name))
assert all((e/name).read_text().strip()=='0' for name in ['native.exit','source-guard.exit','freeze.exit','compare.exit','projection.exit','obstruction02-compile.exit','obstruction02-native.exit'])
assert (e/'omission.exit').read_text().strip()=='101' and not(a/'must-not-exist.json').exists()
for name in ['all-native-records.json.xz','whole-positive-native.txt.xz']:
 p=a/name;(e/(name+'.custody.json')).write_text(json.dumps(dict(workspace_path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),contents='whole native record or stdout; no filtering; XZ roundtrip checked',publication='requires NEW genuine18, not yet remotely published'),indent=2)+'\n')
roots=[n,a,Path('/workspace/scratch/ct77-nondual-model-obstruction-01'),o]
index=[]
for root in roots:
 for p in sorted(root.rglob('*')):
  if p.is_file():index.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(e/'whole-raw-index.json').write_text(json.dumps(index,indent=2)+'\n')
scope=dict(source='87b61e80a62bc0ff6ee832f85e3c0826c74a1bb0',protocol='23ab48, published cf9ca8f5 before phaseA/B code',checkpoint='492150 original43622200522/job132530143829 exact clean87b receipt and localgate0 immediately before native',native='ONE unfiltered test:1pass0failed0ignored0filtered, sourceguards0; actual03 compile/runtime executable bytes equal',whole_records='SIX allfields exact compare0; remove one actual whole MATCHED_MODELS line gives101 and no output',torsion='all64 coordinates, all4096 addition/pairing rows, three actual conjugate maps/Frobenius/135 original masks; pairing is original unique alternating2torsion form, not Miller',selection='currentJ1 original Adapter/NormNew fulltag; full transported mask fixed BEFORE builder; unique matched HLP(2,1); allsix rows retained',outcome='matched smooth true D=(12,0,0) sqrtD=null status=nonsquaretwist;notsuppliedsource; no second supplied-source Jacobian model/map, no retwist/reselection',independent_diagnostic='obstruction02 separate prime-field integer arithmetic exhausts all223 squares and12^111=222; cubic-extension nonsquare uses written tower-law bridge',projection_corrections='01 copied binary launch EACCES before process; chmod correction unchangedbytes.01 summary read absent case key, generated null labels; corrected02 uses original root_index/sign_index and is report source. Native mathematical output unchanged.',standing='unsigned local custody/data; no signed execution, global nonexistence, novelty, calibrated cost or DLP advantage',next='retain negative and model/report; freeze different fixed-kernel continuation prospectively before new code; NEW genuine18 for whole raw/fixture')
(e/'scope.json').write_text(json.dumps(scope,indent=2)+'\n');shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Nondual23ab48 model phaseB atpublished87b after originalcheckpoint492150: ONEunfiltered native test0/sourceguards0/actual03compiled-runtimebinaryequal. Both whole E0/E1parity/all64 actualconjugate torsion/Frobenius/all4096addition+originalalternatingpairing rows/135kernels retained. CurrentJ1 originalAdapterNorm tagchecked; fixedfullmask BEFOREmodelbuilder uniquely matches HLP(2,1): smoothtrue D(12,0,0) sqrtDnull, nonsquaretwist;notsuppliedsource. Endpoint requirement FAILS: no second supplied-source Jacobian model/map; no retwist/reselection. SIXwholeJSON exact0 NOmasks; actualwholeMATCHED_MODELS omission101/nooutput. Independent Rust223squares excludes12 and12^111=222, oddextension inference written. Allsixmodels/whole217960BXZ+150556BXZ/raw/source/actualbinaries retained pendingNEWgenuine18. Diagnostic01 EACCES/nullcaselabel projection corrected02, no native math changed. Unsigned; no globalnonexistence, costgain or novelty.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True)
(o/'result-claim.txt').write_text(claim+'\n')
