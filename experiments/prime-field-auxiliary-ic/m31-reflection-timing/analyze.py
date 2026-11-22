"""Summarize paired timings from panel.gp (milliseconds)."""
from pathlib import Path
import numpy as np

rows = np.loadtxt(Path(__file__).with_name("blocks.csv"), delimiter=",", dtype=int)
assert rows.shape == (108, 6)
blocks = rows.reshape(36, 3, 6)
assert np.all(blocks[:, :, 0] == np.arange(1, 37)[:, None])
assert np.all(blocks[:, :, 1] == np.arange(1, 4))
assert np.all(np.unique(blocks[:, :, 2], axis=0, return_counts=True)[1] == 6)
data = np.take_along_axis(blocks, np.argsort(blocks[:, :, 2])[:, :, None], axis=1)
assert np.all(data[:, :, 2] == np.arange(1, 4))
assert np.all(data[:, :, 4:] > 0)
assert np.all(data[:, 1:, 3] >= data[:, :1, 3])
indices = np.random.default_rng(291142).integers(0, 36, (10000, 36))
for i, name in enumerate(("single", "independent", "reflection")):
    lifts, cpu, wall = data[:, i, 3:].sum(axis=0)
    print(name, "mean lifts", lifts / 9216, "cpu ms", cpu, "wall ms", wall,
          "lifts per CPU ms", lifts / cpu)
for name, col in (("cpu", 4), ("wall", 5)):
    ratios = data[:, 1, col] / data[:, 2, col]
    medians = np.median(ratios[indices], axis=1)
    print(name, "paired speed ratio", np.median(ratios),
          "interval", np.quantile(medians, [0.025, 0.975]),
          "faster blocks", sum(ratios > 1))
