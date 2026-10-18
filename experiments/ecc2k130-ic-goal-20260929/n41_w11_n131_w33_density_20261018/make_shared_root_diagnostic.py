"""Freeze one public-relation code control for the shared-root circuit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


build = json.loads((HERE / 'shared_root_build_result.json').read_text())
assert build['status'] == 'PASS_N41_W11_SHARED_INVERSE_ROOT_CONTROL'
wires = json.loads((HERE / 'shared_root_input_wires.json').read_text())
codes = json.loads((HERE / 'diagnostic_build_result.json').read_text())['known_relation_codes']
source = (HERE / 'shared_root_formula.xcnf').read_text()
head, rest = source.split('\n', 1)
parts = head.split()
assert parts[:2] == ['p', 'cnf'] and len(parts) == 4
assert int(parts[2]) == build['counts']['variables']
assert int(parts[3]) == build['counts']['clauses'] + build['counts']['xor_rows']
clauses = [f'{wire if code >> index & 1 else -wire} 0'
           for code, row in zip(codes, wires['mask'])
           for index, wire in enumerate(row)]
assert len(clauses) == 50
path = HERE / 'shared_root_all5_formula.xcnf'
assert not path.exists()
path.write_text(f'p cnf {parts[2]} {int(parts[3]) + len(clauses)}\n'
                + '\n'.join(clauses) + '\n' + rest)
result = {'status': 'FROZEN_N41_W11_SHARED_ROOT_KNOWN_CODE_CONTROL',
          'candidate_id': None, 'curve_id': build['curve_id'],
          'fixed_codes': codes, 'fixed_clause_count': len(clauses),
          'formula_sha256': sha(path), 'formula_bytes': path.stat().st_size,
          'source_formula_sha256': sha(HERE / 'shared_root_formula.xcnf'),
          'wire_record_sha256': sha(HERE / 'shared_root_input_wires.json'),
          'builder_result_sha256': sha(HERE / 'shared_root_build_result.json')}
out = HERE / 'shared_root_diagnostic_build_result.json'
assert not out.exists()
out.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps(result, sort_keys=True))
