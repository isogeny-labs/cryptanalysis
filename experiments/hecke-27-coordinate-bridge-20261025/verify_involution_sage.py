"""Prove the two j-functions exchange under T-P on 27a1."""
import json
from pathlib import Path

from sage.all import FunctionField, PolynomialRing, QQ

HERE=Path(__file__).resolve().parent


def value(terms,x,y):
    return sum(QQ(t['coefficient'])*x**t['x_power']*y**t['y_power']
               for t in terms)


def jval(mapping,x,y):
    return -value(mapping['numerator'],x,y)/value(mapping['denominator'],x,y)


def main():
    maps=json.loads((HERE/'coordinate_map.json').read_text())
    K=FunctionField(QQ,'x')
    x=K.gen()
    Y=PolynomialRing(K,'Y').gen()
    L=K.extension(Y**2+Y-(x**3-7),'y')
    y=L.gen()
    slope=(-y+4)/(x-3)
    xw=slope**2-x-3
    yw=slope*(3-xw)+4
    assert yw**2+yw==xw**3-7
    assert jval(maps['source_j'],x,y)==jval(maps['target_j'],xw,yw)
    result={'status':'PASS_EXACT_ATKIN_LEHNER_EXCHANGE',
            'involution':'P -> (3,-5) - P',
            'source_equals_target_after_involution':True,
            'function_field':'QQ(x)[y]/(y^2+y-x^3+7)'}
    (HERE/'involution_validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
