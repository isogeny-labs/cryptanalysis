# Random shear controls reproduce the N131 quadratic certificate cutoff

**Eight deterministic random sign-polynomial controls all lose their shared quadratic determinant-value certificate in code 68, matching the frozen W23 panel's code-68 cutoff.** Their first inconsistent row indices are **8,642–8,649**; the actual W23 result first fails at row **8,642**. One control has that exact row and rank. Every control has the same degree-at-most-three sign law and the same seven characteristic-two shear identities as the real Riemann–Roch determinant. The observed 67-code certificate capacity therefore matches a finite-interpolation null on this panel; its rank profile gives no positive evidence for a curve-specific early family filter.

## Matched null and exact calculation

The [W23 capacity result](../n131_w23_rr_quadratic_capacity_20261016/RESULT.md) tests 68 ascending first-pair codes, two x roots and 64 sign choices per code, with five other pair-code/root choices fixed and the frozen N131 public target in the determinant. Its degree-two Boolean score has `131+binom(131,2)=8,646` features. The real first contradiction is an independently checked odd dependency of 4,373 rows at index 8,642.

For each of the same 136 code/root charts, this control replaces the field-valued sign-polynomial coefficients with deterministic SHAKE256-derived 131-bit values. It retains only masks of sign degree at most three. Six cubic coefficients are solved from the six independent five-row shear identities, and one quadratic coefficient is solved from the all-six pair identity. Thus each chart has **35 freely chosen field coefficients** out of the 42 sign monomials of degree at most three. The [frozen protocol](protocol.json) fixes the SHAKE256 domain, seeds `0,…,7`, chart order, source result hashes, one worker, and a 300-second parent cap. It does not reuse the actual curve coordinates or preserve algebraic coupling between the two x roots of a code.

The runner evaluates all 64 sign assignments in each chart, forms the same 8,646 Boolean linear/quadratic features of each synthetic 131-bit value, and inserts rows with right-hand side one until the first inconsistency. It saves every generated coefficient table in [coefficients.json](coefficients.json) and the per-seed cutoff in [result.json](result.json). No sampled synthetic value is zero through its respective stopping row.

| Input | First inconsistent row | Rank before failure | Code ordinal |
| --- | ---: | ---: | ---: |
| Frozen W23 determinant panel | **8,642** | **8,642** | **67** |
| Shear-null seed 0 | 8,643 | 8,643 | 67 |
| Shear-null seed 1 | 8,645 | 8,645 | 67 |
| Shear-null seed 2 | 8,648 | 8,646 | 67 |
| Shear-null seed 3 | 8,649 | 8,646 | 67 |
| Shear-null seed 4 | **8,642** | **8,642** | 67 |
| Shear-null seed 5 | 8,649 | 8,646 | 67 |
| Shear-null seed 6 | 8,645 | 8,645 | 67 |
| Shear-null seed 7 | 8,647 | 8,646 | 67 |

The [independent verifier](verify.py) regenerates every random free coefficient from the frozen SHAKE256 law, checks the degree bound and all seven identities in every chart, evaluates each sign polynomial directly, and recomputes all eight cutoffs with low-pivot elimination. Its [terminal receipt](terminal.json) reports `PASS_N131_SHEAR_RANDOM_NULL_REPLAY`. The one-worker producer took 61.671 seconds inside its Python process on an ordinary host; the independent replay and raw stdout/stderr are retained separately. These are representation controls with `candidate_id: null`.

## Interpretation and next construction

The random controls reproduce both the code-68 boundary and the near-full feature rank. This supports treating the previous shared quadratic score as a post-enumeration interpolation certificate on the tested fixed-five panel. These controls preserve sign degree and shear identities; they do not model the source-code equations, curve point law, or dependence between root charts. A different source-conditioned invariant remains an open algorithmic possibility.

The next test should derive an exact identity **from W23 pair-source code bits and at least two jointly unresolved partial sums**, then show its rejection or retention pattern exceeds this shear-preserving null and can be evaluated before member-code enumeration. Freeze an unpinned N41 public-point run with complete target-dependent synthesis, failed-region and relation-replay costs before any N131 ordinary relation promotion under one worker, 600 seconds and 4 GiB. The later unseen single-target DLP and matched same-point rho comparison remain the active IC acceptance gates.
