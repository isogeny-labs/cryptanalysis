#!/usr/bin/env python3
"""CT132 prospective cold-source-BSGS / neg-rho / mapped-GLV-rho toy panel.
NO complete ECDLP speedup, native comparison or independent PCC claim.
Run exactly 24 fixed public targets per selected seed. [pcc:unverified]
"""
import json
import math
import random
import resource
import sys
import time
from collections import Counter
import ct130_experiment as ec
import ct131_glv_rho as cm

P = 2147483033
Q = 536857417
SEEDS = (20261118, 20261119)
ARMS = ("source_bsgs", "source_neg", "target_glv")
WIDTH = math.isqrt(Q - 1) + 1


def one_arm(name, point, seed):
    if name not in ARMS:
        raise ValueError("unknown arm")
    t0 = time.perf_counter_ns()
    c = ec.Curve(0, 9) if name == 'target_glv' else ec.Curve(cm.SA, cm.SB)
    if name == 'target_glv':
        base, public = cm.mapping(cm.G), cm.mapping(point)
    else:
        base, public = cm.G, point
    if name == 'source_bsgs':
        result, stored = ec.bsgs(c, base, public, Q)
        iterations = 0
        cycles = 0
    else:
        result, iterations, cycles, stored = cm.solve(
            c, base, public, 4 if name == 'target_glv' else 2, seed)
    # The target is never trusted: verify the original public source point.
    verify_curve = ec.Curve(cm.SA, cm.SB)
    if verify_curve.mul(cm.G, result) != point:
        raise ValueError('source-log verification mismatch')
    dt = time.perf_counter_ns() - t0
    if name == 'source_bsgs' and stored != WIDTH:
        raise ValueError('not a fresh complete baby table')
    if dt <= 0 or result < 0 or result >= Q:
        raise ValueError('bad solve duration or log')
    return dict(arm=name, recovered_log=result, ns=dt,
                add_calls=c.ops['add_calls']+verify_curve.ops['add_calls'],
                inverse_calls=c.ops['inversions']+verify_curve.ops['inversions'],
                solver_add_calls=c.ops['add_calls'],
                iterations=iterations, fruitless_cycles=cycles,
                stored_states=stored, source_verified=True)


def run(seed):
    if seed not in SEEDS:
        raise ValueError('seed not in preregistered panel')
    ec.P = P
    source, target = ec.Curve(cm.SA, cm.SB), ec.Curve(0, 9)
    if not (source.on(cm.G) and target.on(cm.H) and source.mul(cm.G, Q) is None
            and target.mul(cm.H, Q) is None and cm.mapping(cm.G) == cm.H):
        raise ValueError('source/subgroup/isogeny failure')
    if (cm.R * cm.R % P != (P-9) % P or cm.I * cm.I % P != P-1
            or cm.L * cm.L % Q != Q-1):
        raise ValueError('CM constants failure')
    rng = random.Random(seed)
    scalars = [rng.randrange(Q//8, Q-1) for _ in range(24)]
    if len(set(scalars)) != 24:
        raise ValueError('duplicate target scalar')
    rows = []
    for idx, k in enumerate(scalars):
        public = source.mul(cm.G, k)
        if public is None or cm.mapping(public) != target.mul(cm.H, k):
            raise ValueError('public source target mismatch')
        sequence = list(ARMS + tuple(reversed(ARMS))) if idx % 2 == 0 else list(tuple(reversed(ARMS)) + ARMS)
        observed = []
        for name in sequence:
            row = one_arm(name, public, seed+19*idx)
            if row['recovered_log'] != k:
                raise ValueError('incorrect known answer')
            observed.append(row)
        rows.append(dict(scalar=k, public_Q=public, schedule=sequence, observations=observed))
    return dict(schema='ct132-three-arm/v1', standing='[pcc:unverified]', seed=seed,
                source_prime=P, source_a=cm.SA, source_b=cm.SB,
                source_G=cm.G, target_H=cm.H, subgroup_prime=Q,
                baby_width=WIDTH, predefined_scalars=scalars,
                rows=rows, peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='producer-only portable Python cold public toy comparison; source rho/BSGS vs target GLV rho; excludes native/Jacobian/IC and offline curve discovery')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python3 -S ct132_three_arm.py <20261118|20261119>')
    print(json.dumps(run(int(sys.argv[1])), sort_keys=True, separators=(',', ':')))
