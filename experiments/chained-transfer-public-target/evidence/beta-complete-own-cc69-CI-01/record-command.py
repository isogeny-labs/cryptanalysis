"""Whole-file custody for strict corrected own-head CI, no research computations."""
from pathlib import Path
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=Path('/workspace/scratch/ct73-cc69-own-CI-01');audit=Path('/workspace/scratch/ct73-cc69-CI-audit-01');e=s/'evidence/beta-complete-own-cc69-CI-01';e.mkdir()
assert(audit/'native.exit').read_text()=='0\n';result=json.loads((audit/'audit-result.json').read_text());assert result['whole_native_records']==419 and result['successful_runs']==21 and result['failed_PCC_runs']==0
for p in sorted((audit/'audit-cli').rglob('*')):
 if p.is_file():dest=e/'audit-cli'/p.relative_to(audit/'audit-cli');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for name in ['prepare.py','compile.txt','native.txt','native.exit','audit-result.json','all75-current-verdicts.json','canonical-digests73.json']:shutil.copyfile(audit/name,e/name)
for name in ['all-jobs.json','all-runs-closed.json']:
 shutil.copyfile(ci/name,e/name)
for label in ['arithmetic','complete','beta','checkpoint']:
 for suffix in ['artifact-members.json','artifact-metadata.json']:shutil.copyfile(ci/(label+'-'+suffix),e/(label+'-'+suffix))
indices=[]
for root in [ci,audit]:
 members=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(root.rglob('*'))if p.is_file()]
 indices.append(dict(root=str(root),members=members,all_files_no_filter=True))
(e/'whole-capture-index.json').write_text(json.dumps(dict(roots=indices,all21_whole_job_logs_retained=True,four_whole_ZIPs_every_member=True,whole_archive_publication_pending='NEWguard14; include oldnegative andallpreviousbulkcaptures',no_signed_execution_standing=True),indent=2)+'\n')
shutil.copyfile(__file__,e/'record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Corrected cc69f16 own-source CI: ALL20distinct workflows/21automaticruns SUCCESS including original synchronize andedited-bodyPCCgates; signjobs2skipped. StrictRustaudit0 ALL419whole native rows exactunderONLYfrozenoldwallmasks/whole7113census+allmetadataNOmasks/73originalcanonicaldigests75actualpassverdicts/15arithmetic+17Beta+20completephasepairs/alloriginalsourceproofguards/checkpointgateandreadbacks0+exactsource4/remote3hashes/RESUMEmeta. BothPCCgates retain f4a048/423f66/8397ab asnotcoveredwithoutfailure; alloriginal881scienceinputs/workflows unchanged by routing. ALL21wholelogs/fourwholeZIPs/everymember/actualRustbinary retained pendingNEWguard14. B691negative6a5f3c remainsseparate, no waived failure, newmasks orsignedexecution/performance inference. Unsigned data.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct73-cc69-CI-acceptance.claim').write_text(claim+'\n');print(claim)
