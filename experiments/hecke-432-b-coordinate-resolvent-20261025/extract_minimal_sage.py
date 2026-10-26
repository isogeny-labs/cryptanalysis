"""Find the first x_B relation inside the weight-56 kernels."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, matrix

HERE = Path(__file__).resolve().parent


def extract(row):
    p=row['prime']
    terms=row['terms']
    K=matrix(GF(p),[v['coefficients'] for v in row['kernel_basis']])
    assert K.nrows()==12 and K.ncols()==len(terms)
    cells=[]
    selected=None
    for weight in range(41,57):
        high=[j for j,(a,b,c) in enumerate(terms) if 2*a+3*b+2*c>weight]
        null=K.matrix_from_columns(high).transpose().right_kernel()
        dimension=int(null.dimension())
        cells.append({'weight':weight,'dimension':dimension})
        if dimension and selected is None:
            v=null.basis()[0]*K
            first=next(j for j,z in enumerate(v) if z)
            v *= v[first]**-1
            assert all(not v[j] for j in high)
            selected={'weight':weight,'dimension':dimension,
                      'normalizing_index':first,'normalizing_term':terms[first],
                      'coefficients':[int(z) for z in v],
                      'nonzero_terms':sum(bool(z) for z in v),
                      'max_x_B_degree':max(terms[j][2] for j,z in enumerate(v) if z)}
    return {'prime':p,'cells':cells,'minimal_relation':selected}


def main():
    screen_path=HERE/'screen_result.json'
    screen=json.loads(screen_path.read_text())
    assert screen['status']=='COMPLETE_B_COORDINATE_SCREEN'
    rows=[r for r in screen['rows'] if r['weighted_degree']==56]
    assert len(rows)==2
    results=[extract(r) for r in rows]
    assert results[0]['cells']==results[1]['cells']
    assert results[0]['minimal_relation']['weight']==results[1]['minimal_relation']['weight']
    out={'status':'COMPLETE_MINIMAL_B_RELATION_EXTRACTION',
         'screen_sha256':sha256(screen_path.read_bytes()).hexdigest(),
         'results':results}
    (HERE/'minimal_result.json').write_text(json.dumps(out,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],
          'minimal_weight':results[0]['minimal_relation']['weight'],
          'dimension':results[0]['minimal_relation']['dimension'],
          'nonzero_terms':[(r['prime'],r['minimal_relation']['nonzero_terms']) for r in results]},sort_keys=True))


if __name__=='__main__':
    main()
