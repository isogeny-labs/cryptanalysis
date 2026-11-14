"""Whole capture inventory, original execution evidence records, data only."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=Path('/workspace/scratch/ct73-complete-own-CI-01');one=Path('/workspace/scratch/ct73-b691-CI-audit-01');two=Path('/workspace/scratch/ct73-b691-CI-audit-02');e=s/'evidence/beta-complete-own-b691-CI-01';e.mkdir()
assert(one/'native.exit').read_text()=='101\n'and(two/'native.exit').read_text()=='0\n'
result=json.loads((two/'audit-result.json').read_text());assert result['whole_native_records']==419 and result['actual_pass_verdicts']==75 and result['successful_runs']==19 and result['failed_PCC_runs']==1
for root,label in [(one,'audit-attempt01-rejected'),(two,'audit-attempt02-corrected')]:
 for path in sorted((root/'audit-cli').rglob('*')):
  if path.is_file():dest=e/label/'audit-cli'/path.relative_to(root/'audit-cli');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
 for name in ['compile.txt','native.txt','native.exit']:
  dest=e/label/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dest)
 if(root/'correction.json').exists():shutil.copyfile(root/'correction.json',e/label/'correction.json')
for name in ['audit-result.json','all75-current-verdicts.json','canonical-digests73.json']:shutil.copyfile(two/name,e/name)
for name in ['all-jobs.json','all-runs-closed.json','complete-artifact-members.json','checkpoint-artifact-members.json','arithmetic-artifact-members.json','beta-artifact-members.json','arithmetic-artifact-metadata.json','beta-artifact-metadata.json']:shutil.copyfile(ci/name,e/name)
indices=[]
for root in [ci,one,two]:
 members=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(root.rglob('*'))if p.is_file()]
 indices.append(dict(root=str(root),members=members,all_files_no_filter=True))
(e/'whole-capture-index.json').write_text(json.dumps(dict(roots=indices,whole_CI_root_genuine_in_guard13_checkpoint=True,root_actual_publication_claim='PCC-20261114-d1f056',genuine_checkpoint=dict(bytes=7880556,sha256='3b693aeeef31a728e49cdea22170be0d9095448acc9c9ef375a6adf2479ca0bd',members=2101),new_audit_roots_publication_pending='NEWguard14',first_audit_failed_manifest_schema_assumption_preserved=True),indent=2)+'\n')
shutil.copyfile(__file__,e/'record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Published b691 own20 CI audit: ALL419whole native records exact under ONLYalreadyfrozenoldwallmasks; whole7113census+allmetadata exactNOmasks;73originalcanonicaldigests/75actualpassverdicts exactsource; arithmetic15/Beta17/complete20phasepairs andallsource/proofguards match; complete3unfiltered/threeactual101controls/original44+1gates/sevenbindings. Overall CI remains19success+EXACTonePCCmissingPNGfailure/signskip1, never all20green. Originalcheckpoint gate/readbacks0/exact4originalsourcehashes+3remoteobjecthashes andRESUME/meta comparisons. Firstaudit101 wronglycompared different4vs3manifest schemas; wholecommand/executable/output retained, correctedRustaudit0 checks eachhash usingunchanged originalRustSHA256/allmathcomparisonsunchanged. Whole20logs/fourZIPs/everymember genuinelypublished guard13; bothauditattempts+actualbinaries pendingNEWguard14. Unsigned data, no execution standing orperformance.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct73-b691-CI-audit-acceptance.claim').write_text(claim+'\n');print(claim)
