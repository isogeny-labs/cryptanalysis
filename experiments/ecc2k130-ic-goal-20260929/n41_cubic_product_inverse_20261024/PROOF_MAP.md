# Quadratic inverse proof map

The characteristic-two inverse norm factors through a quadratic resultant in the third pair product. The Lean module `QuadraticInverse.lean` uses the pinned `leanprover/lean4:v4.35.0` toolchain; `lean QuadraticInverse.lean` completed and the two `#print axioms` checks report only `propext`, `Classical.choice`, and `Quot.sound`. See `lean_build.stdout.txt`, `lean_build.stderr.txt`, `lean_runtime.txt`, and `lean_receipt.json`. `lean4checker --fresh` was unavailable on this host.

Let `K` be a commutative ring with `2 = 0`, and write

- `P(d) = (1+r)d² + rd + S`, `U(d) = Ad² + Bd + D`;
- `L = 1+r`, `M = LB+rA`, `N = LD+SA`;
- `R = (D+SA)² + SB² + rB(D+S(A+B)) + r²D(A+B+D)`;
- `C = LN²+rNM+SM²`.

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| `C = (1+r)R` | `QuadraticInverse.norm_eq_factor_resultant` | Any commutative ring `K` with `2=0`; checked. |
| `P(d)=U(d)=0 ⇒ R=0` | `QuadraticInverse.common_root_resultant_zero` | As above, and cancellation of multiplication by `1+r`; checked. This is valid in a field for `r≠1`. |
| `R=Res_d(P,U)` | No Lean declaration | Verified as an exact identity in `GF(2)[A,B,D,S,r]` independently by Sage polynomial resultant (`run.py`) and a pure-Python 4×4 Sylvester determinant (`verify.py`). Full generic determinant formalization remains open. |
| The N41 chart coefficients and seven-block point replay | No Lean declaration | Frozen geometry and source-conditioned membership checked by `run.py`, with the archived census checked by `verify.py`; formal chart-to-curve bridge remains open. |

The soundness theorem retains the `r=1` exceptional condition. The N41 enumerated third products have `r≠1`; see the source set assertion in `run.py`. The exceptional factor cannot be canceled in a general ring without its explicit hypothesis.
