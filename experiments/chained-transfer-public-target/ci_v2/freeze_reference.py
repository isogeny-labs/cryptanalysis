"""Development-only source inventory; never replaces expected hashes at replay."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in [line.split('  ',1) for line in (s/'reference-02.sha256').read_text().splitlines()]}
assert len(entries)==434
selected=set()
for folder in ['v2','rho-accessor','prime-field']:
    selected.update(p for p in (s/folder).rglob('*') if p.is_file())
selected.update(p for p in ci.iterdir() if p.is_file() and p.name!='reference-01.sha256')
selected.add(s/'reference-02.sha256')
selected.add(s/'COMPLETED_DESCENT_PROTOCOL_02.md')
selected.add(s/'V2_MAPS_01.md')
binding=s/'evidence/prime-field-bindings-02/claims.json';selected.add(binding)
selected.update(r/row['claim_path'] for row in json.loads(binding.read_text()))
selected.add(r/'.github/workflows/chained-transfer-completed-v2.yml')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/') for p in entries),new_consumer_inputs=len(selected),manifest_self_excluded=True)))
