"""CRT and rational reconstruction of the normalized weight-90 relation."""
import json
from hashlib import sha256
from math import prod
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import ZZ

HERE = Path(__file__).resolve().parent


def main():
    minimal_path = HERE/'minimal_result.json'
    lift_path = HERE/'lift_result.json'
    minimal = json.loads(minimal_path.read_text())
    lift = json.loads(lift_path.read_text())
    old_terms = next(r['terms'] for r in json.loads((HERE/'screen_extended_result.json').read_text())['rows']
                     if r['weighted_degree'] == 96)
    indices = [j for j,t in enumerate(old_terms) if 2*t[0]+3*t[1]+2*t[2] <= 90]
    assert [old_terms[j] for j in indices] == lift['terms']
    rows = [{'prime':r['prime'],
             'coefficients':[r['minimal_relation']['coefficients'][j] for j in indices]}
            for r in minimal['results']] + lift['rows']
    assert len({r['prime'] for r in rows}) == len(rows)
    assert all(r['coefficients'][0] == 1 for r in rows)
    training, holdout = rows[:-1], rows[-1]
    mod = prod(r['prime'] for r in training)
    invs = [pow(mod//r['prime'],-1,r['prime']) for r in training]
    residues = []
    for j in range(len(lift['terms'])):
        residues.append(sum(r['coefficients'][j]*(mod//r['prime'])*inv
                            for r,inv in zip(training,invs)) % mod)
    rationals = []
    unreconstructed = []
    holdout_mismatch = []
    for j,a in enumerate(residues):
        try:
            q = ZZ(a).rational_reconstruction(ZZ(mod))
            rationals.append([int(q.numerator()),int(q.denominator())])
            p = holdout['prime']
            if int(q.denominator()) % p == 0 or int(q.numerator())*pow(int(q.denominator()),-1,p)%p != holdout['coefficients'][j]:
                holdout_mismatch.append(j)
        except (ValueError, ArithmeticError):
            rationals.append(None)
            unreconstructed.append(j)
    status = ('PASS_RATIONAL_RECONSTRUCTION_WITH_FRESH_PRIME_HOLDOUT'
              if not unreconstructed and not holdout_mismatch else
              'PARTIAL_RATIONAL_RECONSTRUCTION')
    out = {'status':status, 'terms':lift['terms'], 'modulus':str(mod),
           'training_primes':[r['prime'] for r in training],
           'holdout_prime':holdout['prime'],
           'unreconstructed_indices':unreconstructed,
           'holdout_mismatch_indices':holdout_mismatch,
           'coefficients_num_den':rationals,
           'minimal_sha256':sha256(minimal_path.read_bytes()).hexdigest(),
           'lift_sha256':sha256(lift_path.read_bytes()).hexdigest()}
    (HERE/'reconstruction.json').write_text(json.dumps(out,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'modulus_digits':len(str(mod)),
                      'unreconstructed':len(unreconstructed),
                      'holdout_mismatches':len(holdout_mismatch),
                      'holdout_prime':holdout['prime']},sort_keys=True))


if __name__ == '__main__':
    main()
