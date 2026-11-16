"""Development-only frozen inventory; replay never regenerates its hashes."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in[line.split('  ',1)for line in(s/'ci_kernels/reference-01.sha256').read_text().splitlines()]}
assert len(entries)==554
selected=set()
for folder in ['gluing-models','gluing-maps']:selected.update(p for p in(s/folder).rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in ['GLUING_MODELS_PROTOCOL_01.md','GLUING_MAPS_PROTOCOL_01.md','GLUING_CHAIN_DERIVATION_01.md','GLUING_PROOF_MAP_01.md','ci_kernels/reference-01.sha256']:selected.add(s/name)
for name in ['gluing-models-bindings-01','gluing-chain-bindings-01']:
    binding=s/'evidence'/name/'claims.json';selected.add(binding);selected.update(r/b['claim_path']for b in json.loads(binding.read_text()))
selected.add(r/'.github/workflows/chained-transfer-gluing.yml')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),manifest_self_excluded=True)))
