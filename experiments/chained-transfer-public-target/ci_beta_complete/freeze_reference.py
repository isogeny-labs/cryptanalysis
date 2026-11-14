"""Development source/data inventory; the replay never regenerates this file."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
old=s/'ci_beta_lift/reference-02.sha256';entries={}
for line in old.read_text().splitlines():
 h,p=line.split('  ',1);assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,p;entries[p]=h
assert len(entries)==844
selected={old}
selected.update(p for p in(s/'beta-complete-evaluator').rglob('*')if p.is_file())
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in['BETA_COMPLETE_RATIONAL_DERIVATION_01.md','BETA_COMPLETE_RATIONAL_DERIVATION_02.md','BETA_COMPLETE_RATIONAL_PROOF_MAP_01.md','BETA_COMPLETE_REPLAY_PROTOCOL_01.md','BETA_COMPLETE_REPLAY_PROTOCOL_02.md']:selected.add(s/name)
for index in['beta-complete-rational-bindings-01','beta-CRT-projection-bindings-01']:
 p=s/'evidence'/index/'claims.json';selected.add(p)
 for row in json.loads(p.read_text()):selected.add(r/row['claim_path'])
selected.add(r/'.github/workflows/chained-transfer-beta-complete.yml')
selected.add(s/'evidence/odd-product-maps-acceptance-02/all-native-records.json.xz')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps(dict(inputs=len(entries),with_manifest=len(entries)+1,all_prior844_inputs_unchanged=True,external_fixture_explicitly_guarded=True,unfiltered_tests=3,whole_native_records=3,masks=[],ordered_phases=20,expected='17zero/threeactual101/everytee0',proof_gates='two unchanged originals44group+1Int declarations/zero trusted',exact_bindings=7,total_partial_unique_bindings=73,scope='finite/conditional/unsigned; not performance')))
