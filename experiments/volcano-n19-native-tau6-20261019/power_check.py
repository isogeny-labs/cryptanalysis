"""Power check for the frozen primary (run before freezing; writes analysis/power.json).

Prior: the ten archived tau6 rows of volcano-ic/rho-arm-20261014 (run
38520305068), cold CPU per ECDLP of the baseline (setup was outside that
run's intervals, 0.37 s for all arms together, so it is added as 0.2 s here).
Model: B_i = prior_i * exp(e_B), N_i = prior_i / delta * exp(e_N), with
independent per-process noise e ~ Normal(0, sigma), sigma = 0.10 in log
(a deliberately pessimistic GitHub-VM process noise; the archived run has no
A/A pair to calibrate it). Panel points are drawn from the prior with
replacement. For each panel size and delta, SIMS simulated panels are
analysed with the frozen statistic (stats.ratio_of_means, 2,000 draws here
for speed); power = share with lower bound > 1.
"""
import json
import os

import numpy as np

import stats

HERE = os.path.dirname(os.path.abspath(__file__))
SIMS, DRAWS, SIGMA = 400, 2000, 0.10
SIZES = (8, 12, 16)
DELTAS = (1.0, 1.05, 1.10, 1.20, 1.50, 2.0)
MIN_DELTA = 1.20
CHOSEN = 16


def main():
    arch = [json.loads(l) for l in open(os.path.join(HERE, '..', 'volcano-ic', 'rho-arm-20261014', 'results', 'arms.jsonl'))]
    prior = np.array([r['total_cpu_s'] for r in arch if r['arm'] == 'tau6']) + 0.2
    rng = np.random.default_rng(20261019)
    out = {}
    for n in SIZES:
        for d in DELTAS:
            rej = 0
            for s in range(SIMS):
                pts = prior[rng.integers(0, len(prior), n)]
                b = pts * np.exp(rng.normal(0, SIGMA, n))
                c = pts / d * np.exp(rng.normal(0, SIGMA, n))
                _, lo, _ = stats.ratio_of_means(b, c, draws=DRAWS, seed=int(rng.integers(1 << 31)))
                rej += lo > 1
            out['n%d_delta%.2f' % (n, d)] = rej / SIMS
    res = {'prior': {'source': 'volcano-ic/rho-arm-20261014/results/arms.jsonl (tau6 rows, run 38520305068)',
                     'cold_cpu_s': [float(x) for x in prior]},
           'model': {'sigma_log_per_process': SIGMA, 'sims': SIMS, 'bootstrap_draws': DRAWS},
           'lower_bound_above_1_rate': out, 'min_delta': MIN_DELTA, 'chosen_points': CHOSEN,
           'power_at_min_delta': out['n%d_delta%.2f' % (CHOSEN, MIN_DELTA)],
           'rejection_rate_at_no_effect': out['n%d_delta1.00' % CHOSEN],
           'note': 'the expected effect (local diagnostics: per-call solve 14 us native against 7.4 ms archived Sage) '
                   'is far above min_delta; min_delta 1.20 is the smallest effect the protocol is sized to detect'}
    os.makedirs(os.path.join(HERE, 'analysis'), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, 'analysis', 'power.json'), 'w'), indent=1)
    print(json.dumps(res['lower_bound_above_1_rate'], indent=1))


if __name__ == '__main__':
    main()
