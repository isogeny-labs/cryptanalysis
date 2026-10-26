"""Compare the quarter-shift difference with the normalized 432a1 q-map."""
import json
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, Gamma0, GF, QuadraticField, QQ, LaurentSeriesRing, PolynomialRing

HERE = Path(__file__).resolve().parent


def main():
    precision = 210
    C = EllipticCurve(QQ, [0,0,1,0,-7])
    B = EllipticCurve(QQ, [0,0,0,0,-16])
    t = PolynomialRing(QQ, 't').gen()
    assert ((t**3-16)*(t**3+128)**2/t**6
            -((t**3-64)/t**2)**3-432) == 0
    K = QuadraticField(-1, 'i')
    i = K.gen()
    L = LaurentSeriesRing(K, 'q')
    q = L.gen()
    xC, yC = C.modular_parametrization().power_series(precision)
    xB, yB = B.modular_parametrization().power_series(precision)
    xp, yp = L(xC)(i*q), L(yC)(i*q)
    xm, ym = L(xC)(-i*q), L(yC)(-i*q)
    # Pplus-Pminus on y^2+y=x^3-7.
    yneg = -ym-1
    slope = (yneg-yp)/(xm-xp)
    xD = slope*slope-xp-xm
    yD = slope*(xp-xD)-yp-1
    Hx, Hy = -4*xD, -8*i*(yD+K(1)/2)
    assert all(Hx[n] == Hx[n].conjugate() for n in range(Hx.valuation(), Hx.prec()))
    assert all(Hy[n] == Hy[n].conjugate() for n in range(Hy.valuation(), Hy.prec()))
    bx, by = L(xB), L(yB)
    dual_x = (bx**3-64)/bx**2
    dual_y = by*(bx**3+128)/bx**3
    pullback_quarter = q*Hx.derivative()/(2*Hy)
    pullback_dual = q*dual_x.derivative()/(2*dual_y)
    assert Gamma0(432).index() == 864
    sturm_bound = Gamma0(432).sturm_bound(2)
    assert sturm_bound == 144
    differential_check_precision = int(min(pullback_quarter.prec(),pullback_dual.prec()))
    assert differential_check_precision > sturm_bound
    assert (pullback_quarter-pullback_dual).valuation() >= sturm_bound+1
    Fp = GF(883)
    Bp = EllipticCurve(Fp, [0,0,0,0,-16])
    Ep = EllipticCurve(Fp, [0,0,0,0,432])
    def dual_point(P):
        if P.is_zero():
            return Ep(0)
        X, Y = P[0], P[1]
        return Ep((X**3-64)/X**2, Y*(X**3+128)/X**3)
    dual_images = [dual_point(P) for P in Bp.points()]
    assert Bp.cardinality() == Ep.cardinality() == len(set(dual_images)) == 931
    assert sum(P.is_zero() for P in dual_images) == 1
    out = {'precision_requested':precision,
           'quarter_shift_E_x':str(Hx), 'quarter_shift_E_y':str(Hy),
           'dual_B_x':str(dual_x), 'dual_B_y':str(dual_y),
           'x_difference_valuation':int((Hx-dual_x).valuation()) if Hx != dual_x else None,
           'y_difference_valuation':int((Hy-dual_y).valuation()) if Hy != dual_y else None,
           'x_agrees_to':int(min(Hx.prec(),dual_x.prec())),
           'y_agrees_to':int(min(Hy.prec(),dual_y.prec())),
           'sturm_bound_weight_two_level_432':int(sturm_bound),
           'differential_checked_through':differential_check_precision-1,
           'differential_equal_through_bound':True,
           'quarter_map_cusp_pole_orders':[-int(Hx.valuation()),-int(Hy.valuation())],
           'Fp883_B_and_E_order':931,'Fp883_dual_image_size':len(set(dual_images)),
           'Fp883_dual_identity_preimages':1,'coefficient_descent_to_Q_checked':True}
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('precision_requested','x_difference_valuation',
                                        'y_difference_valuation','x_agrees_to','y_agrees_to',
                                        'sturm_bound_weight_two_level_432',
                                        'differential_checked_through')},sort_keys=True))


if __name__=='__main__':
    main()
