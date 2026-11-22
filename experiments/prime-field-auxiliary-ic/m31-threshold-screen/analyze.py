"""Report milliseconds per qualifying set and paired block-bootstrap intervals."""
from pathlib import Path
import numpy as np

for filename, arms in [("initial.csv", 3), ("replay.csv", 4)]:
    rows = np.loadtxt(Path(__file__).with_name(filename), delimiter=",", dtype=int)
    assert rows.shape == (36 * 4 * arms, 6)
    for threshold in [17, 20, 22, 24]:
        subset = rows[rows[:, 1] == threshold]
        blocks = subset[np.lexsort((subset[:, 2], subset[:, 0]))].reshape(36, arms, 6)
        assert np.all(blocks[:, :, 0] == np.arange(1, 37)[:, None])
        assert np.all(blocks[:, :, 2] == np.arange(1, arms + 1))
        if arms == 4:
            assert np.all(blocks[:, 0, 3] == blocks[:, 3, 3])
        accepted, cpu, wall = blocks[:, :, 3:].sum(axis=0).T
        rng = np.random.default_rng(291144)
        indices = rng.integers(0, 36, size=(10000, 36))
        draws = blocks[indices, :, 3:].sum(axis=1)
        rates = draws[:, :, 0] / draws[:, :, 2]
        interval = np.quantile(rates[:, 2] / rates[:, 0], [.025, .975])
        print(filename, threshold, "accepted", accepted, "ms/set", np.round(wall/accepted, 4),
              "reflection/single rate", round((accepted[2]/wall[2])/(accepted[0]/wall[0]), 3),
              "interval", np.round(interval, 3))
