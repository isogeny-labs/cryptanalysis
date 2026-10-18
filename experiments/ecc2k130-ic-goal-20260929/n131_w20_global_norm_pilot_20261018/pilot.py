"""Bounded valid-W20 global resultant norm on frozen N131 points."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SUPPORT = ROOT / 'n131_w20_sevenpair_gate_20261010/support_w20.tsv'
COEFF = ROOT / 'n131_w33_freecode_resultant_20261018/coefficients.json'
PROTO = HERE / 'protocol.json'
SEED = 898618


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def product_tree(polys, one):
    layer = polys
    while len(layer) > 1:
        layer = [layer[i] * layer[i + 1] if i + 1 < len(layer) else layer[i]
                 for i in range(0, len(layer), 2)]
    return layer[0] if layer else one


def main():
    proto = json.loads(PROTO.read_text())
    for label, path in [('pilot.py', Path(__file__)), ('support_w20.tsv', SUPPORT),
                        ('coefficients.json', COEFF), ('sage_runtime_info.json', HERE / 'sage_runtime_info.json')]:
        assert sha(path) == proto['source_sha256'][label], label
    assert proto['worker_count'] == 1
    signal.alarm(proto['child_alarm_seconds'])
    start = time.monotonic_ns()
    F2 = PolynomialRing(GF(2), 'u')
    u = F2.gen()
    K = GF(2**131, name='u', modulus=u**131 + u**13 + u**2 + u + 1)
    R = PolynomialRing(K, 'P')
    P = R.gen()

    def dec(n):
        return K(F2([(n >> i) & 1 for i in range(131)]))

    def enc(x):
        return sum(int(bit) << i for i, bit in enumerate(x.polynomial().list()))

    cols = {}
    for line in SUPPORT.read_text().splitlines():
        mask, col, _ = map(int, line.split())
        assert mask not in cols
        cols[mask] = col
    pivot = SEED.bit_length() - 1
    valid = {}
    for mask, col in cols.items():
        other = mask ^ SEED
        if mask < other and other in cols and col != cols[other]:
            code = (mask & ((1 << pivot) - 1)) | ((mask >> (pivot + 1)) << pivot)
            valid[code] = mask
    assert len(valid) == 132045
    chosen = sorted(valid)[:proto['subset_size'] - 1]
    assert 16722 not in chosen
    chosen.append(16722)
    chosen.sort()
    assert 3 in chosen and len(chosen) == proto['subset_size']
    seed_value = dec(SEED << 1)
    products = []
    for code in chosen:
        a = dec(valid[code] << 1)
        product = a * (a + seed_value)
        products.append((code, product, product**(2**18)))
    assert enc(products[chosen.index(3)][1]) == 5990700
    coeffs = json.loads(COEFF.read_text())
    assert coeffs['status'] == 'PASS_N131_W33_FREECODE_RESULTANT_EXPORT'
    assert coeffs['seed_mask'] == SEED and coeffs['rotations'] == [0, 18]
    assert enc(products[chosen.index(16722)][2]) == coeffs['rows'][0]['positive_pair_products'][1]
    source_ready_ns = time.monotonic_ns() - start
    vanisher_start = time.monotonic_ns()
    source_vanisher = product_tree([P + first for _, first, _ in products], R.one())
    vanisher_ns = time.monotonic_ns() - vanisher_start
    assert source_vanisher.degree() == proto['subset_size']
    first_by_product = {p:code for code,p,_ in products}
    assert len(first_by_product) == len(products)
    rows = []
    for target_index in proto['target_indices']:
        row_start = time.monotonic_ns()
        frozen = coeffs['rows'][target_index]
        matrix = [[K.zero() for _ in range(5)] for _ in range(5)]
        for i, j, value in frozen['terms']:
            matrix[i][j] = dec(value)
        quartics = []
        for _, _, q in products:
            powers = [K.one(),q,q*q,q*q*q,q*q*q*q]
            quartics.append(sum((sum((matrix[i][j]*powers[j] for j in range(5)), K.zero()) * P**i
                                 for i in range(5)), R.zero()))
        construction_ns = time.monotonic_ns() - row_start
        norm_start = time.monotonic_ns()
        norm = product_tree(quartics, R.one())
        norm_ns = time.monotonic_ns() - norm_start
        gcd_start = time.monotonic_ns()
        common = norm.gcd(source_vanisher)
        gcd_ns = time.monotonic_ns() - gcd_start
        if common.degree() == 0:
            hits = []
        elif common.degree() == 1:
            hits = [first_by_product[common[0]/common[1]]]
        else:
            hits = sorted(first_by_product[root] for root in common.roots(multiplicities=False))
        pairs = []
        for code in hits:
            p = products[chosen.index(code)][1]
            for (second, _, _), quartic in zip(products, quartics):
                if quartic(p) == 0:
                    pairs.append([code, second])
        row = {'target_index': target_index, 'target_name': frozen['name'],
               'target_point': frozen['point'], 'norm_degree': int(norm.degree()),
               'gcd_degree': int(common.degree()), 'first_code_hits': hits,
               'code_pair_hits': pairs, 'construction_ns': construction_ns,
               'norm_ns': norm_ns, 'gcd_ns': gcd_ns,
               'row_ns': time.monotonic_ns() - row_start}
        rows.append(row)
        print('ROW', target_index, 'gcd', row['gcd_degree'], 'pairs', pairs,
              'seconds', row['row_ns']/1e9, flush=True)
    out = {'status': 'COMPLETE_N131_W20_GLOBAL_NORM_PILOT', 'candidate_id': None,
           'curve_id': coeffs['curve_id'], 'subset_size': len(chosen),
           'chosen_codes_sha256': hashlib.sha256(','.join(map(str,chosen)).encode()).hexdigest(),
           'valid_source_size': len(valid), 'source_ready_ns': source_ready_ns,
           'vanisher_ns': vanisher_ns, 'rows': rows,
           'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'protocol_sha256': sha(PROTO)}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
