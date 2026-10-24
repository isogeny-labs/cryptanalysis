"""Reproduce the installed Sage distinct-root volcano classification discrepancy."""
from hashlib import sha256
import inspect
import json
from pathlib import Path

from sage.all import EllipticCurve_from_j, GF, PolynomialRing, classical_modular_polynomial

HERE=Path(__file__).resolve().parent


def main():
    field=GF(11131);ring=PolynomialRing(field,'J');J=ring.gen()
    phi3=classical_modular_polynomial(3)
    method_source=inspect.getsource(EllipticCurve_from_j(field(193)).height_above_floor)
    assert 'roots(multiplicities=False)' in method_source
    assert 'nj1 <= ell' in method_source
    records=[]
    for j in (193,1345):
        curve=EllipticCurve_from_j(field(j))
        roots=[{'j':int(z),'multiplicity':int(m)}
               for z,m in ring(phi3(field(j),J)).roots()]
        explicit=curve.isogenies_prime_degree(3)
        assert (len(roots),sum(r['multiplicity'] for r in roots),len(explicit))==(3,4,4)
        assert curve.height_above_floor(3,1)==0
        assert int(curve.endomorphism_order().conductor())==3
        records.append({'j':j,'phi3_roots':roots,'explicit_isogeny_count':len(explicit),
                        'explicit_codomain_j':sorted(int(f.codomain().j_invariant()) for f in explicit),
                        'sage_height_above_floor_3':0,'sage_reported_endomorphism_conductor':3})
    out={'status':'REPRODUCED_DISTINCT_ROOT_FLOOR_CLASSIFICATION_DISCREPANCY',
         'p':11131,'d':35,
         'method_source_sha256':sha256(method_source.encode()).hexdigest(),
         'method_source_file':inspect.getsourcefile(EllipticCurve_from_j(field(193)).height_above_floor),
         'source_condition':'nj1 = len(Phi_ell(j,Y).roots(multiplicities=False)); on_floor = nj1 <= ell for ell != 2',
         'records':records,
         'script_sha256':sha256((HERE/'sage_bug_receipt.py').read_bytes()).hexdigest()}
    (HERE/'sage_bug_receipt.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'records':len(records)},sort_keys=True))


if __name__=='__main__':main()
