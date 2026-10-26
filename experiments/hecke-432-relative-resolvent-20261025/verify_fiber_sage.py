"""Independently specialize the lifted relation on the 12-point x_E fiber."""
import json
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import GF, PolynomialRing, prod

HERE = Path(__file__).resolve().parent
FIBER = HERE.parent/'hecke-432-geometric-fiber-20261025'/'evaluation.json'


def main():
    rec_path = HERE/'reconstruction.json'
    rec = json.loads(rec_path.read_text())
    fiber = json.loads(FIBER.read_text())
    assert rec['status'] == 'PASS_RATIONAL_RECONSTRUCTION_WITH_FRESH_PRIME_HOLDOUT'
    assert fiber['status'] == 'COMPLETE_GEOMETRIC_E_FIBER'
    assert fiber['selected_C_point'] == [639,232]
    base = GF(997)
    R = PolynomialRing(base,'u')
    u = R.gen()
    modulus = sum(base(v)*u**i for i,v in enumerate(fiber['field_modulus']))
    extension = GF(997**4,'u',modulus=modulus)
    gen = extension.gen()
    P = PolynomialRing(extension,'X')
    X = P.gen()
    specialized = P.zero()
    for (a,b,c),(n,d) in zip(rec['terms'],rec['coefficients_num_den']):
        assert d % 997
        specialized += extension(base(n)/base(d)*base(639)**a*base(232)**b)*X**c
    roots = [tuple(row['E_point'][0]) for row in fiber['rows']]
    unique = list(dict.fromkeys(roots))
    assert len(roots) == 24 and len(unique) == 12
    root_elements = [sum((extension(v)*gen**i for i,v in enumerate(values)),
                         extension.zero()) for values in unique]
    expected = prod((X-v for v in root_elements),P.one())
    assert specialized.degree() == 12 and specialized[12] != 0
    scaled_product_agrees = specialized == specialized[12]*expected
    all_roots_zero = all(specialized(v) == 0 for v in root_elements)
    status = ('PASS_SPECIALIZED_RELATIVE_RESOLVENT_FIBER' if
              scaled_product_agrees and all_roots_zero else
              'FAIL_SPECIALIZED_RELATIVE_RESOLVENT_FIBER')
    out = {'status':status,'field_modulus':fiber['field_modulus'],
           'C_point':fiber['selected_C_point'],'distinct_x_E_values':len(unique),
           'specialized_degree':int(specialized.degree()),
           'specialized_coefficients_low_to_high':[int(base(v)) for v in specialized],
           'scaled_product_agrees':scaled_product_agrees,
           'all_roots_zero':all_roots_zero,
           'reconstruction_sha256':sha256(rec_path.read_bytes()).hexdigest(),
           'fiber_sha256':sha256(FIBER.read_bytes()).hexdigest()}
    (HERE/'fiber_verification.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','distinct_x_E_values',
                                         'specialized_degree','scaled_product_agrees')},sort_keys=True))
    assert scaled_product_agrees and all_roots_zero


if __name__ == '__main__':
    main()
