"""Replay public trial labels and align archived acceptance logs for two M31 bases.

Run with python3. Each output row uses identical trials for both basis choices.
5000 is a retrospective round cutoff before any of the six runs terminated.
The second cutoff is the last trial present in both runs of the given seed.
"""
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = "efb9330c1:experiments/prime-field-auxiliary-ic/snapshot/comparison/field31"


def read(path):
    return subprocess.check_output(["git", "show", f"{ARCHIVE}/{path}"], cwd=HERE, text=True)


def mt19937_64(seed):
    """64-bit engine used by the archived C++ driver."""
    mask = (1 << 64) - 1
    low = (1 << 31) - 1
    state = [seed]
    for i in range(1, 312):
        previous = state[-1]
        state.append((6364136223846793005 * (previous ^ (previous >> 62)) + i) & mask)
    while True:
        for i in range(312):
            z = (state[i] & ~low) | (state[(i + 1) % 312] & low)
            state[i] = state[(i + 156) % 312] ^ (z >> 1) ^ ((z & 1) * 0xB5026F5AA96619E9)
        for value in state:
            value ^= (value >> 29) & 0x5555555555555555
            value ^= (value << 17) & 0x71D67FFFEDA60000
            value ^= (value << 37) & 0xFFF7EEE000000000
            yield value ^ (value >> 43)


def trial_indices(seed, order, count):
    random = mt19937_64(20261114 + seed)
    steps = [(next(random) % order, next(random) % order) for _ in range(32)]
    a, b = next(random) % order, next(random) % order
    indices = {}
    for trial in range(1, count + 1):
        da, db = steps[next(random) % 32]
        a, b = (a + da) % order, (b + db) % order
        assert (a, b) not in indices
        indices[a, b] = trial
    return indices


def hit_indices(folder, indices, metrics):
    rows = [json.loads(line) for line in read(f"{folder}/relations.jsonl").splitlines()]
    hits = [indices[row["a"], row["b"]] for row in rows]
    assert hits == sorted(set(hits)) and len(hits) == metrics["relations"]
    assert hits[-1] == metrics["trials"]
    checkpoints = re.findall(r"^Relations (\d+), rank \d+, attempts (\d+)",
                             read(f"{folder}/stdout.txt"), re.MULTILINE)
    assert len(checkpoints) == len(hits) // 100 + 1
    assert all(hits[int(count) - 1] == int(trial) for count, trial in checkpoints)
    return set(hits)


def main():
    writer = csv.writer(sys.stdout)
    writer.writerow(["seed", "trials", "auxiliary_hits", "plain_hits", "both", "auxiliary_only", "plain_only"])
    for seed in range(3):
        folders = [f"{arm}/seed{seed}" for arm in ("auxiliary", "plain")]
        public = [json.loads(read(f"{folder}/public.json")) for folder in folders]
        assert all(public[0][k] == public[1][k] for k in ("p", "a", "b", "n", "P", "Q"))
        metrics = [json.loads(read(f"{folder}/metrics.json")) for folder in folders]
        stops = [m["trials"] for m in metrics]
        indices = trial_indices(seed, public[0]["n"], max(stops))
        hits = [hit_indices(folder, indices, m) for folder, m in zip(folders, metrics)]
        assert 5000 < min(stops)
        for cutoff in (5000, min(stops)):
            aux, plain = [{trial for trial in h if trial <= cutoff} for h in hits]
            writer.writerow([seed, cutoff, len(aux), len(plain), len(aux & plain),
                             len(aux - plain), len(plain - aux)])


if __name__ == "__main__":
    main()
