# Random-label coupling proof map

Lean toolchain: v4.35.0-rc4. Mathlib revision:
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Hypotheses |
| --- | --- | --- |
| Domain permutation acts bijectively on encodings | relabelEquiv | Any types G,L and permutation of G |
| Injective traces have paired encodings with identical label tuples | injective_trace_label_coupling | Both traces injective |
| Every tuple event has equal encoding count | label_event_card_eq | Finite G,L; arbitrary event |
| Affine traces at two target scalars | affine_trace_label_event_card_eq | Finite field; both evaluated traces injective |

The coupling uses Mathlib's Equiv.Perm.exists_extending_pair to map the two
finite traces, then precomposes every bijective encoding with the inverse
permutation. This gives an equivalence on the complete encoding space.
The subtype equivalence proves event-count equality.

The theorem analyzes fixed collision-free traces. An adaptive generic-group
algorithm still needs a stepwise coupling that preserves operation responses
until collision. Concrete curve coordinates are not random bijective labels.

lake build RandomLabelCoupling completed 3,138 jobs. All four #print axioms
reports list only standard Lean foundations: propext, Classical.choice, and
Quot.sound where used. The source has no placeholders or research axioms.
lean4checker --fresh was unavailable on this host.
