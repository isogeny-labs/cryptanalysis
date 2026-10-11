"""Held-out target-residual selector for one full-width block translation."""

import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PREDICTOR = BASE / "n41_w6_public_seed_predictor_20261011"
RESIDUAL = BASE / "n41_prefix_residual_seed_selector_20261011"
SOURCE = BASE / "n41_coupled_sixpair_full_ic_20261010/heldout_input.txt"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_masks():
    words = SOURCE.read_text().split()
    pos = 0
    _, _, order, blocks = map(int, words[pos:pos+4]); pos += 4
    assert order == 549756390943 and blocks == 6
    output = []
    for block in range(6):
        rotation, size = map(int, words[pos:pos+2]); pos += 2
        assert rotation == block*5 and size == 64
        atoms = []
        for _ in range(size):
            x, y, mask, sign, column = map(int, words[pos:pos+5]); pos += 5
            assert 1 <= mask < 64 and sign in (0, 1) and 0 <= column < 26
            atoms.append((mask, column))
        pairs = [(a[0], b[0], a[0]^b[0])
                 for a in atoms for b in atoms
                 if a[0] < b[0] and a[1] != b[1]]
        assert len(pairs) == 1956
        output.append(pairs)
    assert pos == len(words)
    return output


def labels(rows, pairs):
    chosen = np.flatnonzero(rows[:, 2] == rows[:, 3])
    seeds = rows[chosen, 2].astype(np.int16)
    result = np.empty((len(chosen), 2), dtype=np.int16)
    for j, idx in enumerate(chosen):
        s = int(seeds[j])
        for slot in range(2):
            a = pairs[2+slot][int(rows[idx, 6+slot])]
            b = pairs[4+slot][int(rows[idx, 8+slot])]
            assert a[2] == b[2] == s
            u = a[0]^b[0]
            assert {a[0]^u, a[1]^u} == {b[0], b[1]}
            result[j, slot] = min(u, u^s)
    return chosen, seeds, result


def bit_features(values, columns):
    shifts = np.arange(41, dtype=np.uint64)
    return np.concatenate([((values[:, col, None] >> shifts) & 1).astype(np.float64)
                           for col in columns], axis=1)


def score_arm(x_train, x_test, train_y, test_s, train_s):
    classes = np.arange(64, dtype=np.int16)
    count_u = np.bincount(train_y, minlength=64)
    bitcounts = np.stack([x_train[train_y == u].sum(axis=0) for u in classes])
    probabilities = (bitcounts + 1) / (count_u[:, None] + 2)
    scores = x_test @ np.log(probabilities/(1-probabilities)).T
    scores += np.log(1-probabilities).sum(axis=1)
    priors = np.zeros((64, 64), dtype=np.float64)
    for seed in range(1, 64):
        allowed = np.array([min(u, u^seed) == u for u in classes])
        counts = np.bincount(train_y[train_s == seed], minlength=64)
        priors[seed, allowed] = np.log(counts[allowed]+1)
        priors[seed, ~allowed] = -1e100
    scores += priors[test_s]
    proposals = np.argsort(-scores, axis=1, kind="stable")[:, :7]
    return proposals


def baseline(train_y, train_s, test_s):
    proposals = np.empty((len(test_s), 7), dtype=np.int16)
    for seed in range(1, 64):
        allowed = np.array([min(u, u^seed) == u for u in range(64)])
        counts = np.bincount(train_y[train_s == seed], minlength=64)
        score = counts.astype(np.float64)
        score[~allowed] = -1
        proposals[test_s == seed] = np.argsort(-score, kind="stable")[:7]
    return proposals


def compare(hit, control):
    delta = hit.astype(np.int8)-control.astype(np.int8)
    only_hit = int(np.sum(hit & ~control))
    only_control = int(np.sum(control & ~hit))
    mean = float(delta.mean())
    se = float(delta.std(ddof=1)/math.sqrt(len(delta)))
    return {"difference": mean, "normal95": [mean-1.95996398454*se,
                                                 mean+1.95996398454*se],
            "model_only": only_hit, "baseline_only": only_control,
            "mcnemar_two_sided_p": float(binomtest(only_hit, only_hit+only_control).pvalue)
            if only_hit+only_control else 1.0}


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    paths = {"source": Path(__file__), "source_input": SOURCE,
             "rows": PREDICTOR / "rows.tsv", "residuals": RESIDUAL / "residuals.tsv",
             "generator_protocol": PREDICTOR / "protocol.json",
             "residual_protocol": RESIDUAL / "protocol.json"}
    assert protocol["sha256"] == {key: sha(path) for key, path in paths.items()}
    begin = time.monotonic_ns()
    rows = np.loadtxt(PREDICTOR / "rows.tsv", dtype=np.uint64, delimiter="\t", skiprows=1)
    residuals = np.loadtxt(RESIDUAL / "residuals.tsv", dtype=np.uint64,
                           delimiter="\t", skiprows=1)
    assert rows.shape == residuals.shape == (100000, 10)
    assert np.array_equal(rows[:, :2], residuals[:, :2])
    assert np.array_equal(rows[:, 2:6], residuals[:, 6:10])
    index, seeds, translation = labels(rows, pair_masks())
    train = index < 80000
    test = ~train
    assert train.sum() > 1000 and test.sum() > 1000
    arms = {"public": (0, 1), "after_one_free_pair": (2, 3),
            "after_two_free_pairs": (4, 5)}
    output = {}
    for slot in range(2):
        y = translation[:, slot]
        control = baseline(y[train], seeds[train], seeds[test])
        control_hit = np.any(control == y[test, None], axis=1)
        arm_results = {}
        for name, columns in arms.items():
            features = bit_features(residuals[index], columns)
            proposal = score_arm(features[train], features[test],
                                 y[train], seeds[test], seeds[train])
            hit = np.any(proposal == y[test, None], axis=1)
            arm_results[name] = {"hits": int(hit.sum()),
                                 "paired_vs_conditional_frequency": compare(hit, control_hit)}
        output[f"translation_{slot}"] = {"conditional_frequency_hits": int(control_hit.sum()),
                                          "arms": arm_results,
                                          "holdout_labels_sha256": hashlib.sha256(
                                              y[test].astype("<i2").tobytes()).hexdigest()}
    elapsed_ns = time.monotonic_ns()-begin
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = peak if sys.platform == "darwin" else peak*1024
    status = ("CENSORED_TIME" if elapsed_ns > protocol["wall_cap_seconds"]*10**9
              else "CENSORED_MEMORY" if peak > protocol["rss_cap_bytes"]
              else "COMPLETE_HELDOUT_TRANSLATION_SELECTOR")
    result = {"status": status,
              "candidate_id": None, "proposal_id": protocol["proposal_id"],
              "offset_zero_rows": int(len(index)), "train_rows": int(train.sum()),
              "holdout_rows": int(test.sum()), "source_rows": 100000,
              "translation_policy": "min(u,u XOR seed) per corresponding pair",
              "results": output, "elapsed_ns": elapsed_ns, "peak_rss_bytes": peak,
              "source_sha256": sha(Path(__file__)),
              "protocol_sha256": sha(HERE / "protocol.json")}
    (HERE / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "rows": len(index),
                      "hits": {k:{"baseline":v["conditional_frequency_hits"],
                                  **{a:x["hits"] for a,x in v["arms"].items()}}
                               for k,v in output.items()}}))


if __name__ == "__main__":
    main()
