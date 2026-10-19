# Monomial half-trace seed proof map

Pinned Lean toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`. The module imports Lean `Std` and `Init.Grind.Ring.Basic`, with no external Lean package revision. Run `lean MonomialHalfTrace.lean`; `lean_build.stdout`, `lean_build.stderr`, `lean_version.txt`, and `lean_check.json` preserve the exact check. The local `lean4checker` executable was unavailable.

| Mathematical statement | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| The finite half-trace prefix of `h²+h` equals the paired Frobenius trace prefix of `h`. | `MonomialHalfTrace.halfTraceN_monomial_seed` | Commutative ring `R`; `2 = 0`; all natural prefix lengths and all `h : R`. | Kernel checked. |
| Paired Frobenius trace equals the ordinary trace prefix of even length. | `MonomialHalfTrace.pairedTraceN_eq_traceN` | Commutative ring `R`; all natural prefix lengths and all `h : R`. | Kernel checked. |
| Appending one ordinary trace term adds the indicated repeated square. | `MonomialHalfTrace.traceN_succ_last` | Commutative ring `R`; all lengths and elements. | Kernel checked. |
| In odd degree `2n+1`, zero trace and Frobenius closure force `h` to be the half-trace root of `h²+h`. | `MonomialHalfTrace.monomial_seed_of_trace_zero` | Commutative ring `R`; `2 = 0`; `traceN (2n+1) h = 0`; `frobN (2n+1) h = h`. | Kernel checked. |

The N41 `h=t³` and N131 `h=t⁵` or `h=t¹⁰` instances were evaluated in the declared finite-field representations by the checked Sage launcher and by the independent binary-field circuit model. A Lean construction of those exact quotient fields and a Lean proof of each instance's trace-zero and irreducibility facts remain open. The checked generic theorem retains their exact required hypotheses, so the field-specific computational certificates are not presented as Lean field-instance proofs. The pair-output curve identity belongs to the earlier fixed-seed method; this module formalizes the new seed selection rule.

`#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound` for the recorded declarations. The module contains no `sorry`, `admit`, custom research axiom, or unverified native evaluation.
