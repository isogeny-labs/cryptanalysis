"""One global target-conditioned product over the valid second-code source."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / 'n41_w11_freecode_resultant_20261018/resultant_input.tsv'
PROTO = HERE / 'protocol.json'


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
    assert sha(INPUT) == proto['source_sha256']['resultant_input.tsv']
    assert sha(Path(__file__)) == proto['source_sha256']['oracle.py']
    assert sha(HERE / 'sage_runtime_info.json') == proto['source_sha256']['sage_runtime_info.json']
    assert proto['worker_count'] == 1
    signal.alarm(proto['child_alarm_seconds'])
    F2 = PolynomialRing(GF(2), 'u')
    u = F2.gen()
    K = GF(2**41, name='u', modulus=u**41 + u**3 + 1)
    R = PolynomialRing(K, 'P')
    P = R.gen()

    def dec(n):
        return K(F2([(n >> i) & 1 for i in range(41)]))

    lines = INPUT.read_text().splitlines()
    header = lines.pop(0).split()
    assert header == ['FREECODE', '25', '281', '13']
    source = []
    for _ in range(281):
        row = lines.pop(0).split()
        assert row[0] == 'P'
        source.append((int(row[1]), dec(int(row[2])), dec(int(row[3]))))
    assert len({code for code, _, _ in source}) == 281
    assert len({p for _, p, _ in source}) == 281
    assert len({q for _, _, q in source}) == 281
    prepared = time.monotonic_ns()
    source_vanisher = product_tree([P + p for _, p, _ in source], R.one())
    assert source_vanisher.degree() == 281
    setup_ns = time.monotonic_ns() - prepared

    results = []
    for index in proto['target_indices']:
        target_start = time.monotonic_ns()
        offset = index * 14
        row = lines[offset].split()
        assert row[0] == 'T' and int(row[1]) == index
        coeff = [[K.zero() for _ in range(5)] for _ in range(5)]
        for line in lines[offset + 1:offset + 14]:
            tag, row_index, i, j, value = line.split()
            assert tag == 'C' and int(row_index) == index
            coeff[int(i)][int(j)] = dec(int(value))
        quartics = []
        for _, _, q in source:
            qpower = [K.one(), q, q*q, q*q*q, q*q*q*q]
            polynomial = sum((sum((coeff[i][j] * qpower[j] for j in range(5)), K.zero()) * P**i
                              for i in range(5)), R.zero())
            quartics.append(polynomial)
        construction_ns = time.monotonic_ns() - target_start
        norm_start = time.monotonic_ns()
        norm = product_tree(quartics, R.one())
        norm_ns = time.monotonic_ns() - norm_start
        gcd_start = time.monotonic_ns()
        common = norm.gcd(source_vanisher)
        first_hits = [code for code, p, _ in source if common(p) == 0]
        gcd_ns = time.monotonic_ns() - gcd_start
        pairs = []
        for code, p, _ in source:
            if code not in first_hits:
                continue
            for (second, _, _), quartic in zip(source, quartics):
                if quartic(p) == 0:
                    pairs.append([code, second])
        result = {'index': index, 'point': [int(row[2]), int(row[3])],
                  'norm_degree': int(norm.degree()),
                  'gcd_degree': int(common.degree()),
                  'first_code_hits': first_hits, 'code_pair_hits': pairs,
                  'quartic_construction_ns': construction_ns,
                  'norm_ns': norm_ns, 'gcd_and_localization_ns': gcd_ns,
                  'target_ns': time.monotonic_ns() - target_start}
        results.append(result)
        print('ROW', index, 'norm_degree', result['norm_degree'],
              'gcd_degree', result['gcd_degree'], 'pairs', pairs,
              'target_seconds', result['target_ns']/1e9, flush=True)
    assert len(lines) == 25 * 14
    out = {'status': 'COMPLETE_GLOBAL_VALID_CODE_NORM', 'candidate_id': None,
           'curve_id': 'EC1N41Ckb1h7d5e80d3c4d0', 'valid_codes': len(source),
           'target_indices': proto['target_indices'], 'source_vanisher_degree': int(source_vanisher.degree()),
           'source_setup_ns': setup_ns, 'results': results,
           'self_maxrss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'protocol_sha256': sha(PROTO)}
    (HERE / 'result.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()
