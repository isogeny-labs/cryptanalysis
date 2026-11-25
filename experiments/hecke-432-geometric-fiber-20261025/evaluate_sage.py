"""Evaluate the complete p997 geometric 16-fiber through the E projection."""
import importlib.util
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, PolynomialRing, QQ
from sage.schemes.elliptic_curves.hom_composite import EllipticCurveHom_composite

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KERNEL_PATH = ROOT/'hecke-432-kernel-transport-20261025'/'evaluate_sage.py'
spec = importlib.util.spec_from_file_location('hecke_kernel_transport', KERNEL_PATH)
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def decode(coefficients, field):
    assert len(coefficients) == field.degree()
    if field.degree() == 1:
        return field(coefficients[0])
    return sum((field(c)*field.gen()**i for i,c in enumerate(coefficients)), field(0))


def encode(value, field):
    if field.degree() == 1:
        return [int(value)]
    coefficients = [int(c) for c in field(value).polynomial().list()]
    return coefficients + [0]*(field.degree()-len(coefficients))


def value_at(map_data, point, field):
    def polynomial(terms):
        return sum((field(QQ(t['coefficient']))*point[0]**t['x_power']*
                    point[1]**t['y_power'] for t in terms),field(0))
    denominator = polynomial(map_data['denominator'])
    assert denominator
    return -polynomial(map_data['numerator'])/denominator


def exact_order_four_generator(phi):
    curve = phi.domain()
    for xx,_ in phi.kernel_polynomial().roots():
        for point in curve.lift_x(xx,all=True):
            if not (2*point).is_zero() and (4*point).is_zero() and phi(point).is_zero():
                return point
    raise ValueError('order-four kernel generator absent over selected field')


def two_maps_from_vectors(curve, root_vectors):
    field = curve.base_field()
    x = PolynomialRing(field,'x').gen()
    current = curve
    maps = []
    back = None
    for vector in root_vectors:
        root = decode(vector,field)
        assert current.division_polynomial(2)(root) == 0
        assert back is None or root != back
        phi = current.isogeny(x-root)
        assert phi.degree() == 2
        maps.append(phi)
        dual_poly = phi.dual().kernel_polynomial()
        assert dual_poly.degree() == 1
        back = -dual_poly[0]/dual_poly[1]
        current = phi.codomain()
    assert len(maps) == 4
    return maps


def projected_point(curve, two_maps, three, coordinate_map, intermediate_map, field):
    q = EllipticCurveHom_composite.from_factors(two_maps[:2])
    psi = EllipticCurveHom_composite.from_factors(two_maps[2:])
    qdual = EllipticCurveHom_composite.from_factors(
        [two_maps[1].dual(),two_maps[0].dual()])
    middle = q.codomain()
    R = exact_order_four_generator(psi)
    T0 = exact_order_four_generator(qdual)
    i = field(-1).sqrt()
    T = T0 if R.weil_pairing(T0,4) == i else -T0
    assert R.weil_pairing(T,4) == i
    cpoly = q.push_subgroup(three.kernel_polynomial())
    assert cpoly.degree() == 13 and cpoly.is_squarefree()
    C = EllipticCurve(field,coordinate_map['curve_ainvs'])
    points = []
    for Q4 in (T+R,T-R):
        phi = middle.isogeny(Q4)
        pushed = phi.push_subgroup(cpoly)
        assert pushed.degree() == 13 and pushed.is_squarefree()
        quotient = phi.codomain().isogeny(pushed)
        _,candidates = kernel.roots_for_pair(C,coordinate_map,
                                              phi.codomain().j_invariant(),
                                              quotient.codomain().j_invariant())
        three_kernel = pushed.gcd(phi.codomain().division_polynomial(3))
        assert three_kernel.degree() == 1
        first = phi.codomain().isogeny(three_kernel)
        pushed9 = first.push_subgroup(pushed)
        assert pushed9.degree() == 4
        nine_kernel = pushed9.gcd(first.codomain().division_polynomial(3))
        assert nine_kernel.degree() == 1
        second = first.codomain().isogeny(nine_kernel)
        actual_j3 = first.codomain().j_invariant()
        actual_j9 = second.codomain().j_invariant()
        filtered = [P for P in candidates
                    if value_at(intermediate_map['j3'],P,field) == actual_j3
                    and value_at(intermediate_map['j9'],P,field) == actual_j9]
        assert len(filtered) == 1,(len(candidates),len(filtered))
        points.append(filtered[0])
    D = points[0]-points[1]
    E = EllipticCurve(field,[0,0,0,0,432])
    if D.is_zero():
        H = E(0)
    else:
        H = E(-4*D[0],-8*i*(D[1]+field(1)/2))
    return None if H.is_zero() else [encode(H[0],field),encode(H[1],field)]


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    count = json.loads((HERE/'count_result.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_GEOMETRIC_FIBER'
    assert count['status'] == 'COMPLETE_GEOMETRIC_16_FIBER'
    degree = count['selected_extension_degree']
    field = GF(protocol['prime']**degree,'u')
    selected = next(r for r in count['rows'] if r['extension_degree']==degree)
    assert selected['field_modulus'] == [int(c) for c in field.modulus().list()]
    assert selected['cyclic_16_path_count'] == len(selected['root_vectors']) == 24
    census_path = ROOT/'hecke-432-prime997-20261025'/'census.json'
    coordinate_path = ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json'
    intermediate_path = ROOT/'hecke-432-prime997-20261025'/'intermediate_j.json'
    census = json.loads(census_path.read_text())
    source = next(row for row in census['rows']
                  if row['curve_ainvs']==protocol['selected_source_curve_ainvs']
                  and row['j']==protocol['selected_source_j'])
    path3 = source['three_paths'][protocol['selected_27_path_index']]
    coordinate_map = json.loads(coordinate_path.read_text())
    intermediate_map = json.loads(intermediate_path.read_text())
    C = EllipticCurve(field,coordinate_map['curve_ainvs'])
    _,originals = kernel.roots_for_pair(C,coordinate_map,field(source['j']),
                                         field(path3[-1]['target_j']))
    originals = [P for P in originals
                 if value_at(intermediate_map['j3'],P,field)==field(path3[0]['target_j'])
                 and value_at(intermediate_map['j9'],P,field)==field(path3[1]['target_j'])]
    assert len(originals)==1
    assert [int(originals[0][0]),int(originals[0][1])] == protocol['selected_C_point']
    curve = EllipticCurve(field,source['curve_ainvs'])
    three,_ = kernel.chain(curve,path3)
    rows = []
    for index,vectors in enumerate(selected['root_vectors']):
        try:
            two_maps = two_maps_from_vectors(curve,vectors)
            point = projected_point(curve,two_maps,three,coordinate_map,
                                    intermediate_map,field)
            row = {'index':index,'root_vectors':vectors,'status':'PASS','E_point':point}
        except Exception as exc:
            row = {'index':index,'root_vectors':vectors,'status':'EVALUATION_ERROR',
                   'error_type':type(exc).__name__,'error':str(exc)[:240],
                   'E_point':None}
        rows.append(row)
        print(json.dumps({'completed':index+1,'status':row['status']}),flush=True)
    passed = [row for row in rows if row['status']=='PASS']
    keys = [None if row['E_point'] is None else
            tuple(tuple(v) for v in row['E_point']) for row in passed]
    multiplicities = Counter(keys)
    out = {'status':'COMPLETE_GEOMETRIC_E_FIBER' if len(passed)==24 else
                    'PARTIAL_GEOMETRIC_E_FIBER',
           'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
           'count_sha256':sha256((HERE/'count_result.json').read_bytes()).hexdigest(),
           'source_sha256':{name:sha256(path.read_bytes()).hexdigest() for name,path in
                            [('census',census_path),('coordinate_map',coordinate_path),
                             ('intermediate_j',intermediate_path)]},
           'extension_degree':degree,'field_modulus':selected['field_modulus'],
           'selected_C_point':protocol['selected_C_point'],
           'path_count':len(rows),'evaluated_count':len(passed),
           'distinct_E_outputs':len(multiplicities),
           'E_multiplicity_histogram':dict(Counter(multiplicities.values())),
           'rows':rows}
    (HERE/'evaluation.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','path_count','evaluated_count',
                      'distinct_E_outputs','E_multiplicity_histogram')},sort_keys=True))


if __name__=='__main__':
    main()
