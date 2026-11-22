"""Independent modular rank of prior N41 rows, bucket row, and prefix hits."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
R = 549756390943
OLDER = ("n41_w8_sixpair_mitm_20261011", "n41_w8_ninepair_join_control_20261012",
         "n41_w8_tenpair_xquotient_20261012")
PATHS = [GOAL / name / "audit_result.json" for name in OLDER]
PATHS += [GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal/audit_result.json",
          GOAL / "n131_w18_bucketed_public_20261012/bucket_audit_result.json",
          HERE / "sage_audit_result.json"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row(value):
    if isinstance(value, list):
        return {int(item["column"]): int(item["coefficient_mod_r"]) % R for item in value}
    return {int(k): int(v) % R for k, v in value.items()}


def rank(rows):
    pivots = {}
    for entry in rows:
        work = {k: v for k, v in entry.items() if v}
        while work:
            pivot = min(work)
            if pivot not in pivots:
                scale = pow(work[pivot], -1, R)
                pivots[pivot] = {k: v * scale % R for k, v in work.items()}
                break
            factor = work[pivot]
            for k, v in pivots[pivot].items():
                work[k] = (work.get(k, 0) - factor * v) % R
                if not work[k]:
                    work.pop(k, None)
    return len(pivots)


base = [row(json.loads(path.read_text())["relation_row"]) for path in PATHS[:4]]
bucket = row(json.loads(PATHS[4].read_text())["relation_row"])
prefix = json.loads(PATHS[5].read_text())
hits = {item["label"]: row(item["relation_row"]) for item in prefix["relations"]}
assert rank(base) == 4 and rank(base + [bucket]) == 5
results = []
ordered = list(base) + [bucket]
for label in ("d3_positive", "d3_random3", "d4_positive"):
    before = rank(ordered)
    after = rank(ordered + [hits[label]])
    results.append({"label": label, "rank_before": before, "rank_after": after,
                    "novel": after > before})
    ordered.append(hits[label])
result = {"status": "PASS_INDEPENDENT_N41_RANK_UNION",
          "candidate_id": None, "subgroup_order": R,
          "baseline_rank": rank(base), "rank_with_bucket": rank(base + [bucket]),
          "rank_with_bucket_and_prefix_hits": rank(ordered),
          "prefix_insertions": results,
          "sources": {str(path): sha(path) for path in PATHS},
          "source_sha256": sha(__file__)}
with (HERE / "rank_union_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"], result["rank_with_bucket_and_prefix_hits"])
