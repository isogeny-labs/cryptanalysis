"""Exact affine-span block filter for N41 and N131 two-pair resultants."""
import hashlib
import json
import random
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BinaryField:
    def __init__(self, degree, modulus_tail):
        self.degree = degree
        self.high = 1 << degree
        self.tail = modulus_tail
        self.mask = self.high - 1

    def mul(self, a, b):
        assert 0 <= a <= self.mask and 0 <= b <= self.mask
        out = 0
        while b:
            if b & 1:
                out ^= a
            b >>= 1
            a <<= 1
            if a & self.high:
                a ^= self.high | self.tail
        return out

    def square(self, a):
        return self.mul(a, a)

    def frob(self, a, steps):
        for _ in range(steps):
            a = self.square(a)
        return a


def rank_basis(words):
    pivots = {}
    for word in words:
        while word:
            bit = word.bit_length()-1
            if bit not in pivots:
                pivots[bit] = word
                break
            word ^= pivots[bit]
    return pivots


def reduce(word, pivots):
    while word:
        bit = word.bit_length()-1
        if bit not in pivots:
            return word
        word ^= pivots[bit]
    return 0


def powers(F, value):
    return [1, value, F.square(value),
            F.mul(value, F.square(value)), F.square(F.square(value))]


def source_basis(F, bits, seed, rotations):
    unrotated = []
    for bit in bits:
        a = 1 << (bit+1)
        unrotated.append(F.square(a) ^ F.mul(seed, a))
    return [[F.frob(value, r) for value in unrotated] for r in rotations]


def product(basis, code):
    out = 0
    for j, value in enumerate(basis):
        if code >> j & 1:
            out ^= value
    return out


def evaluate(F, terms, p, q):
    pp, qq = powers(F, p), powers(F, q)
    value = 0
    for i, j, c in terms:
        value ^= F.mul(c, F.mul(pp[i], qq[j]))
    return value


def block_values(F, terms, basis_p, basis_q, code_p, code_q, width):
    low = (1 << width)-1
    base_p, base_q = code_p & ~low, code_q & ~low
    ps = [powers(F, product(basis_p, base_p | i)) for i in range(1 << width)]
    qs = [powers(F, product(basis_q, base_q | j)) for j in range(1 << width)]
    by_i = {i: [(j, c) for ii, j, c in terms if ii == i] for i in range(5)}
    values = []
    for qpow in qs:
        side = [0]*5
        for i in range(5):
            for j, c in by_i[i]:
                side[i] ^= F.mul(c, qpow[j])
        for ppow in ps:
            value = 0
            for i in range(5):
                value ^= F.mul(ppow[i], side[i])
            values.append(value)
    return values


def block_record(F, terms, basis_p, basis_q, code_p, code_q, width, label):
    outputs = block_values(F, terms, basis_p, basis_q, code_p, code_q, width)
    base = outputs[0]
    pivots = rank_basis([value ^ base for value in outputs[1:]])
    residual = reduce(base, pivots)
    return {'label': label, 'width_each': width,
            'base_codes': [code_p & ~((1 << width)-1),
                           code_q & ~((1 << width)-1)],
            'code_pairs_covered': len(outputs),
            'affine_direction_rank': len(pivots),
            'zero_in_affine_span': residual == 0,
            'base_value': base, 'membership_residual': residual,
            'actual_zero_count': outputs.count(0)}


def load_n41(path):
    lines = path.read_text().splitlines()
    assert lines[0] == 'FREECODE 25 281 13'
    products = {}
    rows = {}
    for line in lines[1:]:
        fields = line.split()
        if fields[0] == 'P':
            _, code, p1, p2 = fields
            products[int(code)] = (int(p1), int(p2))
        elif fields[0] == 'T':
            _, index, x, y = fields
            rows[int(index)] = {'point': [int(x), int(y)], 'terms': []}
        elif fields[0] == 'C':
            _, index, i, j, c = fields
            rows[int(index)]['terms'].append((int(i), int(j), int(c)))
        else:
            raise AssertionError(fields[0])
    assert len(products) == 281 and len(rows) == 25
    assert all(len(row['terms']) == 13 for row in rows.values())
    return products, rows


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    for name, digest in cfg['sources'].items():
        source = Path(name)
        if not source.is_absolute():
            source = WORKSPACE / source
        assert sha(source) == digest, name
    assert cfg['sample_seed'] == 10218 and cfg['random_blocks_per_width'] == 8
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda _s, _f: (_ for _ in ()).throw(TimeoutError('block probe cap')))
    signal.alarm(cfg['wall_cap_seconds'])

    F41 = BinaryField(41, (1 << 3) | 1)
    b41 = source_basis(F41, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10],
                       112, [12, 24])
    source41, rows41 = load_n41(WORKSPACE / cfg['n41_input'])
    assert all((product(b41[0], code), product(b41[1], code)) == pair
               for code, pair in source41.items())
    assert evaluate(F41, rows41[0]['terms'],
                    product(b41[0], 253), product(b41[1], 63)) == 0

    F131 = BinaryField(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    seed_mask = 898618
    bits131 = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
    b131 = source_basis(F131, bits131, seed_mask << 1, [0, 18])
    source131 = json.loads((WORKSPACE / cfg['n131_input']).read_text())
    rows131 = [{'point': row['point'],
                'terms': [tuple(term) for term in row['terms']]}
               for row in source131['rows']]
    checks = source131['positive_source_checks']
    assert product(b131[0], 3) == checks[0]['unrotated_product']
    assert F131.frob(product(b131[1], 16722), 113) == checks[1]['unrotated_product']
    assert evaluate(F131, rows131[0]['terms'],
                    product(b131[0], 3), product(b131[1], 16722)) == 0

    cases = []
    rng = random.Random(cfg['sample_seed'])
    for degree, F, basis, rows, positive_codes, widths in (
        (41, F41, b41, rows41, (253, 63), (1, 2, 3, 4)),
        (131, F131, b131, rows131, (3, 16722), (1, 2, 3, 4, 5))):
        code_bits = len(basis[0])
        for width in widths:
            for row_index in (0, 1):
                terms = rows[row_index]['terms']
                record = block_record(F, terms, *basis, *positive_codes,
                                      width, 'positive_code_family')
                record.update(field_degree=degree, target_index=row_index)
                if row_index == 0:
                    assert record['actual_zero_count'] >= 1
                    assert record['zero_in_affine_span']
                else:
                    assert record['actual_zero_count'] == 0
                cases.append(record)
                for sample in range(cfg['random_blocks_per_width']):
                    codes = (rng.randrange(1 << code_bits),
                             rng.randrange(1 << code_bits))
                    random_record = block_record(F, terms, *basis, *codes,
                                                 width, f'random_{sample}')
                    random_record.update(field_degree=degree, target_index=row_index)
                    if random_record['actual_zero_count']:
                        assert random_record['zero_in_affine_span']
                    cases.append(random_record)
        if degree == 41:
            for row_index in range(2, 25):
                record = block_record(F, rows[row_index]['terms'], *basis,
                                      *positive_codes, 2, 'positive_code_family')
                record.update(field_degree=degree, target_index=row_index)
                assert record['actual_zero_count'] == 0
                cases.append(record)

    signal.alarm(0)
    summary = {}
    for degree in (41, 131):
        summary[str(degree)] = {}
        for width in sorted({row['width_each'] for row in cases if row['field_degree'] == degree}):
            sample = [row for row in cases if row['field_degree'] == degree and
                      row['width_each'] == width and row['label'].startswith('random_')]
            summary[str(degree)][str(width)] = {
                'random_cases': len(sample),
                'rejected': sum(not row['zero_in_affine_span'] for row in sample),
                'min_rank': min(row['affine_direction_rank'] for row in sample),
                'max_rank': max(row['affine_direction_rank'] for row in sample)}
    result = {'status': 'PASS_RESULTANT_BLOCK_SPAN_PROBE',
              'candidate_id': None, 'n41_curve_id': cfg['n41_curve_id'],
              'n131_curve_id': cfg['n131_curve_id'],
              'cases': cases, 'summary': summary,
              'wall_seconds': time.monotonic()-started,
              'python_version': sys.version.split()[0],
              'protocol_sha256': sha(HERE / 'protocol.json')}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'wall_seconds': result['wall_seconds'],
                      'summary': summary}, sort_keys=True))


if __name__ == '__main__':
    main()
