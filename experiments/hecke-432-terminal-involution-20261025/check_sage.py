"""Check the exact-level and modular-subgroup inputs to the deck proof."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, Gamma0, QQ, ZZ, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_TERMINAL_INVOLUTION_AUDIT'
    assert protocol['deck_matrix'] == [[1,0],[216,1]]
    gamma = matrix(ZZ,protocol['deck_matrix'])
    assert gamma.det() == 1
    assert gamma[1,0] % 216 == 0 and gamma[1,0] % 432 != 0
    square = gamma*gamma
    assert square == matrix(ZZ,[[1,0],[432,1]])
    indices = {n:int(Gamma0(n).index()) for n in (27,216,432)}
    assert indices == {27:36,216:432,432:864}
    assert indices[432]//indices[216] == 2
    assert indices[216]//indices[27] == 12
    B = EllipticCurve(QQ,[0,0,0,0,-16])
    E = EllipticCurve(QQ,[0,0,0,0,432])
    assert B.conductor() == 432 and E.conductor() == 432
    q = B.modular_form().q_expansion(40)
    assert q[1] == 1 and all(q[n] == 0 for n in (2,3,4,5,6))
    map_path = ROOT/'hecke-432-map-identity-20261025'/'RESULT.md'
    cusp_path = ROOT/'hecke-432-cusp-image-20261025'/'RESULT.md'
    out = {'status':'PASS_DECK_SUBGROUP_AND_EXACT_LEVEL_INPUTS',
           'gamma':protocol['deck_matrix'],
           'gamma_square':[[int(x) for x in row] for row in square.rows()],
           'gamma_in_Gamma0_216':True,'gamma_outside_Gamma0_432':True,
           'subgroup_indices':{str(k):v for k,v in indices.items()},
           'forgetful_degrees':{'432_to_216':2,'216_to_27':12},
           'B_conductor':int(B.conductor()),'E_conductor':int(E.conductor()),
           'B_newform_coefficients_1_to_39':[int(q[n]) for n in range(1,40)],
           'source_sha256':{'map_identity_report':sha256(map_path.read_bytes()).hexdigest(),
                            'cusp_image_report':sha256(cusp_path.read_bytes()).hexdigest()},
           'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest()}
    (HERE/'subgroup_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','subgroup_indices',
                       'forgetful_degrees','B_conductor')},sort_keys=True))


if __name__ == '__main__':
    main()
