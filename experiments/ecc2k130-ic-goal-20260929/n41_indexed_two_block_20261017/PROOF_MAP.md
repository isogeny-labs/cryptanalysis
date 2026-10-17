# Indexed two-block target join proof map

For block-root lists `L` and `R` that contain every field root of
their respective two-slot block polynomials, let

`I_t(u) = {v ∈ F : (1+(ut)²)v² + (ut)v + (u²+t²)=0}`.

In a characteristic-two field,

`U(u,v,t) = (1+(uv)²)t² + uvt + (u+v)²`

equals the polynomial defining `I_t(u)`: expanding both squares
leaves the same terms because the integer cross term `2uv`
vanishes. Thus the indexed join returns exactly the pairs
`(u,v) ∈ L×R` satisfying `U=0`, provided the quadratic solver
returns all field roots (including the identically zero case),
the index retains duplicates, and column-disjointness is applied
identically to both routes. Every group relation in this chart
therefore survives the indexed coordinate filter. A coordinate
hit still requires signed group replay, which the audit performs.

| Result | Lean declaration | Exact scope and status |
| --- | --- | --- |
| Universal polynomial identity | `TargetQuadratic.target_inverse_identity` | Integer polynomial equality `forward = inverseForm + 2uv`; built |
| Characteristic-two specialization | `TargetQuadratic.target_inverse_mod_two` | Equality of zero conditions after coefficient reduction modulo two, for arbitrary integer inputs; built |
| Parity implication | `TargetQuadratic.target_inverse_parity` | Forward even implies inverse even for all integer inputs; built |
| Complete finite-field root enumeration and index equivalence | No declaration yet | Exhaustive N41 field audit compares all 739,200 root pairs to indexed hits; full formal bridge remains open |
| Curve/group relation interpretation | No declaration yet | Independent Sage audit checks 152 block families, 2,432 signed sums, and cofactor-four transport of the positive hit; full curve theorem remains open |

The module [TargetQuadratic.lean](TargetQuadratic.lean) builds with
`lean TargetQuadratic.lean` under pinned Lean 4.34.1. The retained
[`#print axioms` transcript](lean.stdout) lists only `propext`,
`Classical.choice`, and `Quot.sound` for each theorem; the module
contains no `sorry`, `admit`, `sorryAx`, custom claim axiom, or
native-evaluation bypass. `lean4checker --fresh` was unavailable.
The remaining formal dependencies are an actual binary-field type,
complete polynomial-root specification, and the bridge from block
roots and the upper Semaev equation to signed curve sums.
