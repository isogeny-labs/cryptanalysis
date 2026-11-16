"""Development-only frozen inventory;replay never regenerates it."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in[line.split('  ',1)for line in(s/'ci_odd_refinement/reference-01.sha256').read_text().splitlines()]};assert len(entries)==702
selected=set(p for p in(s/'new-target-ic').rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in ['NEW_TARGET_IC_PROTOCOL_01.md','NEW_TARGET_IC_DERIVATION_01.md','NEW_TARGET_IC_PROOF_MAP_01.md','ci_odd_refinement/reference-01.sha256']:selected.add(s/name)
binding=s/'evidence/new-target-IC-bindings-01/claims.json';selected.add(binding);selected.update(r/x['claim_path']for x in json.loads(binding.read_text()))
for name in ['.github/workflows/chained-transfer-new-target-ic.yml','.github/workflows/chained-transfer-original-root-fixture.yml']:selected.add(r/name)
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),manifest_self_excluded=True,phases=9,native_JSON=82,bindings=2)))
