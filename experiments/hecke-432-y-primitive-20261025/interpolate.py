"""Independently interpolate x_E as a polynomial in y_E on the 24-fiber."""
import json
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class Field:
    def __init__(self, p, modulus):
        self.p = p
        self.m = [v % p for v in modulus]
        self.n = len(modulus)-1
        assert self.m[-1] == 1
        self.zero = (0,)*self.n
        self.one = (1,)+(0,)*(self.n-1)

    def element(self, values):
        assert len(values) == self.n
        assert all(isinstance(v,int) and 0 <= v < self.p for v in values)
        return tuple(values)

    def constant(self, value):
        return (value % self.p,)+(0,)*(self.n-1)

    def add(self, a, b):
        return tuple((x+y)%self.p for x,y in zip(a,b))

    def neg(self, a):
        return tuple(-x%self.p for x in a)

    def mul(self, a, b):
        product = [0]*(2*self.n-1)
        for i,x in enumerate(a):
            for j,y in enumerate(b):
                product[i+j] = (product[i+j]+x*y)%self.p
        for i in range(len(product)-1,self.n-1,-1):
            top = product[i]
            for j in range(self.n):
                product[i-self.n+j] = (product[i-self.n+j]-top*self.m[j])%self.p
        return tuple(product[:self.n])

    def power(self, value, exponent):
        result = self.one
        while exponent:
            if exponent&1:
                result = self.mul(result,value)
            value = self.mul(value,value)
            exponent >>= 1
        return result

    def inverse(self, value):
        assert value != self.zero
        result = self.power(value,self.p**self.n-2)
        assert self.mul(result,value) == self.one
        return result


def poly_mul(f, a, b):
    result = [f.zero]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            result[i+j] = f.add(result[i+j],f.mul(x,y))
    return result


def poly_eval(f, poly, value):
    result = f.zero
    for coefficient in reversed(poly):
        result = f.add(f.mul(result,value),coefficient)
    return result


def divide_linear(f, poly, root):
    quotient = [f.zero]*(len(poly)-1)
    quotient[-1] = poly[-1]
    for i in range(len(poly)-2,0,-1):
        quotient[i-1] = f.add(poly[i],f.mul(root,quotient[i]))
    assert f.add(poly[0],f.mul(root,quotient[0])) == f.zero
    return quotient


def main():
    protocol_path = HERE/'interpolation_protocol.json'
    data_path = ROOT/'hecke-432-geometric-fiber-20261025'/'evaluation.json'
    audit_path = ROOT/'hecke-432-geometric-fiber-20261025'/'audit.json'
    protocol = json.loads(protocol_path.read_text())
    data = json.loads(data_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_Y_FIBER_INTERPOLATION'
    assert audit['status'] == 'PASS_INDEPENDENT_GEOMETRIC_FIBER_AUDIT'
    assert data['status'] == 'COMPLETE_GEOMETRIC_E_FIBER'
    assert data['extension_degree'] == 4 and len(data['rows']) == 24
    f = Field(997,data['field_modulus'])
    pairs = [(f.element(row['E_point'][1]),f.element(row['E_point'][0]))
             for row in data['rows']]
    assert len({y for y,x in pairs}) == 24
    M = [f.one]
    for y,x in pairs:
        M = poly_mul(f,M,[f.neg(y),f.one])
    assert len(M) == 25 and M[-1] == f.one
    P = [f.zero]*24
    for y,x in pairs:
        quotient = divide_linear(f,M,y)
        denominator = poly_eval(f,quotient,y)
        factor = f.mul(x,f.inverse(denominator))
        for j,value in enumerate(quotient):
            P[j] = f.add(P[j],f.mul(factor,value))
    assert all(poly_eval(f,M,y) == f.zero and poly_eval(f,P,y) == x
               for y,x in pairs)
    assert all(f.power(x,3) == f.add(f.power(y,2),f.constant(-432))
               for y,x in pairs)
    assert all(all(v == 0 for v in c[1:]) for c in M+P)
    m = [c[0] for c in M]
    p = [c[0] for c in P]
    assert m[-1] == 1
    cube = [0]*(3*(len(p)-1)+1)
    for i,a in enumerate(p):
        for j,b in enumerate(p):
            for k,c in enumerate(p):
                cube[i+j+k] = (cube[i+j+k]+a*b*c)%997
    cube[2] = (cube[2]-1)%997
    cube[0] = (cube[0]+432)%997
    for i in range(len(cube)-1,23,-1):
        top = cube[i]
        for j in range(24):
            cube[i-24+j] = (cube[i-24+j]-top*m[j])%997
        cube[i] = 0
    assert all(v == 0 for v in cube)
    assert all(m[i] == 0 for i in range(1,25,2))
    assert all(p[i] == 0 for i in range(1,24,2))
    Q = [m[2*i] for i in range(13)]
    R = [p[2*i] for i in range(12)]
    out = {'status':'PASS_SPECIAL_FIBER_Y_INTERPOLATION',
           'field_modulus':data['field_modulus'],
           'geometric_points':24,
           'fiber_polynomial_degree':24,
           'interpolant_degree':max(i for i,v in enumerate(p) if v),
           'M_coefficients_low_to_high':m,
           'P_coefficients_low_to_high':p,
           'Q_in_z_equals_y_squared_coefficients_low_to_high':Q,
           'R_for_x_in_z_equals_y_squared_coefficients_low_to_high':R,
           'cubic_remainder_zero':True,
           'M_odd_coefficients_zero':all(m[i] == 0 for i in range(1,25,2)),
           'P_odd_coefficients_zero':all(p[i] == 0 for i in range(1,24,2)),
           'input_sha256':{'protocol':sha256(protocol_path.read_bytes()).hexdigest(),
                           'evaluation':sha256(data_path.read_bytes()).hexdigest(),
                           'independent_arithmetic_audit':sha256(audit_path.read_bytes()).hexdigest()}}
    (HERE/'interpolation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','geometric_points','fiber_polynomial_degree',
                       'interpolant_degree','M_odd_coefficients_zero',
                       'P_odd_coefficients_zero')},sort_keys=True))


if __name__ == '__main__':
    main()
