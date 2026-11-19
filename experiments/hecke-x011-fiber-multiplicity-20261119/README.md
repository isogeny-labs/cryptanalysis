# Distinct modular j values inside X0(11) trace fibers

The complete three-field X0(11) ledger separates modular-point counts from
distinct `j` counts. Across the 78 regular absolute-trace fibers, every
observed `j` has one or two rational preimages in the ledger. The archived
39-point fiber at `p=317, |t|=2` contains 20 distinct `j` values; the archived
40-point fiber at `p=941, |t|=50` also contains 20. This makes the point and
underlying-curve counting units explicit for subsequent Hecke relation-rank
experiments.

| p | regular points | trace fibers | distinct j | j with one point | j with two points | maximum multiplicity |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 317 | 296 | 20 | 176 | 56 | 120 | 2 |
| 941 | 895 | 29 | 448 | 1 | 447 | 2 |
| 1009 | 1017 | 29 | 509 | 1 | 508 | 2 |

The largest recorded fiber has 112 points and 56 distinct `j` values
(`p=941, |t|=18`). The p=1009 maximum has 84 points and 42 distinct `j`
values (`|t|=20`). The exact 78-fiber table, including same-`j` pair counts,
is [result.json](result.json). The counts are a finite census of these three
fields, not an asymptotic estimate. In particular, equality of `j` does not
make two X0(11) points or their images under the modular parametrization
the same point; subsequent rank work must retain those separate columns.

## Method and replay

The [protocol](protocol.json) pins the compressed and uncompressed SHA-256
hashes of the prior [point ledger](../hecke-x011-trace-fiber-census-20261119/points.jsonl.gz),
the field set, partition, statistics, and 30-second resource cap. Only rows
marked `regular` enter the trace partition; the 14 exceptional rows remain
counted separately. For each `(p, |t|)` fiber, `run.py` counts the number of
points at each integer `j` and records its multiplicity distribution.

`audit.py` independently sorts the source rows, groups by `(p, |t|, j)`,
checks coordinate uniqueness, reproduces every fiber statistic, and matches
the per-field trace histograms in the prior census. It passed 2,222 source
rows, including 2,208 regular rows and all 78 fibers. The audit receipt is
[audit.json](audit.json).

From this repository worktree:

```sh
python3 experiments/hecke-x011-fiber-multiplicity-20261119/run.py
python3 experiments/hecke-x011-fiber-multiplicity-20261119/audit.py
```

The next experiment is to build an exact Hecke-neighbor relation matrix on a
preselected fiber with columns indexed by **modular points**, retaining the
`j` multiplicities, and compare its rank with the archived class-rank result.
This census alone supplies counts, not that matrix.
