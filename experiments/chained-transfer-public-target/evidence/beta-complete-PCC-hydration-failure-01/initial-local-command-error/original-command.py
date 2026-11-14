"""Data-path correction only; no research computation or verifier changes."""
from pathlib import Path
import hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
report=s/'reports/beta-complete-rational-01';png=report/'complete-diagram.png'
e=s/'evidence/beta-complete-PCC-hydration-failure-01'
o=Path('/workspace/scratch/ct73-complete-PNG-routing-01');o.mkdir()
canonical=r/'docs/research-artifacts/chained-transfer/beta-complete-rational-01';canonical.mkdir(parents=True)
source=Path('/workspace/crypto/research/chained_jacobian_transfers_20261110/evidence/public-n4-complete-beta-png-handoff-01/.artifacts.json')
manifest=json.loads(source.read_text());entry=manifest['files'][png.name]
assert not png.is_symlink()
body=png.read_bytes();assert len(body)==entry['bytes'] and hashlib.sha256(body).hexdigest()==entry['sha256']
before={}
for claim in (r/'pcc/claims').glob('*.json'):
 for proof in json.loads(claim.read_text()).get('proofs',[]):
  if proof.get('kind')=='attestation' and proof['subject']['path'].startswith(str(report.relative_to(r))+'/'):
   sub=proof['subject'];p=r/sub['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==sub['sha256'];before[sub['path']]=sub['sha256']
workflows={str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest()for p in (r/'.github/workflows').glob('*.yml')}
for name in ['.artifacts.json','.gitignore']:
 shutil.copyfile(report/name,e/('prior-report'+name))
shutil.copyfile(png,o/'original-physical-complete-diagram.png')
(canonical/png.name).write_bytes(body)
(canonical/'.artifacts.json').write_text(json.dumps(dict(schema=manifest['schema'],files={png.name:entry}),indent=2)+'\n')
(canonical/'.gitignore').write_text(png.name+'\n')
target=os.path.relpath(canonical/png.name,report)
assert target=='../../../../docs/research-artifacts/chained-transfer/beta-complete-rational-01/complete-diagram.png'
png.unlink();png.symlink_to(target)
for name in ['.artifacts.json','.gitignore']:(report/name).unlink()
assert png.is_symlink() and png.read_bytes()==body
assert before and all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in before.items())
assert workflows=={p:hashlib.sha256((r/p).read_bytes()).hexdigest()for p in workflows}
checks=[('artifact',['python3','tools/artifacts/artifacts.py','verify','--local',str(canonical.relative_to(r))],0),('f4a048',['python3','tools/pcc/pcc.py','verify','PCC-20261114-f4a048'],2),('source881',['sha256sum','--check',str((s/'ci_beta_complete/reference-01.sha256').relative_to(r))],0)]
exits={}
for name,cmd,want in checks:
 q=subprocess.run(cmd,cwd=r,capture_output=True);raw=q.stdout+q.stderr
 (e/(name+'.txt.xz')).write_bytes(lzma.compress(raw));(e/(name+'.exit')).write_text(str(q.returncode)+'\n');exits[name]=q.returncode
 assert q.returncode==want,raw[:2000]
facts=dict(source='b691714c8c6f7b157f9ec832ccc91413c624c541',failed_PCC_run=43585724193,failed_PCC_job=132419661458,original_genuine_publisher_bot='e149ba385fd3539a58fada68f279e9f1b30f898e',canonical=canonical.relative_to(r).as_posix(),manifest_entry=entry,symlink=png.relative_to(r).as_posix(),symlink_target=target,all_preexisting_report_attestation_subjects=before,all_workflow_hashes=workflows,all_workflows_unchanged=True,checks=exits,automatic_corrected_own_head_CI='required; not inferred from local checks',scope='unsigned storage routing and local controls; no new mathematical or execution standing')
(e/'routing.json').write_text(json.dumps(facts,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Preserved the whole own-b691 PCC missing-PNG failure; routed unchanged151899B genuinePNG through existing docs artifact pull and transparent relative link. All preexisting report attestation subject bytes and all workflow bytes unchanged; original artifact verify0, f4a048 verify2 not_covered, 881sourceguards0. Corrected own-head automaticCI remains required. Unsigned data only.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();(o/'claim.txt').write_text(claim+'\n');print(claim)
