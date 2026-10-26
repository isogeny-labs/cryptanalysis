"""Find the lowest pole-weight relation inside the certified D=96 kernels."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, matrix

HERE = Path(__file__).resolve().parent


def extract(row):
    p = row['prime']
    field = GF(p)
    terms = row['terms']
    K = matrix(field,[x['coefficients'] for x in row['kernel_basis']])
    assert K.nrows() == 6 and K.ncols() == len(terms)
    cells = []
    selected = None
    for D in range(81,97):
        high = [j for j,(a,b,c) in enumerate(terms) if 2*a+3*b+2*c > D]
        constraints = K.matrix_from_columns(high).transpose()
        null = constraints.right_kernel()
        dimension = int(null.dimension())
        cells.append({'weight':D,'relation_dimension':dimension})
        if dimension and selected is None:
            combination = null.basis()[0]
            vector = combination*K
            first = next(j for j,v in enumerate(vector) if v)
            vector *= vector[first]**-1
            assert all(not vector[j] for j in high)
            selected = {'weight':D,'dimension':dimension,
                        'normalizing_term':terms[first],
                        'normalizing_index':first,
                        'coefficients':[int(v) for v in vector],
                        'nonzero_terms':sum(bool(v) for v in vector),
                        'max_x_E_degree':max(terms[j][2] for j,v in enumerate(vector) if v)}
    assert selected is not None
    return {'prime':p,'cells':cells,'minimal_relation':selected}


def main():
    path = HERE/'screen_extended_result.json'
    screen = json.loads(path.read_text())
    assert screen['status'] == 'COMPLETE_EXTENDED_RELATIVE_RESOLVENT_SCREEN'
    rows = [r for r in screen['rows'] if r['weighted_degree'] == 96]
    assert len(rows) == 2
    results = [extract(row) for row in rows]
    assert results[0]['cells'] == results[1]['cells']
    assert results[0]['minimal_relation']['weight'] == results[1]['minimal_relation']['weight']
    out = {'status':'COMPLETE_MINIMAL_RELATION_EXTRACTION',
           'screen_sha256':sha256(path.read_bytes()).hexdigest(),
           'results':results}
    (HERE/'minimal_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],
                      'minimal_weight':results[0]['minimal_relation']['weight'],
                      'dimension':results[0]['minimal_relation']['dimension'],
                      'nonzero_terms':[(r['prime'],r['minimal_relation']['nonzero_terms']) for r in results]},sort_keys=True))


if __name__=='__main__':
    main()
