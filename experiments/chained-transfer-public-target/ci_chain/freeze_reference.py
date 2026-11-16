"""Development-only frozen inventory; replay never regenerates its hashes."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in[line.split('  ',1)for line in(s/'ci_gluing/reference-01.sha256').read_text().splitlines()]}
assert len(entries)==596
selected=set(p for p in(s/'chain-kernels').rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in ['CHAIN_KERNEL_PROTOCOL_01.md','CHAIN_KERNEL_DERIVATION_01.md','CHAIN_KERNEL_PROOF_MAP_01.md','ci_gluing/reference-01.sha256']:selected.add(s/name)
binding=s/'evidence/chain-kernel-bindings-01/claims.json';selected.add(binding)
selected.update(r/b['claim_path']for b in json.loads(binding.read_text()))
selected.add(r/'.github/workflows/chained-transfer-chain-kernels.yml')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),manifest_self_excluded=True)))
