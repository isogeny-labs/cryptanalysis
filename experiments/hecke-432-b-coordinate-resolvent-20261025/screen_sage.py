"""Screen the frozen relative x_B monomial spaces in two prime fields."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, Infinity, LaurentSeriesRing, matrix

HERE = Path(__file__).resolve().parent


def monomials(bound):
    return [(a,b,c) for b in (0,1) for c in range(13)
            for a in range(bound//2+1)
            if 2*a+3*b+2*c <= bound]


def series_from_row(row,name,field,ring):
    q = ring.gen()
    lo,hi = row['coefficient_exponents']
    assert (lo,hi) == (-3,2000)
    return sum((field(v)*q**(lo+i) for i,v in enumerate(row[name]) if v),
               ring.zero()).add_bigoh(hi+1)


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_B_COORDINATE_SCREEN'
    source_path = Path(protocol['source_qseries'])
    assert sha256(source_path.read_bytes()).hexdigest() == protocol['source_sha256']
    source = json.loads(source_path.read_text())
    assert source['status'] == 'COMPLETE_EXTENDED_QSERIES'
    assert [r['prime'] for r in source['rows']] == protocol['fields']
    max_degree = max(protocol['weighted_degrees'])
    per_field = {}
    for row in source['rows']:
        field = GF(row['prime'])
        ring = LaurentSeriesRing(field,'q')
        xc = series_from_row(row,'xc',field,ring)
        yc = series_from_row(row,'yc',field,ring)
        xb = series_from_row(row,'xb',field,ring)
        xcp = [xc**a for a in range(max_degree//2+1)]
        xbp = [xb**c for c in range(13)]
        per_field[row['prime']] = (field,ring,
            {(a,b,c):xcp[a]*(yc if b else ring.one())*xbp[c]
             for a,b,c in monomials(max_degree)})
    results = []
    for degree in protocol['weighted_degrees']:
        terms = monomials(degree)
        for p in protocol['fields']:
            field,ring,cache = per_field[p]
            columns = [cache[t] for t in terms]
            precision = min(int(s.prec()) for s in columns if s.prec()!=Infinity)
            assert precision > 1850,(p,degree,precision)
            A = matrix(field,[[s[n] for s in columns]
                              for n in range(-degree,1701)])
            K = A.right_kernel()
            basis = []
            for v in K.basis():
                first = next(j for j,z in enumerate(v) if z)
                v *= v[first]**-1
                value = sum((v[j]*columns[j] for j in range(len(columns)) if v[j]),
                            ring.zero())
                basis.append({'normalizing_index':first,
                              'coefficients':[int(z) for z in v],
                              'holdout_zero':all(value[n]==0 for n in range(1701,1851)),
                              'max_x_B_degree':max(terms[j][2] for j,z in enumerate(v) if z)})
            result={'prime':p,'weighted_degree':degree,'terms':terms,
                    'columns':len(columns),'training_rows':int(A.nrows()),
                    'rank':int(A.ncols()-K.dimension()),'nullity':int(K.dimension()),
                    'minimum_series_precision':precision,'kernel_basis':basis}
            results.append(result)
            out={'status':'PARTIAL_B_COORDINATE_SCREEN',
                 'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
                 'source_sha256':sha256(source_path.read_bytes()).hexdigest(),
                 'rows':results}
            (HERE/'screen_result.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
            print(json.dumps({k:result[k] for k in ('prime','weighted_degree',
                'columns','rank','nullity','minimum_series_precision')},sort_keys=True),flush=True)
        if all(r['nullity'] and all(v['holdout_zero'] for v in r['kernel_basis'])
               for r in results[-2:]):
            break
    out['status']='COMPLETE_B_COORDINATE_SCREEN'
    (HERE/'screen_result.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps({'status':out['status'],'cells':len(results),
                      'last_weight':results[-1]['weighted_degree']},sort_keys=True))


if __name__=='__main__':
    main()
