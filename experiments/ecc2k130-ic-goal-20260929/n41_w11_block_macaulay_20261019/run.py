"""Degree-bounded Macaulay certificates for blocks of two free W11 codes."""
import hashlib
import json
import resource
import sys
import time
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'n41_n131_macaulay_family_gate_20261019'))
from macaulay import Field, source_basis, source_value, evaluate_resultant, monomials

INPUT = ROOT / 'n41_w11_freecode_resultant_20261018' / 'resultant_input.tsv'
F = Field(41, 9)
POSITIONS = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
LEFT = source_basis(F, 112, POSITIONS, 12)
RIGHT = source_basis(F, 112, POSITIONS, 24)
WIDTH = 2
VARIABLES = WIDTH + 10


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def poly_mul(left, right):
    out = {}
    for m, a in left.items():
        for n, b in right.items():
            key = m | n
            out[key] = out.get(key, 0) ^ F.mul(a, b)
    return {m: v for m, v in out.items() if v}


def poly_square(poly):
    return {m: F.square(value) for m, value in poly.items()}


def poly_powers(poly):
    two = poly_square(poly)
    return [{0: 1}, poly, two, poly_mul(poly, two), poly_square(two)]


def product_anf(terms, anchor):
    assert anchor & 3 == 0
    p0 = source_value(anchor, LEFT)
    p = {0: p0, 1: LEFT[0], 2: LEFT[1]}
    q = {1 << (WIDTH + bit): value for bit, value in enumerate(RIGHT)}
    pp, qq = poly_powers(p), poly_powers(q)
    result = {}
    for (i, j), scalar in terms.items():
        for mask, value in poly_mul(pp[i], qq[j]).items():
            result[mask] = result.get(mask, 0) ^ F.mul(scalar, value)
    return {m: v for m, v in result.items() if v}


def evaluate_anf(poly, left_code, right_code):
    assignment = (left_code & 3) | (right_code << WIDTH)
    out = 0
    for mask, value in poly.items():
        if assignment & mask == mask:
            out ^= value
    return out


def coordinate_rows(poly):
    rows = [0] * F.n
    base = monomials(VARIABLES, 4)
    positions = {m: i for i, m in enumerate(base)}
    for monomial, value in poly.items():
        bitset = 1 << positions[monomial]
        while value:
            low = value & -value
            rows[low.bit_length() - 1] ^= bitset
            value ^= low
    return base, rows


def certificate(base, equations, degree):
    assert degree in (4, 5, 6)
    cols = monomials(VARIABLES, degree)
    index = {mask: i for i, mask in enumerate(cols)}
    factors = monomials(VARIABLES, degree - 4)
    rows = []
    specs = []
    for bit, eq in enumerate(equations):
        present = [i for i in range(len(base)) if eq >> i & 1]
        for factor in factors:
            row = 0
            for i in present:
                row ^= 1 << index[base[i] | factor]
            rows.append(row)
            specs.append((bit, factor))
    pivots = {}
    for row_id, row in enumerate(rows):
        value, combo = row, 1 << row_id
        while value:
            pivot = value.bit_length() - 1
            prior = pivots.get(pivot)
            if prior is None:
                pivots[pivot] = value, combo
                break
            value ^= prior[0]
            combo ^= prior[1]
    value, combo = 1, 0
    while value:
        pivot = value.bit_length() - 1
        prior = pivots.get(pivot)
        if prior is None:
            break
        value ^= prior[0]
        combo ^= prior[1]
    selected = None
    if not value:
        selected = [specs[i] for i in range(len(specs)) if combo >> i & 1]
        replay = 0
        for i in range(len(specs)):
            if combo >> i & 1:
                replay ^= rows[i]
        assert replay == 1
    return {'degree': degree, 'monomials': len(cols), 'equations': len(rows),
            'rank': len(pivots), 'reject': not value,
            'certificate_rows': selected}


def load_terms():
    products = {}
    targets = {}
    for line in INPUT.read_text().splitlines():
        row = line.split()
        if row[0] == 'P':
            products[int(row[1])] = int(row[2]), int(row[3])
        elif row[0] == 'C':
            targets.setdefault(int(row[1]), {})[int(row[2]), int(row[3])] = int(row[4])
    assert len(products) == 281 and len(targets) == 25
    for code, (p, q) in products.items():
        assert source_value(code, LEFT) == p
        assert source_value(code, RIGHT) == q
    return targets


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_N41_W11_BLOCK_MACAULAY'
    for item in protocol['sources'].values():
        assert sha(item['path']) == item['sha256']
    start = time.monotonic()
    targets = load_terms()
    results = []
    for target_index in protocol['target_indices']:
        for anchor in protocol['anchors']:
            begin = time.monotonic()
            poly = product_anf(targets[target_index], anchor)
            max_degree = max((m.bit_count() for m in poly), default=0)
            # Exact field evaluation checks the complete four-code block.
            roots = []
            for left_code in range(anchor, anchor + 4):
                for right_code in range(1024):
                    value = evaluate_anf(poly, left_code, right_code)
                    assert value == evaluate_resultant(F, targets[target_index],
                        source_value(left_code, LEFT), source_value(right_code, RIGHT))
                    if not value:
                        roots.append((left_code, right_code))
            base, equations = coordinate_rows(poly)
            levels = []
            for degree in (4, 5, 6):
                level_start = time.monotonic()
                result = certificate(base, equations, degree)
                result['wall_seconds'] = time.monotonic() - level_start
                assert not (roots and result['reject'])
                levels.append(result)
                if result['reject']:
                    break
            results.append({'target_index': target_index, 'anchor': anchor,
                            'roots': roots, 'anf_terms': len(poly),
                            'anf_degree': max_degree, 'levels': levels,
                            'wall_seconds': time.monotonic() - begin})
    out = {'status': 'COMPLETE_N41_W11_BLOCK_MACAULAY', 'candidate_id': None,
           'curve_id': protocol['curve_id'], 'protocol_sha256': sha(HERE / 'protocol.json'),
           'script_sha256': sha(__file__), 'input_sha256': sha(INPUT),
           'wall_seconds': time.monotonic() - start,
           'peak_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'results': results}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': out['status'], 'wall_seconds': out['wall_seconds'],
                      'cells': len(results), 'rejected': sum(any(l['reject'] for l in r['levels'])
                                                for r in results)}, sort_keys=True))


if __name__ == '__main__':
    main()
