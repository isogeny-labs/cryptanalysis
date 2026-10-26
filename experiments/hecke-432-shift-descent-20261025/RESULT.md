# A rational level-432 modular map through two level-27 shifts

The shifts `τ ↦ τ+1/4` and `τ ↦ τ−1/4` define degree-24 morphisms `θ₊, θ₋: X₀(432) → X₀(27)` over `Q(i)`. Their composition with the level-27 parametrization `Φ_A` of `A: y²+y=x³` gives an algebraic map to `B: y²=x³−16`:

`D = Φ_A∘θ₊ − Φ_A∘θ₋`, `F = (−4x(D), −8i(y(D)+1/2))`.

Complex conjugation exchanges `θ₊` and `θ₋`, so it sends `D` to `−D`; on `A`, negation is `(x,y)↦(x,−y−1)`. Consequently both coordinates of `F` are fixed, and `F` is defined over `Q`. The coordinates agree with the normalized level-432 modular parametrization globally: the pullback invariant differential has the normalized level-432 newform, and both maps send the cusp at infinity to the identity. This supplies the algebraic descent that the preceding [formal-series experiment](../hecke-432-twist-correspondence-20261025/RESULT.md) left open. An explicit function-field evaluator for finite-field points remains to be constructed.

For `γ=[a b; c d]∈Γ₀(432)`, write `c=432k`. The determinant equation gives `ad≡1 (mod 4)`, hence `d−a=4e`. Exact conjugation gives

`t₊γt₊⁻¹ = [a+108k, b+e−27k; c, d−108k]`,

`t₋γt₋⁻¹ = [a−108k, b−e−27k; c, d+108k]`,

where `t₊=[1 1/4;0 1]` and `t₋=[1 −1/4;0 1]`. Both conjugates are integral determinant-one matrices with lower-left entry divisible by 27. The checked [Lean proof](formal/ShiftSubgroup.lean) establishes the arithmetic containment for both signs and the coordinate Galois identity. The subgroup indices are 864 and 36, so each map has degree 24; Sage computes genera 55 and 1. For a source `Γ₀(N)`, the unipotent `[1 0;N 1]` shows that the shift requires `16|N` and target level requires `27|N`; thus `432|N` is necessary, and the displayed calculation makes it sufficient.

Write `f_A(q)=∑a_A(n)qⁿ`. Translation and the invariant differential give

`F*ω_B = (f_A(iq)−f_A(−iq))/(2i) · dq/q`.

The coefficient at `qⁿ` is `χ₋₄(n)a_A(n)`. The [prior frozen coefficient ledger](../hecke-432-twist-correspondence-20261025/result.json) matches the level-432 newform for every `n≤144`; the index-864 weight-two Sturm bound is 144. Both sides are weight-two cusp forms on `Γ₀(432)`, so the [Sturm criterion](https://doc.sagemath.org/html/en/reference/modfrm/sage/modular/modform/space.html) gives equality. Sage also checked `Φ_A*ω_A=f_A(q)dq/q` through `q⁵¹`, and the prior independent chord-law check matched the resulting coordinates through `q⁵¹`. The global identification uses the invariant differential and cusp normalization, rather than extrapolating from those coordinate coefficients.

The analytic quotient maps are algebraic because they are maps of compact modular curves. Their `q`-expansions at the rational infinity cusp have coefficients in `Q(i)`, and the [q-expansion principle](https://escholarship.org/uc/item/4th7g01n) gives the stated field of definition. This is the field-descent step in the written proof; the Lean module formalizes the exact matrix and coordinate algebra, while the modular-curve and Sturm implications remain written mathematics backed by the frozen Sage certificate. The proof map is:

| Claim | Lean declaration | Status |
| --- | --- | --- |
| `Γ₀(432)` conjugates have integral entries, determinant one, and lower-left divisible by 27 | `ShiftSubgroup.bothConjugates` | Checked |
| A level divisible by 16 and 27 is divisible by 432 | `ShiftSubgroup.commonLevel` | Checked |
| Conjugate coordinate expression is invariant | `ShiftSubgroup.conjugateTwistY` | Checked |
| Shift maps and `Q(i)` field of definition | none | Written proof via group inclusion and q-expansion principle; Lean modular-curve definitions absent |
| Equality with normalized `X₀(432)→B` map | none | Written differential/cusp proof with checked 145-coefficient Sturm certificate; Lean modular-form and Abelian-map bridge absent |

The [protocol](protocol.json) freezes levels, shifts, sample seed, and prior commit. [Sage output](result.json) retains genus, index, degree, 10,000 exact-matrix diagnostics and minimality controls. The [global proof-input audit](global_validation.json) binds the prior ledger by SHA-256, checks all 145 coefficients, and verifies cusp pole orders. The actual universal subgroup implication is proved in Lean; the sampled matrices are an independent implementation control. The current map is algebraic and rational, but evaluating it on a specified finite-field modular point still requires an explicit model and rational functions or a proved moduli/isogeny evaluation algorithm. There is no IC candidate or one-target timing result in this artifact.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-432-shift-descent-20261025/sage_runtime.json
./sage -python experiments/hecke-432-shift-descent-20261025/check_sage.py
python3 experiments/hecke-432-shift-descent-20261025/verify_global.py
```
