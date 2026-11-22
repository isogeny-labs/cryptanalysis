"""Freeze the complete tracked original proof-tool/input closure; file operations only."""
from pathlib import Path
import json,hashlib,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=s/'ci_induced_transfer'
b=json.loads((s/'evidence/original-induced-full-transfer-proof-01/bindings.json').read_text());assert len(b)==9
(ci/'statement-bindings-01.txt').write_text(''.join(Path(row['claim']).stem+'\n'for row in b))
paths=[p.relative_to(r).as_posix()for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256']
paths+=['.github/workflows/chained-transfer-induced-proof.yml','pcc/keyring.json']+[row['claim']for row in b]
paths+=[p.relative_to(r).as_posix()for p in(s/'original-induced-transfer-01').rglob('*')if p.is_file()]
paths+=['experiments/chained-transfer-public-target/upstream-commit.txt','experiments/chained-transfer-public-target/evidence/original-induced-full-transfer-proof-01/exact-root-and-structural-coverage.json','experiments/chained-transfer-public-target/evidence/original-induced-full-transfer-proof-01/bindings.json']
consumer=subprocess.check_output(['git','ls-files','--','tools/lean','tools/pcc'],cwd=r,text=True).splitlines();assert len(consumer)==25
paths+=consumer
producer=Path('/workspace/crypto');pin=(s/'upstream-commit.txt').read_text().strip()
original=subprocess.check_output(['git','ls-tree','-r','--name-only',pin,'--','tools/lean'],cwd=producer,text=True).splitlines();assert len(original)==27
for name in original:
 f=producer/name;assert f.is_file()and f.read_bytes()==subprocess.check_output(['git','show',pin+':'+name],cwd=producer),name
 paths.append('../crypto/'+name)
paths=sorted(set(paths))
(ci/'reference-01.sha256').write_text(''.join(hashlib.file_digest((r/name).open('rb'),'sha256').hexdigest()+'  '+name+'\n'for name in paths))
print('new narrow proof replay exact references',len(paths),flush=True)
