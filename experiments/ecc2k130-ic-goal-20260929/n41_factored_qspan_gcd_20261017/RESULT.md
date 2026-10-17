# Sparse modular GCD tests an entire second-product span

**A degree-16 GCD gate tested all 1,600 source-valid first/third-product cells of the frozen N41 public residual, implicitly covering the second product's full 128-element span.** It retained exactly the archived source triple `(97508,1383481007416,216004441708)` and no triple on the negative residual. Replacing generic degree-128 GCD by sparse repeated-squaring reduction lowered the complete query intervals from **76.357 to 42.705 seconds** on the witness and **77.315 to 36.439 seconds** on the negative panel. The intervals are ordinary-host diagnostics, not isolated speedup measurements. Independent binary-field replay checks the retained root and both panels against the previously audited 40³ source-code sweep.

## Method and proof

The inputs are the prior [interpolated eliminants](../n41_first_product_interpolated_eliminant_20261017/RESULT.md) `F(p,q,r;t)` for the public witness and frozen negative suffix, over `GF(2)[t]/(t⁴¹+t³+1)`. The curve is `EC1N41Ckb1h7d5e80d3c4d0`. Each of the three free source slots has 40 admissible pair products. For each source-valid `(p,r)`, specialize `F` to a polynomial `f(q)` of degree at most 16. The seven-dimensional second-product span has the monic degree-128 linearized annihilator

`L_Q(q)=Σᵢ cᵢ q^(2ⁱ)`, for `i=0,…,7`.

Its 128 simple roots are exactly the span products. Therefore `gcd(f,L_Q)` has positive degree exactly when some span product zeros `f`; roots are then checked against the 40 usable products. The archived group audit separately checks the distinct-column rule for the retained triple. This is an exact relaxed family gate: the source filter follows the span test. If `f` is identically zero, the implementation takes `g=L_Q` and checks all span roots.

Version 2 avoids division of the degree-128 `L_Q` by each degree-16 `f`. In `GF(2⁴¹)[q]/(f)`, start with `x₀=q mod f` and repeat `xᵢ₊₁=xᵢ² mod f`. Then `Σ cᵢ xᵢ = L_Q mod f`, and `gcd(f,L_Q)=gcd(f,L_Q mod f)`. The worker checks this identity directly on the first four cells of each panel; the [Lean theorem](SparseLinearized.lean) proves that repeated-squaring evaluation commutes with a ring map, the abstract quotient step. The [proof map](PROOF_MAP.md) records the concrete finite-field and polynomial-GCD bridge.

| Frozen suffix | Full-span GCD query | Sparse modular query | Sparse reduction | Small GCD | Source-valid triples | Peak self RSS, sparse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Public witness | 76.357 s | **42.705 s** | 27.225 s | 11.005 s | **1** | 255,787,008 B |
| Negative control | 77.315 s | **36.439 s** | 23.212 s | 9.498 s | **0** | 255,787,008 B |

Each panel has 1,600 `(p,r)` cells and 1,600 attempted GCDs. The sparse version performs seven modular squarings per nonzero degree-16 specialization, or **11,200** across each panel; all cells here had nonzero specializations. The exclusive timing remainder is polynomial specialization, root checking, and loop overhead; exact phase nanoseconds are in [result_v2.json](result_v2.json). The original [result](result.json) and revised result have separate frozen protocols and raw logs. Both ran as one checked-Sage worker under a 180-second alarm and an observational 4-GiB RSS boundary, after the [runtime record](sage_runtime_info.json) was saved.

The [independent v2 verifier](verification_v2.json) uses a separate shift-and-XOR `GF(2⁴¹)` multiplier for the retained root. It reconstructs all source-valid product sets and the complete 128-element second span, checks the root against the eliminant tensor, compares the source-valid triples with the earlier full-cube sweep, and binds the independent reverse-order 128,000-decision audit and the curve group audit. The [v1 verifier](verification.json) makes the same checks for the generic GCD implementation.

## N131 decision boundary

The selected N131 W20 source has **132,045** valid product codes per slot and a 19-dimensional product span. A literal transfer that tests every valid first/third-product pair requires **17,435,882,025** GCD calls per raw public preimage. The 600-second envelope would require **29,059,803 calls/s** for even one preimage. The sparse annihilator has 20 terms, so this implementation shape also requires at least **331,281,758,475 modular squarings** per preimage, or **552,136,264/s** under that cap, before source filtering or the remaining four pair slots. All four public raw preimages multiply these work counts by four. These are exact operation counts for the stated nested-loop shape, not lower bounds on a different joint algorithm.

The revised N41 gate is a correctness-positive compact second-family oracle, yet it visits every `(p,r)` cell. The next method must reject or merge first/third-product rectangles **before** those calls. The dense 16-factor norm and full separation rank measured in the [preceding experiment](../n41_universal_norm_density_20261017/RESULT.md) show why expanding that rectangle condition into a coefficient array is also unattractive. A prospective joint condition should be frozen on the unpinned N41 public relation, then enter the N131 one-worker 600-second/4-GiB relation gate only after it demonstrates source-bound early rejection. This component has `candidate_id: null`.
