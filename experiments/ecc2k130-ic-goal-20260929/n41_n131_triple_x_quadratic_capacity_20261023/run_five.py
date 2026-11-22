"""Exact quadratic x-feature affine hull on frozen N41 and N131 panels."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "five_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_TRIPLE_X_QUADRATIC_FIVE"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
prior = json.loads(Path(cfg["sources"]["prior_result"]["path"]).read_text())
sets = json.loads(Path(cfg["sources"]["x_sets"]["path"]).read_text())
assert prior["x_sets_sha256"] == cfg["sources"]["x_sets"]["sha256"]
signal.alarm(cfg["wall_cap_seconds"])
started = time.monotonic()


def feature(x, n):
    assert 0 <= x < 1 << n
    out = x
    index = n
    for i in range(n):
        active_i = (x >> i) & 1
        for j in range(i + 1, n):
            if active_i and ((x >> j) & 1):
                out |= 1 << index
            index += 1
    assert index == n + n * (n - 1) // 2
    return out


def reduce(word, pivots):
    while word:
        bit = word.bit_length() - 1
        if bit not in pivots:
            return word
        word ^= pivots[bit]
    return 0


rows = {}
for field, n in (("n41", 41), ("n131", 131)):
    base = None
    pivots = {}
    output = []
    for index, group in enumerate(sets[field], 1):
        for x in group:
            f = feature(x, n)
            if base is None:
                base = f
            word = reduce(f ^ base, pivots)
            if word:
                pivots[word.bit_length() - 1] = word
        decisions = {}
        for name, x in prior[field]["residual_x"].items():
            decisions[name] = {
                "affine_hull_contains": reduce(feature(x, n) ^ base, pivots) == 0,
                "exact_x_member": any(x in sub for sub in sets[field][:index])}
        output.append({"first_family_count": index,
                       "feature_count": n + n * (n - 1) // 2,
                       "affine_rank": len(pivots),
                       "affine_codimension": n + n * (n - 1) // 2 - len(pivots),
                       "target_checks": decisions})
    rows[field] = output
assert rows["n41"][0]["target_checks"]["constructed"]["exact_x_member"]
assert rows["n131"][0]["target_checks"]["constructed"]["exact_x_member"]
result = {"status": "PASS_TRIPLE_X_QUADRATIC_FIVE",
          "candidate_id": None,
          "n41": rows["n41"], "n131": rows["n131"],
          "phase_seconds": {"feature_rank_and_targets": time.monotonic() - started},
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "protocol_sha256": sha(HERE / "five_protocol.json")}
path = HERE / "five_result.json"
assert not path.exists()
path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({"status": result["status"],
                  "n41_ranks": [r["affine_rank"] for r in rows["n41"]],
                  "n131_ranks": [r["affine_rank"] for r in rows["n131"]],
                  "seconds": result["phase_seconds"]["feature_rank_and_targets"]}, sort_keys=True))
