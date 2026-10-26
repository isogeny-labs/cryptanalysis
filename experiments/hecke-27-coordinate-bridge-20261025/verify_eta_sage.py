"""Independently compare the published eta-product coordinates with 27a1."""
import json
from pathlib import Path

from sage.all import EllipticCurve, PowerSeriesRing, QQ

HERE = Path(__file__).resolve().parent


def eta_unit(q, m, precision):
    out = q.parent()(1)
    for k in range(1, (precision-1)//m+1):
        out *= 1-q**(m*k)
    return out


def main():
    precision = 90
    q = PowerSeriesRing(QQ, 'q', default_prec=precision).gen()
    U3, U9, U27 = (eta_unit(q,m,precision) for m in (3,9,27))
    X = q**(-2)*U9**4/(U3*U27**3)
    Y = q**(-3)*U3**3/U27**3
    x,y = EllipticCurve('27a1').modular_parametrization().power_series(precision)
    assert all(X[k]==x[k] and (-Y-5)[k]==y[k] for k in range(-3,60))
    result = {'status':'PASS_ETA_COORDINATE_CROSSCHECK', 'q_exponents_checked':[-3,59],
              'published_model':'Y^2+9Y=X^3-27',
              'optimal_model_change':'x=X, y=-Y-5'}
    (HERE/'eta_validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
