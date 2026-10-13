# Proof map for sparse product-space superset filtering

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Filtering every root returned from a superset gives exactly the usable-product existential predicate | `SupersetFilter.filtered_hit_iff_usable_hit` | Arbitrary product type, explicit containment of the usable list in the superset list, and an exact usable-source predicate. Checked with Lean 4.34.1 and bundled Std; `#print axioms` reports no axioms. |
| Fixed-seed product image is an `F₂`-linear space | Open field bridge | For `s≠0`, `a↦a(a+s)=a²+sa` is additive and has kernel `{0,s}`. On the full 8-bit source subspace, the quotient has dimension seven and 128 distinct products. The checked Sage job enumerated all 128 and confirmed the valid 32 are contained. The analogous N131 W18 source has 17-dimensional full product image; a concrete Lean field/subspace proof remains open. |
| The vanishing polynomial of that full finite linear space is linearized | Open polynomial bridge | The N41 product over the 128 enumerated roots has degree 128 and exactly the nonzero exponents `1,2,4,8,16,32,64,128`. General additive-polynomial theory supplies the proof; Sage checked the complete finite instance. |
| A positive-degree GCD with the full-space polynomial yields only full-space products, and postfiltering removes excluded products | Open polynomial-GCD bridge | Requires exact factorization/root enumeration of the GCD in the concrete field. The query checked all returned roots against the 32 usable products. An excluded zero-product control gave an unfiltered degree-one GCD but zero usable-source hits. |
| Source-filtered algebraic decisions match the curve source | Open curve-law bridge | The prior four-family group audit checked 1,048,576 signed combinations on the same public point. The two overlapping families agree. An independent pair-equation auditor checked the positive and excluded product outputs directly without calling the 266-term resultant or polynomial GCD. |

Readable proof: `a(a+s)` is additive in characteristic two because
`(a+b)²+s(a+b)=(a²+sa)+(b²+sb)`. Its kernel is `a=0` or `a=s` in a
field, so an 8-dimensional source gives a 7-dimensional product image.
The product over that image is a linearized polynomial. If a specialized
four-atom polynomial shares a root with this full-space polynomial, every
recovered root belongs to the full image. The last source predicate
accepts a recovered root exactly when its mask pair is usable. Since the
usable set is contained in the full image, this test is equivalent to
using the product polynomial over usable roots alone. The Lean theorem
proves this last set-level equivalence under its explicit hypotheses.

Build: `lean SupersetFilter.lean` from this directory with `lean-toolchain`.
`lean_version.txt` and `lean_check.log` retain the compiler and axiom
audit. `lean4checker` was unavailable. The concrete field, GCD, and
curve-law bridges above remain partial formalization obligations.
