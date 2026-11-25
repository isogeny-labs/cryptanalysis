"""The frozen statistic (protocol.json "statistics"), shared by power_check.py and
verify_receipt.py: R = mean_i B_i / mean_i N_i over the panel points, 95%
percentile interval from a paired bootstrap over points (10,000 draws)."""
import numpy as np

DRAWS = 10000
SEED = 20261019


def ratio_of_means(base, cand, draws=DRAWS, seed=SEED):
    base, cand = np.asarray(base, float), np.asarray(cand, float)
    n = len(base)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(draws, n))
    boot = base[idx].mean(axis=1) / cand[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(base.mean() / cand.mean()), float(lo), float(hi)


def geo_ratio(num, den, draws=DRAWS, seed=SEED):
    """Geometric mean of per-point ratios num_i / den_i with a bootstrap interval (co-reported)."""
    lr = np.log(np.asarray(num, float) / np.asarray(den, float))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(lr), size=(draws, len(lr)))
    boot = np.exp(lr[idx].mean(axis=1))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return float(np.exp(lr.mean())), float(lo), float(hi)


def verdict(lo, hi):
    if lo > 1:
        return 'improvement'
    if hi < 1:
        return 'regression'
    return 'not_separated'
