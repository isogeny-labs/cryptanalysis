"""Recover 27a1 coordinates from both j-values of a cyclic 27-isogeny."""
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, sage_eval

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent/'hecke-432-moduli-shift-evaluator-20261025'/'result.json'


def components(terms, z, field):
    out = [z.parent().zero(), z.parent().zero()]
    for term in terms:
        out[term['y_power']] += field(QQ(term['coefficient'])) * z**term['x_power']
    return out


def roots_for_pair(curve, coordinate_map, js, jt):
    field = curve.base_field()
    poly = PolynomialRing(field, 'z')
    z = poly.gen()
    a0, a1 = components(coordinate_map['source_j']['denominator'], z, field)
    b0, b1 = components(coordinate_map['source_j']['numerator'], z, field)
    c0, c1 = components(coordinate_map['target_j']['denominator'], z, field)
    d0, d1 = components(coordinate_map['target_j']['numerator'], z, field)
    f0, f1 = js*a0+b0, js*a1+b1
    g0, g1 = jt*c0+d0, jt*c1+d1
    eliminant = f0*g1-g0*f1
    assert eliminant != 0
    points = []
    for xx, _ in eliminant.roots():
        if f1(xx):
            ys = [-f0(xx)/f1(xx)]
        elif g1(xx):
            ys = [-g0(xx)/g1(xx)]
        else:
            ys = [P[1] for P in curve.lift_x(xx, all=True)]
        for yy in ys:
            if yy*yy+yy != xx**3-7:
                continue
            if not (f0(xx)+f1(xx)*yy == 0 and g0(xx)+g1(xx)*yy == 0):
                continue
            if not (a0(xx)+a1(xx)*yy and c0(xx)+c1(xx)*yy):
                continue
            points.append(curve(xx,yy))
    return eliminant, points


def dual_image(P, E):
    if P.is_zero() or P[0] == 0:
        return E(0)
    x, y = P[0], P[1]
    return E((x**3-64)/x**2, y*(x**3+128)/x**3)


def dual_preimages(H, B, E):
    if H.is_zero():
        return [B(0)] if B.base_field().cardinality() % 4 == 3 else []
    t = PolynomialRing(B.base_field(), 't').gen()
    return [P for xx,_ in (t**3-H[0]*t**2-64).roots()
            for P in B.lift_x(xx, all=True) if dual_image(P,E)==H]


def main():
    maps = json.loads((HERE/'coordinate_map.json').read_text())
    previous = json.loads(PREVIOUS.read_text())
    cases = []
    for record in previous['cases']:
        p, degree = record['prime'], record['field_degree']
        field = GF(p**degree, 'u')
        u = field.gen()
        curve = EllipticCurve(field, maps['curve_ainvs'])
        outputs = []
        recovered = []
        for row in record['outputs']:
            js = sage_eval(row['curve_j'], locals={'u':u})
            jt = sage_eval(row['level27_quotient_j'], locals={'u':u})
            eliminant, points = roots_for_pair(curve,maps,js,jt)
            recovered.append(points)
            outputs.append({'shift':row['shift'], 'j_source':str(js), 'j_target':str(jt),
                            'eliminant_degree':int(eliminant.degree()),
                            'eliminant_roots_over_input_field':len(eliminant.roots()),
                            'coordinate_points':[[str(P[0]),str(P[1])] for P in points],
                            'coordinate_point_count':len(points)})
        descent = None
        if degree == 2 and all(o['coordinate_point_count']==1 for o in outputs):
            Pplus=outputs[0]['coordinate_points'][0]
            Pminus=outputs[1]['coordinate_points'][0]
            assert sage_eval(Pplus[0],locals={'u':u})**p == sage_eval(Pminus[0],locals={'u':u})
            assert sage_eval(Pplus[1],locals={'u':u})**p == sage_eval(Pminus[1],locals={'u':u})
            D = recovered[0][0]-recovered[1][0]
            assert not D.is_zero()
            i = sage_eval(record['chosen_i'], locals={'u':u})
            assert i**2 == -1 and i**p == -i
            xe, ye = -4*D[0], -8*i*(D[1]+field(1)/2)
            assert xe**p == xe and ye**p == ye
            base = GF(p)
            E = EllipticCurve(base,[0,0,0,0,432])
            B = EllipticCurve(base,[0,0,0,0,-16])
            H = E(base(xe),base(ye))
            preimages = dual_preimages(H,B,E)
            assert len(preimages)==1 and dual_image(preimages[0],E)==H
            Q = preimages[0]
            descent = {'C_difference':[str(D[0]),str(D[1])],
                       'E_point':[str(H[0]),str(H[1])],
                       'B_point':[str(Q[0]),str(Q[1])],
                       'B_lift_count':len(preimages)}
        cases.append({'prime':p,'field_degree':degree,'outputs':outputs,
                      'twist_and_dual_descent':descent})
    result={'status':'EXACT_J_PAIR_COORDINATE_INVERSION', 'cases':cases}
    (HERE/'coordinate_evaluation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'], 'point_counts':[[o['coordinate_point_count']
                      for o in c['outputs']] for c in cases]},sort_keys=True))


if __name__=='__main__':
    main()
