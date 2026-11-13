"""Versioned reading copies; preserves all frozen subjects and the failed gate."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess

r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
d=s/'evidence/kernel-prose-correction-01';d.mkdir()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=[
 ('GLUING_CHAIN_PROPOSAL_01.md','GLUING_CHAIN_PROPOSAL_02.md','Distinct coefficient arrays are insufficient to prove a nonisomorphic',96),
 ('KERNEL_OBSTRUCTION_DERIVATION_01.md','KERNEL_OBSTRUCTION_DERIVATION_02.md','The written V4 correspondence calculation in V2_MAPS_01.md proves',73),
 ('reports/kernel-census-01/REPORT.md','reports/kernel-census-01/REPORT-02.md','Sources: KERNEL_CENSUS_PROTOCOL_01.md,',33)]
rows=[]
for old,new,needle,line in spec:
 p=s/old;q=s/new;assert not q.exists();raw=p.read_text();ls=raw.splitlines(keepends=True)
 assert ls[line-1].startswith(needle),(old,line)
 ls[line-1]=ls[line-1].rstrip('\n')+' [pcc:unverified]\n'
 q.write_text(''.join(ls));rows.append(dict(frozen=old,frozen_sha256=digest(p),reading_copy=new,reading_sha256=digest(q),only_change='append [pcc:unverified] on original line '+str(line)))
old=s/'evidence/kernel-source-governance-01'
assert (old/'prose.exit').read_text().strip()=='1'
assert (old/'prose.txt').read_text().count("with no [pcc:ID]")==3
wf=r/'.github/workflows/pcc-gate.yml';w=wf.read_text()
assert 'name: Advisory prose lint of changed reports\n        if: github.event_name == \'pull_request\'\n        continue-on-error: true' in w
ob=dict(at=datetime.now(timezone.utc).isoformat(),failed_source_governance='kernel-source-governance-01',original_prose_exit=1,original_findings=3,frozen_subjects_preserved=rows,original_PCC_workflow_sha256=digest(wf),original_workflow_report_lint='advisory continue-on-error:true; lines77-83',required_PR_body_and_ledger='unchanged; must pass independently',scope='tag placement only; no scientific statement or acceptance criterion changed; frozen original documents and CI554 manifest remain byte exact; active reading copies lint separately; all-document lint retains three historical findings')
(d/'correction.json').write_text(json.dumps(ob,indent=2)+'\n')
(d/'original-command.py').write_bytes(Path(__file__).read_bytes())
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Kernel source governance01 stopped at original prose lint exit1 with exactlythree findings in frozen f1d44f/c2270b/9ba899 reading documents. Preserve every original byte and gate output. Add *_02/REPORT-02 reading copies with only same-line unsigned tags; no scientific or acceptance change. Original PCC report lint is explicitly advisory continue-on-error; required PR-body lint/ledger/CI unchanged. Full-document lint retains historical3 findings and active-document lint is a separately named scope, never claimed all-prose0.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
for p in sorted(old.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();print(cl,flush=True)
text='\n\n## '+datetime.now(timezone.utc).isoformat()+' — frozen prose lint and current reading copies\n\nSource governance01 stopped with exactly3 original prose findings; '+cl+' preserves the entire failed gate capture. Frozen proposal01/derivation01/report remain byte exact because they are evidence subjects and CI554 inputs. Current reading copies GLUING_CHAIN_PROPOSAL_02.md, KERNEL_OBSTRUCTION_DERIVATION_02.md and reports/kernel-census-01/REPORT-02.md append only same-line unsigned tags. Full-document lint retains3 historical findings; active-document lint is separately reported. The unchanged original PCC workflow makes report lint advisory; required PR-body/ledger checks remain required. No claim, science, criterion or original test is weakened. Next source checkpoint and clean555-input kernel full replay; HLP Prop15 matches the adjugate proposal with determinant equal to the classical twisting factor, requiring native checks before constructing maps. [pcc:unverified]\n'
for p in [s/'CHECKPOINT.md',s/'STATUS-01.md',r/'.resume/RESUME.md',r/'docs/session-logs/2026-11-13.md']:
 with p.open('a') as f:f.write(text)
