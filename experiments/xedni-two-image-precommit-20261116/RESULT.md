# Two public point images can be fixed before a vector search; their interpolated lifts yield no selected rational relation

A frozen two-image construction produced a nonsingular rational curve with both required public point reductions for **all 512 fresh public query pairs** in the larger-order panel. The 511 pairs with different finite `x` coordinates each determine one short-Weierstrass curve from their centered integer lifts; the one equal-`x` pair has opposite public points and uses an explicit opposite-point lift. Testing the same 13 coefficient vectors per query gave **zero rational relations in 6,656 attempts**, while the public points have **17 relations** in that family. The checked Lean uniqueness theorem identifies the structural constraint: once two distinct-`x` affine lifts are fixed, both curve coefficients are forced.

## Frozen construction and measurement

The [protocol](protocol.json) pins the [larger-order public transcript from PR #1671](https://github.com/isogeny-labs/cryptanalysis/pull/1671) by SHA-256 before this pass. The transcript holds eight prime-order subgroups (`q=293–599`), four SHA-derived targets per field, 16 ordered offset queries per target, and 13 selected vectors per query. Each query's curve and its two rational points are constructed and validated before the runner inspects any coefficient vector.

For finite points `U=(uₓ,uᵧ)` and `V=(vₓ,vᵧ)`, center their coordinates in `[-p/2,p/2]` as `(x₁,y₁)` and `(x₂,y₂)`. When `uₓ≠vₓ`, put

```text
fᵢ = yᵢ² − xᵢ³,
A = (f₁−f₂)/(x₁−x₂),       B = f₁−Ax₁.
```

Then both rational points lie on `E_{A,B}: y²=x³+Ax+B`. Because `x₁−x₂` is nonzero modulo `p`, both coefficients reduce to the public model `A≡−1`, `B≡−2 (mod p)`. For the one pair with `uₓ=vₓ`, the distinct public points are opposites. The runner chooses `(x,y)` and `(x,−y)` on `A=−1`, `B=y²−x³+x`. It records this branch separately.

| Field `p` | Query curves | Public relations / 832 vectors | Rational relations / 832 vectors |
| ---: | ---: | ---: | ---: |
| 313 | 64 | 2 | 0 |
| 421 | 64 | 1 | 0 |
| 431 | 64 | 3 | 0 |
| 547 | 64 | 1 | 0 |
| 571 | 64 | 2 | 0 |
| 593 | 64 | 1 | 0 |
| 617 | 64 | 3 | 0 |
| 677 | 64 | 4 | 0 |
| **Total** | **512** | **17 / 6,656** | **0 / 6,656** |

All 512 curves passed nonsingularity, good reduction at their specified prime, and both point-reduction checks. [queries.jsonl.gz](queries.jsonl.gz) retains the 511 distinct-`x` constructions, the equal-`x` branch, coefficients, points, and statuses. [vectors.jsonl.gz](vectors.jsonl.gz) retains every selected rational and public relation test, including all 17 public hits. The checked Sage run took 0.49 seconds for this bounded script on this host, excluding the launcher check; this is an algorithmic diagnostic with no isolated same-target comparison. The two compressed transcripts are 13,838 and 20,625 bytes, below the repository's artifact policy threshold.

The [independent audit](audit.py) uses Python `Fraction` and separate finite and rational group-law implementations. It reconstructs every curve equation, discriminant, coefficient and point reduction, public relation, and rational vector sum from the pinned source. [audit.json](audit.json) records `PASS`; both run and audit stderr files are empty. The [runtime receipt](sage-runtime.json) was saved before the workload, and [run-result.json](run-result.json) fixes the attempt counts and raw/compressed transcript digests.

## Checked theorem and proof map

The pinned Lean 4 `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` build [TwoImagePrecommit.lean](formal/TwoImagePrecommit.lean). It proves that the interpolation equations hold over any field, that two distinct-`x` point equations uniquely fix `A` and `B`, that distinct same-`x` points have opposite `y`, and that an additive reduction map sends a rational group relation to its public counterpart. [PROOF_MAP.md](PROOF_MAP.md) gives the declaration-level assumptions and remaining bridge. The saved [build output](formal/build-output.txt) reports 9,040 successful jobs; all six `#print axioms` outputs contain only `propext`, `Classical.choice`, and `Quot.sound`. `lean4checker --fresh` was unavailable on this host.

The unique-coefficient theorem applies to the chosen affine lifts. Changing their integer shifts changes the interpolated rational curve, and this experiment does not search those choices. The zero count is exact for the frozen 13-vector family and 512 queries. A next bounded experiment can freeze a two-image shift grid before seeing the vector outcomes, charge every curve and relation attempt, and test whether any shift moves one of the 17 public hits into a rational hit.

From this worktree, reproduce with `/Volumes/SSD990/cryptanalysis/sage --runtime-info`, `/Volumes/SSD990/cryptanalysis/sage -python experiments/xedni-two-image-precommit-20261116/run.py`, `python3 experiments/xedni-two-image-precommit-20261116/audit.py`, `(cd experiments/xedni-two-image-precommit-20261116/formal && lake build TwoImagePrecommit)`, and `python3 experiments/xedni-two-image-precommit-20261116/verify.py`.
