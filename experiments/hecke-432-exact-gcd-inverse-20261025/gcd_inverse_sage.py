"""Construct all rational B candidates from P_B(C,T) and the 3-isogeny cubic."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def specialize(terms, c, field, ring):
    xc, yc = (field(a) for a in c)
    T = ring.gen()
    return sum((field(int(t['integer_coefficient']))
                * xc**t['x_C_exponent'] * yc**t['y_C_exponent']
                * T**t['x_B_exponent'] for t in terms), ring.zero())


def candidates(c, e, terms, field, ring, curve_b):
    xe, ye = (field(a) for a in e)
    T = ring.gen()
    polynomial = specialize(terms, c, field, ring)
    cubic = T**3-xe*T**2-64
    common = polynomial.gcd(cubic)
    b_points = set()
    rational_roots = []
    for x, multiplicity in common.roots():
        rational_roots.append({'x_B': int(x), 'multiplicity': int(multiplicity)})
        for b in curve_b.lift_x(x, all=True):
            y = b[1]
            if x and (x**3-64)/x**2 == xe and y*(x**3+128)/x**3 == ye:
                b_points.add((int(x), int(y)))
    return {'P_B_degree': int(polynomial.degree()),
            'gcd_degree': int(common.degree()),
            'gcd_coefficients_low_to_high': [int(a) for a in common.list()],
            'rational_x_B_roots': rational_roots,
            'B_candidates': [list(b) for b in sorted(b_points)]}


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_EXACT_GCD_INVERSE'
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    previous = inputs['crossprime_result']
    terms = inputs['b_resolvent']['terms']
    result = {'status': 'COMPLETE_EXACT_GCD_INVERSE',
              'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'source_code_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'primes': {}}
    for p in protocol['primes']:
        field = GF(p)
        ring = PolynomialRing(field, 'T')
        curve_b = EllipticCurve(field, [0, 0, 0, 0, -16])
        rows = []
        for shard in previous['primes'][str(p)]['pair_shards']:
            old_path = Path(protocol['inputs'][f"p{p}_{int(shard['file'].split('-')[-1].split('.')[0]):02d}"]['path'])
            assert sha256(old_path.read_bytes()).hexdigest() == shard['sha256']
            for old in json.loads(old_path.read_text()):
                value = candidates(old['C_point'], old['E_point'], terms, field, ring, curve_b)
                if old['status'] == 'VALID':
                    assert value['B_candidates'] == [old['B_point']]
                else:
                    assert not value['B_candidates']
                rows.append({'C_point': old['C_point'], 'E_point': old['E_point'],
                             'prior_branch_status': old['status'], **value})
        assert len(rows) == previous['primes'][str(p)]['resolvent_pairs']
        shards = []
        for offset in range(0, len(rows), 250):
            path = HERE/f'p{p}-gcd-{offset//250:02d}.json'
            block = rows[offset:offset+250]
            path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':'))+'\n')
            shards.append({'file': path.name, 'rows': len(block),
                           'sha256': sha256(path.read_bytes()).hexdigest()})
        hist = Counter((row['prior_branch_status'], row['gcd_degree'],
                        len(row['B_candidates'])) for row in rows)
        result['primes'][str(p)] = {'pair_count': len(rows),
                                   'candidate_count_histogram': dict(sorted(Counter(len(r['B_candidates']) for r in rows).items())),
                                   'gcd_status_degree_candidate_histogram': [
                                       {'branch_status': key[0], 'gcd_degree': key[1],
                                        'B_candidates': key[2], 'count': count}
                                       for key, count in sorted(hist.items())],
                                   'shards': shards}
        print(json.dumps({'prime': p, 'pair_count': len(rows),
                          'candidate_count_histogram': result['primes'][str(p)]['candidate_count_histogram']},
                         sort_keys=True), flush=True)
    (HERE/'result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
