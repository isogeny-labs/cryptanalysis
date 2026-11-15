# Proof map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| The fixed two-point scalar relation is equivalent to `3w=t₁+2t₂` | `XedniDirectRelation.relation_iff_linear` | Any commutative ring, with `w,t₁,t₂` in that ring. |
| The relation recovers `w=(t₁+2t₂)/3` | `XedniDirectRelation.relation_iff_recovery` | Any field with `3≠0`. |
| The public group relation equals `(3w−t₁−2t₂)G=0` | `XedniDirectRelation.group_relation_iff` | Any additive commutative group, integer scalar coordinates, and the fixed coefficient vector `(1,2)`. |
| An additive reduction map carries the lift relation to the group relation | `XedniDirectRelation.relation_reduces` | Any additive commutative lift and base groups and an additive homomorphism between them. Identifying good reduction of an elliptic curve with such a map remains an explicit mathematical hypothesis here. |

The query-index and coefficient-probe comparisons are exact replay outputs.
The Lean module uses the same pinned Lean and Mathlib revisions as the CRT
witness modules. Build command, output, and axiom audit are retained in
`formal/CHECK.md` and `formal/build-output.txt`.
