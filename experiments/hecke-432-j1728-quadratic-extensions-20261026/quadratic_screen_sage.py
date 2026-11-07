"""Factor the certified quartic and octic after small quadratic extensions."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, ZZ, NumberField, PolynomialRing

HERE=Path(__file__).resolve().parent


def from_vector(coeffs,a,K):
    out=K(0)
    for c in reversed(coeffs):out=out*a+K(QQ(c))
    return out


def main():
    pp=HERE/'protocol.json';protocol=json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_QUADRATIC_EXTENSION_FACTORIZATION'
    cp=Path(protocol['input']['path'])
    assert sha256(cp.read_bytes()).hexdigest()==protocol['input']['sha256']
    cert=json.loads(cp.read_text())
    Qx=PolynomialRing(QQ,'x')
    f=Qx([QQ(c) for c in cert['field_polynomial_coefficients_low_to_high']])
    K=NumberField(f,'a');a=K.gen()
    Kz=PolynomialRing(K,'z')
    factors=[Kz([from_vector(c,a,K) for c in record['coefficients_low_to_high']])
             for record in cert['factors']]
    assert [int(g.degree()) for g in factors]==[4,8]
    Kt=PolynomialRing(K,'t');t=Kt.gen()
    rows=[]
    for d in protocol['radicands']:
        row={'radicand':d,'square_in_K':bool(K(d).is_square())}
        if row['square_in_K']:
            row.update({'status':'ALREADY_IN_COORDINATE_FIELD',
                        'quartic_degrees':[4],'octic_degrees':[8]})
        else:
            try:
                L=K.extension(t*t-K(d),'s')
                Lz=PolynomialRing(L,'z')
                degrees=[]
                for g in factors:
                    h=Lz([L(c) for c in g.list()])
                    factorization=h.factor()
                    assert factorization.prod()==h
                    assert all(q.is_irreducible() for q,m in factorization)
                    pieces=sorted(int(q.degree()) for q,m in factorization for _ in range(m))
                    assert sum(pieces)==g.degree()
                    degrees.append(pieces)
                row.update({'status':'EXACT_EXTENSION_FACTORIZATION',
                            'extension_degree_over_K':int(L.relative_degree()),
                            'quartic_degrees':degrees[0],'octic_degrees':degrees[1]})
            except Exception as exc:
                row.update({'status':'FACTORING_ERROR','error_type':type(exc).__name__,
                            'error':str(exc)[:300]})
        rows.append(row)
        (HERE/'quadratic_result.json').write_text(json.dumps({
            'status':'IN_PROGRESS','protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
            'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'cells':rows},sort_keys=True,indent=2)+'\n')
        print(json.dumps(row,sort_keys=True),flush=True)
    status='EXACT_QUADRATIC_EXTENSION_SCREEN' if all(r['status']!='FACTORING_ERROR' for r in rows) else 'PARTIAL_QUADRATIC_EXTENSION_SCREEN'
    out={'status':status,'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),'cells':rows}
    (HERE/'quadratic_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':status,'cells':len(rows)}))


if __name__=='__main__':main()
