# Adaptive stage-hit equivalence

For a finite adaptive add/sub program whose initial public points are
`G` and `Q = w • G`, a checked Lean theorem identifies an informative
group equality at stage `k`: when the old trace has exactly the equality
pattern of its reconstructed affine forms, the stage event holds exactly
when `w` is eligible for that old pattern and is a root of a distinct
old/new form pair. The theorem uses the complete visible label transcript,
the typed prefix program, and injectivity of `s ↦ s • G`.

An exhaustive `Z/7Z` control evaluated seven scalars, all 5,040 bijective
label encodings per scalar, and four stages of one frozen adaptive program.
All 141,120 stage predicates agreed with the affine prediction. The
encoding-fiber cross-check covered 8,617 observed prefix cells.

| Old prefix length | Cases | Eligible | New group equality | Informative event |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 35,280 | 30,240 | 7,560 | 7,560 |
| 3 | 35,280 | 22,680 | 12,600 | 2,520 |
| 4 | 35,280 | 20,160 | 12,600 | 0 |
| 5 | 35,280 | 20,160 | 7,560 | 7,560 |

At prefix length 4 the next form is a known repeat of the zero form;
its point equality is therefore excluded by the distinct-form condition.
At prefix length 3 some equalities occur after the old pattern has already
collapsed, so eligibility excludes those histories. The experiment records
every informative event in `stage-hit-rows.jsonl`; `result.json` gives the
aggregates and SHA-256 of those rows.

This result supplies the pointwise stage-hit bridge to the existing prefix
fiber and aggregate stopping-bound theorems. The next proof step is a
universal first-hit partition that connects these pointwise predicates to
the exact mass identities assumed by the aggregate theorem, including the
initial `G = Q` case. Coordinate-dependent choices require a separate model.

Reproduce with `python3 run.py` and, from `formal/`,
`lake build StageHitEquivalence`. The finite control is an algorithmic
diagnostic, not a CPU timing comparison.
