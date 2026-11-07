# Repeated resolvent roots locate inverse-branch indeterminacy

Across four certified finite fields, the inverse B-branch numerator and denominator vanish **exactly at the rational repeated roots** of the specialized quartic or octic resolvent factor. This was checked for all **499 rational factor roots** on the saved source-`j=1728` C points, then independently replayed with modular polynomial arithmetic, derivatives, and Frobenius gcds. Seven repeated x-roots account for the seven branch-zero x-values: three octic roots at each of the two octic-norm primes and one quartic root at the earlier 83-bit quartic-norm prime. The nearby control has none.

The first frozen prediction was that the quartic and octic factors intersect at the exceptional primes. [`result.json`](result.json) records `PREDICTION_MISMATCH`: their rational root sets are disjoint. The octic factor has 141 distinct rational roots across 18 source points, with three double roots; the quartic has 72 simple roots. Thus there are 213 distinct `x_E` values and 426 E-point lifts at each octic-norm prime. The three double octic roots each lift twice and account for the six branch-zero C–E pairs per prime. [`multiplicity_protocol.json`](multiplicity_protocol.json) froze the corrected derivative criterion after that mismatch and before its replay against the four fields. [`multiplicity_result.json`](multiplicity_result.json) and [`audit_result.json`](audit_result.json) preserve the checked-Sage and independent results.

| Prime | Source polynomial degrees | Rational quartic / octic roots | Repeated roots | C–E pairs | Branch-zero x-values |
| --- | --- | ---: | ---: | ---: | ---: |
| `414340033` | `1^18` | 72 / 141 | 3 octic | 426 | 3 |
| `431435018569` | `1^18` | 72 / 141 | 3 octic | 426 | 3 |
| `414340153` nearby control | `1^18` | 72 / 0 | 0 | 0 | 0 |
| `4335978784654674076339691` | `1^2 2^8` | 1 / 0 | 1 quartic | 2 | 1 |
| `4196094289` quartic-norm factor | `3^6` | source gate closed | — | 0 | — |
| `669968600281` quartic-norm factor | `3^6` | source gate closed | — | 0 | — |

The two smaller quartic-norm factors were frozen as held-out tests for a rational repeated quartic root. [`holdout_result.json`](holdout_result.json) records `QUARTIC_HOLDOUT_PREDICTION_MISMATCH`: their degree-18 source polynomial has no rational root. Their source-point gate therefore closes before the branch criterion can be evaluated on a rational fiber. Checked Sage factors the source polynomial into six irreducible cubics at each prime. The independent Frobenius audit reproduces gcd degrees `[0,0,18]` for `gcd(f,X^(p^d)-X)` at `d=1,2,3`. The other four primes give `[18,18,18]` for the three fully split cases and `[2,18,2]` for the 83-bit prime. [`frobenius_result.json`](frobenius_result.json) retains the exact factor polynomials, and [`frobenius_audit_result.json`](frobenius_audit_result.json) verifies their products, squarefreeness, and Frobenius gcd degrees with independent integer-modular arithmetic.

## Methods, proof map, and scope

[`protocol.json`](protocol.json) pins the first quartic–octic overlap prediction and input hashes. [`run_sage.py`](run_sage.py) preserves its failed result. [`multiplicity_sage.py`](multiplicity_sage.py) checks the derivative at every rational factor root, the two branch values, root multiplicities, and saved E lifts. [`audit_multiplicity.py`](audit_multiplicity.py) independently evaluates the factor polynomials and derivatives, counts their rational roots through `gcd(f,X^p-X)`, and checks all branch values. The held-out and six-prime Frobenius diagnostics each have frozen protocols and saved results. [`validation.json`](validation.json) binds the protocols and receipts. All new local Sage jobs used the checked repository launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) identifies that build.

| Result | Formal or executable check | Status |
| --- | --- | --- |
| A polynomial has a repeated root exactly when it and its derivative vanish there | `J1728FiberOverlap.repeated_root_iff_derivative_root` in [`RepeatedRoot.lean`](formal/RepeatedRoot.lean) | Lean checked with exact field and nonzero-polynomial hypotheses; axioms recorded in [`lean-check.txt`](formal/lean-check.txt) |
| Branch numerator and denominator vanish exactly at repeated rational factor roots in the four tested fields | `multiplicity_result.json`, `audit_result.json` | Checked Sage and independent modular audit of 499 roots |
| Source-polynomial splitting patterns at six primes | `frobenius_result.json`, `frobenius_audit_result.json` | Checked Sage factorizations and independent Frobenius gcd/product audit |

The finite-field branch equivalence is an exact checked statement for these inputs; its general algebraic bridge to the branch formulas remains open. A concrete next proof step is to reduce both branch polynomials against the source-j ideal and each factor together with its derivative, seeking a symbolic identity that explains the common zeros. The Frobenius factorization also supplies an early rational-source gate before local C–E counting: a prime with source-polynomial pattern `3^6` has no rational source point in this model.
