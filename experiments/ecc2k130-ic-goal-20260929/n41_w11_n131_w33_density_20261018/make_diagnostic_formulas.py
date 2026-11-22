"""Fix archived public-relation codes while leaving pair roots unresolved."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
protocol = json.loads((HERE / 'diagnostic_build_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
fixture = json.loads((ROOT / 'n41_n131_w29_rotation_alignment_20261017' /
                      'n41_model_fixture.json').read_text())
wires = json.loads((HERE / 'n41_input_wires.json').read_text())
source = (HERE / 'n41_formula.xcnf').read_text()
head, rest = source.split('\n', 1)
parts = head.split()
assert parts[:2] == ['p', 'cnf'] and len(parts) == 4
assert int(parts[2]) == 19365
assert int(parts[3]) == 51233
codes = [sum(((row['masks'][0] >> bit) & 1) << index
             for index, bit in enumerate(wires['source_bits']))
         for row in fixture['pairs']]
assert len(codes) == 5
assert codes[0] < codes[1] and codes[3] < codes[4]
rows = {}
for label, count in (('first3', 3), ('all5', 5)):
    clauses = []
    for slot in range(count):
        for index, wire in enumerate(wires['mask'][slot]):
            clauses.append(f'{wire if codes[slot] >> index & 1 else -wire} 0')
    path = HERE / f'{label}_formula.xcnf'
    assert not path.exists()
    first = f'p cnf {parts[2]} {int(parts[3]) + len(clauses)}\n'
    path.write_text(first + '\n'.join(clauses) + '\n' + rest)
    rows[label] = {'fixed_code_count': count,
                   'unit_clause_count': len(clauses),
                   'formula_bytes': path.stat().st_size,
                   'formula_sha256': sha(path)}
result = {'status': 'FROZEN_N41_W11_KNOWN_CODE_DIAGNOSTIC_FORMULAS',
          'candidate_id': None,
          'curve_id': protocol['curve_id'],
          'known_relation_codes': codes,
          'base_formula_sha256': sha(HERE / 'n41_formula.xcnf'),
          'arms': rows,
          'protocol_sha256': sha(HERE / 'diagnostic_build_protocol.json')}
(HERE / 'diagnostic_build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
