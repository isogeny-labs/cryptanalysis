# Exact tangent admission condition for two-point lifts

For distinct affine rational points `P=(x,y)` and `R=(u,v)` on a nonsingular short Weierstrass curve `y²=x³+Ax+B`, with `y≠0`, the relation `2P=R` holds exactly when

```text
(y+v)² = (x-u)²(2x+u).                         (1)
```

This gives a direct integer-arithmetic admission test for the selected `(2,-1)` vector. Replaying the frozen 26,624-row two-point search under its SHA-256 seal gives 2,048 attempts for this vector. Among 2,004 admitted rational curves, one candidate satisfies (1), exactly the archived rational relation. All eight positive and eight negative controls agree with (1). The result is an exact filter for this relation shape, and the replay measures its selectivity on the frozen panel.

## Derivation

Let `d=x-u`. Because both points lie on the curve,

```text
d(3x²+A) − 2y(y+v) = d²(2x+u) − (y+v)².     (2)
```

The tangent slope at `P` is `m=(3x²+A)/(2y)`. If `2P=R`, the tangent meets `−R=(u,−v)`, so `m=(y+v)/d`, and the doubling x-coordinate satisfies `u=m²−2x`. These equations give (1). Conversely, (1) and (2), with `d≠0` and `y≠0`, give both `m=(y+v)/d` and `m²=2x+u`; the tangent doubling formulas then yield `R`. Nonsingularity keeps the affine group law defined.

For integer coordinate lifts, (1) implies that `2x+u` is a nonnegative integer square and that `d` divides `y+v`: the rational number `(y+v)/d` has an integral square, hence is an integer. These are useful necessary filters, while (1) is the exact condition. They are evaluated as diagnostics on every distinct-x selected-vector row.

## Frozen replay

The [protocol](protocol.json) pins the archived [source rows](../xedni-vector-shift-lift-search-20261116/rows.jsonl) by SHA-256 `3c75b8f6aed964b99e3135cda848289669f7f6bf54a7a8c603ec37b9198e5b9e`, selects the precommitted vector `(2,-1)`, and fixes the criterion before the replay. The [Python replay](replay.py) evaluates (1) independently of the archived group-law status, retains the archived rejects, and checks the rational controls using exact fractions.

| Selected-vector event | Attempts |
| --- | ---: |
| All candidate constructions | 2,048 |
| Distinct lifted x coordinates | 2,026 |
| Admitted rational curves | 2,004 |
| Public `(2,-1)` relation | 40 |
| `2x+u` is an integer square | 66 |
| `(y+v)/(x-u)` is integral | 94 |
| Both necessary integer conditions | 5 |
| Exact condition (1) | 1 |
| Archived exact rational relation | 1 |

The archived statuses for this vector are 2,003 admitted rational nonrelations, one rational relation, 22 coincident-x rejects, and 22 wrong-reduction rejects. There are no criterion/group-law disagreements among the 2,004 admitted curves. The 40 public relation attempts are four shifts for ten query-vector events; one shift reaches the exact rational relation. [result.json](result.json) preserves field-level counts and the zero-exception audit record. This reuses the frozen panel and adds an arithmetic analysis; it is not a fresh-target yield estimate or a wall-time comparison.

## Formal proof map

The pinned Lean 4 `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` build [TangentAdmission.lean](formal/TangentAdmission.lean). `tangent_square_identity` checks (2) over an arbitrary commutative ring under the two curve equations. `tangent_equation_iff_square_condition` checks the equivalence of the tangent cross-product equation and (1) under the same hypotheses. The [build output](formal/build-output.txt) records `#print axioms` as `[propext, Quot.sound]` for both declarations, with no additional axioms.

The remaining formal bridge is the equivalence between this affine tangent equation and equality `2P=R` in Mathlib's nonsingular elliptic-curve point group, with explicit `x≠u` and `y≠0` hypotheses. The mathematical derivation above and the independent frozen group-law replay establish the criterion for this experiment; the Lean group-law theorem remains open.

The next construction step is to generate integer lifts satisfying the square and divisibility constraints first, then require the selected public reductions and good-reduction curve. A frozen fresh-query panel should count every generated and rejected lift to measure the arithmetic sieve's effect on relation yield while retaining the public relation requirement.
