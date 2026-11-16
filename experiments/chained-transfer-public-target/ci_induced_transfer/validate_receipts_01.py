"""Validate complete original proof logs and exact binding receipts; no mathematics."""
from pathlib import Path
import hashlib,json,re,sys
repo,out=map(Path,sys.argv[1:3])
study=repo/'experiments/chained-transfer-public-target'
coverage=json.loads((study/'evidence/original-induced-full-transfer-proof-01/exact-root-and-structural-coverage.json').read_text())['coverage']
source=(study/'original-induced-transfer-01/lean/InducedFullTransfer.lean').read_bytes()
assert (out/'actual-consumer-InducedFullTransfer.lean').read_bytes()==source
assert (out/'actual-producer-InducedFullTransfer.lean').read_bytes()==source
receipts=[]
for name in ['consumer','producer']:
    root=out/(name+'-proofs')
    statuses=list(root.rglob('status'));logs=list(root.rglob('audit.log'))
    assert len(statuses)==len(logs)==1 and statuses[0].read_text().strip()=='PASS'
    text=logs[0].read_text()
    assert 'audited 21 theorems in [InducedFullTransfer]; 0 failing, 0 trusted (native_decide)'in text
    declarations=re.findall(r'^ok\s+(\S+)',text,re.M)
    wanted=coverage[name]['nine_planned_named_roots']+coverage[name]['additional_structure_declarations']
    assert len(declarations)==len(set(declarations))==21
    assert set(declarations)==set(wanted)
    receipts.append(dict(gate=name,actual_declarations=declarations,failing=0,trusted=0))
bindings=json.loads((study/'evidence/original-induced-full-transfer-proof-01/bindings.json').read_text())
assert len(bindings)==9
expected=(study/'ci_induced_transfer/statement-bindings-01.txt').read_text().splitlines()
assert expected==[Path(v['claim']).stem for v in bindings]
assert {p.name for p in out.glob('binding-*.txt')}=={'binding-'+name+'.txt'for name in expected}
for row in bindings:
    claim=json.loads((repo/row['claim']).read_text())
    canonical=json.dumps({k:v for k,v in claim.items()if k!='standing'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    verdict=json.loads((out/('binding-'+claim['id']+'.txt')).read_text())
    assert verdict['claim_sha256']==hashlib.sha256(canonical).hexdigest()
    assert verdict['verdict']=='pass'and all(v['verdict']=='pass'for v in verdict['proofs'])
    assert verdict['commit']==(out/'consumer-head.txt').read_text().strip()
(out/'whole-proof-coverage-and-bindings.json').write_text(json.dumps(dict(gates=receipts,all_nine_exact_bindings=bindings,scope='unsigned exact proof replay only; conditional quotient algebra and actual model/program/cost bridges remain explicit'),indent=2)+'\n')
