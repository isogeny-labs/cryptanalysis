"""Rank the quartic ANF coefficient span of the frozen two-pair resultant."""
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'protocol.json').read_text())
for path, expected in cfg['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path


class BinaryField:
    def __init__(self, degree, reduction):
        self.degree = degree
        self.mask = (1 << degree) - 1
        self.reduction = reduction

    def mul(self, a, b):
        assert 0 <= a <= self.mask and 0 <= b <= self.mask
        out = 0
        while b:
            if b & 1:
                out ^= a
            b >>= 1
            a <<= 1
            if a >> self.degree:
                a = (a & self.mask) ^ self.reduction
        return out

    def square(self, a):
        return self.mul(a, a)

    def frob(self, a, steps):
        for _ in range(steps):
            a = self.square(a)
        return a


def rank_with_pivots(vectors):
    pivots = {}
    selected = []
    for label, value in vectors:
        w = value
        while w:
            bit = w.bit_length() - 1
            if bit not in pivots:
                pivots[bit] = w
                selected.append({'label': label, 'value': value, 'pivot_bit': bit})
                break
            w ^= pivots[bit]
    return len(pivots), selected


def basis_products(field, seed, positions, rotation):
    out = []
    for bit in positions:
        a = 1 << (bit + 1)
        out.append(field.frob(field.square(a) ^ field.mul(seed, a), rotation))
    return out


def pair_coeff(field, basis, i, j):
    ai, aj = basis[i], basis[j]
    return field.mul(field.square(ai), aj) ^ field.mul(ai, field.square(aj))


def coeff33_n41(index):
    lines = (ROOT / 'n41_w11_freecode_resultant_20261018' / 'resultant_input.tsv').read_text().splitlines()
    assert lines[0] == 'FREECODE 25 281 13'
    pos = 1 + 281 + index * 14
    target = list(map(int, lines[pos].split()[1:]))
    assert target[0] == index
    terms = []
    for line in lines[pos+1:pos+14]:
        tag, row, i, j, c = line.split()
        assert tag == 'C' and int(row) == index
        terms.append((int(i), int(j), int(c)))
    assert len(terms) == 13
    return target[1:], dict(((i, j), c) for i, j, c in terms)[(3, 3)]


def coeff33_n131(index):
    data = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018' / 'coefficients.json').read_text())
    row = data['rows'][index]
    return row['point'], dict(((i, j), c) for i, j, c in row['terms'])[(3, 3)]


started = time.monotonic()
rows = []
for degree in (41, 131):
    if degree == 41:
        field = BinaryField(41, (1 << 3) | 1)
        seed, positions, rotations = 112, [0, 1, 2, 3, 4, 6, 7, 8, 9, 10], (12, 24)
        coeff = coeff33_n41
        widths = [2, 3, 4, 5]
    else:
        field = BinaryField(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
        seed_mask = 898618
        seed = seed_mask << 1
        positions = [i for i in range(33) if i != seed_mask.bit_length()-1]
        rotations = (0, 18)
        coeff = coeff33_n131
        widths = [2, 3, 4]
    p_basis = basis_products(field, seed, positions, rotations[0])
    q_basis = basis_products(field, seed, positions, rotations[1])
    p_pairs = [(i, j, pair_coeff(field, p_basis, i, j))
               for i in range(len(positions)) for j in range(i+1, len(positions))]
    q_pairs = [(i, j, pair_coeff(field, q_basis, i, j))
               for i in range(len(positions)) for j in range(i+1, len(positions))]
    q_rank, q_pivots = rank_with_pivots(((i, j), value) for i, j, value in q_pairs)
    for target_index in (0, 1):
        target, c33 = coeff(target_index)
        assert c33 != 0
        block_ranks = []
        for k in widths:
            terms = []
            for i, j, a in p_pairs:
                if j >= k:
                    continue
                for u, v, b in q_pairs:
                    terms.append(((i, j, u, v), field.mul(c33, field.mul(a, b))))
            rank, pivots = rank_with_pivots(terms)
            block_ranks.append({'first_free_bits': k, 'quartic_monomials': len(terms),
                                'coefficient_rank': rank,
                                'pivot_labels': [entry['label'] for entry in pivots]})
        rows.append({'field_degree': degree, 'target_index': target_index,
                     'target_point': target, 'c33': c33,
                     'p_first_pair_coefficient': p_pairs[0][2],
                     'q_pair_count': len(q_pairs), 'q_pair_rank': q_rank,
                     'q_pair_pivots': q_pivots,
                     'block_ranks': block_ranks})
out = {'status': 'COMPLETE_RESULTANT_TOPDEGREE_RANK', 'candidate_id': None,
       'rows': rows, 'wall_seconds': time.monotonic()-started,
       'protocol_sha256': hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest()}
(HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
print(json.dumps({'status': out['status'], 'wall_seconds': out['wall_seconds'],
                  'ranks': [(r['field_degree'], r['target_index'], r['q_pair_rank'],
                             [(b['first_free_bits'], b['coefficient_rank']) for b in r['block_ranks']])
                            for r in rows]}, sort_keys=True))
