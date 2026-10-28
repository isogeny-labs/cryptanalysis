"""Independent SymPy resultant replay for the j1728 source equation."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import sympy as sp

HERE=Path(__file__).resolve().parent


def main():
    protocol_path=HERE/'elimination_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_CHARACTERISTIC_ZERO_J1728_ELIMINATION'
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    result_path=HERE/'elimination_result.json'
    result=json.loads(result_path.read_text())
    assert result['protocol_sha256']==sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256']==sha256((HERE/'eliminate_sage.py').read_bytes()).hexdigest()
    record=json.loads(Path(protocol['inputs']['coordinate_map']['path']).read_text())['source_j']
    x,y=sp.symbols('x y')
    def polynomial(terms):
        total=sp.Integer(0)
        for t in terms:
            q=Fraction(t['coefficient'])
            total+=sp.Rational(q.numerator,q.denominator)*x**t['x_power']*y**t['y_power']
        return total
    h=polynomial(record['numerator'])+1728*polynomial(record['denominator'])
    curve=y*y+y-x**3+7
    res=sp.Poly(sp.resultant(h,curve,y),x,domain=sp.QQ)
    den=sp.ilcm(*[c.q for c in res.all_coeffs()])
    ints=sp.Poly(sp.expand(res.as_expr()*den),x,domain=sp.ZZ)
    content,primitive=ints.primitive()
    if primitive.LC()<0:primitive=-primitive
    actual=[int(c) for c in reversed(primitive.all_coeffs())]
    expected=[int(c) for c in result['primitive_resultant_coefficients_low_to_high']]
    assert actual==expected and primitive.degree()==36
    factor=result['factors'][0]
    f=sp.Poly.from_list(list(reversed([sp.Rational(c) for c in factor['coefficients_low_to_high']])),gens=x,domain=sp.QQ)
    assert f.degree()==18 and factor['multiplicity']==2
    _,factorization=sp.factor_list(f)
    assert len(factorization)==1 and factorization[0][0].degree()==18 and factorization[0][1]==1
    quotient=sp.cancel(res.as_expr()/f.as_expr()**2)
    assert quotient.is_Rational and quotient!=0
    out={'status':'PASS_INDEPENDENT_SYMPY_J1728_RESULTANT_AUDIT',
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'resultant_degree':36,'factor_degree':18,'factor_multiplicity':2,
         'resultant_factor_square_scalar':str(quotient)}
    (HERE/'elimination_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
