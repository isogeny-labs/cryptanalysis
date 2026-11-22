"""Screen rational x_B formulas using both coordinates of projected E."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, LaurentSeriesRing, QQ, matrix

HERE = Path(__file__).resolve().parent


def monomials(bound):
    return [(a, b, c, d) for b in (0, 1) for d in (0, 1)
            for c in range(bound // 2 + 1)
            for a in range(bound // 2 + 1)
            if 2*a + 3*b + 2*c + 3*d <= bound]


def reduce_series(s, field, ring, precision):
    q = ring.gen()
    out = ring.zero()
    for n in range(int(s.valuation()), min(int(s.prec()), precision)):
        if s[n]:
            out += field(QQ(s[n])) * q**n
    return out.add_bigoh(min(int(s.prec()), precision))


def coefficients(s, lo, hi):
    return [int(s[n]) for n in range(lo, hi + 1)]


def nonzero_denominator_basis(kernel, a_series, field, lo, hi):
    projected = []
    witness = None
    for vector in kernel.basis():
        series = sum((vector[k] * a_series[k]
                      for k in range(len(a_series))), a_series[0].parent().zero())
        row = [series[n] for n in range(lo, hi + 1)]
        if any(row):
            projected.append(row)
            if witness is None:
                witness = [int(x) for x in vector]
    dimension = matrix(field, projected).rank() if projected else 0
    return int(dimension), witness


def screen_field(p, source, protocol):
    field = GF(p)
    ring = LaurentSeriesRing(field, 'q')
    precision = protocol['q_series_precision']
    xc = reduce_series(source['xc'], field, ring, precision)
    yc = reduce_series(source['yc'], field, ring, precision)
    xb = reduce_series(source['xb'], field, ring, precision)
    yb = reduce_series(source['yb'], field, ring, precision)
    hx = (xb**3 - 64) / xb**2
    hy = yb * (xb**3 + 128) / xb**3
    assert (yc**2 + yc - xc**3 + 7).add_bigoh(980) == 0
    assert (yb**2 - xb**3 + 16).add_bigoh(980) == 0
    assert (hy**2 - hx**3 - 432).add_bigoh(980) == 0
    print(json.dumps({'prime':p,'series_precision':min(int(s.prec())
                      for s in (xc,yc,xb,yb,hx,hy))}),flush=True)
    store_lo, store_hi = protocol['stored_coefficients']
    series_record = {
        'prime': p, 'coefficient_exponents': [store_lo, store_hi],
        'xc': coefficients(xc, store_lo, store_hi),
        'yc': coefficients(yc, store_lo, store_hi),
        'xb': coefficients(xb, store_lo, store_hi),
        'yb': coefficients(yb, store_lo, store_hi),
        'hx': coefficients(hx, store_lo, store_hi),
        'hy': coefficients(hy, store_lo, store_hi),
    }
    rows = []
    for degree in protocol['weighted_degrees']:
        aa, bb = monomials(degree), monomials(degree + 2)
        def make(term):
            a,b,c,d = term
            return xc**a * yc**b * hx**c * hy**d
        a_series = [make(term) for term in aa]
        joined = [s*xb for s in a_series] + [make(term) for term in bb]
        lo = -(degree + 2)
        train_hi = protocol['training_exponents'][1]
        holdout_hi = protocol['holdout_exponents'][1]
        assert min(s.prec() for s in joined) > holdout_hi
        training = matrix(field, [[s[n] for s in joined]
                                  for n in range(lo, train_hi + 1)])
        extended = matrix(field, [[s[n] for s in joined]
                                  for n in range(lo, holdout_hi + 1)])
        train_kernel = training.right_kernel()
        extended_kernel = extended.right_kernel()
        pivot_rows = [int(i) for i in training.transpose().echelon_form().pivots()]
        assert len(pivot_rows) == training.rank()
        pivot_determinant = None
        if len(pivot_rows) == training.ncols():
            pivot_determinant = int(training.matrix_from_rows(pivot_rows).det())
            assert pivot_determinant != 0
        denominator_dim, witness = nonzero_denominator_basis(
            extended_kernel, a_series, field, -degree, holdout_hi)
        row = {
            'prime':p,'weighted_degree':degree,
            'a_terms':aa,'b_terms':bb,
            'training_rows':training.nrows(),'extended_rows':extended.nrows(),
            'columns':training.ncols(),
            'training_rank':int(training.rank()),
            'training_nullity':int(train_kernel.dimension()),
            'pivot_rows':pivot_rows,
            'pivot_minor_determinant_mod_p':pivot_determinant,
            'extended_rank':int(extended.rank()),
            'extended_nullity':int(extended_kernel.dimension()),
            'extended_nonzero_denominator_dimension':denominator_dim,
            'heldout_candidate_coefficients':witness,
        }
        rows.append(row)
        print(json.dumps({k:row[k] for k in ('prime','weighted_degree','columns',
              'training_nullity','extended_nullity',
              'extended_nonzero_denominator_dimension')},sort_keys=True),flush=True)
    return rows, series_record


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_FULL_E_SCREEN'
    precision=protocol['q_series_precision']
    C=EllipticCurve('27a1')
    B=EllipticCurve(QQ,[0,0,0,0,-16])
    xc,yc=C.modular_parametrization().power_series(precision)
    xb,yb=B.modular_parametrization().power_series(precision)
    source={'xc':xc,'yc':yc,'xb':xb,'yb':yb}
    rows=[]
    qrecords=[]
    for p in protocol['auxiliary_fields']:
        rr,qq=screen_field(p,source,protocol)
        rows.extend(rr)
        qrecords.append(qq)
    out={'status':'COMPLETE_FULL_E_DIRECT_LIFT_SCREEN',
         'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
         'rows':rows}
    (HERE/'screen_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    (HERE/'qseries_modp.json').write_text(json.dumps(qrecords,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(rows)},sort_keys=True))


if __name__=='__main__':
    main()
