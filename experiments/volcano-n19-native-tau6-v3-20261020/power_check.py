"""Power check for the frozen primary of protocol v3 (run before freezing; writes analysis/power.json).

Design: 20 points x K = 3 alternating B/N pairs, R = sum cold CPU(B) / sum cold
CPU(N), two-stage paired bootstrap (stats.two_stage, 1,000 draws here for
speed; 10,000 in the verifier). Model, per point i and process:
B_ij = c_i exp(e), N_ij = c_i / delta exp(e'), e, e' ~ Normal(0, sigma)
independent per process (no shared pair effect: pessimistic). c_i is drawn
with replacement from a prior of per-point baseline costs:
  * `v2_runner`: the 16 B processes of v2 run 39376405326 (same runner class
    and image; launcher wall s, which includes Sage start-up and the crash; the
    rows have no CPU interval because they crashed after it);
  * `archived`: the ten tau6 rows of run 38520305068 (total CPU s + 0.2 s setup).
sigma = 0.10 and 0.20 (log, per process; GitHub VMs; deliberately pessimistic).
Power = share of simulated panels whose 95% lower bound exceeds 1;
`rejection_rate_at_no_effect` is the same share at delta = 1.
The A/A control (3 N/Naa pairs per point, window [0.95, 1.05] on the
estimate) is simulated the same way at delta = 1: `aa_false_fail_rate`.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats  # noqa: E402

SIMS, DRAWS = 200, 1000
POINTS, K, K_AA = 20, 3, 3
DELTAS = (1.0, 1.05, 1.10, 1.20)
SIGMAS = (0.10, 0.20)
MIN_DELTA = 1.20
V2_B_LAUNCHER_WALL_S = [67.6, 84.5, 69.0, 98.8, 66.6, 83.5, 90.2, 81.0, 64.8, 57.1, 63.8, 64.4, 69.9, 63.1, 68.7, 83.9]


def prior():
    arch = [json.loads(l) for l in open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'results',
                                                     'arms.jsonl'))]
    return {'v2_runner': V2_B_LAUNCHER_WALL_S,
            'archived': [r['total_cpu_s'] + 0.2 for r in arch if r['arm'] == 'tau6']}


def panel(rng, costs, delta, sigma, k):
    pts = []
    for _ in range(POINTS):
        c = rng.choice(costs)
        pts.append([(c * rng.lognormvariate(0, sigma), c / delta * rng.lognormvariate(0, sigma)) for _ in range(k)])
    return pts


def main():
    rng = random.Random('volcano-n19-native-tau6-v3-20261020:power')
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
           'note': 'the expected effect is far above min_delta (v2 run 39376405326: B processes 57-99 s, N processes '
                   '1.8-2.2 s of launcher wall including about 1.5 s of Sage start-up); min_delta 1.20 is the '
                   'smallest effect the design is sized to detect'}
    os.makedirs(os.path.join(HERE, 'analysis'), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, 'analysis', 'power.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('lower_bound_above_1_rate', 'aa_false_fail_rate',
                                          'power_at_min_delta_worst', 'rejection_rate_at_no_effect_worst')}, indent=1))


if __name__ == '__main__':
    main()
