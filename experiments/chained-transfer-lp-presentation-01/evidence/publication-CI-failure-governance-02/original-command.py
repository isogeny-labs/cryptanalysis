"""Govern complete metadata custody before starting LP foundation code."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');base='71ce8c85fd47b3144ce8e839a16bcfd51cc1426c'
g=r/'experiments/chained-transfer-lp-presentation-01/evidence/publication-CI-failure-governance-02';g.mkdir()
shutil.copyfile(__file__,g/'original-command.py')
scope=['experiments/chained-transfer-lp-presentation-01','experiments/chained-transfer-relation-diagnostics-02/evidence','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-15.md','.resume/RESUME.md','.gitattributes']
def paths():return sorted(set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))-{b''})
def run(n,c):
 q=subprocess.run(c,cwd=r,capture_output=True);b=q.stdout+q.stderr
 (g/(n+('.txt.xz'if len(b)>60000 else'.txt'))).write_bytes(lzma.compress(b)if len(b)>60000 else b);(g/(n+'.exit')).write_text(str(q.returncode)+'\n');print(n,q.returncode,flush=True);assert q.returncode==0
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whole1605-original-guards',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'])
run('whitespace',['git','diff','--check','--',*scope]);run('bench-records',['python3','tools/benchrec.py','gate'])
def stage():
 names=paths();f=Path('/workspace/scratch/ct133-publication-CI-failure.paths0');f.write_bytes(b'\0'.join(p for p in names if p!=b'.resume/RESUME.md')+b'\0')
 subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md','.gitattributes'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(names)
 for n in selected:
  if n.startswith(b'pcc/claims/'):
   for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256'];assert s['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,capture_output=True).returncode==0
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree]);stage()
subprocess.run(['git','commit','--quiet','-m','research: checkpoint published LP protocol and complete CI02 source failure'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();print('commit',head,flush=True)
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115','/workspace/scratch/ct133-publication-CI-failure-normal-publication-02'],cwd=r,capture_output=True);Path('/workspace/scratch/ct133-publication-CI-failure-publication-caller02.txt').write_bytes(q.stdout+q.stderr);print('normalpub',q.returncode,flush=True)
