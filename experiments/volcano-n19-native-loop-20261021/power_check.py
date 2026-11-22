"""Power check for the frozen primary (run before freezing; writes analysis/power.json).

Design: 24 points x K = 5 alternating N/N2 pairs, R = sum cold CPU(N) / sum cold CPU(N2),
two-stage paired bootstrap (stats.two_stage, 500 draws and 100 simulated panels per cell here for speed; 10,000 in the
verifier). Model, per point i and process: N_ij = c_i exp(e), N2_ij = c_i / delta exp(e'),
e, e' ~ Normal(0, sigma) independent per process (no shared pair effect: pessimistic).
c_i is drawn with replacement from the per-point mean cold CPU of arm N in v3 run
39387473809 (the 20 points; only the spread between points matters to the ratio).
sigma = 0.05, 0.10, 0.20 (log, per process). In v3 the A/A ratio of two N arms was
1.0003 [0.9964, 1.0035] over 60 pairs, i.e. a per-process sigma near 0.01-0.02 for N;
N2's processes are about 6x shorter, so larger sigmas are the pessimistic range.
Power = share of simulated panels whose 95% lower bound exceeds 1;
`rejection_rate_at_no_effect` is the same share at delta = 1. The A/A control (3 N2/N2aa
pairs per point, window [0.95, 1.05] on the estimate) is simulated at delta = 1.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats  # noqa: E402

SIMS, DRAWS = 100, 500
POINTS, K, K_AA = 24, 5, 3
DELTAS = (1.0, 1.05, 1.10, 1.20)
SIGMAS = (0.05, 0.10, 0.20)
MIN_DELTA = 1.10
V3_ROWS = os.path.join(HERE, '..', 'volcano-n19-native-tau6-v3-20261020', 'run_github_39387473809', 'timed', 'panel',
                       'rows')


def prior():
    per = {}
    for name in sorted(os.listdir(V3_ROWS)):
        r = json.load(open(os.path.join(V3_ROWS, name)))
        if r.get('arm') == 'N':
            per.setdefault(r['point'], []).append(r['cold_cpu_s'])
    return {'v3_N_cold_cpu_per_point': [sum(v) / len(v) for _, v in sorted(per.items())]}


def panel(rng, costs, delta, sigma, k):
    pts = []
    for _ in range(POINTS):
        c = rng.choice(costs)
        pts.append([(c * rng.lognormvariate(0, sigma), c / delta * rng.lognormvariate(0, sigma)) for _ in range(k)])
    return pts


def main():
    rng = random.Random('volcano-n19-native-loop-20261021:power')
    pri = prior()
    rates, aa = {}, {}
    for name, costs in pri.items():
        for sigma in SIGMAS:
            for d in DELTAS:
                rej = 0
                for _ in range(SIMS):
                    res = stats.two_stage(panel(rng, costs, d, sigma, K), seed=rng.randrange(1 << 30), draws=DRAWS)
                    rej += res['ci95'][0] > 1
                rates['%s_sigma%.2f_delta%.2f' % (name, sigma, d)] = rej / SIMS
            fails = 0
            for _ in range(SIMS):
                est = stats.ratio_of_sums(panel(rng, costs, 1.0, sigma, K_AA))
                fails += not (0.95 <= est <= 1.05)
            aa['%s_sigma%.2f' % (name, sigma)] = fails / SIMS
    res = {'design': {'points': POINTS, 'primary_pairs_per_point': K, 'aa_pairs_per_point': K_AA,
                      'statistic': 'ratio of sums, two-stage paired bootstrap', 'sims': SIMS, 'bootstrap_draws': DRAWS},
           'prior': pri, 'sigmas_log_per_process': list(SIGMAS), 'deltas': list(DELTAS),
           'lower_bound_above_1_rate': rates, 'aa_false_fail_rate': aa, 'min_delta': MIN_DELTA,
           'power_at_min_delta_worst': min(v for k, v in rates.items() if k.endswith('delta%.2f' % MIN_DELTA)),
           'rejection_rate_at_no_effect_worst': max(v for k, v in rates.items() if k.endswith('delta1.00')),
           'note': 'the expected effect is far above min_delta: the native solve was 15.4% of N\'s cold CPU in v3 '
                   'run 39387473809 and N2 keeps that solve, so with the rest of N removed the ratio would be '
                   'about 1 / 0.154 = 6.5 if the port cost nothing; locally (cloud VM, not timing evidence) N2 '
                   'took about 60 ms per point, nearly all in the v3 solve. min_delta 1.10 is the smallest '
                   'effect the design is sized to detect'}
    os.makedirs(os.path.join(HERE, 'analysis'), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, 'analysis', 'power.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('lower_bound_above_1_rate', 'aa_false_fail_rate',
                                          'power_at_min_delta_worst', 'rejection_rate_at_no_effect_worst')}, indent=1))


if __name__ == '__main__':
    main()
