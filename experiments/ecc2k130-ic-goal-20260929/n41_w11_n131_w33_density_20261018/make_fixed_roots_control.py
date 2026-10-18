"""Fix the archived pair outputs while leaving S3 middle values free."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


fixture_path = ROOT / 'n41_n131_w29_rotation_alignment_20261017' / 'n41_model_fixture.json'
fixture = json.loads(fixture_path.read_text())
wires = json.loads((HERE / 'shared_root_input_wires.json').read_text())
build = json.loads((HERE / 'shared_root_build_result.json').read_text())
source = (HERE / 'shared_root_all5_formula.xcnf').read_text()
head, rest = source.split('\n', 1)
parts = head.split()
assert parts[:2] == ['p', 'cnf'] and len(parts) == 4
values = [row['output_reciprocal'] for row in fixture['pairs']]
assert len(values) == len(wires['out']) == 5
clauses = [f'{wire if value >> index & 1 else -wire} 0'
           for value, row in zip(values, wires['out'])
           for index, wire in enumerate(row)]
assert len(clauses) == 5 * 41
path = HERE / 'shared_root_fixed_outputs_formula.xcnf'
assert not path.exists()
path.write_text(f'p cnf {parts[2]} {int(parts[3]) + len(clauses)}\n'
                + '\n'.join(clauses) + '\n' + rest)
result = {'status': 'FROZEN_N41_W11_FIXED_PAIR_OUTPUT_CONTROL',
          'candidate_id': None, 'curve_id': build['curve_id'],
          'input_law': 'frozen N41 public point with five independently verified source codes and pair outputs fixed; three S3 intermediate values remain free',
          'fixed_pair_outputs': values, 'additional_unit_clauses': len(clauses),
          'formula_sha256': sha(path), 'formula_bytes': path.stat().st_size,
          'base_formula_sha256': sha(HERE / 'shared_root_all5_formula.xcnf'),
          'fixture_sha256': sha(fixture_path),
          'wire_record_sha256': sha(HERE / 'shared_root_input_wires.json')}
out = HERE / 'fixed_roots_build_result.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
