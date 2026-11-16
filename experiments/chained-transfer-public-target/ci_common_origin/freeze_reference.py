"""Development-only inventory;replay never regenerates it."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={p:h for h,p in[line.split('  ',1)for line in(s/'ci_new_target_ic/reference-01.sha256').read_text().splitlines()]};assert len(entries)==729
selected=set(p for p in(s/'common-origin-ic').rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in ['COMMON_ORIGIN_IC_PROTOCOL_01.md','COMMON_ORIGIN_IC_DERIVATION_01.md','COMMON_ORIGIN_REPLAY_PROTOCOL_01.md','ci_new_target_ic/reference-01.sha256']:selected.add(s/name)
for name in ['.github/workflows/chained-transfer-common-origin.yml','.github/workflows/chained-transfer-checkpoint-transport.yml']:selected.add(r/name)
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(portable_inputs=len(entries),producer_inputs=sum(p.startswith('../crypto/')for p in entries),manifest_self_excluded=True,phases=9,native_JSON=51,reused_bindings=2,total_bindings=57)))
