"""Enumerate geometric cyclic 16-isogeny paths above one original 27-point."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent


def encode(value, field):
    if field.degree() == 1:
        return [int(value)]
    coefficients = [int(coefficient) for coefficient in field(value).polynomial().list()]
    return coefficients + [0] * (field.degree() - len(coefficients))


def paths(curve, depth, back_root=None, prefix=()):
    if depth == 0:
        yield prefix
        return
    field = curve.base_field()
    x = PolynomialRing(field, 'x').gen()
    for root, multiplicity in curve.division_polynomial(2).roots():
        assert multiplicity == 1
        if back_root is not None and root == back_root:
            continue
        phi = curve.isogeny(x-root)
        assert phi.degree() == 2
        dual_poly = phi.dual().kernel_polynomial()
        assert dual_poly.degree() == 1
        next_back = -dual_poly[0]/dual_poly[1]
        yield from paths(phi.codomain(), depth-1, next_back,
                         prefix + (encode(root, field),))


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_GEOMETRIC_FIBER'
    p = protocol['prime']
    rows = []
    selected = None
    for degree in protocol['extension_degrees']:
        field = GF(p) if degree == 1 else GF(p**degree, 'u')
        curve = EllipticCurve(field, protocol['selected_source_curve_ainvs'])
        assert curve.j_invariant() == field(protocol['selected_source_j'])
        found = list(paths(curve, 4))
        assert len(found) == len(set(tuple(tuple(edge) for edge in path) for path in found))
        assert len(found) <= 24
        row = {'extension_degree':degree,'field_modulus':None if degree == 1 else
               [int(c) for c in field.modulus().list()],
               'cyclic_16_path_count':len(found),'root_vectors':found}
        rows.append(row)
        print(json.dumps({'extension_degree':degree,
                          'cyclic_16_path_count':len(found)}),flush=True)
        if len(found) == 24:
            selected = degree
            break
    out = {'status':'COMPLETE_GEOMETRIC_16_FIBER' if selected else 'FIELD_COVERAGE_OPEN',
           'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
           'selected_extension_degree':selected,'rows':rows}
    (HERE/'count_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],
                      'selected_extension_degree':selected},sort_keys=True))


if __name__ == '__main__':
    main()
