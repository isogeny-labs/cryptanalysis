"""Validate existing data-path correction and preserve its initial CLI error."""
from pathlib import Path
import hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
e=s/'evidence/beta-complete-PCC-hydration-failure-01';o=Path('/workspace/scratch/ct73-complete-PNG-routing-01')
report=s/'reports/beta-complete-rational-01';png=report/'complete-diagram.png'
canonical=r/'docs/research-artifacts/chained-transfer/beta-complete-rational-01'
failed=e/'initial-local-command-error';failed.mkdir()
shutil.copyfile('/workspace/scratch/ct73_route_complete_png.py',failed/'original-command.py')
for n in ['artifact.txt.xz','artifact.exit']:shutil.copyfile(e/n,failed/n)
(failed/'caller.exit').write_text('1\n')
(failed/'scope.json').write_text(json.dumps(dict(observation='original artifact verify rejected unsupported --local option; subprocess2, caller assertion1; before math/source checking; routing edits already in place',correction='documented default verify is local; execute a fresh validation without rerunning mutations',no_mathematical_negative_inferred=True),indent=2)+'\n')
source=Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-beta-png-handoff-01/.artifacts.json')
entry=json.loads(source.read_text())['files'][png.name];manifest=json.loads((canonical/'.artifacts.json').read_text())
assert manifest['files']=={png.name:entry}
assert png.is_symlink() and os.readlink(png)=='../../../../docs/research-artifacts/chained-transfer/beta-complete-rational-01/complete-diagram.png'
body=png.read_bytes();assert body==(o/'original-physical-complete-diagram.png').read_bytes() and len(body)==entry['bytes'] and hashlib.sha256(body).hexdigest()==entry['sha256']
before={}
for claim in (r/'pcc/claims').glob('*.json'):
 for proof in json.loads(claim.read_text()).get('proofs',[]):
  if proof.get('kind')=='attestation' and proof['subject']['path'].startswith(str(report.relative_to(r))+'/'):
   sub=proof['subject'];assert hashlib.sha256((r/sub['path']).read_bytes()).hexdigest()==sub['sha256'];before[sub['path']]=sub['sha256']
workflows={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (r/'.github/workflows').glob('*.yml')}
assert not subprocess.check_output(['git','diff','--name-only','b691714c8c6f7b157f9ec832ccc91413c624c541','--','.github/workflows','tools','scripts'],cwd=r)
exits={}
for name,cmd,want in [('artifact',['python3','tools/artifacts/artifacts.py','verify',str(canonical.relative_to(r))],0),('f4a048',['python3','tools/pcc/pcc.py','verify','pcc/claims/PCC-20261114-f4a048.json','--json'],2),('source881',['sha256sum','--check',str((s/'ci_beta_complete/reference-01.sha256').relative_to(r))],0)]:
 q=subprocess.run(cmd,cwd=r,capture_output=True);raw=q.stdout+q.stderr;(e/(name+'.txt.xz')).write_bytes(lzma.compress(raw));(e/(name+'.exit')).write_text(str(q.returncode)+'\n');exits[name]=q.returncode;assert q.returncode==want,raw[:2000]
verdict=json.loads(lzma.decompress((e/'f4a048.txt.xz').read_bytes()));assert verdict['verdict']=='not_covered',verdict
facts=dict(source='b691714c8c6f7b157f9ec832ccc91413c624c541',failed_PCC_run=43585724193,failed_PCC_job=132419661458,original_genuine_publisher_bot='e149ba385fd3539a58fada68f279e9f1b30f898e',canonical=canonical.relative_to(r).as_posix(),manifest_entry=entry,symlink=png.relative_to(r).as_posix(),symlink_target=os.readlink(png),all_preexisting_report_attestation_subjects=before,all_workflow_hashes=workflows,all_workflows_unchanged=True,checks=exits,automatic_corrected_own_head_CI='required; not inferred from local checks',scope='unsigned storage routing and local controls; no new mathematical or execution standing')
(e/'routing.json').write_text(json.dumps(facts,indent=2)+'\n')
shutil.copyfile(__file__,e/'validation-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Whole own-b691 PCC missing-PNG failure retained; unchanged151899B genuinePNG routed through existing docs artifact pull and transparent relative link. All preexisting report attestation subjects and all workflow bytes unchanged; original artifact verify0, f4a048 verify2 not_covered, 881sourceguards0. First local CLI option error2/caller1 retained without mathematical inference. Corrected own-head automaticCI remains required. Unsigned data only.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();(o/'claim.txt').write_text(claim+'\n');print(claim)
