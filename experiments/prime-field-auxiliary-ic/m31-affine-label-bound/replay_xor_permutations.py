"""Randomization control for the best balanced XOR fit on each archived label table."""
import hashlib
import json
import subprocess
from itertools import combinations

import numpy as np

from replay_xor_cut_errors import FIXTURE, HERE, P, SHA256, offsets, optimum


def main():
    data = subprocess.check_output(["git", "show", f"HEAD:{FIXTURE}"], cwd=HERE)
    assert hashlib.sha256(data).hexdigest() == SHA256
    roots = json.loads(data)["structured_roots"]
    labels = np.array([[pow((x**3 + 2*x + b) % P, (P-1)//2, P) == 1 for x in roots]
                       for b in (14, 36)])
    cuts = []
    for other in combinations(range(1, 8), 3):
        axes = (0, *other)
        cuts.append(np.bitwise_or.outer(offsets(axes), offsets([i for i in range(8) if i not in axes])))
    assert len(cuts) == 35
    for cut in cuts:
        assert np.array_equal(np.sort(cut.ravel()), np.arange(256))

    def best_errors(tables):
        return [min(optimum(table[cut]) for cut in cuts) for table in tables]

    observed = best_errors(labels)
    assert observed == [78, 78]
    rng = np.random.Generator(np.random.PCG64(1953))
    scores = np.array([best_errors(labels[:, rng.permutation(256)]) for _ in range(199)])
    print("curve_b,observed_errors,median_shuffled_errors,as_good_or_better,permutations")
    for b, obs, shuffled in zip((14, 36), observed, scores.T, strict=True):
        print(b, obs, int(np.median(shuffled)), int(np.count_nonzero(shuffled <= obs)),
              len(shuffled), sep=",")
    print("Paired permutations meeting both observed scores:",
          int(np.count_nonzero((scores <= observed).all(axis=1))))


if __name__ == "__main__":
    main()
