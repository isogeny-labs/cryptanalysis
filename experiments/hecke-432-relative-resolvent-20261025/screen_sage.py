"""Screen degree-at-most-12 relative x_E polynomials over X0(27)."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, LaurentSeriesRing, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def monomials(bound):
    return [(a,b,c) for b in (0,1) for c in range(13)
            for a in range(bound//2+1)
            if 2*a+3*b+2*c <= bound]


def source_series(record,name,field,ring):
    q = ring.gen()
    lo,hi = record['coefficient_exponents']
    values = record[name]
    assert (lo,hi) == (-3,1050) and len(values) == hi-lo+1
    return sum((field(v)*q**(lo+i) for i,v in enumerate(values) if v),
               ring.zero()).add_bigoh(hi+1)


def screen(record,protocol):
    p = record['prime']
    field = GF(p)
    ring = LaurentSeriesRing(field,'q')
    xc = source_series(record,'xc',field,ring)
    yc = source_series(record,'yc',field,ring)
    xe = source_series(record,'hx',field,ring)
    max_d = max(protocol['weighted_degrees'])
    xcp = [xc**a for a in range(max_d//2+1)]
    xep = [xe**c for c in range(13)]
    cache = {(a,b,c):xcp[a]*(yc if b else ring.one())*xep[c]
             for a,b,c in monomials(max_d)}
    rows = []
    for degree in protocol['weighted_degrees']:
        terms = monomials(degree)
        series = [cache[t] for t in terms]
        min_precision = int(min(s.prec() for s in series))
        assert min_precision > 950,(p,degree,min_precision)
        lo,hi = -degree,900
        training = matrix(field,[[s[n] for s in series]
                                 for n in range(lo,hi+1)])
        kernel = training.right_kernel()
        rank = int(training.ncols()-kernel.dimension())
        pivot_rows = [int(i) for i in training.transpose().echelon_form().pivots()]
        assert len(pivot_rows) == rank
        determinant = None
        if rank == training.ncols():
            determinant = int(training.matrix_from_rows(pivot_rows).det())
            assert determinant != 0
        basis = []
        for vector in kernel.basis():
            combo = sum((vector[i]*series[i] for i in range(len(series))),ring.zero())
            basis.append({'coefficients':[int(x) for x in vector],
                          'max_x_E_degree':max((terms[i][2] for i,x in enumerate(vector) if x),default=-1),
                          'holdout_zero':all(combo[n] == 0 for n in range(901,951))})
        row = {'prime':p,'weighted_degree':degree,'terms':terms,
               'columns':int(training.ncols()),'training_rows':int(training.nrows()),
               'training_rank':rank,'training_nullity':int(kernel.dimension()),
               'pivot_rows':pivot_rows,'pivot_minor_determinant_mod_p':determinant,
               'kernel_basis':basis,'minimum_series_precision':min_precision}
        rows.append(row)
        print(json.dumps({k:row[k] for k in ('prime','weighted_degree','columns',
                           'training_rank','training_nullity','minimum_series_precision')},sort_keys=True),flush=True)
    return rows


def main():
    protocol_path = HERE/'protocol.json'
    source_path = ROOT/'hecke-432-full-e-lift-20261025'/'qseries_modp.json'
    verified_path = ROOT/'hecke-432-full-e-lift-20261025'/'verification.json'
    protocol = json.loads(protocol_path.read_text())
    source = json.loads(source_path.read_text())
    verified = json.loads(verified_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_RELATIVE_RESOLVENT_SCREEN'
    assert verified['status'] == 'PASS_INDEPENDENT_PIVOT_REPLAY'
    assert [r['prime'] for r in source] == protocol['auxiliary_fields']
    rows = [x for r in source for x in screen(r,protocol)]
    out = {'status':'COMPLETE_RELATIVE_RESOLVENT_SCREEN',
           'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256':sha256(source_path.read_bytes()).hexdigest(),
           'source_verification_sha256':sha256(verified_path.read_bytes()).hexdigest(),
           'rows':rows}
    (HERE/'screen_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(rows)},sort_keys=True))


if __name__=='__main__':
    main()
