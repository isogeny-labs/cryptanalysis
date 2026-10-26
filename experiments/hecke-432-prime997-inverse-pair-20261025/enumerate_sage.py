"""Enumerate rational (C,E) pairs from the exact resolvent, independently of the source census."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'
from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
P = 997


def evaluate(terms, xc, yc, xe):
    return sum(int(t['integer_coefficient']) * pow(xc, t['x_C_exponent'], P) *
               pow(yc, t['y_C_exponent'], P) * pow(xe, t['x_E_exponent'], P)
               for t in terms) % P


def source_key(c, e):
    return tuple(c) + tuple(e)


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_INDEPENDENT_PAIR_ENUMERATION'
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    h = inputs['resolvent']
    branch = inputs['branch']
    sources = inputs['source_pairs']['rows']
    assert h['degree_in_X'] == 12 and len(sources) == 1800
    field = GF(P)
    C = EllipticCurve(field, [0, 0, 1, 0, -7])
    E = EllipticCurve(field, [0, 0, 0, 0, 432])
    R = PolynomialRing(field, 'T')
    T = R.gen()
    grouped = [[] for _ in range(13)]
    for term in h['terms']:
        grouped[term['x_E_exponent']].append(term)
    source_index = {source_key(row['C_point'], row['E_point']): index
                    for index, row in enumerate(sources)}
    assert len(source_index) == len(sources)
    pairs = []
    root_hist = Counter()
    degree_hist = Counter()
    exceptions = []
    for cp in C.points():
        if cp.is_zero():
            continue
        xc, yc = int(cp[0]), int(cp[1])
        coeffs = [field(evaluate(terms, xc, yc, 1)) for terms in grouped]
        polynomial = sum((coefficient * T**i for i, coefficient in enumerate(coeffs)), R.zero())
        if polynomial == 0:
            exceptions.append({'C_point':[xc,yc], 'reason':'zero_specialization'})
            continue
        degree_hist[polynomial.degree()] += 1
        roots = polynomial.roots()
        root_hist[len(roots)] += 1
        for root, multiplicity in roots:
            xe = int(root)
            # E.lift_x returns both signs, including a single point when y=0.
            for ep in E.lift_x(root, all=True):
                ye = int(ep[1])
                key = (xc,yc,xe,ye)
                n = evaluate(branch['numerator_terms'], xc, yc, xe)
                d = evaluate(branch['denominator_terms'], xc, yc, xe)
                record = {'C_point':[xc,yc], 'E_point':[xe,ye],
                          'x_E_root_multiplicity':int(multiplicity),
                          'source_index':source_index.get(key)}
                if d == 0:
                    record['branch_status'] = 'ZERO_DENOMINATOR'
                else:
                    xb = n * pow(d,-1,P) % P
                    yden = (xb**3 + 128) % P
                    if xb == 0 or yden == 0:
                        record['branch_status'] = 'UNDEFINED_Y_INVERSE'
                    else:
                        yb = ye * pow(xb,3,P) * pow(yden,-1,P) % P
                        record['B_point'] = [xb,yb]
                        record['branch_status'] = ('VALID' if
                            (yb*yb-xb**3+16)%P == 0 and
                            (xb**3-xe*xb*xb-64)%P == 0 else 'INVALID')
                pairs.append(record)
    pairs.sort(key=lambda row:(*row['C_point'],*row['E_point']))
    keys=[source_key(row['C_point'],row['E_point']) for row in pairs]
    duplicate_pairs=len(keys)-len(set(keys))
    observed=set(keys)
    expected=set(source_index)
    shards=[]
    for offset in range(0,len(pairs),300):
        path=HERE/f'pairs-{offset//300:02d}.json'
        path.write_text(json.dumps(pairs[offset:offset+300],sort_keys=True,separators=(',',':'))+'\n')
        shards.append({'file':path.name,'rows':len(pairs[offset:offset+300]),
                       'sha256':sha256(path.read_bytes()).hexdigest()})
    result={'status':'COMPLETE_INVERSE_PAIR_SCREEN' if not exceptions and not duplicate_pairs else 'PARTIAL_INVERSE_PAIR_SCREEN',
            'prime':P,'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
            'C_group_order':int(C.cardinality()),'C_affine_points':int(C.cardinality()-1),
            'E_group_order':int(E.cardinality()),'rational_pair_count':len(pairs),
            'source_pair_count':len(expected),'matched_source_pairs':len(observed & expected),
            'extra_pair_count':len(observed-expected),'missing_pair_count':len(expected-observed),
            'extra_pairs':[list(k) for k in sorted(observed-expected)],
            'missing_pairs':[list(k) for k in sorted(expected-observed)],
            'duplicate_pairs':duplicate_pairs,
            'root_count_per_C_histogram':{str(k):int(v) for k,v in sorted(root_hist.items())},
            'specialized_degree_histogram':{str(k):int(v) for k,v in sorted(degree_hist.items())},
            'root_multiplicity_histogram':dict(sorted(Counter(row['x_E_root_multiplicity'] for row in pairs).items())),
            'branch_status_histogram':dict(sorted(Counter(row['branch_status'] for row in pairs).items())),
            'exceptions':exceptions,'pair_shards':shards}
    (HERE/'result.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps({k:result[k] for k in ('status','C_group_order','E_group_order','rational_pair_count','matched_source_pairs','extra_pair_count','missing_pair_count','branch_status_histogram')},sort_keys=True))


if __name__=='__main__':
    main()
