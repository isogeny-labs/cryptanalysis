"""Prospective source-free p1367 restricted-Jacobian screen."""
import importlib.util
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(path):
    spec = importlib.util.spec_from_file_location('frozen_inverse', path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def gradients(terms, c, b, p):
    x, y = c
    t, by = b
    dcx, dcy = (2*y+1) % p, 3*x*x % p
    value = dt = dc = 0
    for row in terms:
        coeff = int(row['integer_coefficient']) % p
        a, e, k = row['x_C_exponent'], row['y_C_exponent'], row['x_B_exponent']
        xa, ye, tk = pow(x,a,p), pow(y,e,p), pow(t,k,p)
        value += coeff*xa*ye*tk
        if k:
            dt += coeff*k*xa*ye*pow(t,k-1,p)
        if a:
            dc += dcx*coeff*a*pow(x,a-1,p)*ye*tk
        if e:
            dc += dcy*coeff*e*xa*pow(y,e-1,p)*tk
    value, dt, dc = value%p, dt%p, dc%p
    return value, dt, dc, (2*by*dt)%p


def main():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_P1367_SOURCE_FREE_SCREEN'
    for name, record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256'], name
    p = protocol['prime']
    assert p == 1367
    inverse = module(protocol['inputs']['inverse_filter']['path'])
    resolvent = json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    branch = json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    terms = json.loads(Path(protocol['inputs']['b_resolvent']['path']).read_text())['terms']
    cs, es = inverse.curve_points(p, 'C'), inverse.curve_points(p, 'E')
    e_by_x = defaultdict(list)
    for ex, ey in es:
        e_by_x[ex].append(ey)
    rows=[]
    for c in cs:
        coeffs=inverse.resolvent_coefficients(resolvent['terms'],c,p)
        for ex, ys in e_by_x.items():
            if inverse.horner(coeffs,ex,p):
                continue
            for ey in ys:
                e=(ex,ey)
                evaluated=inverse.evaluate_pair(c,e,p,resolvent,branch)
                row={'C_point':list(c),'E_point':list(e),**evaluated}
                if evaluated['status']=='VALID':
                    b=evaluated['B_point']
                    val,dt,dc,db=gradients(terms,c,b,p)
                    assert val==0
                    row.update({'dT':dt,'dC':dc,'restricted_B_derivative':db,
                                'predicted_double':dc==0 and db==0})
                rows.append(row)
    rows.sort(key=lambda r:(r['C_point'],r['E_point']))
    outpath=HERE/'source_free_rows.json'
    outpath.write_text(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n')
    valid=[r for r in rows if r['status']=='VALID']
    hist=Counter((r['dC']==0,r['restricted_B_derivative']==0,r['predicted_double']) for r in valid)
    result={'status':'COMPLETE_P1367_SOURCE_FREE_JACOBIAN_SCREEN',
            'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
            'screen_source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'rows_sha256':sha256(outpath.read_bytes()).hexdigest(),
            'C_group_order':len(cs)+1,'E_group_order':len(es)+1,
            'resolvent_pairs':len(rows),'valid_triples':len(valid),
            'status_histogram':dict(Counter(r['status'] for r in rows)),
            'predicted_doubles':sum(r['predicted_double'] for r in valid),
            'gradient_histogram':[{'dC_zero':a,'dB_zero':b,'predicted_double':c,'count':v} for (a,b,c),v in sorted(hist.items())]}
    (HERE/'screen_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('resolvent_pairs','valid_triples','predicted_doubles','status_histogram')},sort_keys=True))


if __name__=='__main__':
    main()
