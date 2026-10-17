"""Exact low-degree code-label screen for the aligned root quotient."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN = ROOT / 'n41_w9_lazy_source_20261017/circuit.py'
STATES = HERE / 'aligned_states.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parity(value):
    return value.bit_count() & 1


def pivots(vectors):
    rows = {}
    for value in vectors:
        while value:
            bit = value.bit_length() - 1
            if bit not in rows:
                rows[bit] = value
                break
            value ^= rows[bit]
    return rows


def orthogonal_basis(vectors, width):
    rows = pivots(vectors)
    free = [bit for bit in range(width) if bit not in rows]
    out = []
    for bit in free:
        value = 1 << bit
        for pivot in sorted(rows):
            if parity(rows[pivot] & value):
                value |= 1 << pivot
        assert all(parity(value & v) == 0 for v in vectors)
        out.append(value)
    assert len(out) + len(rows) == width
    return out


def fit_degree(codes, labels, width, degree):
    monomials = [sum(1 << bit for bit in subset)
                 for d in range(degree + 1)
                 for subset in itertools.combinations(range(width), d)]
    basis = {}
    for code, label in zip(codes, labels):
        row = sum((1 << i) for i, monomial in enumerate(monomials)
                  if code & monomial == monomial)
        bit_value = label
        while row:
            pivot = row.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = (row, bit_value)
                break
            old_row, old_value = basis[pivot]
            row ^= old_row
            bit_value ^= old_value
        if not row and bit_value:
            return {'fits': False, 'rank_at_contradiction': len(basis),
                    'feature_count': len(monomials)}
    return {'fits': True, 'rank': len(basis),
            'feature_count': len(monomials)}


protocol = {'status': 'FROZEN_BEFORE_N41_ALIGNED_QUOTIENT_LABEL_SCREEN',
            'source_sha256': {'script': sha(Path(__file__)),
                              'design': sha(DESIGN), 'states': sha(STATES),
                              'branch_rank': sha(HERE / 'branch_rank_result.json')}}
with (HERE / 'quotient_label_protocol.json').open('x') as out:
    json.dump(protocol, out, sort_keys=True, indent=2)
    out.write('\n')

spec = importlib.util.spec_from_file_location('n41_quotient_design', DESIGN)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)
states = json.loads(STATES.read_text())
assert states['rotations'] == [0, 0, 12, 12, 24]
inverse_C = design.F.inverse(design.C)
branch_basis = [design.F.mul(value, inverse_C) for value in design.PB]
vectors = [design.F.frob(value, rotation)
           for rotation in (0, 12, 24) for value in branch_basis]
duals = orthogonal_basis(vectors, 41)
assert len(duals) == 17

codes, roots = [], []
for index in range(0, 284, 4):
    block = states['states'][0][index:index + 4]
    mask = block[0]['masks'][0]
    assert all(row['masks'][0] == mask for row in block)
    code = sum(((mask >> bit) & 1) << i for i, bit in enumerate(design.BITS))
    root_values = sorted({design.F.inverse(row['point'][0]) for row in block})
    assert len(root_values) == 2
    assert root_values[0] ^ root_values[1] == design.F.mul(
        design.F.square(mask << 1) ^ design.F.mul(design.SEED, mask << 1), inverse_C)
    assert all(parity(dual & root_values[0]) == parity(dual & root_values[1])
               for dual in duals)
    codes.append(code)
    roots.append(root_values[0])
assert len(codes) == len(set(codes)) == 71

rows = []
for dual in duals:
    labels = [parity(dual & value) for value in roots]
    fits = {str(d): fit_degree(codes, labels, 8, d) for d in range(4)}
    minimum = next((d for d in range(4) if fits[str(d)]['fits']), '>3')
    rows.append({'dual_mask': dual, 'ones': sum(labels),
                 'minimum_degree_through_3': minimum, 'fits': fits})
histogram = {str(d): sum(row['minimum_degree_through_3'] == d for row in rows)
             for d in (0, 1, 2, 3, '>3')}
result = {'status': 'PASS_EXACT_N41_QUOTIENT_CODE_LABEL_SCREEN',
          'curve_id': states['curve_id'], 'rotations': states['rotations'],
          'source_codes': len(codes), 'quotient_dimension': len(duals),
          'degree_histogram': histogram, 'rows': rows,
          'protocol_sha256': sha(HERE / 'quotient_label_protocol.json')}
with (HERE / 'quotient_label_result.json').open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'status': result['status'],
                  'source_codes': result['source_codes'],
                  'quotient_dimension': result['quotient_dimension'],
                  'degree_histogram': histogram}))
