#!/usr/bin/env sage -python
"""Exact Boolean-cube norm of the frozen N41 target eliminant."""
import hashlib
import itertools
import json
import resource
import signal
import struct
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FLATS = ROOT / 'n41_valid_affine_flat_target_20261017'
TENSOR = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
RUNTIME = HERE / 'sage_runtime_info.json'
GRID_SIZE = 40


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write('\n')


def source_hashes():
    files = {'script': Path(__file__), 'geometry': GEOMETRY,
             'flat_result': FLATS / 'result.json',
             'witness_tensor': TENSOR / 'witness_result_v2.json',
             'negative_tensor': TENSOR / 'negative_result_v2.json',
             'witness_grid': FLATS / 'grid_witness.bin',
             'negative_grid': FLATS / 'grid_negative.bin',
             'runtime': RUNTIME}
    return {key: sha(path) for key, path in files.items()}


def freeze():
    flat = json.loads((FLATS / 'result.json').read_text())
    assert flat['three_flat_count'] == 8
    assert [0, 3, 1] in flat['panels'][0]['zero_block_indices']
    assert [0, 0, 0] not in flat['panels'][0]['zero_block_indices']
    assert flat['panels'][1]['zero_block_indices'] == []
    save('protocol.json', {'status': 'FROZEN_N41_BOOLEAN_CUBE_NORM_BEFORE_RUN',
         'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0',
         'field': 'GF(2)[t]/(t^41+t^3+1)',
         'selector_bits': 9, 'code_flats_per_slot': 8,
         'panels': [{'tensor': 'witness', 'flat_indices': [0, 3, 1],
                     'expected_zero': True},
                    {'tensor': 'witness', 'flat_indices': [0, 0, 0],
                     'expected_zero': False},
                    {'tensor': 'negative', 'flat_indices': [0, 0, 0],
                     'expected_zero': False}],
         'worker_count': 1, 'alarm_seconds': 180,
         'rss_observational_cap_bytes': 4294967296,
         'source_sha256': source_hashes(), 'candidate_id': None})


class Ops:
    def __init__(self):
        self.mul = 0
        self.square = 0
        self.add = 0

    def m(self, a, b):
        self.mul += 1
        return a * b

    def s(self, a):
        self.square += 1
        return a * a

    def plus(self, a, b):
        self.add += 1
        return a + b

    def record(self):
        return {'field_multiplications': self.mul,
                'field_squarings': self.square,
                'field_additions': self.add}


def mobius(values, width, ops):
    result = list(values)
    for bit in range(width):
        for mask in range(1 << width):
            if mask >> bit & 1:
                result[mask] = ops.plus(result[mask], result[mask ^ (1 << bit)])
    return result


def code_cube(flat_index, flats):
    anchor, directions = flats[flat_index]
    return [anchor ^ (directions[0] if code & 1 else 0)
            ^ (directions[1] if code & 2 else 0)
            ^ (directions[2] if code & 4 else 0)
            for code in range(8)]


def power_tables(products, maximum, ops):
    values = [[value**exponent for value in products] for exponent in range(maximum+1)]
    anfs = [mobius(row, 3, ops) for row in values]
    return values, anfs


def add_to(table, key, value, ops, zero):
    if value:
        table[key] = ops.plus(table.get(key, zero), value)
        if not table[key]:
            del table[key]


def symbolic_coefficients(terms, pvalues, panf, qanf, ranf, ops, zero):
    result = {}
    for qi, ri, pterms in terms:
        pa = [zero] * 8
        for pi, coefficient in pterms:
            for i, power in enumerate(panf[pi]):
                if power:
                    pa[i] = ops.plus(pa[i], ops.m(coefficient, power))
        qr = [(j, k, ops.m(qv, rv))
              for j, qv in enumerate(qanf[qi]) if qv
              for k, rv in enumerate(ranf[ri]) if rv]
        for i, pv in enumerate(pa):
            if pv:
                for j, k, qrv in qr:
                    if qrv:
                        add_to(result, i | j << 3 | k << 6,
                               ops.m(pv, qrv), ops, zero)
    return result


def cube_norm(coeffs, ops, zero):
    current = dict(coeffs)
    stages = []
    for bit in range(8, -1, -1):
        lower = {mask: value for mask, value in current.items()
                 if mask >> bit & 1 == 0}
        upper = {mask ^ (1 << bit): value for mask, value in current.items()
                 if mask >> bit & 1}
        next_poly = {}
        before = ops.record()
        for mask, value in lower.items():
            add_to(next_poly, mask, ops.s(value), ops, zero)
        for m0, v0 in lower.items():
            for m1, v1 in upper.items():
                add_to(next_poly, m0 | m1, ops.m(v0, v1), ops, zero)
        after = ops.record()
        stages.append({'eliminated_bit': bit, 'input_terms': len(current),
                       'lower_terms': len(lower), 'upper_terms': len(upper),
                       'output_terms': len(next_poly),
                       'field_multiplications': after['field_multiplications']-
                       before['field_multiplications'],
                       'field_squarings': after['field_squarings']-
                       before['field_squarings']})
        current = next_poly
    assert set(current) <= {0}
    return current.get(0, zero), stages


def direct_values(terms, ppowers, qpowers, rpowers, ops, zero):
    values = []
    for ip in range(8):
        specialized = []
        for qi, ri, pterms in terms:
            value = zero
            for pi, coefficient in pterms:
                value = ops.plus(value, ops.m(coefficient, ppowers[pi][ip]))
            specialized.append((qi, ri, value))
        for iq in range(8):
            by_r = [zero] * 25
            for qi, ri, coefficient in specialized:
                if coefficient:
                    by_r[ri] = ops.plus(by_r[ri],
                                         ops.m(coefficient, qpowers[qi][iq]))
            for ir in range(8):
                result = zero
                for coefficient in reversed(by_r):
                    result = ops.plus(ops.m(result, rpowers[1][ir]), coefficient)
                values.append(result)
    return values


def evaluate_anf(coeffs, selector, zero):
    value = zero
    for mask, coefficient in coeffs.items():
        if mask & selector == mask:
            value += coefficient
    return value


def run():
    signal.alarm(180)
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_N41_BOOLEAN_CUBE_NORM_BEFORE_RUN'
    assert protocol['source_sha256'] == source_hashes()
    setup_start = time.monotonic_ns()
    flat = json.loads((FLATS / 'result.json').read_text())
    geometry = json.loads(GEOMETRY.read_text())
    allowed = sorted(geometry['permitted_canonical_a'])
    index = {mask: i for i, mask in enumerate(allowed)}
    assert len(allowed) == GRID_SIZE
    F2 = PolynomialRing(GF(2), 't')
    t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41+t**3+1)
    zero = field.zero()
    def dec(value):
        return field(F2([int(value >> i & 1) for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def product(slot, mask):
        bits = 0
        for i, vector in enumerate(geometry['blocks'][slot]['product_basis']):
            if mask >> i & 1:
                bits ^= vector
        return dec(bits)
    tensors = {name: json.loads((TENSOR / f'{name}_result_v2.json').read_text())
               for name in ('witness', 'negative')}
    grids = {name: (FLATS / f'grid_{name}.bin').read_bytes()
             for name in ('witness', 'negative')}
    setup_ns = time.monotonic_ns() - setup_start
    rows = []
    for panel in protocol['panels']:
        name = panel['tensor']
        ids = panel['flat_indices']
        cube = [code_cube(i, flat['canonical_bases']) for i in ids]
        products = [[product(slot, code) for code in codes]
                    for slot, codes in enumerate(cube)]
        terms = [(qi, ri, [(pi, dec(c)) for pi, c in poly])
                 for qi, ri, poly in tensors[name]['coefficient_terms']]
        assert len(terms) == 213
        pre_ops = Ops()
        pre_start = time.monotonic_ns()
        ppowers, panf = power_tables(products[0], 16, pre_ops)
        qpowers, qanf = power_tables(products[1], 16, pre_ops)
        rpowers, ranf = power_tables(products[2], 24, pre_ops)
        pre_ns = time.monotonic_ns() - pre_start
        direct_ops = Ops()
        direct_start = time.monotonic_ns()
        direct = direct_values(terms, ppowers, qpowers, rpowers, direct_ops, zero)
        direct_ns = time.monotonic_ns() - direct_start
        assert len(direct) == 512
        symbolic_ops = Ops()
        symbolic_start = time.monotonic_ns()
        coefficients = symbolic_coefficients(terms, products[0], panf,
                                              qanf, ranf, symbolic_ops, zero)
        coefficients_ns = time.monotonic_ns() - symbolic_start
        norm_start = time.monotonic_ns()
        norm, norm_stages = cube_norm(coefficients, symbolic_ops, zero)
        norm_ns = time.monotonic_ns() - norm_start
        audit_start = time.monotonic_ns()
        for (i, j, k), value in zip(itertools.product(range(8), repeat=3), direct):
            assert evaluate_anf(coefficients, i | j << 3 | k << 6, zero) == value
        grid = grids[name]
        grid_values = [struct.unpack_from('<Q', grid, 8*(
            index[cube[0][i]]*1600 + index[cube[1][j]]*40 + index[cube[2][k]]))[0]
            for i, j, k in itertools.product(range(8), repeat=3)]
        assert [enc(value) for value in direct] == grid_values
        direct_product = field.one()
        for value in direct:
            direct_product *= value
        assert norm == direct_product
        zeros = [i for i, value in enumerate(direct) if not value]
        assert bool(zeros) == panel['expected_zero']
        audit_ns = time.monotonic_ns()-audit_start
        row = {'panel': name, 'flat_indices': ids,
               'source_codes': cube, 'zero_positions': zeros,
               'direct_values_sha256': hashlib.sha256(b''.join(
                   enc(value).to_bytes(8,'little') for value in direct)).hexdigest(),
               'norm_zero': not bool(norm), 'norm_value': enc(norm),
               'initial_anf_terms': len(coefficients),
               'precompute_ns': pre_ns, 'precompute_ops': pre_ops.record(),
               'direct_ns': direct_ns, 'direct_ops': direct_ops.record(),
               'symbolic_coefficient_ns': coefficients_ns,
               'symbolic_norm_ns': norm_ns,
               'symbolic_ops': symbolic_ops.record(),
               'norm_stages': norm_stages,
               'audit_ns': audit_ns}
        rows.append(row)
        print(name, ids, 'zeros', len(zeros), 'direct_ns', direct_ns,
              'symbolic_ns', coefficients_ns+norm_ns, flush=True)
    out = {'status': 'PASS_N41_BOOLEAN_CUBE_NORM_SCREEN',
           'candidate_id': None, 'curve_id': protocol['curve_id'],
           'source_sha256': protocol['source_sha256'],
           'protocol_sha256': sha(HERE / 'protocol.json'),
           'source_setup_ns': setup_ns, 'panels': rows,
           'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save('result.json', out)
    signal.alarm(0)
    print(out['status'], flush=True)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
