# Fresh group-oracle output coupling proof map

Lean toolchain: v4.35.0-rc4. Mathlib revision:
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Appending a fresh point preserves injectivity | fresh_snoc_injective | Prior trace injective; new point outside its range |
| Old and new labels can be paired together | fresh_oracle_step_coupling | Two injective traces; both new points fresh |
| Every event on the extended visible tuple has equal encoding counts | fresh_oracle_step_event_count | Finite group and label sets; both extensions fresh |
| The same statement for an addition oracle call | fresh_add_oracle_step | Same prior indices chosen in both traces; both sums fresh |

The module imports the exact RandomLabelCoupling source from the parent
experiment through a relative symlink. Its SHA-256 is pinned in the seal.
The fresh-step proof uses Fin.snoc_injective_iff, then applies the parent's
injective-trace coupling to the extended trace. The event-count theorem
allows an event to constrain the complete old-plus-new label tuple, so it
also covers counts conditioned on any specified prior visible labels.

The theorem handles a single fresh result. A complete adaptive generic
group proof still needs induction over an arbitrary operation schedule,
case analysis at the first collision, and the work-to-collision accounting.
It does not model concrete curve coordinates.

lake build OracleStep completed 3,139 jobs including the parent module.
The four new #print axioms reports use only propext, Classical.choice, and
Quot.sound where applicable. No placeholder or custom research axiom occurs.
lean4checker --fresh was unavailable on this host.
