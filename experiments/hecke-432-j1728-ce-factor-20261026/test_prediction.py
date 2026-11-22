"""Prospective factor-parity test on the source-free selected primes."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from sympy import Poly, Symbol, factor_list

from factor_sample import coefficients

HERE = Path(__file__).resolve().parent
X = Symbol('x_E')


def main():
    pp = HERE/'protocol.json'; sp = HERE/'selection.json'
    protocol = json.loads(pp.read_text()); selection = json.loads(sp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_PROSPECTIVE_SOURCE_SELECTION'
    assert selection['status']=='PROSPECTIVE_SOURCE_SELECTION_COMPLETE'
    assert selection['protocol_sha256']==sha256(pp.read_bytes()).hexdigest()
    rp = Path(protocol['inputs']['resolvent']['path'])
    assert sha256(rp.read_bytes()).hexdigest()==protocol['inputs']['resolvent']['sha256']
    terms = json.loads(rp.read_text())['terms']
    rows = []; cells = []
    for residue in (1,5,11):
        for selected in selection['selected'][str(residue)]:
            p = selected['prime']; source_rows = []
            for c in selected['C_points']:
                a = coefficients(terms,c,p)
                f = Poly.from_list(list(reversed(a)),X,modulus=p)
                _, factors = factor_list(f)
                degrees = sorted(q.degree() for q,m in factors for _ in range(m))
                assert sum(degrees)==12
                linear = []
                for q,m in factors:
                    if q.degree()!=1:continue
                    b0,b1 = [int(q.nth(i))%p for i in (0,1)]
                    xe = -b0*pow(b1,-1,p)%p
                    rhs = (xe**3+432)%p
                    count = 1 if rhs==0 else (2 if pow(rhs,(p-1)//2,p)==1 else 0)
                    linear.append({'x_E':xe,'multiplicity':m,'rational_E_y_count':count})
                row = {'prime':p,'class_mod_12':residue,'C_point':c,
                       'factor_degrees':degrees,'linear_roots':linear,
                       'rational_CE_pairs':sum(z['rational_E_y_count'] for z in linear)}
                rows.append(row); source_rows.append(row)
            actual_pairs = sum(r['rational_CE_pairs'] for r in source_rows)
            if residue==1:
                passed = len(source_rows)>=18 and all(all(d%2==0 for d in r['factor_degrees']) for r in source_rows) and actual_pairs==0
            elif residue==11:
                passed = len(source_rows)>=2 and all(r['factor_degrees']==[1,1,1,1,2,2,2,2] for r in source_rows) and actual_pairs>0
            else:
                passed = not source_rows
            cell = {'prime':p,'class_mod_12':residue,'C_points':len(source_rows),
                    'rational_CE_pairs':actual_pairs,
                    'factor_patterns':{str(k):v for k,v in Counter(tuple(r['factor_degrees']) for r in source_rows).items()},
                    'prediction_pass':passed}
            cells.append(cell)
            print(json.dumps(cell,sort_keys=True),flush=True)
    out={'status':'PASS_PROSPECTIVE_FACTOR_PARITY' if all(c['prediction_pass'] for c in cells) else 'FAIL_PROSPECTIVE_FACTOR_PARITY',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'selection_sha256':sha256(sp.read_bytes()).hexdigest(),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'factor_helper_sha256':sha256((HERE/'factor_sample.py').read_bytes()).hexdigest(),
         'cells':cells,'rows':rows}
    (HERE/'test_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'cells':len(cells),'rows':len(rows)}))


if __name__=='__main__':main()
