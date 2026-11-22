# The cubic–B resultant is exactly −16 times the x_E resolvent

On the exact degree-18 source-`j=1728` fiber, the saved degree-12 B-coordinate relation projects through the cubic isogeny equation to the saved degree-12 E-coordinate relation with a **constant factor of −16**:

\[
\operatorname{Res}_T\bigl(T^3-zT^2-64,\ P_B(x_C,y_C,T)\bigr)
   =-16\,R_E(x_C,y_C,z)
   =-16\,u\,q_4(z)q_8(z).
\]

Here `K=Q(α)` is defined by the pinned degree-18 source polynomial, `y_C` is its saved rational function of `α`, and the equality is in `K[z]`. The source polynomial is irreducible; its saved `y_C` satisfies `y_C²+y_C=α³−7`. [`exact_result.json`](exact_result.json) checks every coefficient of the first equality. An independent **direct** Sage resultant calculation in [`exact_audit_result.json`](exact_audit_result.json) reproduces the factor `−16`, checks the irreducibility of the degree-4 and degree-8 factors, and verifies their exact product with the certified unit `u`.

The universal cubic/quadratic resultant has only eight terms. If `P_B mod (T³−zT²−64)=aT²+bT+c`, then

\[
\operatorname{Res}_T(T^3-zT^2-64,aT^2+bT+c)=
4096a^3-128a^2cz+64ab^2z-192abc+ac^2z^2+64b^3+bc^2z+c^3.
\]

[`UniversalResultant.lean`](formal/UniversalResultant.lean) proves this identity as the determinant of the exact 5×5 Sylvester matrix over an arbitrary commutative ring. The build and `#print axioms` receipt are in [`lean-check.txt`](formal/lean-check.txt). Checked Sage independently verified the same universal formula as a polynomial resultant before substituting the source-field coefficients.

## Finite-field reduction and verification

The frozen [`protocol.json`](protocol.json) selected all 56 saved rational source points across the two octic-norm primes, nearby control, and 83-bit quartic-norm prime. [`run_sage.py`](run_sage.py) computed the cubic–B resultant at each source point and matched **all 13 coefficients** to `−16R_E` modulo the prime. Its derivative vanishes at exactly the seven quadratic common-B-gcd roots among the 499 saved rational `x_E` factor roots. [`audit_formula.py`](audit_formula.py) reconstructed the quadratic remainder by the recurrence `T³=zT²+64`, applied the eight-term formula with independent modular polynomial arithmetic, and reproduced all 56 coefficient arrays and 499 derivative checks. The field-specific scalar is `p−16` in every case.

The characteristic-zero run was frozen in [`exact_protocol.json`](exact_protocol.json) with a 90-second cap; [`exact_attempt.json`](exact_attempt.json) records completion and [`exact_result.json`](exact_result.json) retains the nonzero scalar and degree checks. The independent direct-resultant audit has its own hash-bound protocol. [`validation.json`](validation.json) binds all receipts. Every new local Sage job used the checked repository launcher, with [`sage-runtime-info.txt`](sage-runtime-info.txt) saved before execution.

| Result | Proof or executable check | Status |
| --- | --- | --- |
| Universal eight-term Sylvester determinant | `J1728Projection.sylvester_resultant_formula` | Lean checked over any commutative ring |
| Exact `Res_T(F,P_B)=−16R_E=−16u q_4q_8` in the degree-18 source field | `exact_result.json`, `exact_audit_result.json` | Two exact Sage constructions; one uses the eight-term remainder, the other the direct resultant |
| Reduction to 56 source points and derivative/gcd agreement at 499 roots | `result.json`, `audit_result.json` | Checked Sage and independent modular polynomial audit |

The full 89-term B-polynomial and 278-term E-polynomial substitution into the degree-18 field is checked exactly by the two Sage constructions. Its Lean formalization is **partial**: the universal Sylvester identity is checked, while Lean definitions for this specific source field and the 13 resulting coefficient equalities have not yet been built. The next proof step is to connect a repeated root of `q_4` or `q_8` to a quadratic common factor of the cubic and B-remainder over the source function field. The exact resultant identity supplies the projection equation and fixes its normalization for that work.
