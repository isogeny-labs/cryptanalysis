"""Enumerate the p887 rational C,E resolvent pairs without a source lookup."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
P = 887


def evaluate(terms, xc, yc, xe):
    return sum(int(t['integer_coefficient']) * pow(xc, t['x_C_exponent'], P)
               * pow(yc, t['y_C_exponent'], P) * pow(xe, t['x_E_exponent'], P)
               for t in terms) % P


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_P887_INVERSE_ENUMERATION'
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    field = GF(P)
    curve_c = EllipticCurve(field, [0, 0, 1, 0, -7])
    curve_e = EllipticCurve(field, [0, 0, 0, 0, 432])
    ring = PolynomialRing(field, 'T')
    T = ring.gen()
    grouped = [[] for _ in range(13)]
    for term in inputs['resolvent']['terms']:
        grouped[term['x_E_exponent']].append(term)
    branch = inputs['branch']
    rows = []
    root_hist = Counter()
    degree_hist = Counter()
    exceptions = []
    for point in curve_c.points():
        if point.is_zero():
            continue
        xc, yc = int(point[0]), int(point[1])
        coeffs = [field(evaluate(terms, xc, yc, 1)) for terms in grouped]
        polynomial = sum((a * T**i for i, a in enumerate(coeffs)), ring.zero())
        if polynomial == 0:
            exceptions.append({'C_point': [xc, yc], 'reason': 'zero_specialization'})
            continue
        degree_hist[int(polynomial.degree())] += 1
        roots = polynomial.roots()
        root_hist[len(roots)] += 1
        for root, multiplicity in roots:
            xe = int(root)
            for epoint in curve_e.lift_x(root, all=True):
                ye = int(epoint[1])
                numerator = evaluate(branch['numerator_terms'], xc, yc, xe)
                denominator = evaluate(branch['denominator_terms'], xc, yc, xe)
                row = {'C_point': [xc, yc], 'E_point': [xe, ye],
                       'x_E_root_multiplicity': int(multiplicity)}
                if denominator == 0:
                    row['branch_status'] = 'ZERO_DENOMINATOR'
                else:
                    xb = numerator * pow(denominator, -1, P) % P
                    yden = (xb**3 + 128) % P
                    if xb == 0 or yden == 0:
                        row['branch_status'] = 'UNDEFINED_Y_INVERSE'
                    else:
                        yb = ye * pow(xb, 3, P) * pow(yden, -1, P) % P
                        row['B_point'] = [xb, yb]
                        row['branch_status'] = ('VALID' if
                            (yb*yb - xb**3 + 16) % P == 0 and
                            (xb**3 - xe*xb*xb - 64) % P == 0 else 'INVALID')
                rows.append(row)
    rows.sort(key=lambda row: (*row['C_point'], *row['E_point']))
    assert len(rows) == len({(*row['C_point'], *row['E_point']) for row in rows})
    shards = []
    for offset in range(0, len(rows), 250):
        path = HERE / f'pairs-{offset//250:02d}.json'
        block = rows[offset:offset+250]
        path.write_text(json.dumps(block, sort_keys=True, separators=(',', ':')) + '\n')
        shards.append({'file': path.name, 'rows': len(block),
                       'sha256': sha256(path.read_bytes()).hexdigest()})
    result = {'status': 'COMPLETE_P887_RESOLVENT_SCREEN' if not exceptions else 'PARTIAL_P887_RESOLVENT_SCREEN',
              'prime': P, 'protocol_sha256': sha256(protocol_path.read_bytes()).hexdigest(),
              'C_group_order': int(curve_c.cardinality()),
              'E_group_order': int(curve_e.cardinality()),
              'pair_count': len(rows),
              'root_count_per_C_histogram': dict(sorted(root_hist.items())),
              'degree_histogram': dict(sorted(degree_hist.items())),
              'root_multiplicity_histogram': dict(sorted(Counter(row['x_E_root_multiplicity'] for row in rows).items())),
              'branch_status_histogram': dict(sorted(Counter(row['branch_status'] for row in rows).items())),
              'exceptions': exceptions, 'pair_shards': shards}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'C_group_order', 'E_group_order',
                                                   'pair_count', 'branch_status_histogram')}, sort_keys=True))


if __name__ == '__main__':
    main()
