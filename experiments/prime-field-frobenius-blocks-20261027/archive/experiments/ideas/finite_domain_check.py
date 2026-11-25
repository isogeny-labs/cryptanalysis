"""Check the fixed-small-parameter-domain obstruction for both orbit lifts.

An irreducible quadratic pair or cubic orbit polynomial determines at most
two nonzero elliptic traces: one trace and its negative. A prescribed set
of B parameter values therefore covers <=2B targets, even if the sampler
may choose any of the constant-degree lifts. This does not rule out a new
nonuniform point-construction algorithm; it diagnoses rejection sampling.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import prime_order_curve, sqrt_mod
from norm_trace_lift import lift
from cubic_trace_lift import lift_parameters


def main():
    records = []; pairs = 0
    for p, B in [(17, 4), (41, 8), (97, 8), (257, 16), (1153, 16)]:
        E, r, P = prime_order_curve(p)
        delta = next(d for d in range(2, p) if sqrt_mod(d, p) is None)
        images = {'quadratic': {}, 'cubic': {}}
        for T in E.points():
            values = {'quadratic': {2*R[0][0] % p for R in lift(E, T, 1, delta)},
                      'cubic': {q['h'] for q in lift_parameters(E, T, 1, 0)['candidates']}}
            for family, parameters in values.items():
                for h in parameters:
                    images[family].setdefault(h, set()).add(T); pairs += 1
                    if family == 'quadratic':
                        X = T[0]
                        G = X*X*(h*h-4)-2*((E.a+1)*h+2*E.b)*X+(E.a-1)**2-4*E.b*h
                        assert G % p == 0
        for family, image in images.items():
            assert max(map(len, image.values()), default=0) <= 2
            for h, targets in image.items():
                assert len(targets) == 2 and targets == {E.neg(T) for T in targets}
            domain = {h for h in range(1, p) if pow(h, B, p) == 1}
            assert len(domain) == B
            full = set().union(*image.values()) if image else set()
            restricted = set().union(*(image[h] for h in domain if h in image))
            assert len(restricted) <= 2*B
            record = {'p': p, 'r': r, 'family': family, 'B': B,
                      'free_parameter_liftable_targets': len(full),
                      'prescribed_coset_liftable_targets': len(restricted),
                      'maximum_targets_per_parameter': max(map(len, image.values()), default=0),
                      'upper_bound': 2*B, 'targets': r-1}
            records.append(record); print(record, flush=True)
    output = {'records': records, 'parameter_trace_pairs_verified': pairs,
              'errors': 0, 'bound': 'prescribed B parameter values cover at most 2B nonzero traces'}
    Path(__file__).with_name('finite_domain_validation.json').write_text(json.dumps(output, indent=2)+'\n')


if __name__ == '__main__':
    main()
