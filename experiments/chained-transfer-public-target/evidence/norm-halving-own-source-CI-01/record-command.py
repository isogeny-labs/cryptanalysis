"""Retain strict additive own-source CI audit and complete capture indices."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=Path('/workspace/scratch/ct74-norm-halving-own-CI-01');a=Path('/workspace/scratch/ct74-norm-halving-CI-audit-01');e=s/'evidence/norm-halving-own-source-CI-01';e.mkdir();result=json.loads((a/'audit-result.json').read_text());assert(a/'native.exit').read_text()=='0\n';assert result['whole_native_records']==423 and result['successful_runs']==22 and result['canonical_original_PCC_digests']==82 and result['actual_pass_verdicts']==84
for root,label in [(a/'audit-cli','audit-cli')]:
 for p in sorted(root.rglob('*')):
  if p.is_file():q=e/label/p.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
for name in ['prepare.py','compile.txt','compile.exit','native.txt','native.exit','audit-result.json','all84-current-verdicts.json','canonical-digests82.json']:
 p=a/name
 if p.stat().st_size<=60000:shutil.copyfile(p,e/name)
for name in ['all-jobs.json','all-runs-closed.json']:
 p=ci/name;(e/(name+'.xz')).write_bytes(lzma.compress(p.read_bytes()))
for label in ['arithmetic','complete','beta','checkpoint','norm-halving']:
 for suffix in ['artifact-members.json','artifact-metadata.json']:
  p=ci/(label+'-'+suffix)
  if p.stat().st_size<=60000:shutil.copyfile(p,e/p.name)
roots=[]
for root in [ci,a]:
 files=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(root.rglob('*'))if p.is_file()];roots.append({'root':str(root),'all_files_no_filter':files})
(e/'whole-capture-index.json').write_text(json.dumps({'roots':roots,'all22_whole_job_logs_retained':True,'five_whole_ZIPs_and_every_member':True,'all_actual_Rust_audit_and_CI_norm_binaries_retained':True,'whole_publication':'pending NEWguard17; no files omitted','scope':'unsigned evidence; no signed execution standing'},indent=2)+'\n');shutil.copyfile(__file__,e/'record-command.py')
(e/'actual-audit-binary.json').write_text(json.dumps({'path':str(a/'actual-audit-executable.bin'),'bytes':(a/'actual-audit-executable.bin').stat().st_size,'sha256':hashlib.sha256((a/'actual-audit-executable.bin').read_bytes()).hexdigest(),'compiled_and_invoked_path':'/workspace/scratch/ct57-n4-unit-01-build-cache/release/n4-ci-evidence-audit','compile_exit':0,'native_exit':0},indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Published5ac59843 ownsourceCI ALL21distinctworkflows/22automaticruns SUCCESS/twoPCCsignjobs skipped. StrictadditiveRustaudit0: ALL423whole nativecomparisonrecords exact usingONLYalreadyfrozenoldwallmasks; newFOURnormrecordsNOmasks; whole7113census andallmetadataNOmasks;82originalcanonicaldigests84actualpassverdicts/exacttwooldreusedbindings. All15arithmetic+17Beta+20complete+21normphasepairs andactual101/alltee0, allsource/proofguards/sourceheads, bothneworiginal10gates/ninebindings, threeactualnormCIbinarydigests/Cargo compile-runtimepaths/certificates/negativecontrols exact. Originalcheckpointgate/readbacks0/exact4source+3remotehashes/resumemeta match. ALL22wholelogs/FIVEwholeZIPs/every1611+73+64+28+70filemembers/actualauditbinary retained pendingNEWguard17. Originalpriornegativecaptures remain; no newmask/waiver/signedexecution/performance promotion.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct74-norm-halving-CI-acceptance.claim').write_text(cl+'\n');print(cl)
