"""Extend the relative degree-12 relation screen through weight 144."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, LaurentSeriesRing, matrix

HERE = Path(__file__).resolve().parent


def monomials(bound):
    return [(a,b,c) for b in (0,1) for c in range(13)
            for a in range(bound//2+1)
            if 2*a+3*b+2*c <= bound]


def series_from_row(row,name,field,ring):
    q = ring.gen()
    lo,hi = row['coefficient_exponents']
    values = row[name]
    assert (lo,hi) == (-3,2000) and len(values) == hi-lo+1
    return sum((field(v)*q**(lo+i) for i,v in enumerate(values) if v),
               ring.zero()).add_bigoh(hi+1)


def screen(row,protocol):
    p = row['prime']
    field = GF(p)
    ring = LaurentSeriesRing(field,'q')
    xc = series_from_row(row,'xc',field,ring)
    yc = series_from_row(row,'yc',field,ring)
    xe = series_from_row(row,'hx',field,ring)
    max_d = max(protocol['weighted_degrees'])
    xcp = [xc**a for a in range(max_d//2+1)]
    xep = [xe**c for c in range(13)]
    cache = {(a,b,c):xcp[a]*(yc if b else ring.one())*xep[c]
             for a,b,c in monomials(max_d)}
    rows = []
    for degree in protocol['weighted_degrees']:
        terms = monomials(degree)
        columns = [cache[t] for t in terms]
        precision = int(min(s.prec() for s in columns))
        assert precision > 1850,(p,degree,precision)
        training = matrix(field,[[s[n] for s in columns]
                                 for n in range(-degree,1701)])
        kernel = training.right_kernel()
        rank = int(training.ncols()-kernel.dimension())
        pivots = [int(v) for v in training.transpose().echelon_form().pivots()]
        assert len(pivots) == rank
        determinant = None
        if rank == training.ncols():
            determinant = int(training.matrix_from_rows(pivots).det())
            assert determinant != 0
        basis = []
        for vector in kernel.basis():
            combination = sum((vector[i]*columns[i] for i in range(len(columns))),
                              ring.zero())
            basis.append({'coefficients':[int(v) for v in vector],
                          'max_x_E_degree':max((terms[i][2] for i,v in enumerate(vector) if v),default=-1),
                          'holdout_zero':all(combination[n] == 0 for n in range(1701,1851))})
        result = {'prime':p,'weighted_degree':degree,'terms':terms,
                  'columns':int(training.ncols()),'training_rows':int(training.nrows()),
                  'training_rank':rank,'training_nullity':int(kernel.dimension()),
                  'pivot_rows':pivots,'pivot_minor_determinant_mod_p':determinant,
                  'kernel_basis':basis,'minimum_series_precision':precision}
        rows.append(result)
        print(json.dumps({k:result[k] for k in ('prime','weighted_degree','columns',
                           'training_rank','training_nullity','minimum_series_precision')},sort_keys=True),flush=True)
    return rows


def main():
    protocol_path = HERE/'extension_protocol.json'
    source_path = HERE/'qseries_extended.json'
    protocol = json.loads(protocol_path.read_text())
    source = json.loads(source_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_EXTENDED_RELATIVE_RESOLVENT'
    assert source['status'] == 'COMPLETE_EXTENDED_QSERIES'
    assert source['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert [r['prime'] for r in source['rows']] == protocol['auxiliary_fields']
    rows = [x for r in source['rows'] for x in screen(r,protocol)]
    out = {'status':'COMPLETE_EXTENDED_RELATIVE_RESOLVENT_SCREEN',
           'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
           'source_sha256':sha256(source_path.read_bytes()).hexdigest(),
           'rows':rows}
    (HERE/'screen_extended_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(rows)},sort_keys=True))


if __name__=='__main__':
    main()
