"""Independent binary replay and selected direct field evaluations."""
from collections import Counter
import hashlib
import itertools
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
RECTANGLE = ROOT / 'n41_trace_rectangle_certificate_20261017'
MASK = (1 << 41) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mul(a, b):
    result = 0
    for _ in range(41):
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a >> 41:
            a = (a & MASK) ^ 9
    return result


def powers(x, last):
    out = [1]
    for _ in range(last):
        out.append(mul(out[-1], x))
    return out


def product(geometry, slot, code):
    result = 0
    for index, vector in enumerate(geometry['blocks'][slot]['product_basis']):
        if code >> index & 1:
            result ^= vector
    return result


def flats(legal):
    allowed = set(legal)
    found = set()
    for anchor in legal:
        others = [x for x in legal if x > anchor]
        for x, y, z in itertools.combinations(others, 3):
            u, v, w = x ^ anchor, y ^ anchor, z ^ anchor
            cube = {anchor, x, y, z, anchor ^ u ^ v, anchor ^ u ^ w,
                    anchor ^ v ^ w, anchor ^ u ^ v ^ w}
            if len(cube) == 8 and cube <= allowed:
                found.add(tuple(sorted(cube)))
    return sorted(found)


def rank_and_separator(values):
    base = values[0]
    basis = {}
    for value in values[1:]:
        v = value ^ base
        while v:
            pivot = v.bit_length() - 1
            if pivot in basis:
                v ^= basis[pivot]
            else:
                basis[pivot] = v
                break
    v = base
    while v:
        pivot = v.bit_length() - 1
        if pivot in basis:
            v ^= basis[pivot]
        else:
            break
    return len(basis), v != 0


def direct_block(geometry, tensor, codes):
    products = [[product(geometry, slot, code) for code in group]
                for slot, group in enumerate(codes)]
    terms = tensor['coefficient_terms']
    result = []
    for p in products[0]:
        pp = powers(p, 16)
        specialized = [(qi, ri, reduce_xor(mul(pp[pi], c) for pi, c in coeff))
                       for qi, ri, coeff in terms]
        for q in products[1]:
            qq = powers(q, 16)
            cp = [0] * 25
            for qi, ri, value in specialized:
                cp[ri] ^= mul(qq[qi], value)
            for r in products[2]:
                value = 0
                for coefficient in reversed(cp):
                    value = mul(value, r) ^ coefficient
                result.append(value)
    return result


def reduce_xor(values):
    out = 0
    for value in values:
        out ^= value
    return out


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    result_path = HERE / 'result.json'
    result = json.loads(result_path.read_text())
    paths = {'run.py': HERE / 'run.py', 'protocol.json': HERE / 'protocol.json',
             'geometry.json': GEOMETRY, 'sweep_result.json': SOURCE / 'sweep_result.json',
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json',
             'rectangle_verification.json': RECTANGLE / 'verification.json'}
    assert result['status'] == 'PASS_N41_VALID_AFFINE_FLAT_TARGET_SURVEY'
    assert result['source_sha256'] == {name: sha(path) for name, path in paths.items()}
    assert result['candidate_id'] is None
    assert result['peak_self_rss_raw'] < protocol['resource_envelope']['rss_boundary_bytes']
    geometry = json.loads(GEOMETRY.read_text())
    legal = sorted(geometry['permitted_canonical_a'])
    found = flats(legal)
    assert len(found) == 8 and found == [tuple(row) for row in result['flats']]
    covered = set().union(*(set(flat) for flat in found))
    assert len(covered) == 27 and sorted(covered) == result['covered_masks']
    allowed = set(legal)
    assert not any(set(flat).isdisjoint({x ^ d for x in flat})
                   and {x ^ d for x in flat} <= allowed
                   for flat in found for d in range(1, 256))
    assert result['four_flat_count'] == 0
    assert result['blocks_per_panel'] == 512
    cube_codes = []
    for flat, (anchor, directions) in zip(found, result['canonical_bases']):
        codes = [anchor ^ reduce_xor(d for i, d in enumerate(directions) if bits >> i & 1)
                 for bits in range(8)]
        assert sorted(codes) == list(flat)
        cube_codes.append(codes)
    index = {code: i for i, code in enumerate(legal)}
    checks = []
    for panel in result['panels']:
        label = panel['label']
        grid_path = HERE / ('grid_' + label + '.bin')
        data = grid_path.read_bytes()
        assert len(data) == 40**3 * 8 == panel['grid_bytes']
        assert sha(grid_path) == panel['grid_sha256']
        grid = struct.unpack('<' + 'Q' * 40**3, data)
        assert all(value <= MASK for value in grid)
        def lookup(x, y, z):
            return grid[(index[x]*40 + index[y])*40 + index[z]]
        histogram = Counter()
        certified = zero_blocks = zero_assignments = 0
        witnesses = []
        for i, j, k in itertools.product(range(8), repeat=3):
            values = [lookup(x, y, z) for x, y, z in itertools.product(
                cube_codes[i], cube_codes[j], cube_codes[k])]
            rank, separated = rank_and_separator(values)
            histogram[rank] += 1
            certified += int(separated)
            zero_blocks += int(0 in values)
            zero_assignments += values.count(0)
            if 0 in values:
                witnesses.append([i, j, k])
            if (i, j, k) == (0, 0, 0):
                assert panel['example'] == {
                    'flat_indices': [0, 0, 0], 'rank': rank,
                    'has_separator': separated, 'first_value': values[0],
                    'value_sha256': hashlib.sha256(json.dumps(values).encode()).hexdigest()}
        assert dict(sorted(histogram.items())) == {int(k): v for k, v in panel['rank_histogram'].items()}
        assert certified == panel['certified_blocks'] == 0
        assert zero_blocks == panel['zero_blocks']
        assert zero_assignments == panel['zero_assignments_with_multiplicity']
        assert witnesses == panel['zero_block_indices']
        selected = [[0, 0, 0]]
        if label == 'witness':
            selected.append(witnesses[0])
        else:
            selected.append(result['panels'][0]['zero_block_indices'][0])
        tensor = json.loads((SOURCE / (label + '_result_v2.json')).read_text())
        for i, j, k in selected:
            codes = [cube_codes[i], cube_codes[j], cube_codes[k]]
            actual = direct_block(geometry, tensor, codes)
            frozen = [lookup(x, y, z) for x, y, z in itertools.product(*codes)]
            assert actual == frozen
            assert rank_and_separator(actual) == (41, False)
            checks.append({'label': label, 'flat_indices': [i, j, k],
                           'field_values_checked': len(actual), 'zeros': actual.count(0)})
    receipt = {'status': 'PASS_INDEPENDENT_N41_AFFINE_FLAT_REPLAY',
               'result_sha256': sha(result_path), 'verifier_sha256': sha(Path(__file__)),
               'blocks_checked_per_panel': 512, 'direct_field_checks': checks}
    (HERE / 'verification.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(receipt['status'], len(checks), flush=True)


if __name__ == '__main__':
    main()
