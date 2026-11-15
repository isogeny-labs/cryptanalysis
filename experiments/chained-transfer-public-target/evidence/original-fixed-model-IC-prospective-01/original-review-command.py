"""Retain primary-source passages, KB failures and header-only vault status; no mathematics."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
w=Path('/workspace');raw=w/'scratch/ct96-original-fixed-model-IC-prospective-01';raw.mkdir();shutil.copyfile(__file__,raw/'original-review-command.py')
queries=[['status'],['search','original fixed prime-field genus3 plane quartic index calculus chained Jacobian transfer','--top-k','8'],['search','negative incomplete costs norm assisted sampler original prime models','--top-k','8'],['theorems','quotient induced integer linearity checked class IC soundness prime order']]
rows=[]
for i,args in enumerate(queries):
 cmd=['bash','/workspace/crypto/scripts/research-kb',*args];q=subprocess.run(cmd,capture_output=True)
 (raw/f'KB-{i}-command.json').write_text(json.dumps(cmd)+'\n');(raw/f'KB-{i}.txt').write_bytes(q.stdout+q.stderr);(raw/f'KB-{i}.exit').write_text(str(q.returncode)+'\n');rows.append(dict(command=cmd,actual_exit=q.returncode))
vault=w/'crypto-autoresearcher';headers={}
for name in ['AGENTS.md','tools/lead_atlas.py']:
 with(vault/name).open('rb')as f:headers[name]=f.read(4).decode('ascii')
assert all(v=='VLT1'for v in headers.values())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=vault,text=True).strip()=='8edec422a60d87b2cbc656fb02f99f42eba959c7'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=vault)
primary=w/'scratch/ct90-prime-descent-primary-review-01';passages=[]
for name,start,end in [('diem-plane-curves-2012.txt',90,121),('tian-cover-2020v1.txt',37,77)]:
 p=primary/name;lines=p.read_text().splitlines();quote='\n'.join(lines[start-1:end])+'\n'
 target=raw/(name+'.reviewed-lines.txt');target.write_text(quote)
 passages.append(dict(full_retained_primary_text=str(p),whole_sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),reviewed_lines=[start,end],literal_passage=str(target)))
receipt=dict(at=datetime.now(timezone.utc).isoformat(),KB=rows,vault_head='8edec422a60d87b2cbc656fb02f99f42eba959c7',vault_header_bytes=4,vault_headers=headers,vault_locked_clean_unchanged=True,earlier_probe_observation='A prior head-line probe read beyond the four-byte binary header; no plaintext was obtained, no decryption/execution/edit occurred. This recorded check reads exactly four bytes.',primary_passages=passages,interpretation='Diem2012 Theorem1 gives expected soft-O(q) for nonhyperelliptic genus3 class-group DLP; Tian2020 describes applicable cover/isogeny-transfer setting and qualifications. Existing literature is not a new asymptotic claim, an implementation certificate or calibrated q223 advantage.',scope='independent primary reading and access-status evidence only; no novelty or absence inference')
(raw/'primary-KB-vault-review.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(KB_actual_exits=[v['actual_exit']for v in rows],vault_locked_clean_unchanged=True,full_primary_passages_retained=len(passages))),flush=True)
