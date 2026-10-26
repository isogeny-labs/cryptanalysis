"""Replay GF(997^4) E equations, Frobenius equivariance, and fiber counts."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class PrimePowerField:
    def __init__(self, prime, modulus):
        self.p = prime
        self.m = [coefficient % prime for coefficient in modulus]
        self.degree = len(modulus)-1
        assert self.m[-1] == 1
        self.zero = (0,)*self.degree
        self.one = (1,)+(0,)*(self.degree-1)

    def element(self, vector):
        assert len(vector) == self.degree
        assert all(isinstance(c,int) and 0 <= c < self.p for c in vector)
        return tuple(vector)

    def constant(self, value):
        return ((value % self.p),)+(0,)*(self.degree-1)

    def add(self, a, b):
        return tuple((x+y)%self.p for x,y in zip(a,b))

    def mul(self, a, b):
        coefficients = [0]*(2*self.degree-1)
        for i,x in enumerate(a):
            for j,y in enumerate(b):
                coefficients[i+j] = (coefficients[i+j]+x*y)%self.p
        for i in range(len(coefficients)-1,self.degree-1,-1):
            leading = coefficients[i]
            for j in range(self.degree):
                coefficients[i-self.degree+j] = (
                    coefficients[i-self.degree+j]-leading*self.m[j])%self.p
        return tuple(coefficients[:self.degree])

    def power(self, value, exponent):
        result = self.one
        while exponent:
            if exponent & 1:
                result = self.mul(result,value)
            value = self.mul(value,value)
            exponent >>= 1
        return result


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    count=json.loads((HERE/'count_result.json').read_text())
    evaluation=json.loads((HERE/'evaluation.json').read_text())
    assert count['protocol_sha256']==sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    assert evaluation['protocol_sha256']==count['protocol_sha256']
    assert evaluation['count_sha256']==sha256((HERE/'count_result.json').read_bytes()).hexdigest()
    assert evaluation['status']=='COMPLETE_GEOMETRIC_E_FIBER'
    assert [(r['extension_degree'],r['cyclic_16_path_count']) for r in count['rows']]==[(1,8),(2,16),(4,24)]
    assert evaluation['extension_degree']==count['selected_extension_degree']==4
    assert evaluation['field_modulus']==count['rows'][-1]['field_modulus']
    field=PrimePowerField(protocol['prime'],evaluation['field_modulus'])
    assert field.degree==4
    rows=evaluation['rows']
    assert evaluation['path_count']==evaluation['evaluated_count']==len(rows)==24
    assert [r['index'] for r in rows]==list(range(24))
    paths=[tuple(field.element(v) for v in r['root_vectors']) for r in rows]
    assert all(len(path)==4 for path in paths)
    assert len(set(paths))==24
    by_path={path:index for index,path in enumerate(paths)}
    images=[]
    for row in rows:
        assert row['status']=='PASS'
        point=row['E_point']
        if point is None:
            images.append(None)
            continue
        x,y=map(field.element,point)
        assert field.mul(y,y)==field.add(field.power(x,3),field.constant(432))
        assert field.power(x,field.p**4)==x
        assert field.power(y,field.p**4)==y
        images.append((x,y))
    assert len(set(images))==evaluation['distinct_E_outputs']==24
    assert evaluation['E_multiplicity_histogram']=={'1':24}
    orbit_lengths=[]
    for index,path in enumerate(paths):
        frobenius=tuple(field.power(root,field.p) for root in path)
        assert frobenius in by_path
        other=images[by_path[frobenius]]
        image=images[index]
        if image is None:
            assert other is None
        else:
            assert other==(field.power(image[0],field.p),
                           field.power(image[1],field.p))
        length=next(k for k in (1,2,4) if all(field.power(root,field.p**k)==root
                                            for root in path))
        orbit_lengths.append(length)
    assert Counter(orbit_lengths)==Counter({1:8,2:8,4:8})
    baseline_path=ROOT/'hecke-432-original-C-lift-20261025'/'result.json'
    baseline=json.loads(baseline_path.read_text())
    previous={None if r['E_point'] is None else tuple(r['E_point'])
              for r in baseline['rows']
              if r['C_point']==protocol['selected_C_point']}
    rational={None if image is None else
              ((image[0][0],image[1][0])) for image in images
              if image is None or all(c==0 for c in image[0][1:]+image[1][1:])}
    assert len(previous)==len(rational)==8
    assert previous==rational
    out={'status':'PASS_INDEPENDENT_GEOMETRIC_FIBER_AUDIT',
         'path_count':len(paths),'distinct_E_outputs':len(set(images)),
         'path_frobenius_degree_histogram':dict(sorted(Counter(orbit_lengths).items())),
         'rational_E_outputs_matching_prior_census':len(previous),
         'baseline_sha256':sha256(baseline_path.read_bytes()).hexdigest()}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':
    main()
