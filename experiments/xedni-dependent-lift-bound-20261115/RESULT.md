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
| Reduction of any integer lift relation | `XedniObstruction.relation_reduces` in the pinned base module | Rebuilt from the identified mainline source in this package. |
| Fixed finite candidate sample bound | `XedniObstruction.sampled_integer_candidate_union_count` in the pinned base module | Rebuilt from the identified mainline source in this package. |
| Arithmetic short-relation witness bound for a specific rational lift family | Open bridge | Requires the chosen curve family and height/discriminant conditions to show every dependent selected lift has at least one relation bounded by the same `B<q`. The theorem exposes that obligation as `short_relation_witness`. |
| Good-reduction realization of `red` for a specific lift family | Open bridge | Requires a specified elliptic model, good reduction, and proof that its point reduction is the additive map used here. |

`SOURCE.json` identifies the exact mainline base module copied into this
versioned formalization addition. The pinned Lean toolchain and Mathlib
manifest, build output, verifier, and file seal are retained. The current
module introduces no custom axiom, `sorry`, `admit`, or native proof step.
The older base module's universal relation-bound declaration is rebuilt for
source fidelity but is not used by this new theorem.
