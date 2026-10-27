# One local certificate and two rank-raising rows in cross-discriminant class walks

The frozen one-step Hecke-commutator search finds an exact nine-row certificate for the recovered degree-2 row at source 10 of the D=-7, conductor-14 class. Its coefficient denominator is 3, and its addition leaves the archived rational rank at 17. The other recovered degree-2 row in that class, at source 25, raises rank to 18 and has no certificate under this one-step archived-row search. In the D=-79, conductor-2 class, both recovered degree-2 rows raise rank independently from 8 to 9 and jointly to 10; neither enters an available one-step commutator with a nonzero coefficient.

| Discriminant | Conductor | Field | Points | Partner degree | Archived rows/rank | Corrected rows/rank | Degree-2 source | Rank after addition | Search result |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| -79 | 2 | 83 | 20 | 5 | 8 / 8 | 10 / 10 | 2 | 9 | `NO_ONE_STEP`; 0 nonzero-coefficient probes of 20 |
| -79 | 2 | 83 | 20 | 5 | 8 / 8 | 10 / 10 | 19 | 9 | `NO_ONE_STEP`; 0 nonzero-coefficient probes of 20 |
| -7 | 14 | 347 | 32 | 7 | 17 / 17 | 20 / 18 | 10 | 17 | `ONE_STEP_CERTIFICATE`; anchor 10, support 9, denominator 3 |
| -7 | 14 | 347 | 32 | 7 | 17 / 17 | 20 / 18 | 25 | 18 | `NO_ONE_STEP`; 1 nonzero-coefficient probe of 32, with an unavailable row |

The corrected D=-7 record also adds one degree-7 row. The degree-2 comparison above uses the *original* 17-row matrix for each individual rank, so it isolates what each repeated-root repair contributes. The joint degree-2 rank is 18. For D=-79, the collector reports eight simple and two recovered repeated degree-2 fibers; all degree-5 probes lack a complete rational in-class fiber. For D=-7, it reports 17 simple and three recovered repeated fibers across degrees 2 and 7.

The tested identity is the same local shifted-operator commutator as [the D=-7 conductor census](../hecke-d7-local-commutator-20261027/RESULT.md). Its abstract algebraic step and nonzero-coefficient isolation already have the checked Lean declarations `HeckeCommutator.shifted_commutator` and `HeckeCommutator.isolate_one_missing` in that experiment's [proof map](../hecke-d7-local-commutator-20261027/formal/PROOF_MAP.json). This experiment adds no new mathematical theorem; it tests the finite availability condition on two other frozen class records.

The [protocol](PROTOCOL.md) fixed the cases and search order. [inputs.json](inputs.json) pins the old and corrected matrices and the collector source hashes. [run.py](run.py) reconstructs complete fibers through the repository's checked Sage build, checks modular-polynomial roots and group sums, tests each integer commutator, and records the first available certificate or bounded search counts. The independent [verify.py](verify.py) checks input hashes, the recovered-row multiset, all rational ranks through a separate `Fraction` elimination, and the integer certificate. Its output was:

```text
-79 2 rank 8 individual {'19': 9, '2': 9} joint 10 certificates 0
-7 14 rank 17 individual {'10': 17, '25': 18} joint 18 certificates 1
```

To reproduce from the repository root, first save `./sage --runtime-info` as `sage-runtime-info.txt` in this directory, then run:

```sh
./sage -python experiments/hecke-commutator-boundary-20261027/run.py --DK -79 --conductor 2
./sage -python experiments/hecke-commutator-boundary-20261027/run.py --DK -7 --conductor 14
python3 experiments/hecke-commutator-boundary-20261027/verify.py
```

The next bounded experiment is to test multi-step commutator combinations or add verified degree-7 rows as allowable witnesses for source 25. Those searches need a separately frozen witness policy and should preserve the original matrix as the baseline.
