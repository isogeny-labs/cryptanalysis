"""Ablate the algebraic source gate using the exact finite W9 code table."""
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
sys.path.insert(0, str(ROOT / 'n131_w20_selector_elimination_v2_20261013'))
import circuit as design
import selector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'table_build_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
keys = json.loads((HERE / 'keys.json').read_text())
source = json.loads(Path(protocol['source_states']).read_text())
rows = []
for key_id in ('P0', 'N1'):
    start = time.monotonic()
    key = next(row for row in keys['keys'] if row['key_id'] == key_id)
    path = HERE / f'{key_id}_table.xcnf'
    assert not path.exists()
    circ = design.KaratsubaCircuit(design.N, design.TAPS)
    alg = design.Algebra(circ, design.F, dense_and_threshold=3000)
    mask_wires, output_wires, nodes = [], [], []
    for rotation in (0, 6):
        code = [circ.variable() for _ in design.BITS]
        mask_wires.append(code)
        for forbidden in range(1 << len(design.BITS)):
            if forbidden not in design.ALLOWED_CODES:
                circ.clauses.append(' '.join(
                    str(-wire if forbidden >> bit & 1 else wire)
                    for bit, wire in enumerate(code)) + ' 0')
        product = alg.expression(zip(code, design.PB))
        z_bits = [circ.variable() for _ in range(design.N)]
        output_wires.append(z_bits)
        circ.clauses.append(' '.join(map(str, z_bits)) + ' 0')
        z = alg.from_bits(z_bits)
        cz2 = alg.expression((wire, design.F.mul(design.C, basis))
                             for wire, basis in alg.square(z).terms)
        circ.require_zero(alg.add(cz2, alg.mul(product, z),
                                  alg.expression(((-1, design.H),))).bits())
        rotated = circ.linear_element(z_bits,
            [design.F.frob(1 << bit, rotation) for bit in range(design.N)])
        nodes.append(alg.from_bits(rotated))
    a, b = nodes
    target = alg.expression(((-1, key['reciprocal_x']),))
    ab = alg.mul(a, b)
    abz = alg.mul(ab, target)
    circ.require_zero(alg.add(alg.square(abz), abz,
                              alg.square(alg.add(a, b)), alg.square(target)).bits())
    circ.write(path)
    counts = {'variables': circ.next_var - 1, 'clauses': len(circ.clauses),
              'xor_rows': len(circ.xors), 'and_gates': circ.and_count}
    witness_check = None
    if key['exact_member']:
        assignment = {}
        for slot, state_id in enumerate(key['reference_witness']):
            state = source['states'][slot][state_id]
            mask = state['masks'][0]
            code = sum(((mask >> bit) & 1) << index
                       for index, bit in enumerate(design.BITS))
            raw_x = design.F.frob(state['point'][0], (design.N - (0, 6)[slot]) % design.N)
            raw_z = design.F.inverse(raw_x)
            assignment.update({wire: code >> bit & 1
                               for bit, wire in enumerate(mask_wires[slot])})
            assignment.update({wire: raw_z >> bit & 1
                               for bit, wire in enumerate(output_wires[slot])})
        witness_check = selector.old.check_assignment(
            circ, selector.old.complete_assignment(circ, assignment))
        assert witness_check == {'clauses': counts['clauses'],
                                 'native_xor_rows': counts['xor_rows']}
    rows.append({'key_id': key_id, 'exact_member': key['exact_member'],
                 'formula_sha256': sha(path), 'formula_bytes': path.stat().st_size,
                 'counts': counts, 'constructed_witness_check': witness_check,
                 'build_wall_seconds': time.monotonic() - start})
result = {'status': 'PASS_N41_TWO_PAIR_TABLE_ABLATION_BUILD',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'rows': rows, 'protocol_sha256': sha(HERE / 'table_build_protocol.json')}
(HERE / 'table_build_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':result['status'],'counts':rows[0]['counts']}))
