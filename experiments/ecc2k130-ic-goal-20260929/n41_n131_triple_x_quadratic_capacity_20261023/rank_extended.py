"""Incremental GF(2) quadratic-feature rank over 280 exact N131 families."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "extended_rank_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_EXTENDED_QUADRATIC_RANK"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
source = json.loads((HERE / "extended_result.json").read_text())
prior = json.loads(Path(cfg["sources"]["prior_result"]["path"]).read_text())
five = json.loads((HERE / "five_result.json").read_text())
assert source["sets_sha256"] == cfg["sources"]["sets"]["sha256"]
assert source["family_count"] == cfg["source_families"]
signal.alarm(cfg["wall_cap_seconds"])
started = time.monotonic()
n = cfg["field_degree"]
width = n + n * (n - 1) // 2
assert width == 8646
targets = prior["n131"]["residual_x"]


def feature(x):
    assert 0 <= x < 1 << n
    out = x
    index = n
    for i in range(n):
        active = (x >> i) & 1
        for j in range(i + 1, n):
            if active and ((x >> j) & 1):
                out |= 1 << index
            index += 1
    return out


def reduce(word, pivots):
    while word:
        bit = word.bit_length() - 1
        if bit not in pivots:
            return word
        word ^= pivots[bit]
    return 0


base = None
pivots = {}
coordinate_set = set()
feature_seconds = rank_seconds = target_seconds = 0.0
first_full = None
rows_path = HERE / "extended_rank_rows.jsonl"
assert not rows_path.exists()
with Path(cfg["sources"]["sets"]["path"]).open() as src, rows_path.open("x") as dst:
    for family_index, line in enumerate(src, 1):
        record = json.loads(line)
        assert len(record["x"]) == 32 and len(set(record["x"])) == 32
        if family_index <= 5:
            assert record["masks"] == prior["n131"]["first_masks"][family_index - 1]
        new_pivots = 0
        for x in record["x"]:
            coordinate_set.add(x)
            tick = time.monotonic()
            f = feature(x)
            feature_seconds += time.monotonic() - tick
            if base is None:
                base = f
            tick = time.monotonic()
            word = reduce(f ^ base, pivots)
            if word:
                pivots[word.bit_length() - 1] = word
                new_pivots += 1
            rank_seconds += time.monotonic() - tick
        tick = time.monotonic()
        target_checks = {name: {
            "exact_x_member": x in coordinate_set,
            "quadratic_hull_contains": reduce(feature(x) ^ base, pivots) == 0}
            for name, x in targets.items()}
        target_seconds += time.monotonic() - tick
        row = {"family_count": family_index,
               "last_masks": record["masks"],
               "distinct_x": len(coordinate_set),
               "quadratic_rank": len(pivots),
               "quadratic_codimension": width - len(pivots),
               "new_pivots": new_pivots,
               "target_checks": target_checks}
        if family_index <= 5:
            assert row["quadratic_rank"] == five["n131"][family_index - 1]["affine_rank"]
            assert {name: {"exact_x_member": value["exact_x_member"],
                           "affine_hull_contains": value["quadratic_hull_contains"]}
                    for name, value in target_checks.items()} == five["n131"][family_index - 1]["target_checks"]
        if first_full is None and len(pivots) == width:
            first_full = family_index
        dst.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        dst.flush()
assert family_index == cfg["source_families"]
result = {"status": "PASS_N131_EXTENDED_QUADRATIC_RANK",
          "candidate_id": None,
          "source_families": family_index,
          "field_degree": n, "feature_width": width,
          "first_full_rank_prefix": first_full,
          "last_rank": len(pivots),
          "last_target_checks": row["target_checks"],
          "phase_seconds": {"feature_construction": feature_seconds,
                            "rank_reduction": rank_seconds,
                            "target_queries": target_seconds,
                            "other": time.monotonic() - started - feature_seconds - rank_seconds - target_seconds},
          "wall_seconds": time.monotonic() - started,
          "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          "rows_sha256": sha(rows_path),
          "protocol_sha256": sha(HERE / "extended_rank_protocol.json")}
(HERE / "extended_rank_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps({k: result[k] for k in ("status", "source_families",
                                             "first_full_rank_prefix", "last_rank",
                                             "wall_seconds", "self_maxrss_raw")}, sort_keys=True))
