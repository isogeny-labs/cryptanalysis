"""Check bounded coefficient alphabets on the six archived row dependences."""
import json
from pathlib import Path
import subprocess

import numpy as np
from flint import nmod_mat

from audit import BASE, ROOT

ORDER = 2147505293
BOUND = 2**23


def archive(arm, seed, name):
    path = f"{BASE}/{arm}/seed{seed}/{name}"
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)


def check(arm, seed, witnesses):
    rows = archive(arm, seed, "relations.jsonl").splitlines()
    weights = json.loads(archive(arm, seed, "certificate.json"))["weights"]
    assert len(weights) == len(rows) and weights[-1] == 1
    assert all(0 <= w < ORDER for w in weights)
    entries = []
    residues = [0] * 500
    for line, weight in zip(rows, weights, strict=True):
        row = [0] * 500
        for code in json.loads(line)["codes"]:
            j = code // 2
            sign = 1 - 2*(code % 2)
            row[j] += sign
            residues[j] += sign * weight
        entries.extend(row)
    assert all(v % ORDER == 0 for v in residues)
    assert nmod_mat(len(rows), 500, entries, ORDER).rank() == len(rows) - 1

    # Because the final weight is one, every bounded nonzero multiple must
    # use a scalar in ±[1, BOUND]. Overall negation preserves centered size.
    magnitudes = list(dict.fromkeys(min(w, ORDER-w) for w in weights if w))
    assert witnesses == magnitudes[:5]
    used = 0
    for first in range(1, BOUND + 1, 65536):
        scales = np.arange(first, min(first + 65536, BOUND + 1), dtype=np.int64)
        for count, mag in enumerate(magnitudes, 1):
            # Both factors are at most 2^31, so signed 64-bit products are exact.
            values = scales * mag % ORDER
            scales = scales[(values <= BOUND) | (values >= ORDER - BOUND)]
            if not len(scales):
                used = max(used, count)
                break
        else:
            raise ValueError(f"bounded multiple exists at scale {scales[0]}")
    return sum(w != 0 for w in weights), len(magnitudes), used


if __name__ == "__main__":
    lean = Path(__file__).with_name("ScaleBound.lean").read_text()
    declaration = "def witnesses : List (List ℕ) := "
    panels = json.loads(lean.split(declaration, 1)[1].splitlines()[0])
    assert len(panels) == 6
    for arm_index, arm in enumerate(("auxiliary", "plain")):
        for seed in range(3):
            print(arm, seed, *check(arm, seed, panels[arm_index*3 + seed]))
