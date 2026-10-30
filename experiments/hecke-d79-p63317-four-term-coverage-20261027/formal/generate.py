"""Generate the finite residual arithmetic certificates from frozen results."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
PLAN = json.loads((HERE.parent / 'inputs.json').read_text())
POST = json.loads((HERE.parent / 'post-run.json').read_text())
raw = (HERE.parent / 'result.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == POST['result_sha256']
result = json.loads(raw)
item = PLAN['frozen']['class-logs.json']
log_raw = (ROOT / item['path']).read_bytes()
assert hashlib.sha256(log_raw).hexdigest() == item['sha256']
logs = json.loads(log_raw)['q_logs']

lines = [
    'module', '', 'public import Init', '', 'namespace FourTermCoverage',
    'public theorem four_transport {G H : Type}',
    '    (addG : G → G → G) (addH : H → H → H) (φ : G → H)',
    '    (B0 B1 B2 B3 Q : G)',
    '    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))',
    '    (relation : Q = addG (addG (addG B0 B1) B2) B3) :',
    '    φ Q = addH (addH (addH (φ B0) (φ B1)) (φ B2)) (φ B3) := by',
    '  rw [relation, map_add, map_add, map_add]',
    '#print axioms four_transport', '',
]
for n, row in enumerate(result['residual_rows']):
    assert row['status'] == 'FOUND'
    w = row['witness']
    terms = [f'({s * logs[i]})' for i, s in zip(w[::2], w[1::2])]
    formula = ' + '.join(terms)
    lines += [f'public theorem residual_{n} : ({formula}) % 2531 = {row["scalar"]} := by decide',
              f'#print axioms residual_{n}']
lines += ['', 'end FourTermCoverage', '']
(HERE / 'FourTermCoverage.lean').write_text('\n'.join(lines))
print(f'generated {len(result["residual_rows"])} residual certificates')
