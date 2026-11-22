#!/usr/bin/env sage -python
"""Exact binary-linear zero-exclusion on N41 product-code rectangles."""
from array import array
from collections import Counter
import hashlib
import itertools
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reduce_vector(value, basis):
    for pivot in sorted(basis, reverse=True):
        if value >> pivot & 1:
            value ^= basis[pivot]
    return value


def coefficient_span(values, bits):
    coefficients = values[:]
    for bit in range(bits):
        for mask in range(1 << bits):
            if mask >> bit & 1:
                coefficients[mask] ^= coefficients[mask ^ (1 << bit)]
    basis = {}
    for value in coefficients[1:]:
        value = reduce_vector(value, basis)
        if value:
            basis[value.bit_length() - 1] = value
            if len(basis) == 41:
                break
    return len(basis), reduce_vector(coefficients[0], basis) != 0, coefficients


def valid_affine_span(values):
    constant = values[0]
    basis = {}
    for value in values[1:]:
        value = reduce_vector(value ^ constant, basis)
        if value:
            basis[value.bit_length() - 1] = value
            if len(basis) == 41:
                break
    return len(basis), reduce_vector(constant, basis) != 0


def separator(values):
    """Solve lambda dot value = 1 for every listed field-vector value."""
    equations = {}
    for value in values:
        row, rhs = value, 1
        for pivot in sorted(equations, reverse=True):
            if row >> pivot & 1:
                other, parity = equations[pivot]
                row ^= other
                rhs ^= parity
        if not row:
            if rhs:
                return None
            continue
        equations[row.bit_length() - 1] = (row, rhs)
    solution = 0
    for pivot in sorted(equations):
        row, rhs = equations[pivot]
        bit = rhs ^ ((row & solution).bit_count() & 1)
        if bit:
            solution |= 1 << pivot
    assert all((solution & value).bit_count() & 1 for value in values)
    return solution


def main():
    signal.alarm(300)
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    files = {'rectangle.py': Path(__file__), 'geometry.json': GEOMETRY,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sweep_result.json': SOURCE / 'sweep_result.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    assert protocol['source_sha256'] == {name: sha(path) for name, path in files.items()}
    geo = json.loads(GEOMETRY.read_text())
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    F2 = PolynomialRing(GF(2), 't')
    t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
    def dec(value):
        return field(F2([(int(value) >> i) & 1 for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    source_masks = geo['permitted_canonical_a']
    assert len(source_masks) == 40 and len(set(source_masks)) == 40
    bmax = max(protocol['low_bits_per_slot'])
    high = sorted({mask >> bmax for mask in source_masks})
    domain = sorted((prefix << bmax) | low for prefix in high for low in range(1 << bmax))
    assert len(domain) == 128
    index = {mask: i for i, mask in enumerate(domain)}
    def product(slot, mask):
        value = 0
        for i, basis in enumerate(geo['blocks'][slot]['product_basis']):
            if mask >> i & 1:
                value ^= basis
        return value
    products = [[dec(product(slot, mask)) for mask in domain] for slot in range(3)]
    panels = []
    for label in protocol['panels']:
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())
        terms = [(qi, ri, [(pi, dec(c)) for pi, c in coeff])
                 for qi, ri, coeff in tensor['coefficient_terms']]
        start = time.monotonic_ns()
        grid = array('Q', [0]) * (len(domain)**3)
        rfield = products[2]
        qpower = [[value**i for i in range(17)] for value in products[1]]
        for ip, pvalue in enumerate(products[0]):
            pp = [pvalue**i for i in range(17)]
            specialized = [(qi, ri, sum((c*pp[pi] for pi, c in coeff), field.zero()))
                           for qi, ri, coeff in terms]
            for iq, qp in enumerate(qpower):
                cp = [field.zero()] * 25
                for qi, ri, c in specialized:
                    cp[ri] += c*qp[qi]
                base = (ip*len(domain) + iq)*len(domain)
                for ir, rvalue in enumerate(rfield):
                    value = field.zero()
                    for c in reversed(cp):
                        value = value*rvalue + c
                    grid[base + ir] = enc(value)
            if ip % 32 == 31:
                print(label, 'grid_p', ip + 1, flush=True)
        grid_ns = time.monotonic_ns() - start
        def lookup(pm, qm, rm):
            return grid[(index[pm]*len(domain) + index[qm])*len(domain) + index[rm]]
        panel = {'label': label, 'grid_values': len(grid), 'grid_ns': grid_ns,
                 'grid_sha256': hashlib.sha256(grid.tobytes()).hexdigest(),
                 'widths': [], 'peak_self_rss_raw': 0}
        for bits in protocol['low_bits_per_slot']:
            start = time.monotonic_ns()
            groups = {}
            for prefix in sorted({mask >> bits for mask in source_masks}):
                groups[prefix] = [mask & ((1 << bits) - 1)
                                  for mask in source_masks if mask >> bits == prefix]
            size = 1 << bits
            full_rank = Counter()
            valid_rank = Counter()
            full_certified = valid_certified = 0
            full_covered = valid_covered = 0
            full_zero = valid_zero = valid_triples = 0
            examples = []
            witness_rectangle = None
            for triple_prefix in itertools.product(groups, repeat=3):
                pa, qa, ra = triple_prefix
                values = [0] * (size**3)
                for ilp in range(size):
                    pm = (pa << bits) | ilp
                    for ilq in range(size):
                        qm = (qa << bits) | ilq
                        base = ilp | (ilq << bits)
                        for ilr in range(size):
                            rm = (ra << bits) | ilr
                            values[base | (ilr << (2*bits))] = lookup(pm, qm, rm)
                rank, certified, coefficients = coefficient_span(values, 3*bits)
                actual = [values[lp | (lq << bits) | (lr << (2*bits))]
                          for lp, lq, lr in itertools.product(groups[pa], groups[qa], groups[ra])]
                assert actual
                actual_rank, actual_certified = valid_affine_span(actual)
                nvalid = len(actual)
                valid_triples += nvalid
                full_rank[rank] += 1
                valid_rank[actual_rank] += 1
                full_zero += int(0 in values)
                valid_zero += int(0 in actual)
                if certified:
                    assert 0 not in values
                    full_certified += 1
                    full_covered += nvalid
                    if len(examples) < 1:
                        witness = separator(values)
                        assert witness is not None
                        examples.append({'prefixes': triple_prefix, 'functional_mask': witness,
                                         'full_value_count': len(values), 'valid_value_count': nvalid,
                                         'first_value': values[0], 'rank': rank})
                if actual_certified:
                    assert 0 not in actual
                    valid_certified += 1
                    valid_covered += nvalid
                if all((mask >> bits) == prefix for mask, prefix in zip(
                        protocol['witness_masks'], triple_prefix)):
                    witness_rectangle = {'prefixes': triple_prefix,
                                         'full_rank': rank, 'valid_rank': actual_rank,
                                         'full_certified': certified,
                                         'valid_certified': actual_certified,
                                         'valid_triples': nvalid, 'valid_zeros': actual.count(0)}
            assert valid_triples == 40**3
            expected_zeros = len(next(x for x in sweep['panels'] if x['name'] == label)['zero_triples'])
            assert valid_zero == expected_zeros
            if label == 'witness':
                assert witness_rectangle is not None and witness_rectangle['valid_zeros'] == 1
            row = {'low_bits_per_slot': bits, 'free_bits': 3*bits,
                   'rectangles': len(groups)**3, 'full_cube_evaluations': len(groups)**3 * size**3,
                   'valid_triples': valid_triples,
                   'full_certified_rectangles': full_certified,
                   'valid_certified_rectangles': valid_certified,
                   'full_certified_valid_triples': full_covered,
                   'valid_certified_valid_triples': valid_covered,
                   'full_zero_rectangles': full_zero,
                   'valid_zero_rectangles': valid_zero,
                   'full_rank_histogram': dict(sorted(full_rank.items())),
                   'valid_rank_histogram': dict(sorted(valid_rank.items())),
                   'certificate_examples': examples,
                   'witness_rectangle': witness_rectangle,
                   'analysis_ns': time.monotonic_ns() - start}
            panel['widths'].append(row)
            print(label, 'bits', bits, 'full_cert', full_certified, 'valid_cert', valid_certified,
                  'rectangles', row['rectangles'], flush=True)
        panel['peak_self_rss_raw'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        panels.append(panel)
        del grid
    result = {'status': 'PASS_N41_TRACE_RECTANGLE_RANK_SURVEY',
              'candidate_id': None, 'curve_id': geo['curve_id'],
              'protocol_sha256': sha(protocol_path),
              'source_sha256': protocol['source_sha256'],
              'panels': panels,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
