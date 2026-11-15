# Sampled bounded-witness obstruction for xedni lifting

The checked Lean theorem `XedniObstruction.dependent_lift_sample_count` bounds the uniform-sample incidence of dependent lifts. Suppose each sampled lift tuple that has an integer relation also has **some** nontrivial relation with coefficients of magnitude at most `B < q`, where `q` is the prime subgroup order. Let `S` be a fixed finite list containing every such bounded relation. For fixed public coefficients `s` and target scalar `w`, the theorem proves

`|{t : the compatible lift at t is dependent}| · q ≤ |S| · q^r`.

Thus, under the full uniform law for `t ∈ (F_q)^r`, the incidence is at most `|S|/q`. The bounded witness may differ from the relation that first established dependence. This is the noncircular hypothesis needed to connect the deterministic reduction obstruction to the finite-field count.

## Mathematical argument and hypotheses

For each input `t`, the reduced coordinates are `x_i = s_i w − t_i`, and the chosen lifted points `L_i(t)` satisfy `red(L_i(t)) = x_i`. The proof assumes a uniform `B` over this lift family and a fixed candidate list `S` that covers all nontrivial integer vectors whose coordinates have magnitude at most `B`. If a tuple has a relation, the bounded-witness hypothesis supplies `a ∈ S` with `Σ a_i L_i(t) = 0`. Applying the reduction homomorphism gives `Σ a_i x_i = 0` in `F_q`.

Since `B < q`, a nonzero integer coordinate of `a` stays nonzero modulo `q`. The corresponding dot-product map on `(F_q)^r` is surjective, so its zero fiber has exactly `q^(r−1)` elements. A union bound over fixed `S` gives at most `|S| q^(r−1)` reduced tuples. The map `t ↦ (s_i w − t_i)_i` is involutive, so its preimage has the same cardinality. The Lean proof carries these steps through finite-set inclusion and cardinal inequalities.

The result applies to a fixed `s,w`, full-support uniform sampling, compatible lifts, and a supplied bounded-witness principle. The height/discriminant and Lang hypotheses used by Jacobson, Koblitz, Silverman, Stein, and Teske to obtain such witnesses for their lift family remain a separate proof obligation; so does the actual curve-selection distribution. See [*Analysis of the Xedni Calculus Attack*](https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf), §§3–4.

## Proof map and verification

| Result | Lean declaration | Exact role |
| --- | --- | --- |
| Lift relations reduce | `relation_reduces` | Additive reduction homomorphism |
| Noncircular lift obstruction | `no_dependent_lift`, `all_compatible_lifts_blocked` | Dependence yields a bounded witness |
| Integer coefficient survives reduction | `intCast_ne_zero_of_natAbs_lt`, `bounded_intVector_cast_nonzero` | `B < q` |
| Relation event count | `dotHom_surjective`, `zero_relation_fiber_count`, `zeroFiber_count`, `bounded_relation_union_count`, `integer_candidate_union_count` | Fixed list and uniform finite-field tuples |
| Sampling law preserves event size | `xedniSampleMap_involutive`, `xedniSampleMap_bijective`, `xedni_sample_event_card`, `sampled_integer_candidate_union_count` | Fixed `s,w` |
| Dependent-lift sample bound | `dependent_lift_sample_count` | Compatible lifts, bounded witness, complete fixed list, `B < q` |

The new module is a versioned extension of the corrected original `XedniObstruction.lean` at main commit `c021359ce7b5f4f5b867ffc50b4873769bde6f9a` (2026-11-15). The earlier merged [bounded-witness correction](../xedni-bounded-witness-20261030/RESULT.md) established that a universal bound on every relation is circular; this extension uses the existential witness formulation. The source, pinned Lean and Mathlib revisions, complete build output, and exact hashes are recorded in `formal/`. `verify.py` checks the source/build seals and every `#print axioms` result. `lean4checker --fresh` was unavailable on this host.

The next mathematical step is to formalize the height-theoretic existence of a bounded witness for the paper's lift family, preserving its discriminant, canonical-height, rank, and exceptional-case hypotheses. A separate sampling argument must model the paper's curve-selection procedure before this count can be applied to its complete algorithm.
