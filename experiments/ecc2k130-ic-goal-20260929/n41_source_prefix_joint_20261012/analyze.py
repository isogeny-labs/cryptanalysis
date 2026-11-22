"""Exact labeled source counts for each frozen prefix family and N131 transfer."""

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "n131_w18_allseed_fourpair_20261012"
sys.path.insert(0, str(SOURCE))
import fourpair_v2  # noqa: E402

R41 = 549756390943
R131 = 680564733841876926932320129493409985129
TABLE = SOURCE / "n41_diagonal/pairs.tsv"
SUPPORT131 = HERE.parent / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pair_states(first, second, columns):
    left = Counter(columns[m] for m in first)
    right = Counter(columns[m] for m in second)
    colliding = sum(n * right.get(c, 0) for c, n in left.items())
    return 4 * (len(first) * len(second) - colliding)


def domains(columns, width, depth, prefixes):
    return [set(m for m in columns if (m >> (width - depth)) == prefix)
            for prefix in prefixes]


panel = json.loads((HERE / "panel.json").read_text())
support41 = fourpair_v2.support("n41")
support131 = fourpair_v2.support("n131")
table = []
for line in TABLE.read_text().splitlines()[1:]:
    parts = line.split()
    if parts and parts[0] == "S":
        table.append((int(parts[1]), int(parts[3]), int(parts[4])))
assert len(table) == 4 * 30952
rows = []
for row in panel["rows"]:
    depth = row["depth"]
    prefixes = row["prefixes"]
    d41 = domains(support41, 8, depth, prefixes)
    counts41 = [pair_states(d41[2 * i], d41[2 * i + 1], support41)
                for i in range(4)]
    independent = [0] * 4
    for slot, a, b in table:
        if a in d41[2 * slot] and b in d41[2 * slot + 1]:
            independent[slot] += 1
        if b in d41[2 * slot] and a in d41[2 * slot + 1]:
            independent[slot] += 1
    assert counts41 == independent, row["label"]
    d131 = domains(support131, 18, depth, prefixes)
    counts131 = [pair_states(d131[2 * i], d131[2 * i + 1], support131)
                 for i in range(4)]
    n41 = math.prod(counts41)
    n131 = math.prod(counts131)
    rows.append({"label": row["label"], "depth": depth,
                 "n41_slot_signed_ordered_pair_states": counts41,
                 "n41_labeled_four_tuple_count_before_cross_slot_shield": n41,
                 "n41_uniform_raw_target_mean_exact": f"{n41}/{4 * R41}",
                 "n131_slot_signed_ordered_pair_states": counts131,
                 "n131_labeled_four_tuple_count_before_cross_slot_shield": n131,
                 "n131_uniform_raw_target_mean_exact": f"{n131}/{4 * R131}"})
result = {"status": "PASS_N41_SOURCE_TABLE_REPLAY_AND_N131_EXACT_PREFIX_COUNT",
          "candidate_id": None, "n41_curve_order": 4 * R41,
          "n131_curve_order": 4 * R131,
          "n41_signed_pair_table_rows": len(table), "rows": rows,
          "input_sha256": {str(p): sha(p) for p in
                           (HERE / "panel.json", TABLE, SUPPORT131,
                            HERE.parent / "n41_w7_entropy_cubic_20261011/w8/geometry.json")},
          "source_sha256": sha(__file__)}
with (HERE / "analysis.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"], len(rows))
