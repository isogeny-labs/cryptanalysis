# Level-432 map from the level-27 quadratic twist

The level-432 map to `B: y²=x³−16` has a direct construction from the genus-one level-27 parametrization of `A: y²+y=x³`. For `q=e^(2πiτ)`, let `P₁=Φ_A(iq)`, `P₃=Φ_A(−iq)`, and `D=P₁−P₃` in the group law on `A`. The coordinate transform

`X_B(q)=−4 x(D)`, `Y_B(q)=−8i(y(D)+1/2)`

agrees with Sage's independently computed level-432 modular-parametrization Laurent series through every coefficient below `q^52`. The curve equation `Y_B²=X_B³−16` and differential identity `X_B′/(2Y_B)=f_B(q)/q` pass to the same cap. Its leading terms are `X_B=q⁻²+2q⁴+q¹⁰+4q¹⁶+8q²²+…` and `Y_B=−q⁻³+5q³+5q⁹+9q¹⁵+14q²¹+…`.

The weight-two newforms satisfy `a_B(n)=χ₋₄(n)a_A(n)` for every `0≤n≤144`, the level-432 Sturm bound. The independent verifier uses `χ₋₄(n)=0` for even `n`, `+1` for `n≡1 mod 4`, and `−1` for `n≡3 mod 4`; it also reconstructs `D` by the explicit chord slope rather than Sage point subtraction. The checked installation, exact models, coefficient vectors, all compared Laurent coefficients, and replay output are in [the protocol](protocol.json), [runtime receipt](sage_runtime.json), [result](result.json), and [validation](validation.json). The protocol was frozen before this persisted run, after an exploratory identity at shorter precision.

The algebraic coordinate transport has a checked Lean theorem, `TwistCoordinates.forward`, with hypotheses `i²=−1` and `y²+y=x³` over a characteristic-zero field. The [proof](formal/TwistCoordinates.lean) builds under the pinned toolchain and Mathlib revision in [DEPENDENCIES.json](formal/DEPENDENCIES.json); `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`. The written proof is the calculation

`(−8i(y+1/2))² = 64i²(y+1/2)² = −64(y²+y)−16 = (−4x)³−16`.

| Result | Formal declaration | Verification and remaining bridge |
| --- | --- | --- |
| Coordinate transport `A→B` | `TwistCoordinates.forward` | Kernel-checked; exact hypotheses above |
| Newform twist through Sturm bound | none | Exhaustive checked-Sage coefficient equality `n≤144`; global modular-form twist theorem not formalized here |
| Group-law Laurent identity | none | Independent Sage and manual chord-law agreement below `q^52`; modular descent and period-lattice identification remain open |

The next construction step is to express the translated points as algebraic functions on a defined modular-curve model or a twisting correspondence over the rational base, including the period/lattice normalization. That would allow reduction at a prime and exact evaluation on finite-field moduli. The current result is a formal-series map construction with `candidate_id: null`; no IC target workload or online-time comparison was run.

Reproduce with:

```sh
./sage --runtime-info > experiments/hecke-432-twist-correspondence-20261025/sage_runtime.json
./sage -python experiments/hecke-432-twist-correspondence-20261025/produce_sage.py
./sage -python experiments/hecke-432-twist-correspondence-20261025/verify_sage.py
```
