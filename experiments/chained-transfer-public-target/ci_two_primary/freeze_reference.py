"""Development-only exact input inventory; never regenerates hashes at replay."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in [line.split('  ',1)for line in(s/'ci_completed/reference-01.sha256').read_text().splitlines()]}
assert len(entries)==483
selected=set(p for p in(s/'two-primary').rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
selected.add(s/'ci_completed/reference-01.sha256')
binding=s/'evidence/two-primary-bindings-01/claims.json';selected.add(binding)
selected.update(r/row['claim_path']for row in json.loads(binding.read_text()))
selected.add(r/'.github/workflows/chained-transfer-two-primary.yml')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),manifest_self_excluded=True)))
