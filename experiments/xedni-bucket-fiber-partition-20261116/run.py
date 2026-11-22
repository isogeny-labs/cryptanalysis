"""Exhaustive visible-bucket mass identities for a fixed adaptive Z/7 program."""
import gzip
import hashlib
import itertools
import json
from collections import Counter
from math import factorial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
protocol = json.loads((ROOT / "protocol.json").read_text())
assert protocol["schema"] == "xedni-bucket-fiber-partition-protocol-v1"
Q = 7
LENGTHS = tuple(protocol["prefix_lengths"])
assert LENGTHS == (2, 3, 4, 5)


def forms(labels, count):
    fs = [(0, 1), (1, 0)]
    if count >= 3:
        fs.append((1, 1) if labels[0] < labels[1] else (-1, 1))
    if count >= 4:
        fs.append((0, 0))
    if count >= 5:
        fs.append((0, 0))
    if count >= 6:
        fs.append((0, 2))
    return tuple((a % Q, b % Q) for a, b in fs)


def value(f, w):
    return (f[0] * w + f[1]) % Q


def actual_points(w, enc):
    return (1, w, (1 + w) % Q if enc[1] < enc[w] else (1 - w) % Q,
            0, 0, 2)


actual_fiber = Counter()
actual_live = Counter()
actual_hit = Counter()
for w in range(Q):
    for enc in itertools.permutations(range(Q)):
        pts = actual_points(w, enc)
        labels = tuple(enc[x] for x in pts)
        fs = forms(labels, 6)
        assert tuple(value(f, w) for f in fs) == pts
        raw_hits = [j for j in range(1, 6)
                    if any(fs[i] != fs[j] and pts[i] == pts[j] for i in range(j))]
        first = min(raw_hits) if raw_hits else None
        for k in LENGTHS:
            key = (k, w, labels[:k])
            actual_fiber[key] += 1
            if first is None or first >= k:
                actual_live[key] += 1
            if first == k:
                actual_hit[key] += 1

rows = []
by_length = {}
cells = 0
positive = 0
for k in LENGTHS:
    total_fiber = total_live = total_hit = 0
    for w in range(Q):
        for labels in itertools.product(range(Q), repeat=k):
            key = (k, w, labels)
            old = forms(labels, k)
            vals = tuple(value(f, w) for f in old)
            consistent = all((labels[i] == labels[j]) == (vals[i] == vals[j])
                             for i in range(k) for j in range(i))
            expected_fiber = factorial(Q - len(set(vals))) if consistent else 0
            eligible = all(vals[i] != vals[j] for i in range(k)
                           for j in range(i) if old[i] != old[j])
            new = forms(labels, k + 1)[k]
            candidate = any(old[i] != new and vals[i] == value(new, w)
                            for i in range(k))
            fiber = actual_fiber[key]
            live = actual_live[key]
            hit = actual_hit[key]
            assert fiber == expected_fiber, (key, fiber, expected_fiber)
            assert live == expected_fiber * int(eligible), (key, live)
            assert hit == expected_fiber * int(eligible and candidate), (key, hit)
            total_fiber += fiber
            total_live += live
            total_hit += hit
            cells += 1
            if fiber:
                positive += 1
                rows.append({"k": k, "w": w, "labels": labels,
                             "fiber": fiber, "live": live, "first_hit": hit})
    assert total_fiber == Q * factorial(Q)
    by_length[str(k)] = {"fiber": total_fiber, "live": total_live,
                         "first_hit": total_hit}

raw = ROOT / "positive-bucket-rows.jsonl.gz"
with raw.open("wb") as file:
    with gzip.GzipFile(fileobj=file, mode="wb", mtime=0, filename="") as stream:
        for row in rows:
            stream.write((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode())
result = {"schema": "xedni-bucket-fiber-partition-result-v1", "status": "PASS",
          "executions": Q * factorial(Q), "cells_checked": cells,
          "positive_fiber_cells": positive, "zero_fiber_cells": cells - positive,
          "mismatches": 0, "by_length": by_length,
          "rows_sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}
(ROOT / "result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
