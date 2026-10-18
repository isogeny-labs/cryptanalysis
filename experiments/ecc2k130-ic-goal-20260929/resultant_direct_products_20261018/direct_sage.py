"""Derive four second pair products from four first pair curve states."""
import hashlib
import itertools
import json
import statistics
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup_field(degree):
    P = PolynomialRing(GF(2), 'u')
    u = P.gen()
    modulus = (u**41+u**3+1) if degree == 41 else (u**131+u**13+u**2+u+1)
    K = GF(2**degree, name='u', modulus=modulus)
    E = EllipticCurve(K, [1, 0, 0, 0, 1])

    def dec(value):
        return K(P([(value >> i) & 1 for i in range(degree)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    return K, E, dec, enc


def halftrace(value, degree):
    field = value.parent()
    result = field.zero()
    term = value
    for _ in range((degree+1)//2):
        result += term
        term = term**4
    assert result*result+result == value
    return result


def source_points(E, dec, enc, degree, code, bits, seed_mask, rotation):
    mask = sum(1 << bits[j] for j in range(len(bits)) if code >> j & 1)
    companion = mask ^ seed_mask
    a, b = dec(mask << 1), dec(companion << 1)
    assert a and b and a+b == dec(seed_mask << 1)
    assert a.trace() == 0 and b.trace() == 0
    assert (1/a).trace() == 0 and (1/b).trace() == 0

    def options(parameter):
        root = halftrace(parameter, degree)
        assert root
        x = 1+1/root
        points = sorted(E.lift_x(x, all=True), key=lambda point: enc(point[1]))
        assert len(points) == 2
        return points

    aa, bb = options(a), options(b)
    states = []
    for i, j in itertools.product(range(2), repeat=2):
        pair = aa[i]+bb[j]
        assert pair != E(0)
        rotated = E(pair[0]**(1 << rotation), pair[1]**(1 << rotation))
        assert rotated != E(0)
        states.append(rotated)
    assert len({(enc(point[0]), enc(point[1])) for point in states}) == 4
    return states, [mask, companion]


def decode_basis(basis):
    pivots = {}
    for j, value in enumerate(basis):
        word, code = value, 1 << j
        while word:
            bit = word.bit_length()-1
            if bit not in pivots:
                pivots[bit] = (word, code)
                break
            pivot, pivot_code = pivots[bit]
            word ^= pivot
            code ^= pivot_code
        assert word

    def decode(value):
        code = 0
        while value:
            bit = value.bit_length()-1
            if bit not in pivots:
                return None
            pivot, pivot_code = pivots[bit]
            value ^= pivot
            code ^= pivot_code
        return code

    return decode


def inputs(cfg, degree):
    if degree == 41:
        lines = (WORKSPACE / cfg['n41_input']).read_text().splitlines()
        assert lines[0] == 'FREECODE 25 281 13'
        sources, targets = {}, {}
        for line in lines[1:]:
            row = line.split()
            if row[0] == 'P':
                sources[int(row[1])] = (int(row[2]), int(row[3]))
            elif row[0] == 'T':
                targets[int(row[1])] = {'point': [int(row[2]), int(row[3])], 'terms': []}
            elif row[0] == 'C':
                targets[int(row[1])]['terms'].append(tuple(map(int, row[2:])))
        assert len(sources) == 281
        return sources, targets
    source = json.loads((WORKSPACE / cfg['n131_input']).read_text())
    targets = {i: {'point': row['point'],
                   'terms': [tuple(term) for term in row['terms']]}
               for i, row in enumerate(source['rows'])}
    return None, targets


def poly_eval(K, dec, terms, p, q):
    pp = [K.one(), p, p*p, p*p*p, p*p*p*p]
    qq = [K.one(), q, q*q, q*q*q, q*q*q*q]
    return sum((dec(c)*pp[i]*qq[j] for i, j, c in terms), K.zero())


def run(degree, cfg):
    root_result = json.loads((HERE / f'n{degree}_root_result.json').read_text())
    assert root_result['status'] == ('PASS_N41_QUARTIC_ROOT_CONTROL'
                                     if degree == 41 else 'PASS_N131_QUARTIC_ROOT_PANEL')
    K, E, dec, enc = setup_field(degree)
    seed_mask = 56 if degree == 41 else 898618
    bits = ([0, 1, 2, 3, 4, 6, 7, 8, 9, 10] if degree == 41
            else [bit for bit in range(33) if bit != seed_mask.bit_length()-1])
    r1, r2 = (12, 24) if degree == 41 else (0, 18)
    seed = dec(seed_mask << 1)
    h = halftrace(seed, degree)
    H = h*h
    C = 1+H
    H2, C2 = H**(1 << r2), C**(1 << r2)
    assert H2 and C2
    sources, targets = inputs(cfg, degree)
    codes = sorted(sources) if degree == 41 else sorted({row['first_code'] for row in root_result['rows']})

    if degree == 41:
        q_to_code = {q: code for code, (_p, q) in sources.items()}
        assert len(q_to_code) == len(sources)

        def decode(q):
            return q_to_code.get(q)

        def valid(code):
            return code in sources
    else:
        masks = [dec(1 << (bit+1)) for bit in bits]
        basis = [(a*a+seed*a)**(1 << r2) for a in masks]
        decode = decode_basis([enc(value) for value in basis])

        def valid(code):
            a = sum((masks[j] for j in range(len(bits)) if code >> j & 1), K.zero())
            return bool(a and a+seed and a.trace() == 0 and
                        (1/a).trace() == 0 and (1/(a+seed)).trace() == 0)

    state_started = time.monotonic()
    states = {}
    source_masks = {}
    for code in codes:
        choices, masks_pair = source_points(E, dec, enc, degree, code,
                                           bits, seed_mask, r1)
        states[code] = choices
        source_masks[code] = masks_pair
        if degree == 41:
            a = dec(masks_pair[0] << 1)
            product = (a*(a+seed))**(1 << r1)
            assert enc(product) == sources[code][0]
    state_seconds = time.monotonic()-state_started

    reference = {(row['target_index'], row['first_code']): row
                 for row in root_result['rows']}
    rows = []
    for target_index in (0, 1):
        target = E(*(dec(v) for v in targets[target_index]['point']))
        assert target != E(0)
        for number, code in enumerate(codes):
            started = time.monotonic()
            products = []
            exceptions = []
            for branch, first_pair in enumerate(states[code]):
                residual = target-first_pair
                if residual == E(0):
                    exceptions.append({'branch': branch, 'kind': 'IDENTITY'})
                    continue
                x = residual[0]
                if not x:
                    exceptions.append({'branch': branch, 'kind': 'ZERO_X'})
                    continue
                q = C2*(1/x)+H2*x
                products.append((branch, q))
            derivation_seconds = time.monotonic()-started
            started = time.monotonic()
            hits = []
            for branch, q in products:
                second_code = decode(enc(q))
                if second_code is not None:
                    hits.append({'second_code': second_code,
                                 'valid_source': bool(valid(second_code)),
                                 'distinct': second_code != code})
            decode_seconds = time.monotonic()-started
            started = time.monotonic()
            if not exceptions:
                assert len(products) == 4
                assert len({enc(q) for _branch, q in products}) == 4
            if degree == 41:
                p = dec(sources[code][0])
            else:
                a = dec(source_masks[code][0] << 1)
                p = a*(a+seed)
            for _branch, q in products:
                assert poly_eval(K, dec, targets[target_index]['terms'], p, q) == 0
            expected = reference[(target_index, code)]
            assert expected['quartic_degree'] == 4
            assert expected['field_roots'] == 4
            assert not exceptions
            assert sorted(hits, key=lambda item: item['second_code']) == sorted(
                expected['span_root_hits'], key=lambda item: item['second_code'])
            check_seconds = time.monotonic()-started
            rows.append({'target_index': target_index, 'first_code': code,
                         'q_products': [enc(q) for _branch, q in products],
                         'span_root_hits': hits, 'exceptions': exceptions,
                         'derivation_seconds': derivation_seconds,
                         'decode_seconds': decode_seconds,
                         'check_seconds': check_seconds})
            if number % 32 == 0:
                print(json.dumps({'event': 'PROGRESS', 'degree': degree,
                                  'target_index': target_index,
                                  'first_codes_done': number+1}), flush=True)
    assert len(rows) == 2*len(codes)
    output = {'status': 'PASS_DIRECT_FOUR_PRODUCT_REPLAY',
              'candidate_id': None, 'degree': degree,
              'curve_id': cfg['n41_curve_id'] if degree == 41 else cfg['n131_curve_id'],
              'first_codes': len(codes), 'target_indices': [0, 1],
              'state_setup_seconds': state_seconds,
              'target_derivation_seconds': sum(row['derivation_seconds'] for row in rows),
              'span_decode_seconds': sum(row['decode_seconds'] for row in rows),
              'verification_seconds': sum(row['check_seconds'] for row in rows),
              'median_derivation_seconds': statistics.median(row['derivation_seconds'] for row in rows),
              'rows': rows,
              'protocol_sha256': sha(HERE / 'protocol.json')}
    return output


def main():
    degree = int(sys.argv[1])
    assert degree in (41, 131)
    if degree == 131:
        gate = json.loads((HERE / 'n131_gate.json').read_text())
        assert gate['status'] == 'FROZEN_AFTER_N41_DIRECT_REPLAY'
        for name, expected in gate['sources'].items():
            path = Path(name)
            if not path.is_absolute():
                path = WORKSPACE / path
            assert sha(path) == expected, name
        control = json.loads((HERE / 'n41_result.json').read_text())
        assert control['status'] == 'PASS_DIRECT_FOUR_PRODUCT_REPLAY'
        assert control['first_codes'] == 281
    cfg = json.loads((HERE / 'protocol.json').read_text())
    for name, expected in cfg['sources'].items():
        path = Path(name)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert sha(path) == expected, name
    path = HERE / f'n{degree}_result.json'
    assert not path.exists()
    started = time.monotonic()
    result = run(degree, cfg)
    result['wall_seconds'] = time.monotonic()-started
    path.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'degree', 'first_codes', 'wall_seconds',
                       'state_setup_seconds', 'target_derivation_seconds',
                       'span_decode_seconds', 'verification_seconds')},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
