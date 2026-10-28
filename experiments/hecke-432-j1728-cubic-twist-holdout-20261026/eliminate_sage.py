"""Exact characteristic-zero j1728 eliminant on the C model."""
import json
from hashlib import sha256
from pathlib import Path
from sage.all import QQ, ZZ, PolynomialRing, gcd, lcm

HERE=Path(__file__).resolve().parent


def main():
    protocol_path=HERE/'elimination_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_CHARACTERISTIC_ZERO_J1728_ELIMINATION'
    for name,rec in protocol['inputs'].items():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256'],name
    coord=json.loads(Path(protocol['inputs']['coordinate_map']['path']).read_text())['source_j']
    Qx=PolynomialRing(QQ,'x');x=Qx.gen()
    Qxy=PolynomialRing(Qx,'y');y=Qxy.gen()
    def expression(terms):
        return sum((QQ(term['coefficient'])*x**term['x_power']*y**term['y_power'] for term in terms),Qxy.zero())
    n=expression(coord['numerator']);d=expression(coord['denominator'])
    h=n+1728*d
    curve=y*y+y-x**3+7
    result=h.resultant(curve)
    factors=[{'degree':int(f.degree()),'multiplicity':int(m),
              'coefficients_low_to_high':[str(c) for c in f.list()]}
             for f,m in result.factor()]
    content=lcm([c.denominator() for c in result.list()])
    coefficients=[ZZ(content*c) for c in result.list()]
    divisor=gcd(coefficients)
    primitive=Qx([c/divisor for c in coefficients])
    if primitive.leading_coefficient()<0:
        primitive=-primitive
    out={'status':'EXACT_J1728_X_ELIMINANT','protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'resultant_degree':int(result.degree()),
         'primitive_resultant_coefficients_low_to_high':[str(c) for c in primitive.list()],
         'factors':factors}
    (HERE/'elimination_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'degree':out['resultant_degree'],'factors':[(r['degree'],r['multiplicity']) for r in factors]}))


if __name__=='__main__':main()
