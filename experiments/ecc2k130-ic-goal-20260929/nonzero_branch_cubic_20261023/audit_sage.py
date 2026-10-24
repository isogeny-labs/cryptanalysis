"""Independent Sage audit of branch products and positive resultant roots."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'protocol.json').read_text())
for path, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path


def instance(degree):
    R = PolynomialRing(GF(2), 'u')
    u = R.gen()
    modulus = u**41 + u**3 + 1 if degree == 41 else u**131 + u**13 + u**2 + u + 1
    K = GF(2**degree, name='u', modulus=modulus)

    def dec(value):
        return K(R([(int(value) >> i) & 1 for i in range(degree)]))

    if degree == 41:
        path = ROOT / 'n41_w11_freecode_resultant_20261018/resultant_input.tsv'
        lines = path.read_text().splitlines()
        assert lines[0] == 'FREECODE 25 281 13'
        products = {}
        for line in lines[1:282]:
            tag, code, p, q = line.split()
            assert tag == 'P'
            products[int(code)] = (dec(p), dec(q))
        terms = []
        for index in (0, 1):
            pos = 1 + 281 + index * 14
            assert lines[pos].split()[0:2] == ['T', str(index)]
            terms.append([(int(i), int(j), dec(c))
                          for _, _, i, j, c in (line.split() for line in lines[pos+1:pos+14])])
        seed = dec(112)
        bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
        rotations = (12, 24)
        return K, dec, seed, bits, rotations, products, terms
    data = json.loads((ROOT / 'n131_w33_freecode_resultant_20261018/coefficients.json').read_text())
    seed_mask = 898618
    bits = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    terms = [[(int(i), int(j), dec(c)) for i, j, c in row['terms']] for row in data['rows'][:2]]
    return K, dec, dec(seed_mask << 1), bits, (0, 18), None, terms


def product(K, dec, seed, bits, rotation, code):
    a = K.zero()
    for i, bit in enumerate(bits):
        if (code >> i) & 1:
            a += dec(1 << (bit + 1))
    return a, (a * (a + seed)) ** (1 << rotation)


def evaluate(terms, p, q):
    return sum((c * p**i * q**j for i, j, c in terms), p.parent().zero())


rows = []
for degree, base, width in ((41, 225, 4), (131, 1, 3), (131, 1, 4)):
    K, dec, seed, bits, rotations, products, terms = instance(degree)
    codes = [base | sum(((local >> i) & 1) << (i + 1) for i in range(width))
             for local in range(1 << width)]
    computed = {}
    for code in codes:
        a, p = product(K, dec, seed, bits, rotations[0], code)
        assert a != 0 and a != seed and p != 0
        computed[code] = p
        if products is not None and code in products:
            assert p == products[code][0]
    positive_pair = (253, 63) if degree == 41 else (3, 16722)
    if positive_pair[0] in computed:
        _, q = product(K, dec, seed, bits, rotations[1], positive_pair[1])
        if products is not None:
            assert q == products[positive_pair[1]][1]
        assert evaluate(terms[0], computed[positive_pair[0]], q) == 0
    else:
        raise AssertionError('positive code missing from fixed branch')
    row = {'degree': degree, 'first_base_code': base, 'free_code_positions': list(range(1, width+1)),
           'nonzero_codes': len(codes), 'positive_pair': list(positive_pair), 'positive_resultant_zero': True}
    if degree == 41:
        zero_pairs = []
        ordinary_zeros = []
        for code in codes:
            p = computed[code]
            for right_code, (_, q) in products.items():
                if evaluate(terms[0], p, q) == 0:
                    zero_pairs.append([code, right_code])
                if evaluate(terms[1], p, q) == 0:
                    ordinary_zeros.append([code, right_code])
        assert zero_pairs == [[253, 63]] and ordinary_zeros == []
        row['positive_valid_code_roots'] = zero_pairs
        row['ordinary_valid_code_roots'] = ordinary_zeros
    rows.append(row)

replay = json.loads((ROOT / 'n131_w33_resultant_core_20261018/replay_result.json').read_text())
assert replay['status'] == 'PASS_INDEPENDENT_N131_CURVE_REPLAY'
assert replay['source_codes'] == [3, 16722]
out = {'status': 'PASS_SAGE_NONZERO_BRANCH_AUDIT', 'candidate_id': None, 'rows': rows,
       'n131_prior_group_replay_sha256': hashlib.sha256((ROOT / 'n131_w33_resultant_core_20261018/replay_result.json').read_bytes()).hexdigest()}
with (HERE / 'audit_result.json').open('x') as stream:
    json.dump(out, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(out['status'])
