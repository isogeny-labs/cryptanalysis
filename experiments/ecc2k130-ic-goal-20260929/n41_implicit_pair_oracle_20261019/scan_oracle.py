"""Target-conditioned pair lookup using a linear product-span gate."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_w9_lazy_source_20261017'))
import circuit as design


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


protocol = json.loads((HERE / 'scan_protocol.json').read_text())
for path, expected in protocol['sources'].items():
    assert sha(path) == expected, path
assert not (HERE / 'scan_result.json').exists()
keys = json.loads((HERE / 'keys.json').read_text())
source = json.loads(Path(protocol['source_states']).read_text())
Fbits = design.F
R = PolynomialRing(GF(2), 'u')
u = R.gen()
F = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
E = EllipticCurve(F, [1, 0, 0, 0, 1])


def dec(word):
    return F(R([(int(word) >> bit) & 1 for bit in range(41)]))


def enc(value):
    return sum(int(coefficient) << bit
               for bit, coefficient in enumerate(value.polynomial().list()))


def point(xy):
    return E(*map(dec, xy))


def halftrace(value):
    return sum((value**(1 << (2 * i)) for i in range(21)), F.zero())


# Build a left-to-right XOR basis, carrying the source-code witness.
basis = {}
for bit, value in enumerate(design.PB):
    vector, code = value, 1 << bit
    while vector:
        pivot = vector.bit_length() - 1
        if pivot not in basis:
            basis[pivot] = (vector, code)
            break
        v, c = basis[pivot]
        vector ^= v
        code ^= c
    else:
        raise AssertionError('dependent source-product basis')
assert len(basis) == 8


def source_code(value):
    vector, code = value, 0
    while vector:
        pivot = vector.bit_length() - 1
        if pivot not in basis:
            return None
        v, c = basis[pivot]
        vector ^= v
        code ^= c
    return code


mask_columns = {}
for slot in source['states']:
    for row in slot:
        for mask, column in zip(row['masks'], row['columns']):
            assert mask_columns.setdefault(mask, column) == column


def reconstruct(mask, sign_a, sign_b):
    leaves = []
    for m, sign in ((mask, sign_a), (mask ^ design.SEED_MASK, sign_b)):
        w = dec(m << 1)
        if not w or w.trace() or (1 / w).trace():
            return None
        h = halftrace(w)
        if not h or h**2 + h != w:
            return None
        x = 1 + 1 / h
        leaf = E.lift_x(x, all=True)[0]
        leaves.append(-leaf if sign else leaf)
    total = leaves[0] + leaves[1]
    if total == E(0):
        return None
    return E(total[0]**(1 << 6), total[1]**(1 << 6))


left = [(point(row['point']), set(row['columns']), sid)
        for sid, row in enumerate(source['states'][0])]
rows = []
for key in keys['keys']:
    started = time.monotonic()
    target = point(key['point'])
    counts = {'left_scanned': 0, 'nonzero_second_x': 0,
              'product_span_hits': 0, 'source_trace_passes': 0,
              'reconstructed_point_hits': 0, 'column_compatible_hits': 0}
    witnesses = []
    for left_point, left_columns, left_id in left:
        counts['left_scanned'] += 1
        second = target - left_point
        if second == E(0) or second[0] == 0:
            continue
        counts['nonzero_second_x'] += 1
        raw_x = enc(second[0]**(1 << 35))
        z = Fbits.inverse(raw_x)
        product = Fbits.mul(design.C, z) ^ Fbits.mul(design.H, Fbits.inverse(z))
        code = source_code(product)
        if code is None:
            continue
        counts['product_span_hits'] += 1
        mask = sum(1 << bit for index, bit in enumerate(design.BITS)
                   if code >> index & 1)
        if not product or mask not in mask_columns or (mask ^ design.SEED_MASK) not in mask_columns:
            continue
        inverse = Fbits.inverse(product)
        a = mask << 1
        if design.trace(Fbits.mul(a, inverse)) or design.trace(Fbits.mul(design.SEED, inverse)):
            continue
        counts['source_trace_passes'] += 1
        for sign_a in (0, 1):
            for sign_b in (0, 1):
                candidate = reconstruct(mask, sign_a, sign_b)
                if candidate != second:
                    continue
                counts['reconstructed_point_hits'] += 1
                columns = {mask_columns[mask], mask_columns[mask ^ design.SEED_MASK]}
                if len(columns) != 2 or not left_columns.isdisjoint(columns):
                    continue
                counts['column_compatible_hits'] += 1
                witnesses.append({'left_state_id': left_id, 'second_mask': mask,
                                  'second_signs': [sign_a, sign_b],
                                  'second_columns': sorted(columns)})
    result = {'key_id': key['key_id'], 'exact_member': key['exact_member'],
              'oracle_member': bool(witnesses), 'witnesses': witnesses,
              'counts': counts, 'query_wall_seconds': time.monotonic() - started}
    assert result['oracle_member'] == result['exact_member'], result
    rows.append(result)
    print(json.dumps({'key_id':key['key_id'],'member':result['oracle_member'],
                      'span_hits':counts['product_span_hits'],
                      'wall_seconds':result['query_wall_seconds']}),flush=True)
result = {'status': 'PASS_N41_TWO_PAIR_IMPLICIT_SPAN_ORACLE_PANEL',
          'candidate_id': None, 'curve_id': protocol['curve_id'],
          'product_basis_rank': len(basis), 'rows': rows,
          'keys_sha256': sha(HERE / 'keys.json'),
          'protocol_sha256': sha(HERE / 'scan_protocol.json')}
(HERE / 'scan_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
