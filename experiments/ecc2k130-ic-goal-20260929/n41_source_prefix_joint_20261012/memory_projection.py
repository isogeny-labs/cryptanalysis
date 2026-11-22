"""Exact four-column distinct counts for literal two-pair prefix tables."""

import hashlib
import itertools
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
sys.path.insert(0, str(GOAL / "n131_w18_allseed_fourpair_20261012"))
import fourpair_v2  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def partitions(indices):
    if not indices:
        yield ()
        return
    head, *tail = indices
    for rest in partitions(tail):
        yield ((head,),) + rest
        for i, block in enumerate(rest):
            changed = list(rest)
            changed[i] = (head,) + block
            yield tuple(changed)


PARTITIONS = list(partitions(list(range(4))))
assert len(PARTITIONS) == 15


def distinct_four(counts):
    columns = set().union(*(set(count) for count in counts))
    total = 0
    for partition in PARTITIONS:
        coefficient = math.prod((-1) ** (len(block) - 1) * math.factorial(len(block) - 1)
                                for block in partition)
        mass = math.prod(sum(math.prod(counts[i].get(col, 0) for i in block)
                             for col in columns) for block in partition)
        total += coefficient * mass
    assert total >= 0
    return total


def source_counts(support, width, depth, prefixes):
    return [Counter(col for mask, col in support.items()
                    if mask >> (width - depth) == prefix)
            for prefix in prefixes[:4]]


panel = json.loads((HERE / "panel.json").read_text())
join = json.loads((HERE / "join_summary.json").read_text())
receipts = {receipt["label"]: receipt for receipt in join["receipts"]}
support41 = fourpair_v2.support("n41")
support131 = fourpair_v2.support("n131")
results = []
for case in panel["rows"]:
    depth, prefixes = case["depth"], case["prefixes"]
    c41 = source_counts(support41, 8, depth, prefixes)
    c131 = source_counts(support131, 18, depth, prefixes)
    orientations = math.prod(2 if prefixes[i] == prefixes[i + 1] else 1
                             for i in (0, 2))
    ordered41 = 16 * distinct_four(c41)
    ordered131 = 16 * distinct_four(c131)
    assert ordered41 % orientations == 0 and ordered131 % orientations == 0
    literal41 = ordered41 // orientations
    literal131 = ordered131 // orientations
    if case["label"] in receipts:
        line = (HERE / f"{case['label']}.join.stdout").read_text().splitlines()
        left = next(item for item in line if item.startswith("LEFT_DONE "))
        assert int(left.split()[2]) == literal41, case["label"]
    results.append({"label": case["label"], "depth": depth,
                    "first_two_pair_orientation_quotient": orientations,
                    "n41_ordered_four_mask_signed_count": ordered41,
                    "n41_literal_left_entries": literal41,
                    "n131_ordered_four_mask_signed_count": ordered131,
                    "n131_literal_left_entries": literal131,
                    "n131_one_bit_per_entry_bytes_min": (literal131 + 7) // 8,
                    "n131_ratio_to_4gib_one_bit_min_decimal":
                        f"{((literal131 + 7) // 8) / (4 * 1024**3):.9f}"})
result = {"status": "PASS_EXACT_PREFIX_LITERAL_LEFT_COUNT_N41_REPLAY",
          "candidate_id": None, "partition_terms": len(PARTITIONS),
          "one_worker_rss_cap_bytes": 4 * 1024**3,
          "scope": "literal two-pair hash entries after exact four-column filtering",
          "rows": results,
          "source_hashes": {str(path): sha(path) for path in
                            (HERE / "panel.json", HERE / "join_summary.json",
                             GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json",
                             GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv")},
          "producer_sha256": sha(__file__)}
with (HERE / "memory_projection_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"], len(results))
