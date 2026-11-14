"""Development-only source inventory; replay never regenerates this manifest."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];ci=Path(__file__).resolve().parent;s=ci.parent
entries={}
for ref in [s/'ci_norm_sampling/reference-01.sha256',s/'arithmetic-audit/reference-03.sha256']:
 for line in ref.read_text().splitlines():
  h,p=line.split('  ',1)
  if p in entries:assert entries[p]==h,p
  assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h,p
  entries[p]=h
 selected={ref}
 for f in selected:entries[f.relative_to(r).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
selected={p for p in (s/'beta-rational-lift').rglob('*')if p.is_file()}
selected.update(p for p in ci.iterdir()if p.is_file()and p.name!='reference-01.sha256')
for name in ['BETA_RATIONAL_LIFT_PROTOCOL_01.md','BETA_IMPLEMENTATION_BOUNDARIES_01.md','BETA_RATIONAL_LIFT_DERIVATION_01.md','BETA_RATIONAL_LIFT_PROOF_MAP_01.md']:selected.add(s/name)
for index in ['beta-rational-lift-bindings-01','beta-quadratic-norm-bindings-01']:
 p=s/'evidence'/index/'claims.json';selected.add(p)
 for claim in json.loads(p.read_text()):selected.add(r/claim['claim_path'])
selected.add(r/'.github/workflows/chained-transfer-beta-rational-lift.yml')
selected.add(r/'../crypto/src/cryptanalysis/identity_certificate.rs')
for p in selected:entries[p.relative_to(r).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(ci/'reference-01.sha256').write_text(''.join(h+'  '+p+'\n'for p,h in sorted(entries.items())))
print(json.dumps({'selected_sources':len(entries),'plus_manifest_self':len(entries)+1,'original_norm_sources':784,'original_arithmetic_sources':22,'old18_workflows_unchanged':True,'native_records':3,'unfiltered_tests':2,'proof_declarations_in_each_original_gate':21,'faithful_bindings':6,'ordered_phases':17,'expected_phase_exits':'16positive0/oneactualnegative101/tee0','scope':'finite/conditional/unsigned; nextbeta evaluator separate crate'}))
