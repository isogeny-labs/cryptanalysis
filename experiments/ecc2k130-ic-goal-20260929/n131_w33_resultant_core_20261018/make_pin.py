"""Pin only the first 32 source-code bits in the relaxed positive core."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


cfg = json.loads((HERE / 'pin_protocol.json').read_text())
for name, digest in cfg['sources'].items():
    assert sha(Path(name)) == digest, name
assert cfg['first_code'] == 3
source = (HERE / 'positive_core.xcnf').read_text().splitlines()
assert source[0].startswith('p cnf ')
_, _, variables, constraints = source[0].split()
assert int(variables) == 11868 and int(constraints) == 25618
units = [str((j+1) if cfg['first_code'] >> j & 1 else -(j+1))+' 0'
         for j in range(32)]
source[0] = f'p cnf {variables} {int(constraints)+32}'
out = HERE / 'positive_core_pin_first.xcnf'
assert not out.exists()
out.write_text('\n'.join([source[0], *units, *source[1:]])+'\n')
result = {'status': 'PASS_CORE_PIN_FIRST_FORMULA', 'candidate_id': None,
          'curve_id': cfg['curve_id'], 'known_first_code': cfg['first_code'],
          'second_code_bits_free': 32, 'formula_sha256': sha(out),
          'formula_bytes': out.stat().st_size,
          'protocol_sha256': sha(HERE / 'pin_protocol.json')}
(HERE / 'pin_build_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps(result, sort_keys=True))
