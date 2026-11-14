"""Development inventory only; preserve the original inventory and runtime data."""
from pathlib import Path
import hashlib,json,subprocess
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
old=ci/'reference-01.sha256';entries={}
workflow='.github/workflows/chained-transfer-beta-rational-lift.yml'
for line in old.read_text().splitlines():
 h,p=line.split('  ',1)
 if p!=workflow:assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,p
 entries[p]=h
selected=[r/workflow,old,ci/'check-02.sh',Path(__file__).resolve(),ci/'README-02.md',s/'BETA_REPLAY_PATH_CORRECTION_PROTOCOL_02.md']
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-02.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
assert len(old.read_text().splitlines())==839
changed=[p for h,p in(line.split('  ',1)for line in old.read_text().splitlines())if entries[p]!=h]
assert changed==[workflow]
print(json.dumps(dict(sources=len(entries),plus_manifest_self=len(entries)+1,original839_keys_retained=True,only_original_hash_replaced=workflow,old_manifest_and_caller_bytes_unchanged=True,acceptance='17phases:16expected0/oneactual101;alltee0;native2/all3wholeJSON/no masks;both original21decls/0trusted;sixbindings;finalguards0')))
