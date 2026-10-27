# Eleven conductor-6 Hecke matrices retain every row under multiplicity replay

The multiplicity-aware collector reproduces the complete integer row
multiset of **eleven frozen conductor-6 class matrices**: 2,766 verified
relations across the panel, with no added or lost row. Three rational
neighbor fibers have repeated x-roots. The generic collector recovers
each and agrees with the archived regularized producer. Exact row
multiset equality preserves every matrix rank and the cycle analyses
built from those matrices.

| Repeated fiber | Field | Degree | Source column | Rational x-root multiplicities | Status |
| --- | ---: | ---: | ---: | --- | --- |
| `D_K=-183, f=6` | 1663 | 3 | 93 | `(1,1,2)` | `RECOVERED_REPEATED` |
| `D_K=-1295, f=6` | 11719 | 2 | 49 | `(1,2)` | `RECOVERED_REPEATED` |
| `D_K=-2631, f=6` | 23743 | 3 | 247 | `(1,1,2)` | `RECOVERED_REPEATED` |

The [protocol](PROTOCOL.md) and [input manifest](inputs.json) froze
eleven matrix hashes, the regularized Hecke producer, and the generic
collector before the census. The panel retains the repaired D=-1407
matrix and its distinct fresh-prime instance. D=-39, D=-1295, and
D=-2631 serve as prior-coverage controls. For every saved point and
degree 2 or 3, [census.py](census.py) records the rational-root pattern,
uses the collector on repeated roots, verifies classical modular
polynomial and group-sum identities for complete rows, and compares
the resulting integer row multiset with the archived matrix. The
[summary](summary.json), case receipts, and full per-case ledgers retain
all results and statuses.

The separate [integer validator](validate.py) re-reads each pinned
input, compares all 2,766 reconstructed rows to the archived multiset,
checks every saved point on `y²+y=x³−x²−10x−20`, and independently
evaluates all 2,766 Hecke group sums by affine arithmetic. It also
rechecks the three repeated-fiber x-multiplicities from the persisted
rows. The validator returned `INDEPENDENT_INTEGER_CENSUS_PASS`.
Because every integer row multiset is exactly equal, the corresponding
row spaces and ranks are equal over any coefficient field; no
additional rank computation is needed for these unchanged matrices.

Run from the repository root:

```sh
./sage --runtime-info > experiments/hecke-f6-multiplicity-census-20261027/runtime-info.json
./sage -python experiments/hecke-f6-multiplicity-census-20261027/census.py
python3 experiments/hecke-f6-multiplicity-census-20261027/validate.py
```

The checked Sage census returned `PASS` for each of the eleven cases.
This closes the repeated-rational-root coverage question for the exact
saved matrices and degrees in `inputs.json`. The next coverage test is
on conductor panels outside `f=6`, especially the saved `D_K=-7`
conductors 60 and 90 that were not in the earlier four-conductor
multiplicity panel. Their source matrices and degree sets should be
frozen before inspection.
