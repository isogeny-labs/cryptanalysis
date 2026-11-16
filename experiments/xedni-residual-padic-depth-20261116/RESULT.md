# Formal-parameter depth of two-image relation residuals

Exact arithmetic places all 13,750 rational relation residuals from the wide-shift panel in the reduction kernel and measures their formal-parameter depths. The histogram is **13,723 at depth 1, 26 at depth 2, and one at depth 3**. Every nonidentity residual satisfies `v_p(x) = -2k` and `v_p(y) = -3k` for `k = v_p(-x/y) ≥ 1`. The minimum-model-height selection and the preceding 81-grid selection both choose depth 1 on all 22 frozen public hits. A vector-aware maximum-depth oracle finds a deeper residual on 17 hits, but no exact relation.

## Frozen input and exact method

The [protocol](protocol.json) pins the 625-shift parent experiment by source and result hashes. It admits all 13,750 passed candidate rows, preserving their event, vector, and shift order. The parent panel consists of 22 public relation hits selected from 512 fresh two-image queries. This study reuses those hits conditionally; it does not resample targets or estimate natural hit frequency.

For each candidate rational curve and its two rational points, checked Sage reconstructs the residual `R = aP1+bP2`. If `R` is nonidentity, it computes exact integer valuations of each reduced rational coordinate and of the formal parameter `t=-x/y` at the parent field prime `p`. The producer records `v_p(x)`, `v_p(y)`, `k=v_p(t)`, and whether the stated coordinate pattern holds. A separate [pure-Python audit](audit.py) rederives each curve, point, residual, parent digest, and valuation using `Fraction` arithmetic. No floating-point approximation enters the group or valuation checks.

| Exact result | Count |
| --- | ---: |
| Candidate attempts / passed / failed | 13,750 / 13,750 / 0 |
| Nonidentity / identity residuals | 13,750 / 0 |
| Coordinate valuation pattern passed / failed | 13,750 / 0 |
| `k=1` | 13,723 |
| `k=2` | 26 |
| `k=3` | 1 |
| Parent minimum-model choice with `k≥2` | 0 / 22 |
| Prior 81-grid choice with `k≥2` | 0 / 22 |
| Vector-aware maximum-depth choice with `k≥2` | 17 / 22 |

The raw valuation rows, one compressed part per public hit, are indexed in [run-result.json](run-result.json). The producer's checked-Sage script interval was 8.49 seconds on this ordinary host, with [runtime verification](sage-runtime.json) saved before it. This is a diagnostic interval, with no matched same-target timing comparison. The [independent audit receipt](audit.json) is `PASS`.

As a descriptive reference, summing `625/p` over the 22 field primes gives 25.84 expected depth-2-or-higher rows under independent uniform residues; 27 were observed. The coordinate shifts are dependent and the public hits were conditioned on, so this reference is not a fitted distribution or significance test. The vector-aware depth oracle uses the relation coefficients and therefore cannot serve as a precommitted lift rule. Its deeper residuals remain nonzero rational points.

## Proof relationship and next test

The checked torsion-section result in the preceding study proves that an exact homomorphic rational lift of the full large-prime subgroup cannot exist under rational torsion exclusion. This panel addresses smaller coefficient vectors instead: it measures the nonzero defect left by 13,750 specific rational models. The observed coordinate pattern is a complete empirical check for this panel, not a Lean proof of the general formal-group valuation theorem. A full formalization would need a good-reduction group map and rational `p`-adic valuation lemmas for short Weierstrass points.

A next experiment can use a coefficient-independent proxy for depth, such as a bounded-precision `qP` kernel computation on each candidate lift, and test whether it predicts deeper `aP1+bP2` residuals on fresh public hits. It must charge that computation, preserve every candidate and failure, and require exact rational vanishing for a relation result.

Reproduce the sealed evidence with `python3 verify.py`. New local Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` followed by `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
