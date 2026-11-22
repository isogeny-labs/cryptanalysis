"""Independent source-label and held-out score replay of the translation panel."""

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / "n41_coupled_sixpair_full_ic_20261010/heldout_input.txt"
PREDICTOR = BASE / "n41_w6_public_seed_predictor_20261011/rows.tsv"
RESIDUALS = BASE / "n41_prefix_residual_seed_selector_20261011/residuals.tsv"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pairs_from_source():
    lines = SOURCE.read_text().splitlines()
    header = [int(x) for x in lines[0].split()]
    assert header[2:] == [549756390943, 6]
    out = []
    line = 1
    for block in range(6):
        rotation, size = map(int, lines[line].split()); line += 1
        assert rotation == 5*block and size == 64
        masks, columns = [], []
        for _ in range(size):
            x, y, mask, sign, column = map(int, lines[line].split()); line += 1
            masks.append(mask)
            columns.append(column)
        pairs = []
        for i in range(size):
            for j in range(size):
                if masks[i] < masks[j] and columns[i] != columns[j]:
                    pairs.append((masks[i], masks[j], masks[i]^masks[j]))
        assert len(pairs) == 1956
        out.append(pairs)
    assert line == len(lines)
    return out


def feature(data, columns):
    return np.concatenate([((data[:, col, None] >> np.arange(41, dtype=np.uint64))
                            & 1).astype(np.float64) for col in columns], axis=1)


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert result["status"] == "COMPLETE_HELDOUT_TRANSLATION_SELECTOR"
    assert result["protocol_sha256"] == sha(HERE / "protocol.json")
    assert protocol["sha256"]["source"] == sha(HERE / "run.py")
    assert protocol["sha256"]["source_input"] == sha(SOURCE)
    assert protocol["sha256"]["rows"] == sha(PREDICTOR)
    assert protocol["sha256"]["residuals"] == sha(RESIDUALS)
    assert protocol["sha256"]["generator_protocol"] == sha(BASE / "n41_w6_public_seed_predictor_20261011/protocol.json")
    assert protocol["sha256"]["residual_protocol"] == sha(BASE / "n41_prefix_residual_seed_selector_20261011/protocol.json")
    assert protocol["prior_protocol_sha256"] == sha(HERE / "protocol_v1.json")
    assert protocol["prior_result_sha256"] == sha(HERE / "result_v1.json")
    assert sha(HERE / "run_v1.py") == json.loads((HERE / "protocol_v1.json").read_text())["sha256"]["source"]
    old = json.loads((HERE / "result_v1.json").read_text())
    assert old["results"] == result["results"]
    rows = np.loadtxt(PREDICTOR, dtype=np.uint64, delimiter="\t", skiprows=1)
    residual = np.loadtxt(RESIDUALS, dtype=np.uint64, delimiter="\t", skiprows=1)
    assert rows.shape == residual.shape == (100000, 10)
    assert np.array_equal(rows[:, :2], residual[:, :2])
    assert np.array_equal(rows[:, 2:6], residual[:, 6:10])
    pairs = pairs_from_source()
    selected = np.flatnonzero(rows[:, 2] == rows[:, 3])
    seed = rows[selected, 2].astype(np.int16)
    label = np.zeros((len(selected), 2), dtype=np.int16)
    for j, row_index in enumerate(selected):
        s = int(seed[j])
        for slot in range(2):
            x = pairs[2+slot][int(rows[row_index, 6+slot])]
            y = pairs[4+slot][int(rows[row_index, 8+slot])]
            assert x[2] == y[2] == s
            options = [x[0]^y[0], x[0]^y[1]]
            assert options[0]^options[1] == s
            label[j, slot] = min(options)
    train = selected < 80000
    test = ~train
    assert (len(selected), int(train.sum()), int(test.sum())) == (14781, 11827, 2954)
    replay = {}
    arms = {"public": (0, 1), "after_one_free_pair": (2, 3),
            "after_two_free_pairs": (4, 5)}
    for slot in range(2):
        y = label[:, slot]
        assert hashlib.sha256(y[test].astype("<i2").tobytes()).hexdigest() == result["results"][f"translation_{slot}"]["holdout_labels_sha256"]
        baseline = np.empty((int(test.sum()), 7), dtype=np.int16)
        seed_test = seed[test]
        for s in range(1, 64):
            valid = np.array([min(u, u^s) == u for u in range(64)])
            counts = np.bincount(y[train & (seed == s)], minlength=64).astype(float)
            counts[~valid] = -1
            baseline[seed_test == s] = np.argsort(-counts, kind="stable")[:7]
        base_hit = np.any(baseline == y[test, None], axis=1)
        assert int(base_hit.sum()) == result["results"][f"translation_{slot}"]["conditional_frequency_hits"]
        arm_hits = {}
        counts = np.bincount(y[train], minlength=64)
        for name, cols in arms.items():
            x = feature(residual[selected], cols)
            bitcounts = np.stack([x[train & (y == u)].sum(axis=0) for u in range(64)])
            prob = (bitcounts+1)/(counts[:, None]+2)
            score = np.einsum("ij,kj->ik", x[test], np.log(prob), optimize=False)
            score += np.einsum("ij,kj->ik", 1-x[test], np.log(1-prob), optimize=False)
            for j, s in enumerate(seed_test):
                valid = np.array([min(u, u^int(s)) == u for u in range(64)])
                prior = np.bincount(y[train & (seed == s)], minlength=64)
                score[j, valid] += np.log(prior[valid]+1)
                score[j, ~valid] = -1e100
            proposals = np.argsort(-score, axis=1, kind="stable")[:, :7]
            hit = np.any(proposals == y[test, None], axis=1)
            observed = int(hit.sum())
            assert observed == result["results"][f"translation_{slot}"]["arms"][name]["hits"]
            arm_hits[name] = observed
        replay[f"translation_{slot}"] = {"baseline": int(base_hit.sum()), **arm_hits}
    output = {"status": "PASS_HELDOUT_TRANSLATION_REPLAY",
              "offset_zero_rows": len(selected), "train_rows": int(train.sum()),
              "holdout_rows": int(test.sum()), "hits": replay,
              "result_sha256": sha(HERE / "result.json"),
              "source_sha256": sha(Path(__file__))}
    (HERE / "audit.json").write_text(json.dumps(output, sort_keys=True, indent=2)+"\n")
    print(json.dumps({"status": output["status"], "hits": replay}))


if __name__ == "__main__":
    main()
