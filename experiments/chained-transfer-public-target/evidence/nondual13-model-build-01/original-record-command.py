"""Build/source/binary custody only; the model test has not executed."""
from pathlib import Path
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';pkg=s/'nondual13-preflight/models';e=s/'evidence/nondual13-model-build-01';e.mkdir();rows=[]
for suffix in ['01','02','03']:
 raw=Path('/workspace/scratch/ct77-nondual-model-build-'+suffix)
 for n in ['lock.txt','lock.exit','compile.stderr.txt','compile.exit']:shutil.copyfile(raw/n,e/(suffix+'-'+n))
 artifacts=[json.loads(l)for l in(raw/'compile.jsonl').read_text().splitlines()];bins=[v for v in artifacts if v.get('reason')=='compiler-artifact'and v.get('executable')and v.get('target',{}).get('name')=='chained_n4_nondual13_model_preflight'];assert len(bins)==1
 p=Path(bins[0]['executable']);copy=raw/'actual-test-executable.bin'
 # Each version has its own Cargo package path or final source fingerprint.
 # Save the current03 actual binary;02/01 historical binaries may share02 path,
 # so only record an actual copy when the original build-specific path remains.
 if suffix=='03' or p.exists() and suffix=='01':
  shutil.copyfile(p,copy);rows.append({'build':suffix,'cargo_artifact':bins[0],'actual_copy':str(copy),'bytes':copy.stat().st_size,'sha256':hashlib.sha256(copy.read_bytes()).hexdigest()})
 if suffix=='03':shutil.copytree(pkg,raw/'actual-source')
(e/'actual-binaries.json').write_text(json.dumps(rows,indent=2)+'\n')
shutil.copyfile(pkg/'generated/custody.json',e/'literal-model-torsion-custody.json')
for n in ['original-local-artifact-verify.txt','original-local-artifact-verify.exit','original-local-artifact-verify02.txt','original-local-artifact-verify02.exit']:shutil.copyfile(Path('/workspace/scratch/ct77-nondual-model-build-02')/n,e/n)
(e/'scope.json').write_text(json.dumps({'protocol':'23ab48 beforecode; fields/models unknown until actual native run','builds':'scratch01/portable02/strengthened currentJ1 identity03 allcompile0; no native model test executed','versions':'02 original test binary path was reused by03 and not copied before rebuild; retain full02 Cargo artifact/source as compiled metadata, do not claim surviving02 historical executable.03 and scratch01 actualcopies retained.','literal':'original generic model/source/even and original finite-space helper prefixes exact, constructor appended in source module; original check/Hasse/prime generator preserved','actual_data':'full64 gamma2/coefficientconjugate coordinates, all4096 addition/pairing rows, Frobenius and135 kernels plus both E0/E1 whole model parity are implemented but unrun','selection':'currentJ1 checked by original NormNew/Adapter fulltag; transported mask printed/fixed before E2 builder; allsix outcomes retained, no eligible-case filtering','artifact_verify':'first original verifier exits0 withzeroentries before manifest staging, not a two-object check. After staging original tool reports2entries2hydrated0problems0. No remote read claimed.'},indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Nondual full-product/model phaseB underprospective23ab48 implemented additively withliteral originalgeneric/source/even/finite-space helpers andappendedactualE2constructor. Scratch01/portable02/currentJ1-strengthened03 builds0; native POSITIVE NOT RUN, matchedJ2 unknown. CurrentJ1 fulloriginalNormNew/Adapter tag is asserted beforemasktransport; exactmask fixed beforeE2modelbuilder, all64coordinates/4096actualaddition+pairing rows/Frobenius/135kernels/botholdfullpanels/allsixnewcases implemented. OriginalSourceE prime-generator/uniqueHassecheck retained. Actual03 andscratch01 binaries pinned;02 historical path reused by03, no02binarysurvival claim. Originalartifactverify first0entries beforestaging, thenactual2hydrated0problems0. Buildcustodyunsigned, no model/mathematical/cost success yet.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
