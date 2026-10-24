"""Independent low-pivot replay of all quadratic family and target decisions."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg = json.loads((HERE / "audit_protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_N131_QUADRATIC_RANK_AUDIT"
for name, item in cfg["sources"].items():
    assert sha(item["path"]) == item["sha256"], name
source = json.loads((HERE / "extended_result.json").read_text())
rank_result = json.loads((HERE / "extended_rank_result.json").read_text())
prior = json.loads(Path(cfg["sources"]["prior_result"]["path"]).read_text())
assert source["sets_sha256"] == cfg["sources"]["sets"]["sha256"]
assert rank_result["rows_sha256"] == cfg["sources"]["rank_rows"]["sha256"]
signal.alarm(cfg["wall_cap_seconds"])
started = time.monotonic()
n = cfg["field_degree"]
pair_width = n * (n - 1) // 2
width = pair_width + n
assert width == rank_result["feature_width"]


def feature_reverse(x):
    assert 0 <= x < 1 << n
    out = x << pair_width
    index = 0
    for j in range(1, n):
        if (x >> j) & 1:
            for i in range(j):
                if (x >> i) & 1:
                    out |= 1 << index
                index += 1
        else:
            index += j
    assert index == pair_width
    return out


def reduce_low(word, pivots):
    while word:
        bit = (word & -word).bit_length() - 1
        if bit not in pivots:
            return word
        word ^= pivots[bit]
    return 0


base = None
pivots = {}
coordinates = set()
checked = target_checks = 0
first_full = None
with Path(cfg["sources"]["sets"]["path"]).open() as sets, \
     Path(cfg["sources"]["rank_rows"]["path"]).open() as rows:
    for family_index, (source_line, rank_line) in enumerate(zip(sets, rows), 1):
        source_row = json.loads(source_line)
        measured = json.loads(rank_line)
        assert measured["family_count"] == family_index
        assert measured["last_masks"] == source_row["masks"]
        assert len(source_row["x"]) == 32
        coordinates.update(source_row["x"])
        for x in source_row["x"]:
            f = feature_reverse(x)
            if base is None:
                base = f
            reduced = reduce_low(f ^ base, pivots)
            if reduced:
                bit = (reduced & -reduced).bit_length() - 1
                pivots[bit] = reduced
        assert measured["distinct_x"] == len(coordinates)
        assert measured["quadratic_rank"] == len(pivots)
        assert measured["quadratic_codimension"] == width - len(pivots)
        for name, x in prior["n131"]["residual_x"].items():
            decision = {"exact_x_member": x in coordinates,
                        "quadratic_hull_contains":
                        reduce_low(feature_reverse(x) ^ base, pivots) == 0}
            assert measured["target_checks"][name] == decision
            target_checks += 1
        if first_full is None and len(pivots) == width:
            first_full = family_index
        checked += 1
assert checked == cfg["family_count"]
assert first_full == rank_result["first_full_rank_prefix"]
assert len(pivots) == rank_result["last_rank"]
out = {"status": "PASS_INDEPENDENT_N131_QUADRATIC_RANK_AUDIT",
       "candidate_id": None,
       "families_checked": checked, "target_checks": target_checks,
       "first_full_rank_prefix": first_full, "last_rank": len(pivots),
       "wall_seconds": time.monotonic() - started,
       "self_maxrss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       "protocol_sha256": sha(HERE / "audit_protocol.json")}
(HERE / "audit_result.json").write_text(json.dumps(out, sort_keys=True, indent=2) + "\n")
signal.alarm(0)
print(json.dumps(out, sort_keys=True))
