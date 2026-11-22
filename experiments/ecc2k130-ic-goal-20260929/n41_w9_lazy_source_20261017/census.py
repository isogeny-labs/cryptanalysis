"""Exhaustively compare exact inverse-trace source gates with W9 table codes."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('w9_lazy_circuit', HERE / 'circuit.py')
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


accepted = set()
rows = []
for code in range(1 << len(design.BITS)):
    mask = sum((code >> j & 1) << bit for j, bit in enumerate(design.BITS))
    a = mask << 1
    b = a ^ design.SEED
    p = design.F.mul(a, b)
    if p:
        inverse = design.F.inverse(p)
        gate1 = design.trace(design.F.mul(a, inverse)) == 0
        gate2 = design.trace(design.F.mul(design.SEED, inverse)) == 0
        if gate1 and gate2:
            accepted.add(code)
            assert a and b
            assert design.trace(a) == design.trace(b) == 0
            assert design.trace(design.F.inverse(a)) == 0
            assert design.trace(design.F.inverse(b)) == 0
            rows.append({'code': code, 'mask': mask,
                         'source_inverse_product': inverse})
assert accepted == design.ALLOWED_CODES
result = {'status': 'PASS_EXHAUSTIVE_W9_SOURCE_GATE_TABLE_EQUIVALENCE',
          'evaluated_codes': 256, 'accepted_codes': len(accepted),
          'rows': rows, 'source_sha256': {
              'script': sha(Path(__file__)), 'circuit': sha(HERE / 'circuit.py'),
              'source_states': sha(design.SOURCE)}}
with (HERE / 'census_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'accepted_codes': result['accepted_codes']}))
