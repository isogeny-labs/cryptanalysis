"""Development-only inventory;the replay never regenerates it."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in[line.split('  ',1)for line in(s/'ci_common_origin/reference-01.sha256').read_text().splitlines()]};assert len(entries)==754
selected=set(p for p in(s/'norm-assisted-ic').rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in ['NORM_ASSISTED_SAMPLING_PROTOCOL_01.md','NORM_ASSISTED_SAMPLING_DERIVATION_01.md','NORM_ASSISTED_SAMPLING_PROOF_MAP_01.md','NORM_SAMPLING_REPLAY_STORAGE_PROTOCOL_01.md','ARITHMETIC_COVERAGE_INVENTORY_01.md','ci_common_origin/reference-01.sha256','evidence/norm-sampling-bindings-02/claims.json']:selected.add(s/name)
for c in json.loads((s/'evidence/norm-sampling-bindings-02/claims.json').read_text()):selected.add(r/c['claim_path'])
selected.add(r/'.github/workflows/chained-transfer-norm-sampling.yml')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),manifest_self_excluded=True,phases=10,native_JSON=86,new_bindings=3,total_unique_bindings=60)))
