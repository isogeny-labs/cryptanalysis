"""Development inventory only; never invoked by replay."""
from pathlib import Path
import hashlib,json
ci=Path(__file__).resolve().parent;s=ci.parent;r=ci.parents[2]
old=s/'ci_beta_complete/reference-01.sha256';entries={}
for line in old.read_text().splitlines():
 h,p=line.split('  ',1);assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,p;entries[p]=h
assert len(entries)==881
selected={old,r/'.github/workflows/chained-transfer-norm-halving.yml'}
selected.update(p for p in(s/'norm-halving-evaluator').rglob('*')if p.is_file()and 'target'not in p.parts)
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
selected.update(p for p in(s/'reports/norm-halving-results-01').iterdir()if p.is_file())
selected.update(p for p in(r/'docs/research-artifacts/chained-transfer/norm-halving-01').iterdir()if p.is_file())
for name in ['NORM_HALVING_PROTOCOL_01.md','NORM_HALVING_DERIVATION_01.md','NORM_HALVING_PROOF_MAP_01.md','NORM_HALVING_REPLAY_PROTOCOL_01.md']:selected.add(s/name)
index=s/'evidence/norm-halving-bindings-01/claims.json';selected.add(index)
for row in json.loads(index.read_text()):selected.add(r/row['claim_path'])
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps({'inputs':len(entries),'with_manifest':len(entries)+1,'old881unchanged':True,'unfiltered_tests':4,'whole_native_records':4,'masks':[],'phases':21,'expected':'19zero/twoactual101/alltee0','original_gates':'10declarations/zero trusted each','exact_bindings':9,'total_partial_bindings':82,'standing':'unsigned finite and conditional'}))
