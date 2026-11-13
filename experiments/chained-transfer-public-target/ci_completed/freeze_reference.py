"""Development-only inventory/hash generation; never replaces hashes in replay."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in [line.split('  ',1)for line in(s/'ci_v2/reference-01.sha256').read_text().splitlines()]};assert len(entries)==468
selected={p for p in(s/'completed-descent').rglob('*')if p.is_file()}
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
selected.add(s/'ci_v2/reference-01.sha256');selected.add(r/'.github/workflows/chained-transfer-completed-descent.yml')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),new_consumer_inputs=len(selected),manifest_self_excluded=True)))
