"""Run ORIGINAL PCC on copied fixtures;never mutate the real report subjects."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'evidence/new-target-report-layout-01';v=json.loads((d/'original-PCC-report-pin.json').read_text())
assert(d/'original-PCC-report-pin.exit').read_text().strip()=='2'and v['verdict']=='not_covered'
assert v['reasons']==['a statement claim has no proof kind and can never be verified']
assert all(p['verdict']=='not_covered'and not p['reasons']for p in v['proofs'])
(d/'initial-collector-assertion.json').write_text(json.dumps(dict(scope='collector bookkeeping only',actual_original_PCC_exit=2,actual_verdict='not_covered',actual_per_proof_failures=0,initial_bad_expectation='empty top-level reasons;original statement-kind reason is mandatory',correction='require exact original statement-kind reason and zero failed proofs;no verifier/gate/claim/source/report changes'),indent=2)+'\n')
shutil.copyfile('/workspace/scratch/ct69_prepare_report_layout.py',d/'original-layout-command.py')
fixture=Path('/workspace/scratch/ct69-original-PCC-report-fixture-01');fixture.mkdir()
subprocess.run(['git','init','--quiet',str(fixture)],check=True);subprocess.run(['git','-C',str(fixture),'-c','user.name=Local PCC fixture','-c','user.email=local-fixture@example.invalid','commit','--allow-empty','--quiet','-m','Original verifier file-pin fixture only'],check=True)
claim=r/'pcc/claims/PCC-20261113-d1027f.json';record=json.loads(claim.read_text())
for item in record['proofs']:
 p=r/item['subject']['path'];dest=fixture/item['subject']['path'];dest.parent.mkdir(parents=True,exist_ok=True)
 if p.is_symlink():dest.symlink_to(os.readlink(p))
 else:shutil.copyfile(p,dest)
canonical=r/'docs/research-artifacts/chained-transfer/new-target-IC-01/report.pdf';fc=fixture/canonical.relative_to(r);fc.parent.mkdir(parents=True,exist_ok=True);body=canonical.read_bytes();fc.write_bytes(body)
cp=fixture/'pcc/claims'/claim.name;cp.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(claim,cp);shutil.copyfile(r/'pcc/keyring.json',fixture/'pcc/keyring.json')
results=[]
def run(name,expected):
 p=subprocess.run(['python3',str(r/'tools/pcc/pcc.py'),'--repo',str(fixture),'verify','pcc/claims/'+claim.name,'--json'],cwd=fixture,capture_output=True);(d/(name+'.json')).write_bytes(p.stdout+p.stderr);(d/(name+'.exit')).write_text(str(p.returncode)+'\n');j=json.loads(p.stdout);assert p.returncode==expected
 if expected==2:assert j['verdict']=='not_covered'and all(x['verdict']=='not_covered'and not x['reasons']for x in j['proofs'])
 else:assert j['verdict']=='fail'and any(x['verdict']=='fail'for x in j['proofs'])
 results.append(dict(control=name,original_exit=expected,verdict=j['verdict']))
run('copied-exact-symlink-and-bytes',2)
fc.unlink();run('missing-canonical-PDF',1)
fc.write_bytes(body[:-1]+bytes([body[-1]^1]));run('substituted-canonical-PDF',1)
fc.write_bytes(body);run('restored-exact-copy',2)
assert canonical.read_bytes()==body and(s/'reports/new-target-IC-01/report.pdf').read_bytes()==body
(d/'negative-controls.json').write_text(json.dumps(dict(original_verifier='unchanged tools/pcc/pcc.py',copied_isolated_repo=str(fixture),controls=results,real_report_subjects_never_mutated=True,original_kind_reason='statement claims remain not_covered even with matching bytes',genuine_remote='pending actual publisher;local copy is not remote evidence'),indent=2)+'\n');shutil.copyfile(__file__,d/'original-controls-command.py')
(canonical.parent/'README.md').write_text('''# Canonical whole IC report object

The whole69377-byte PDF is the unchanged d1027f report. The research report
path is a relative symlink here so the ORIGINAL PCC workflow's existing
docs hydration reads genuine managed bytes. Publication/manifests remain
pending actual unchanged remote byte replay;no availability claim yet.
Source,editable figures and report generation remain under
experiments/chained-transfer-public-target/reports/new-target-IC-01.
No policy,gate,verifier,workflow,claim pin or mathematical change.
[pcc:unverified]
''')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','WholefinalPDF69377byte layout under prospectivee95275:canonical documentation data object and research relative symlink preserve d1027f bytes/hash inside repository;originalPCCreportpin2/notcovered/all9proofsunsigned/no failures. Firstcollector incorrectly expected emptytoplevel reasons;exactmandatory statement-kind reason now recognized,originaloutputunchanged. ORIGINALunmodifiedPCC copied-fixture controls2good/1missingPDF/1substitutedPDF/2restored;realreportbytes nevermutated. Originaldocs-hydrationworkflow/policies/verifier/keyring/PCCpins/science unchanged;genuineS3manifeststillpendingactualpublisher,no remoteavailability or verifiedstandingclaim.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),json.dumps(results),flush=True)
