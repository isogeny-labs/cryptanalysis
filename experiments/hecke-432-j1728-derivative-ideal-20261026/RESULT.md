# A cubic–quadratic gcd explains the branch-zero fibers

The inverse B-branch becomes zero-over-zero exactly where the cubic isogeny equation and the selected quadratic remainder have a **quadratic common factor** in the 499 rational resolvent-root cells carried forward from the preceding experiment. The frozen prediction held in all four fields: 492 cells have a linear common factor and seven have a squarefree quadratic common factor. Those seven cells are exactly the seven repeated-resolvent-root and branch-zero x-values.

The quadratic factors make the geometry more precise. Six occur at the two octic-norm primes and each splits into two distinct rational `x_B` roots. The seventh occurs at the 83-bit quartic-norm prime and is irreducible over that base field; its two distinct `x_B` roots lie over a quadratic extension. The nearby control has 72 linear common factors and no quadratic one. These are statements about common `x_B` roots; the saved C–E point records and their equation checks are in the parent experiment.

| Prime | Rational factor roots checked | Linear `gcd_T(F,R)` | Quadratic `gcd_T(F,R)` | Rational roots per quadratic |
| --- | ---: | ---: | ---: | --- |
| `414340033` | 213 | 210 | 3 | 2, 2, 2 |
| `431435018569` | 213 | 210 | 3 | 2, 2, 2 |
| `414340153` control | 72 | 72 | 0 | — |
| `4335978784654674076339691` | 1 | 0 | 1 | 0 |

## Exact algebraic bridge

Let `F(T)=T³−x_E T²−64` be the cubic equation for `x_B`, and let `R(T)=aT²+bT+c` be the remainder of the saved degree-12 B-resolvent after division by `F`. The exported branch polynomials are

`D=b(a x_E+b)−ac`, `N=64a²−c(a x_E+b)`.

The exact identity

`D T−N = a(aF−T R)+(a x_E+b)R`

shows that every common root of `F` and `R` satisfies `D T=N`. Two **distinct** common roots force `D=N=0`. Conversely, when `a≠0` and `D=N=0`, every root of `R` is also a root of `F`. The checked Lean theorem [`BranchCollision.two_remainder_roots_common_iff_indeterminate`](formal/BranchCollision.lean) states this equivalence with two distinct remainder roots and the nonzero leading-coefficient hypothesis; the same module checks the identity and both directions separately. [`lean-check.txt`](formal/lean-check.txt) includes the build command, pinned toolchain, dependency revision, and `#print axioms` output.

[`run.py`](run.py) independently specializes the 89-term B-resolvent at every saved `(C,x_E)` root, computes `R=P_B mod F` and `gcd_T(F,R)` with the fixed-degree modular polynomial kernel, checks `N` and `D` against the saved branch values, and records the full gcd coefficients. The source fields and root lists are SHA-pinned in [`protocol.json`](protocol.json). [`audit_sage.py`](audit_sage.py) reconstructs the same equations with checked Sage, verifies the polynomial identity at every cell, repeats the gcds and squarefreeness checks, and counts rational roots of each quadratic. Its separate hash-bound protocol and [`audit_result.json`](audit_result.json) preserve all 499 checks. [`validation.json`](validation.json) binds the receipts. [`sage-runtime-info.txt`](sage-runtime-info.txt) records the checked local Sage build.

## Proof map and next step

| Result | Checked declaration or receipt | Status |
| --- | --- | --- |
| Cubic/remainder elimination identity and common-root branch equation | `BranchCollision.elimination_identity`, `branch_equation` | Lean checked |
| Two distinct common roots force zero-over-zero; with `a≠0`, zero-over-zero makes all remainder roots common | `two_common_roots_force_indeterminacy`, `indeterminate_branch_forces_cubic_on_remainder_roots`, `two_remainder_roots_common_iff_indeterminate` | Lean checked with exact hypotheses |
| Seven quadratic common factors among 499 finite-field cells, with their rational splitting counts | `result.json`, `audit_result.json` | Modular polynomial run and independent checked-Sage audit |

The algebraic theorem explains the branch behavior once the cubic and quadratic share two distinct roots. The remaining symbolic step is to derive, over the source function field, why a repeated root of the quartic or octic `x_E` factor produces that quadratic common `x_B` factor. A resultant or first-subresultant identity could replace the current finite-field bridge with a general criterion and predict further exceptional fibers before point enumeration.
