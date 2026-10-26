"""Lift the weight-90 two-prime kernel through fresh modular characteristics."""
import json
import sys
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, Infinity, LaurentSeriesRing, QQ, matrix

HERE = Path(__file__).resolve().parent
TRAIN_HI = 1100
HOLDOUT_HI = 1200
PRECISION = 1450


def reduce_series(series, field, ring):
    q = ring.gen()
    return sum((field(QQ(series[n])) * q**n
                for n in range(int(series.valuation()), int(series.prec()))
                if series[n]), ring.zero()).add_bigoh(int(series.prec()))


def main():
    minimal_path = HERE / 'minimal_result.json'
    prior = json.loads(minimal_path.read_text())
    screen = json.loads((HERE / 'screen_extended_result.json').read_text())
    old_terms = next(r['terms'] for r in screen['rows'] if r['weighted_degree'] == 96)
    terms = [t for t in old_terms if 2*t[0] + 3*t[1] + 2*t[2] <= 90]
    term_indices = [old_terms.index(t) for t in terms]
    old_vectors = [r['minimal_relation']['coefficients'] for r in prior['results']]
    support = [j for j,k in enumerate(term_indices) if any(v[k] for v in old_vectors)]
    assert 0 in support and len(support) < len(terms)
    requested = [int(s) for s in sys.argv[1:]]
    existing_path = HERE/'lift_result.json'
    existing = json.loads(existing_path.read_text()) if existing_path.exists() else None
    assert requested and not set(requested) & {997, 1009}
    if existing:
        assert existing['terms'] == terms and existing['support'] == support

    C = EllipticCurve('27a1')
    B = EllipticCurve(QQ, [0, 0, 0, 0, -16])
    xc_qq, yc_qq = C.modular_parametrization().power_series(PRECISION)
    xb_qq, _ = B.modular_parametrization().power_series(PRECISION)
    rows = []
    for p in requested:
        field = GF(p)
        ring = LaurentSeriesRing(field, 'q')
        xc = reduce_series(xc_qq, field, ring)
        yc = reduce_series(yc_qq, field, ring)
        xb = reduce_series(xb_qq, field, ring)
        xe = (xb**3 - 64) / xb**2
        selected = [terms[j] for j in support]
        xcp = [xc**a for a in range(46)]
        xep = [xe**c for c in range(13)]
        columns = [xcp[a] * (yc if b else ring.one()) * xep[c]
                   for a, b, c in selected]
        min_precision = min(int(s.prec()) for s in columns if s.prec() != Infinity)
        assert min_precision > HOLDOUT_HI, (p, min_precision)
        A = matrix(field, [[s[n] for s in columns]
                           for n in range(-90, TRAIN_HI + 1)])
        K = A.right_kernel()
        assert K.dimension() == 1, (p, K.dimension())
        v = K.basis()[0]
        assert v[support.index(0)] != 0
        v *= v[support.index(0)]**-1
        combination = sum((v[j]*columns[j] for j in range(len(columns))),
                          ring.zero())
        assert all(combination[n] == 0 for n in range(TRAIN_HI+1, HOLDOUT_HI+1))
        full = [0]*len(terms)
        for j, k in enumerate(support):
            full[k] = int(v[j])
        result = {'prime': p, 'support_columns':len(support),
                  'training_rows':A.nrows(), 'rank':A.ncols()-1,
                  'holdout_zero':True, 'minimum_series_precision':min_precision,
                  'coefficients':full}
        rows.append(result)
        print(json.dumps({k:result[k] for k in result if k != 'coefficients'},
                         sort_keys=True), flush=True)
    merged = {r['prime']:r for r in existing['rows']} if existing else {}
    for row in rows:
        if row['prime'] in merged:
            assert merged[row['prime']] == row
        merged[row['prime']] = row
    out = {'status':'COMPLETE_FRESH_PRIME_LIFT',
           'minimal_sha256':sha256(minimal_path.read_bytes()).hexdigest(),
           'terms':terms, 'support':support,
           'rows':[merged[p] for p in sorted(merged)]}
    (HERE/'lift_result.json').write_text(json.dumps(out,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'primes':requested,
                      'terms':len(terms),'support':len(support)},sort_keys=True))


if __name__ == '__main__':
    main()
