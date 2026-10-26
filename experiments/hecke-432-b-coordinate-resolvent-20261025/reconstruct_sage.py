"""CRT and rational reconstruction of the weight-44 x_B relation."""
import json
from hashlib import sha256
from math import prod
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import ZZ

HERE=Path(__file__).resolve().parent


def main():
    minimal_path=HERE/'minimal_result.json'
    lift_path=HERE/'lift_result.json'
    minimal=json.loads(minimal_path.read_text())
    lift=json.loads(lift_path.read_text())
    screen=json.loads((HERE/'screen_result.json').read_text())
    old_terms=next(r['terms'] for r in screen['rows'] if r['weighted_degree']==56)
    indices=[j for j,t in enumerate(old_terms) if 2*t[0]+3*t[1]+2*t[2]<=44]
    assert [old_terms[j] for j in indices]==lift['terms']
    rows=[{'prime':r['prime'],
           'coefficients':[r['minimal_relation']['coefficients'][j] for j in indices]}
          for r in minimal['results']]+lift['rows']
    assert len({r['prime'] for r in rows})==len(rows)
    normal=lift['normalizing_index']
    assert all(r['coefficients'][normal]==1 for r in rows)
    training,holdout=rows[:-1],rows[-1]
    mod=prod(r['prime'] for r in training)
    invs=[pow(mod//r['prime'],-1,r['prime']) for r in training]
    residues=[sum(r['coefficients'][j]*(mod//r['prime'])*inv
                  for r,inv in zip(training,invs))%mod
              for j in range(len(lift['terms']))]
    fractions=[]
    missing=[]
    mismatches=[]
    for j,a in enumerate(residues):
        try:
            q=ZZ(a).rational_reconstruction(ZZ(mod))
            n,d=int(q.numerator()),int(q.denominator())
            fractions.append([n,d])
            p=holdout['prime']
            if d%p==0 or n*pow(d,-1,p)%p!=holdout['coefficients'][j]:
                mismatches.append(j)
        except (ValueError,ArithmeticError):
            fractions.append(None)
            missing.append(j)
    status=('PASS_RATIONAL_B_RECONSTRUCTION_WITH_HOLDOUT'
            if not missing and not mismatches else 'PARTIAL_RATIONAL_B_RECONSTRUCTION')
    out={'status':status,'terms':lift['terms'],'normalizing_index':normal,
         'modulus':str(mod),'training_primes':[r['prime'] for r in training],
         'holdout_prime':holdout['prime'],'unreconstructed_indices':missing,
         'holdout_mismatch_indices':mismatches,'coefficients_num_den':fractions,
         'minimal_sha256':sha256(minimal_path.read_bytes()).hexdigest(),
         'lift_sha256':sha256(lift_path.read_bytes()).hexdigest()}
    (HERE/'reconstruction.json').write_text(json.dumps(out,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'modulus_digits':len(str(mod)),
                      'unreconstructed':len(missing),'holdout_mismatches':len(mismatches),
                      'holdout_prime':holdout['prime']},sort_keys=True))


if __name__=='__main__':main()
