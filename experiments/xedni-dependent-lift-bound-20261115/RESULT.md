# Checked dependent-lift sample bound for xedni

The new Lean theorem bounds the number of sampled offset tuples that admit a
nontrivial relation among lifts chosen *after* seeing those offsets. For a
fixed prime subgroup order `q`, public coefficients `s`, target scalar `w`,
and fixed finite integer candidate set `S`, it proves

`|{t : some nontrivial relation holds among lifts(t)}| · |ZMod q|
 ≤ |S| · |Fin r → ZMod q|`.

Thus a uniform independent draw of the full `t` tuple has event probability
at most `|S|/q`. The lift function may depend arbitrarily on `t`; the proof
does not assume a fixed rational curve or independent lifts. Its structural
step carries every lifted relation through the additive reduction map to a
relation on the sampled reduced tuple. The existing bijection and finite
candidate union bound then control that event.

The new `boundedCandidates B` construction supplies the complete nonzero
integer box, with membership equivalent to nontriviality and coefficient
bound `B`. Lean proves its cardinality is `(2B+1)^r−1` and derives the
explicit inequality

`|{t : some nontrivial relation holds among lifts(t)}| · q
 ≤ ((2B+1)^r−1) · q^r`.

The resulting probability bound is `((2B+1)^r−1)/q`; it is informative when
the box size is small relative to `q`. The fixed-candidate cover conditions
are discharged by the construction in this corollary.

The height-pigeonhole bridge now supplies the short witness from a finite
image certificate. For each sampled tuple `t`, give a finite set `values(t)`
containing all sums with coefficients in `[-L,L]^r`. If dependence implies
`|values(t)| < (2L+1)^r`, the checked pigeonhole theorem produces a relation
bounded by `2L`. `dependent_lift_height_count` applies the sample bound with
that witness. This connects the two independently checked proof modules.

The new impossibility theorem is more direct. Suppose the same strict
height-cover inequality holds for **every** sampled tuple and `2L<q`. Then
every tuple has a short relation, while the sampling bound permits at most
`((4L+1)^r−1)/q` of the tuples. When `(4L+1)^r−1<q`, Lean derives `False`.
The rank-and-torsion corollary replaces the abstract value sets by a
rank-`d<r` lattice representation: at most `T(2K+1)^d` sums, with
`K≤cL` and `T(2c+1)^d<L`. It proves the same contradiction under the
explicit coordinate representation premise. This is a quantified obstruction
to a **uniform** low-rank, bounded-height lift rule; applying it to a
particular rational curve construction requires its height-to-coordinate
estimate and good-reduction map.

## Exact hypotheses and proof

The theorem `XedniObstruction.dependent_lift_sample_count` takes an additive
map `red : H →+ ZMod q`, a lift-selection function
`lifts : (Fin r → ZMod q) → Fin r → H`, and compatibility
`red(lifts(t,i)) = sᵢw−tᵢ`. It assumes a **uniform short-witness bound**
`B<q`: whenever `lifts(t)` is dependent, at least one nontrivial integer
relation has each coefficient's absolute value at most `B`. The fixed finite
set `S` must cover every nontrivial vector in that box, and every member of
`S` must itself be nontrivial and bounded. These cover conditions are
independent of the sampled `t`. The assumption concerns one short witness,
not every multiple of a relation.

If `t` has a lifted relation, the short-witness hypothesis supplies a
bounded relation whose coefficient vector lies in `S`. Reduction transports
that relation to `ZMod q`; compatibility
turns it into a zero-fiber event for `sᵢw−tᵢ`. Consequently, the set of
dependent-lift samples is contained in the preimage of the fixed union of
zero fibers. The previously checked `xedni_sample_event_card` and
`sampled_integer_candidate_union_count` theorems bound that preimage by
`|S|/q`. The new Lean module checks this inclusion and final cardinality
inequality without assuming the conclusion.

| Result | Lean declaration | Verification and scope |
| --- | --- | --- |
| A sampled dependent lift lies in the fixed reduced relation event, giving the stated count bound | `XedniObstruction.dependent_lift_sample_count` | Pinned `lake build XedniDependentLift` passed; `#print axioms` reports `propext`, `Classical.choice`, `Quot.sound`. Exact hypotheses are in the theorem signature above. |
| The complete nonzero coefficient box has `(2B+1)^r−1` members | `XedniObstruction.mem_boundedCandidates`, `XedniObstruction.boundedCandidates_card` | Pinned build and axiom audit passed. |
| Dependent-lift sample bound with the box constructed and counted | `XedniObstruction.dependent_lift_box_count`, `XedniObstruction.dependent_lift_explicit_count` | Pinned build and axiom audit passed; retains the uniform short-witness and reduction-map hypotheses. |
| Finite height-image count supplies a short witness for each dependent lift tuple | `XedniObstruction.dependent_lift_height_count` | Imports the pinned `XedniHeightPigeonhole.bounded_witness_of_card_lt_on_dependence`; requires `2L<q`, a finite image certificate, and the count when dependence holds. |
| Uniform finite height cover of size below the coefficient box is incompatible with a sub-`q` witness box | `XedniObstruction.no_uniform_small_height_cover` | Checked proof of `False` under compatibility, all-sample cover and count, `2L<q`, and `(4L+1)^r−1<q`. |
| Rank-gap and bounded-coordinate version of the uniform obstruction | `XedniObstruction.no_uniform_rank_gap_cover` | Checked proof of `False` under `d<r`, `K≤cL`, `T(2c+1)^d<L`, and exact representation of every short sum, in addition to the preceding reduction and box bounds. |
| Reduction of any integer lift relation | `XedniObstruction.relation_reduces` in the pinned base module | Rebuilt from the identified mainline source in this package. |
| Fixed finite candidate sample bound | `XedniObstruction.sampled_integer_candidate_union_count` in the pinned base module | Rebuilt from the identified mainline source in this package. |
| Arithmetic short-relation witness bound for a specific rational lift family | Open bridge | Requires the chosen curve family and height/discriminant conditions to show every dependent selected lift has at least one relation bounded by the same `B<q`. The theorem exposes that obligation as `short_relation_witness`. |
| Good-reduction realization of `red` for a specific lift family | Open bridge | Requires a specified elliptic model, good reduction, and proof that its point reduction is the additive map used here. |

`SOURCE.json` identifies the exact mainline base and height-pigeonhole modules
copied into this versioned formalization addition. The pinned Lean toolchain and Mathlib
manifest, build output, verifier, and file seal are retained. The current
module introduces no custom axiom, `sorry`, `admit`, or native proof step.
The older base module's universal relation-bound declaration is rebuilt for
source fidelity but is not used by this new theorem.
