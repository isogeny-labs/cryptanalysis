# Proof map

| Result | Exact hypotheses | Lean verification | Concrete bridge |
| --- | --- | --- | --- |
| Finite product vanishes exactly on its source list | Arbitrary field `F`, finite list `xs : List F`, `z : F`; repeated entries allowed | `FlatProduct.vanishingValue_eq_zero_iff_mem` in [FlatProduct.lean](FlatProduct.lean), pinned Lean 4.34.1; `lean FlatProduct.lean` passed and `#print axioms` shows only `propext`, `Classical.choice`, `Quot.sound` | Pure-Python verifier builds every degree-eight and degree-27 product over the concrete `GF(2^41)` encoding and tests all 40 legal right products. |
| GCD detects an exact flat root | Field `F`; `V_A` is a product of distinct linear factors; `f∈F[R]` | **Partial formalization:** no Lean polynomial ring and Bézout/linear-factor bridge in this experiment | Checked Sage computes `gcd(f,V_A)` for every one of the 1,600 specialized pairs; all positive GCDs receive direct root-member checks. Both variants agree with the full direct scan and frozen prior sweep. |
| Query cost and N131 literal-loop count | Exact source sizes and route work; one local worker and stated interval boundaries | Timings are empirical; integer work counts are in [RESULT.md](RESULT.md) | Both programs record exclusive phase nanoseconds and source hashes; independent replay checks full N41 zero grids and program counts. |

The readable GCD proof is that an irreducible common factor of `f` and a product of distinct linear factors `∏(R−a)` must be one of those linear factors. Such a factor divides `f` precisely when `f(a)=0`. The concrete source-to-field map, target eliminant tensor, and exhaustive GCD computation are checked by the frozen arithmetic receipts. The full curve-to-polynomial and concrete finite-rank bridges remain open in Lean.
