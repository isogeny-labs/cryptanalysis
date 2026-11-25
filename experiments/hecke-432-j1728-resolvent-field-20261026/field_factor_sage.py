"""Characteristic-zero specialization of the C-E resolvent at source j=1728."""
import json
from hashlib import sha256
from pathlib import Path

from sage.all import QQ, ZZ, NumberField, PolynomialRing

HERE = Path(__file__).resolve().parent


def terms_in_xy(terms,x,y,parent):
    return sum((QQ(t['coefficient'])*x**t['x_power']*y**t['y_power'] for t in terms),parent.zero())


def k_vector(q):
    return [str(c) for c in q.polynomial().list()]


def main():
    pp=HERE/'protocol.json'; protocol=json.loads(pp.read_text())
    assert protocol['status']=='FROZEN_BEFORE_CHARACTERISTIC_ZERO_RESOLVENT_SPECIALIZATION'
    for name,rec in protocol['inputs'].items():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256'],name
    coord=json.loads(Path(protocol['inputs']['coordinate']['path']).read_text())['source_j']
    eliminant=json.loads(Path(protocol['inputs']['eliminant']['path']).read_text())
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    Qx=PolynomialRing(QQ,'x');x=Qx.gen()
    Qxy=PolynomialRing(Qx,'y');y=Qxy.gen()
    h=terms_in_xy(coord['numerator'],x,y,Qxy)+1728*terms_in_xy(coord['denominator'],x,y,Qxy)
    curve=y*y+y-x**3+7
    rem=h%curve
    assert rem.degree()==1
    A,B=rem[0],rem[1]
    f=Qx([QQ(t) for t in eliminant['factors'][0]['coefficients_low_to_high']])
    assert f.degree()==18 and f.leading_coefficient()==1
    K=NumberField(f,'a');a=K.gen()
    ya=-A(a)/B(a)
    assert ya*ya+ya==a**3-7
    assert A(a)+B(a)*ya==0
    print(json.dumps({'stage':'exact_coordinate_field','degree':int(K.degree()),
                      'reduced_j_equation_y_degree':int(rem.degree()),
                      'B_nonzero':bool(B(a))}),flush=True)
    checkpoint={'status':'EXACT_J1728_COORDINATE_FIELD',
                'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
                'source_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
                'field_degree':int(K.degree()),
                'A_coefficients_low_to_high':[str(c) for c in A.list()],
                'B_coefficients_low_to_high':[str(c) for c in B.list()],
                'curve_identity_verified':True,'source_j_identity_verified':True}
    (HERE/'coordinate_field.json').write_text(json.dumps(checkpoint,sort_keys=True,indent=2)+'\n')
    Kz=PolynomialRing(K,'z');z=Kz.gen()
    R=Kz.zero()
    for t in resolvent['terms']:
        R += ZZ(t['integer_coefficient'])*a**t['x_C_exponent']*ya**t['y_C_exponent']*z**t['x_E_exponent']
    assert R.degree()==12
    print(json.dumps({'stage':'resolvent_built','degree':int(R.degree())}),flush=True)
    factors=R.factor()
    rows=[{'degree':int(g.degree()),'multiplicity':int(m),
           'nonzero_exponents':[i for i,c in enumerate(g.list()) if c],
           'coefficient_sha256':sha256(json.dumps([str(c) for c in g.list()]).encode()).hexdigest()}
          for g,m in factors]
    assert sum(q['degree']*q['multiplicity'] for q in rows)==12
    assert Kz(factors.prod())==R
    certificate={'field_polynomial_coefficients_low_to_high':[str(c) for c in f.list()],
                 'source_y_numerator_coefficients_low_to_high':[str(c) for c in (-A).list()],
                 'source_y_denominator_coefficients_low_to_high':[str(c) for c in B.list()],
                 'unit':k_vector(factors.unit()),
                 'factors':[{'multiplicity':int(m),
                             'coefficients_low_to_high':[k_vector(c) for c in g.list()]}
                            for g,m in factors]}
    cp=HERE/'factor_certificate.json'
    cp.write_text(json.dumps(certificate,sort_keys=True,indent=2)+'\n')
    out={**checkpoint,'status':'EXACT_J1728_CE_RESOLVENT_FACTORIZATION',
         'resolvent_degree':int(R.degree()),'factors':rows,
         'factor_certificate_sha256':sha256(cp.read_bytes()).hexdigest()}
    (HERE/'field_factor_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'stage':'factored','degrees':[(q['degree'],q['multiplicity']) for q in rows]}),flush=True)


if __name__=='__main__':main()
