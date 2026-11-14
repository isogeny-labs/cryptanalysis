from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='21afb40f425f89774fe3eaf77695f5f30342a186';d=s/'evidence/arithmetic-audit-protocol-stage-recovery-01';d.mkdir()
(d/'observed-caller-failure.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),caller='/workspace/scratch/ct72_publish_arithmetic_protocol.py',failure='AssertionError: (120, 9)',cause='second staging collection used only unstaged modified/untracked paths and omitted the existing index',all_original_governance_checks_exit=0,scientific_run_started=False,commit_created=False,remedy='union the unchanged existing index and new owned paths; check actual staged subjects then commit'),indent=2)+'\n')
(d/'recovery-command.py').write_bytes(Path(__file__).read_bytes())
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Arithmetic protocol commit caller failed after all actual governance checks0: secondpathset9 omitted111already-staged files, yielding assertion(120,9). No commit/scientificrun. Preserve originalcaller andobservedtool-return diagnosis; recovery unions existingownedindex plusnewpaths andchecks allsubjects withoutchanging scientificsource/verifier.']
for f in sorted(d.iterdir()):c+=['--proof','attestation:'+str(f.relative_to(r))]
print(subprocess.check_output(c,cwd=r,text=True).strip(),flush=True)
scopes=[str(s.relative_to(r)),'docs/chained-transfer-checkpoint-transport/acceptance-03','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','problems/chained-transfer-new-jacobian-ic-cost-coverage.md','.resume/RESUME.md']
paths=set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'));paths.discard(b'')
f=Path('/workspace/scratch/ct72-arithmetic-protocol-recovery.paths0');f.write_bytes(b'\0'.join(sorted(x for x in paths if x!=b'.resume/RESUME.md'))+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==paths
for p in selected:
 if p.startswith(b'pcc/claims/'):
  for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];assert x['path'].encode() in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0
for cmd in [['git','diff','--cached','--check'],['python3','tools/pcc/pcc.py','ledger','verify','--base',base],['python3','tools/pcc/pcc.py','lint-prose',*[x.decode() for x in selected if x.endswith(b'.md')]],['python3','tools/artifacts/artifacts.py','check',base,subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip()]]:
 p=subprocess.run(cmd,cwd=r,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
subprocess.run(['git','commit','--quiet','-m','research: settle exact sampling replay and freeze arithmetic audit'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print(head,len(selected),flush=True)
p=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-public-target-20261113','/workspace/scratch/ct72-arithmetic-protocol-publication-01'],cwd=r,capture_output=True);Path('/workspace/scratch/ct72-arithmetic-protocol-publication-caller.txt').write_bytes(p.stdout+p.stderr);print('normalpub',p.returncode,flush=True);assert p.returncode==0
