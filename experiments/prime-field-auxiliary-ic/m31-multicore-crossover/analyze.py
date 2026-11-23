"""Summarize wall latency on paired rounds. Method 2 uses ten CPU tasks."""
from pathlib import Path
import numpy as np
import sys

rows = np.loadtxt(Path(__file__).with_name(sys.argv[1] if len(sys.argv)>1 else "rows.csv"), delimiter=",")
assert rows.shape == (20 * 10 * 5, 5)
indices = np.random.default_rng(291158).integers(0, 20, (10000, 20))
for size in sorted(set(rows[:, 1])):
    selected = rows[rows[:, 1] == size]
    data = selected[np.lexsort((selected[:, 2], selected[:, 0]))].reshape(20, 5, 5)
    assert np.all(data[:, :, 0] == np.arange(20)[:, None])
    assert np.all(data[:, :, 2] == np.arange(5))
    wall = data[:, :, 3]
    assert np.all(wall > 0) and np.all(data[:, 4, 4] > 0)
    ratios = wall[:, 2] / wall[:, 4]
    medians = np.median(wall, axis=0)*1e6
    print(int(size), np.round(medians, 2), "10-task/GPU",
          round(np.median(ratios), 3), np.round(np.quantile(
              np.median(ratios[indices], axis=1), [.025, .975]), 3),
          "GPU wins", int(sum(ratios > 1)))
