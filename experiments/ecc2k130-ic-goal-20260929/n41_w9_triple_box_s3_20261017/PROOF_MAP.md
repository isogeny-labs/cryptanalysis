# Three-code S3 box: proof map

The [Lean module](TripleBox.lean) builds under pinned Lean 4.34.1 with
`lean TripleBox.lean`. Its [axiom output](lean.stdout) reports only
`propext`, `Classical.choice`, and `Quot.sound` for the algebraic
theorems. The closed N131 payload inequality uses no axioms. The
module contains no `sorry`, `admit`, `sorryAx`, custom axiom, or native
evaluation proof. `lean4checker --fresh` was unavailable here.

| Result | Lean declaration | Scope and bridge |
| --- | --- | --- |
| S3 is quadratic in its third reciprocal coordinate | `s3_as_quadratic` | Exact identity in any commutative ring. Checked. Curve point addition implies S3 only on the nonexceptional chart; every N41 instance in the full index is checked independently by group addition. |
| Two roots exhaust a nondegenerate quadratic | `quadratic_root_pair`, `char_two_root_pair` | For `A≠0`, any two roots are equal or paired by `−x−B/A`; in characteristic two they are equal or differ by `B/A`. Checked. The producer verifies its half-trace root for every tested equation, and the independent group audit checks the complete concrete root sets. The general finite-field trace-zero existence theorem is still an open Lean bridge. |
| N131 raw-coordinate payload exceeds 4 GiB | `n131_one_coordinate_payload`, `conditional_payload_over_four_gib` | Checked exact integer inequality and its conditional monotonic form. The orbit-to-code incidence bound, rank-28 product decoding, and source-valid sample count are written and checked by the frozen external records; their concrete elliptic-curve formalization remains open. |

For an actual nonexceptional point triple, take `z=1/x(P₁+P₂)`.
The group-to-S3 formula puts `z` in `L(c₁,c₂)`. The equality
`P₁+P₂=T−P₃` puts the same `z` in `R_T(c₃)`. Since each S3 equation is
a nondegenerate quadratic on the checked chart, the half-trace root
pair enumerated by the producer contains this `z`. Thus a witness
cannot be rejected by the intersection test. The independent
[full group audit](full_audit_result.json) constructs every stored
left and right coordinate directly from curve points and reproduces
the complete table digests and both exact witnesses.

The transfer argument uses the already checked 16,677-code W29 sample,
the exact 28-bit product-map rank, and orbit size at most 131. Each
source leaf participates in one canonical fixed-seed code, so a folded
orbit is incident to at most 131 codes. Excluding four fixed columns
and then those four plus a selected first code's two columns yields the
`4·131` and `6·131` terms. The pair-output identity
`p=Cz+H/z`, with injective canonical product map, makes a reciprocal
coordinate identify at most one code in a slot. For each of the two
first-code roots, only `b=a` and `b=1/a` are exceptional, so four
more right codes cover these cases. The resulting nonexceptional pair
count and 17-byte coordinate width give the Lean-checked payload
inequality. This proof concerns a literal full-coordinate record per
pair; it leaves compressed family representations open. The
[independent integer audit](transfer_audit_result.json) also tests the
incidence bound against the full N41 source, where the maximum observed
code incidence per folded column is two.

Formalization of the concrete source-orbit incidence and elliptic-curve
group-to-S3 bridges is partial. Their written arguments and exact
frozen arithmetic/group checks remain here; the full concrete Lean
theorem is open.
