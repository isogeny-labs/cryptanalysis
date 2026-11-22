#!/usr/bin/env sage -python
"""Exact N41 target-conditioned linear certificates on all-valid affine flats."""
from collections import Counter
import hashlib
import itertools
import json
import resource
import signal
import struct
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
RECTANGLE = ROOT / 'n41_trace_rectangle_certificate_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def affine_flats(masks, dimension):
    valid = set(masks)
    flats = set()
    for anchor in masks:
        directions = [v ^ anchor for v in masks if v != anchor]
        for basis in itertools.combinations(directions, dimension):
            points = {anchor}
            for direction in basis:
                points |= {point ^ direction for point in tuple(points)}
            if len(points) == 1 << dimension and points <= valid:
                flats.add(tuple(sorted(points)))
    return sorted(flats)


def canonical_basis(flat):
    anchor = flat[0]
    basis = []
    points = {anchor}
    for code in flat[1:]:
        direction = code ^ anchor
        if code not in points:
            basis.append(direction)
            points |= {point ^ direction for point in tuple(points)}
    assert len(basis) == 3 and points == set(flat)
    return anchor, basis


def affine_test(values):
    constant = values[0]
    basis = {}
    for vector in values[1:]:
        vector ^= constant
        for pivot in sorted(basis, reverse=True):
            if vector >> pivot & 1:
                vector ^= basis[pivot]
        if vector:
            basis[vector.bit_length() - 1] = vector
    vector = constant
    for pivot in sorted(basis, reverse=True):
        if vector >> pivot & 1:
            vector ^= basis[pivot]
    return len(basis), vector != 0


def main():
    signal.alarm(300)
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['resource_envelope']['alarm_seconds'] == 300
    assert protocol['panels'] == ['witness', 'negative']
    files = {'run.py': Path(__file__), 'protocol.json': HERE / 'protocol.json',
             'geometry.json': GEOMETRY, 'sweep_result.json': SOURCE / 'sweep_result.json',
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
             'rectangle_verification.json': RECTANGLE / 'verification.json'}
    source_sha256 = {name: sha(path) for name, path in files.items()}
    geometry = json.loads(GEOMETRY.read_text())
    masks = sorted(geometry['permitted_canonical_a'])
    assert len(masks) == 40
    flats = affine_flats(masks, 3)
    four_flats = affine_flats(masks, 4)
    assert len(flats) == 8 and len(four_flats) == 0
    covered = set().union(*(set(flat) for flat in flats))
    assert len(covered) == 27
    F2 = PolynomialRing(GF(2), 't')
    t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41 + t**3 + 1)
    def dec(value):
        return field(F2([(int(value) >> i) & 1 for i in range(41)]))
    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))
    def product(slot, mask):
        out = 0
        for i, vector in enumerate(geometry['blocks'][slot]['product_basis']):
            if mask >> i & 1:
                out ^= vector
        return dec(out)
    products = [[product(slot, mask) for mask in masks] for slot in range(3)]
    indices = {mask: i for i, mask in enumerate(masks)}
    bases = [canonical_basis(flat) for flat in flats]
    cube_codes = []
    for anchor, directions in bases:
        cube_codes.append([anchor ^ (directions[0] if i & 1 else 0)
                           ^ (directions[1] if i & 2 else 0)
                           ^ (directions[2] if i & 4 else 0) for i in range(8)])
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    panels = []
    for label in protocol['panels']:
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())
        terms = [(qi, ri, [(pi, dec(c)) for pi, c in coeff])
                 for qi, ri, coeff in tensor['coefficient_terms']]
        start = time.monotonic_ns()
        grid = [[[0 for _ in masks] for _ in masks] for _ in masks]
        qpower = [[value**i for i in range(17)] for value in products[1]]
        for ip, pvalue in enumerate(products[0]):
            pp = [pvalue**i for i in range(17)]
            specialized = [(qi, ri, sum((c*pp[pi] for pi, c in coeff), field.zero()))
                           for qi, ri, coeff in terms]
            for iq, qp in enumerate(qpower):
                cp = [field.zero()] * 25
                for qi, ri, c in specialized:
                    cp[ri] += c*qp[qi]
                for ir, rvalue in enumerate(products[2]):
                    value = field.zero()
                    for c in reversed(cp):
                        value = value*rvalue + c
                    grid[ip][iq][ir] = enc(value)
        grid_ns = time.monotonic_ns() - start
        grid_path = HERE / ('grid_' + label + '.bin')
        grid_path.write_bytes(b''.join(struct.pack('<Q', value)
                                      for plane in grid for row in plane for value in row))
        grid_sha256 = sha(grid_path)
        rank_histogram = Counter()
        certified = zero_blocks = zero_assignments = 0
        witnesses = []
        begin = time.monotonic_ns()
        for i, j, k in itertools.product(range(len(flats)), repeat=3):
            a, b, c = cube_codes[i], cube_codes[j], cube_codes[k]
            values = [grid[indices[x]][indices[y]][indices[z]]
                      for x, y, z in itertools.product(a, b, c)]
            rank, has_separator = affine_test(values)
            rank_histogram[rank] += 1
            certified += int(has_separator)
            zero_blocks += int(0 in values)
            zero_assignments += values.count(0)
            if 0 in values:
                witnesses.append([i, j, k])
            if (i, j, k) == (0, 0, 0):
                example = {'flat_indices': [i, j, k], 'rank': rank,
                           'has_separator': has_separator, 'first_value': values[0],
                           'value_sha256': hashlib.sha256(json.dumps(values).encode()).hexdigest()}
        expected = len(next(x for x in sweep['panels'] if x['name'] == label)['zero_triples'])
        assert zero_assignments == expected * (18 if label == 'witness' else 0)
        if label == 'witness':
            assert len(witnesses) == 18 and zero_blocks == 18
        else:
            assert not witnesses
        panels.append({'label': label, 'grid_ns': grid_ns, 'grid_sha256': grid_sha256,
                       'grid_bytes': grid_path.stat().st_size,
                       'analysis_ns': time.monotonic_ns()-begin,
                       'rank_histogram': dict(sorted(rank_histogram.items())),
                       'certified_blocks': certified, 'zero_blocks': zero_blocks,
                       'zero_assignments_with_multiplicity': zero_assignments,
                       'zero_block_indices': witnesses, 'example': example})
        print(label, panels[-1], flush=True)
    result = {'status': 'PASS_N41_VALID_AFFINE_FLAT_TARGET_SURVEY',
              'candidate_id': None, 'source_sha256': source_sha256,
              'flats': flats, 'canonical_bases': bases,
              'covered_masks': sorted(covered), 'three_flat_count': len(flats),
              'four_flat_count': len(four_flats), 'blocks_per_panel': len(flats)**3,
              'panels': panels, 'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
