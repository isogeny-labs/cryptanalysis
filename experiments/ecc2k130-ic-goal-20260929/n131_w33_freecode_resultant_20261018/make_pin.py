"""Freeze one-code-pinned N131 positive diagnostic from exact XCNF."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / 'pin_build_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
out = HERE / 'positive_pin_first.xcnf'
assert not out.exists()
lines = (HERE / 'positive.xcnf').read_text().splitlines()
assert lines[0].startswith('p cnf ')
_, _, variables, constraints = lines[0].split()
assert int(variables) == 21194 and int(constraints) == 51716
known_first_code = 3
unit_clauses = [str((j+1) if known_first_code >> j & 1 else -(j+1))+' 0'
                for j in range(32)]
lines[0] = f'p cnf {variables} {int(constraints)+len(unit_clauses)}'
out.write_text('\n'.join([lines[0], *unit_clauses, *lines[1:]])+'\n')
result = {'status': 'PASS_N131_W33_PIN_FIRST_FORMULA',
          'candidate_id': None, 'curve_id': cfg['curve_id'],
          'known_first_code': known_first_code,
          'pinned_input_variables': 32,
          'second_code_bits_free': 32,
          'inverse_witness_bits_free': 262,
          'formula_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
          'formula_bytes': out.stat().st_size,
          'protocol_sha256': hashlib.sha256((HERE / 'pin_build_protocol.json').read_bytes()).hexdigest()}
(HERE / 'pin_build_result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(result, sort_keys=True))
