#!/usr/bin/env python3
"""Independent finite-field modular gate check for the D15 first cell."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing, classical_modular_polynomial, hilbert_class_polynomial, kronecker

P = Path(__file__).resolve().parent
sha = lambda n: hashlib.sha256((P / n).read_bytes()).hexdigest()
protocol = json.loads((P / 'protocol.json').read_text())
launch = json.loads((P / 'launch.json').read_text())
producer = json.loads((P / 'data/exp11_class_walk_D15_f6.json').read_text())
gate = json.loads((P / 'audit_D15_gate_protocol.json').read_text())
assert gate['status'] == 'FROZEN_BEFORE_D15_GATE_AUDIT'
assert gate['audit_sha256'] == sha('audit_D15_gate.py')
for name, digest in gate['files'].items():
    assert sha(name) == digest, name
assert protocol['status'] == 'FROZEN_BEFORE_D15_F6_PRODUCER'
assert launch['status'] == 'PROCESS_COMPLETE' and launch['exit_code'] == 0
assert launch['result_sha256'] == sha('data/exp11_class_walk_D15_f6.json')
assert (producer['DK'], producer['f'], producer['p'], producer['u']) == (-15, 6, 139, 4)

fp = GF(139)
ring = PolynomialRing(fp, 'J')
J = ring.gen()
cm_js = hilbert_class_polynomial(-15).change_ring(fp).roots(multiplicities=False)
phi11 = classical_modular_polynomial(11)
records = []
for j in cm_js:
    modular_roots = ring(phi11(j, J)).roots()
    records.append({'j': int(j), 'rational_modular_neighbours':
                    [{'j': int(root), 'multiplicity': int(mult)} for root, mult in modular_roots]})
assert len(cm_js) == 2
assert all(not x['rational_modular_neighbours'] for x in records)
assert producer['class_size'] == 0 and producer['relations'] == 0
result = {'status': 'D15_F6_RATIONAL_X0_11_GATE_FAILED',
          'quadratic_character_at_11': int(kronecker(-15, 11)),
          'cm_j_records': records, 'matrix_rank': None, 'candidate_id': None,
          'protocol_sha256': sha('protocol.json'),
          'launch_sha256': sha('launch.json'),
          'producer_sha256': sha('data/exp11_class_walk_D15_f6.json')}
assert result['quadratic_character_at_11'] == -1
(P / 'audit_D15_gate.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
