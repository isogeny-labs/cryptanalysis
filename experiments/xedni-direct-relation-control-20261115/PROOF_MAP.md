# Proof map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| The fixed two-point scalar relation is equivalent to `3w=t₁+2t₂` | `XedniDirectRelation.relation_iff_linear` | Any commutative ring, with `w,t₁,t₂` in that ring. |
| The relation recovers `w=(t₁+2t₂)/3` | `XedniDirectRelation.relation_iff_recovery` | Any field with `3≠0`. |
| The public group relation equals `(3w−t₁−2t₂)G=0` | `XedniDirectRelation.group_relation_iff` | Any additive commutative group, integer scalar coordinates, and the fixed coefficient vector `(1,2)`. |
| An additive reduction map carries the lift relation to the group relation | `XedniDirectRelation.relation_reduces` | Any additive commutative lift and base groups and an additive homomorphism between them. Identifying good reduction of an elliptic curve with such a map remains an explicit mathematical hypothesis here. |
| A finite scalar relation is equivalent to `Cw=S` | `XedniDirectRelation.finite_relation_iff` | Any finite index set and commutative ring; `C=Σcᵢ`, `S=Σcᵢtᵢ`. |
| A finite relation with `C≠0` recovers `w=S/C` | `XedniDirectRelation.finite_relation_recovers` | Any field, finite index set, and nonzero coefficient sum. |
| A finite relation with `C=0` has equation `S=0` | `XedniDirectRelation.finite_zero_sum_relation` | Any commutative ring, finite index set, and zero coefficient sum. |
| The finite public-group relation is `(Cw−S)G` | `XedniDirectRelation.finite_group_identity` | Any additive commutative group, finite index set, integer coefficients and offsets, and `Q=wG`. |

The query-index and coefficient-probe comparisons are exact replay outputs.
The Lean module uses the same pinned Lean and Mathlib revisions as the CRT
witness modules. Build command, output, and axiom audit are retained in
`formal/CHECK.md` and `formal/build-output.txt`.
