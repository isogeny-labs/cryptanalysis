from pathlib import Path
import numpy as np

def load(filename):
    data = np.loadtxt(Path(__file__).with_name(filename), dtype=np.int64, delimiter=",")
    assert data.shape == (108, 4)
    rows = data[np.lexsort((data[:, 1], data[:, 0]))].reshape(36, 3, 4)
    assert np.all(rows[:, :, 0] == np.arange(36)[:, None])
    assert np.all(rows[:, :, 1] == [0, 1, 2])
    assert np.all(rows[:, :, 2] > 0)
    return rows

arm = load("arm.csv")
translated = load("translated.csv")
assert np.array_equal(arm[:, :, 3], translated[:, :, 3])
samples = np.random.default_rng(291148).integers(0, 36, (10000, 36))
for label, data in [("arm64", arm), ("translated AVX2", translated)]:
    times = data[:, :, 2] / 8192
    print(label, "ns per input", np.median(times, axis=0))
    for control in [0, 1]:
        ratios = times[:, 2] / times[:, control]
        print("20/control", control, np.median(ratios),
              np.quantile(np.median(ratios[samples], axis=1), [.025, .975]))
