# Distinct modular j values inside X0(11) trace fibers

The corrected three-field X0(11) ledger separates modular-point counts from
distinct `j` counts. Across the 78 regular absolute-trace fibers, every
observed `j` has one or two rational preimages. After evaluating the
removable `j`-map branch at `(16,60)`, the full `p=317, |t|=2` fiber has
**40 points over 20 distinct `j` values**. The archived class list has 39
of those points. The `p=941, |t|=50` fiber remains 40 points over 20 `j`
values. This makes the point and underlying-curve counting units explicit
for subsequent Hecke relation-rank experiments.

| p | regular points | trace fibers | distinct j | j with one point | j with two points | maximum multiplicity |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 317 | 297 | 20 | 176 | 55 | 121 | 2 |
| 941 | 896 | 29 | 448 | 0 | 448 | 2 |
| 1009 | 1018 | 29 | 509 | 0 | 509 | 2 |

The largest recorded fiber has 112 points and 56 distinct `j` values
(`p=941, |t|=18`). The p=1009 maximum has 84 points and 42 distinct `j`
values (`|t|=20`). The exact 78-fiber table, including same-`j` pair counts,
is [result_v2.json](result_v2.json). The counts are a finite census of these three
fields, not an asymptotic estimate. In particular, equality of `j` does not
make two X0(11) points or their images under the modular parametrization
the same point; subsequent rank work must retain those separate columns.

## Method and replay

The original [protocol](protocol.json), producer, result and audit remain
frozen. The [v2 protocol](protocol_v2.json) pins both SHA-256 hashes of the
[corrected source ledger](../hecke-x011-trace-fiber-census-20261119/points_v2.jsonl.gz),
the same field set, partition, statistics, and 30-second resource cap. Only
rows marked `regular` enter the trace partition; the 11 finite exceptional
rows remain counted separately. For each `(p, |t|)` fiber, `run_v2.py`
counts the points at each integer `j` and their multiplicities.

`audit_v2.py` independently sorts the source rows, groups by `(p, |t|, j)`,
checks coordinate uniqueness, reproduces every fiber statistic, and matches
the corrected per-field trace histograms. It passed 2,222 source rows,
including 2,211 regular rows and all 78 fibers. The corrected receipt is
[audit_v2.json](audit_v2.json). The v1 result remains available as the
original denominator-exclusion-policy evidence.

From this repository worktree:

```sh
python3 experiments/hecke-x011-fiber-multiplicity-20261119/run_v2.py
python3 experiments/hecke-x011-fiber-multiplicity-20261119/audit_v2.py
```

The next experiment is to add `(16,60)` as a **new modular-point column** to
the archived p317 class relation matrix, generate and verify its Hecke rows,
and measure the resulting rank. The archived 39-column certificate remains
valid for its saved submatrix. This census supplies the corrected 40-column
index set, not the new rank.
