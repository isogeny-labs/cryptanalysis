"""Canonical whole-byte documentation object and a transparent report symlink."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';original=s/'reports/new-target-IC-01/report.pdf';canonical=r/'docs/research-artifacts/chained-transfer/new-target-IC-01/report.pdf';assert not original.is_symlink()
body=original.read_bytes();assert len(body)==69377
claim=json.loads((r/'pcc/claims/PCC-20261113-d1027f.json').read_text());pin=next(x['subject']for x in claim['proofs']if x['subject']['path']==str(original.relative_to(r)));assert hashlib.sha256(body).hexdigest()==pin['sha256']
canonical.parent.mkdir(parents=True);canonical.write_bytes(body);relative=os.path.relpath(canonical,original.parent);assert (original.parent/relative).resolve()==canonical
original.unlink();original.symlink_to(relative);assert original.read_bytes()==body and canonical.read_bytes()==body
d=s/'evidence/new-target-report-layout-01';d.mkdir();(d/'observation.json').write_text(json.dumps(dict(report_subject=pin,canonical=str(canonical.relative_to(r)),canonical_bytes=len(body),canonical_sha256=hashlib.sha256(body).hexdigest(),relative_Git_symlink=relative,all_original_PDF_bytes_preserved=True,all729_original_CI_inputs='unchanged;checked separately',genuine_manifest='pending actualunchangedpublisher;no syntheticmanifest',PCC_hydration='existingoriginalworkflow pull docs covers canonicalpath;researchsubjectresolvesinside repo'),indent=2)+'\n')
p=subprocess.run(['python3','tools/pcc/pcc.py','verify','pcc/claims/PCC-20261113-d1027f.json','--json'],cwd=r,capture_output=True);(d/'original-PCC-report-pin.json').write_bytes(p.stdout+p.stderr);(d/'original-PCC-report-pin.exit').write_text(str(p.returncode)+'\n');v=json.loads(p.stdout);assert p.returncode==2 and v['verdict']=='not_covered'and not v['reasons']
shutil.copyfile(__file__,d/'original-command.py');(canonical.parent/'README.md').write_text('''# Canonical whole IC report object

The whole69377-byte PDF is the unchanged d1027f report. The research report
path is a relative symlink here so the ORIGINAL PCC workflow's existing
docs hydration reads genuine managed bytes. Publication/manifests remain
pending actual unchanged remote byte replay;no availability claim yet.
Source,editable figures and report generation remain under
experiments/chained-transfer-public-target/reports/new-target-IC-01.
No policy,gate,verifier,workflow,claim pin or mathematical change.
[pcc:unverified]
''')
print(json.dumps(dict(bytes=len(body),sha256=pin['sha256'],symlink=relative,original_PCC_exit=2,standing='unsigned/not_covered',genuine='pending')))
