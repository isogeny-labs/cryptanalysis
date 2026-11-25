"""Screen x_B linear relations over the three generators x_C,y_C,y_E."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, LaurentSeriesRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def monomials(bound):
    return [(a,b,k) for b in (0,1)
            for k in range(bound//3+1)
            for a in range(bound//2+1)
            if 2*a+3*b+3*k <= bound]


def source_series(record, name, field, ring):
    q = ring.gen()
    lo, hi = record['coefficient_exponents']
    values = record[name]
    assert len(values) == hi-lo+1
    return sum((field(c)*q**(lo+i) for i,c in enumerate(values) if c),
               ring.zero()).add_bigoh(hi+1)


def screen_field(record, protocol):
    p = record['prime']
    field = GF(p)
    ring = LaurentSeriesRing(field,'q')
    xc = source_series(record,'xc',field,ring)
    yc = source_series(record,'yc',field,ring)
    xb = source_series(record,'xb',field,ring)
    ye = source_series(record,'hy',field,ring)
    assert int(xc.valuation()) == -2
    assert int(yc.valuation()) == -3
    assert int(xb.valuation()) == -2
    assert int(ye.valuation()) == -3
    max_d = max(protocol['weighted_degrees'])
    xc_powers = [xc**a for a in range((max_d+2)//2+1)]
    ye_powers = [ye**k for k in range((max_d+2)//3+1)]
    terms = set(monomials(max_d+2))
    cache = {(a,b,k):xc_powers[a]*(yc if b else ring.one())*ye_powers[k]
             for a,b,k in terms}
    rows = []
    for degree in protocol['weighted_degrees']:
        aa,bb = monomials(degree),monomials(degree+2)
        joined = [cache[t]*xb for t in aa]+[cache[t] for t in bb]
        lo,train_hi,hold_hi = -(degree+2),900,980
        min_precision = int(min(s.prec() for s in joined))
        assert min_precision > hold_hi,(degree,p,min_precision)
        train = matrix(field,[[s[n] for s in joined]
                              for n in range(lo,train_hi+1)])
        kernel = train.right_kernel()
        rank = int(train.ncols()-kernel.dimension())
        pivot_rows = [int(i) for i in train.transpose().echelon_form().pivots()]
        assert len(pivot_rows) == rank
        determinant = None
        if rank == train.ncols():
            determinant = int(train.matrix_from_rows(pivot_rows).det())
            assert determinant != 0
        candidate_rows = []
        for vector in kernel.basis():
            combined = sum((vector[j]*joined[j] for j in range(len(joined))),
                           ring.zero())
            holdout_zero = all(combined[n] == 0 for n in range(train_hi+1,hold_hi+1))
            denominator = sum((vector[j]*cache[aa[j]] for j in range(len(aa))),
                              ring.zero())
            denominator_nonzero = any(denominator[n] != 0
                                      for n in range(-degree,hold_hi+1))
            candidate_rows.append({'holdout_zero':holdout_zero,
                                   'denominator_nonzero':denominator_nonzero,
                                   'coefficients':[int(v) for v in vector]})
        row = {'prime':p,'weighted_degree':degree,'a_terms':aa,'b_terms':bb,
               'columns':int(train.ncols()),'training_rows':int(train.nrows()),
               'training_rank':rank,'training_nullity':int(kernel.dimension()),
               'minimum_series_precision':min_precision,
               'pivot_rows':pivot_rows,'pivot_minor_determinant_mod_p':determinant,
               'kernel_basis_holdout':candidate_rows}
        rows.append(row)
        print(json.dumps({k:row[k] for k in ('prime','weighted_degree','columns',
                           'training_rank','training_nullity',
                           'minimum_series_precision')},sort_keys=True),flush=True)
    return rows


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_Y_PRIMITIVE_SCREEN'
    source_path = ROOT/'hecke-432-full-e-lift-20261025'/'qseries_modp.json'
    verification_path = ROOT/'hecke-432-full-e-lift-20261025'/'verification.json'
    source = json.loads(source_path.read_text())
    verification = json.loads(verification_path.read_text())
    assert len(source) == 2
    assert [row['prime'] for row in source] == protocol['auxiliary_fields']
    assert verification['status'].startswith('PASS'),verification['status']
    rows = [result for record in source for result in screen_field(record,protocol)]
    out = {'status':'COMPLETE_Y_ONLY_RATIONAL_LIFT_SCREEN',
           'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
           'qseries_source_sha256':sha256(source_path.read_bytes()).hexdigest(),
           'qseries_independent_verification_sha256':sha256(verification_path.read_bytes()).hexdigest(),
           'rows':rows}
    (HERE/'screen_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(rows)},sort_keys=True),flush=True)


if __name__ == '__main__':
    main()
