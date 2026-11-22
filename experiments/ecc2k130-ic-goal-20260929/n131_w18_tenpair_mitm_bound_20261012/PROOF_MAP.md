# Fixed-list join coverage proof map

`JoinCoverage.orbit_join_coverage_bound` in [JoinCoverage.lean](JoinCoverage.lean)
is the central checked theorem. It quantifies over arbitrary left and right
state lists, a list of tested automorphism labels, raw-point addition, a
cofactor map into public targets, a Frobenius action and its inverse, and
an enumerated duplicate-free list of successful public targets. Its
explicit `hundo` hypothesis states that the inverse action undoes each
tested Frobenius action. Its explicit `hhit` hypothesis supplies a genuine
join witness for every counted target. The conclusion bounds distinct
successful public targets by the product of the three list lengths.

`outcomes_length` proves the product count for all labeled triples, and
`distinct_successes_bound` proves that collisions, duplicate states, or
failed column checks can only reduce target coverage. The cofactor map
turns each raw group sum into one public point; the theorem consequently
does not multiply coverage by the number of raw preimages of that public
point. For a uniformly selected target from a subgroup of order `r`, the
counting theorem gives probability at most `min(1, JLR/r)` when both lists
and their sampling randomness are independent of that target.

`lean-toolchain` pins Lean 4.34.1 and its bundled `Std`. The saved
`lean_check.txt` is the output of `lean JoinCoverage.lean`, including the
`#print axioms` audit. The theorem uses standard `propext`,
`Classical.choice`, and `Quot.sound`; it contains no `sorry`, `admit`,
custom research axiom, or native-evaluation step. `lean4checker --fresh`
was unavailable on this host.

The concrete bridge from `hundo` to Frobenius on the exact binary curve,
and from the abstract cofactor map to `[4]` on its point group, is not
formalized here. Those exact field, curve, and subgroup facts are inherited
from the source experiment's checked Sage replay. The uniform-target
probability calculation is exact integer division in `projection.py` and
independently replayed by `verify.py`; it is conditional on lists fixed
independently of the target. A target-guided list generator changes that
input law and lies outside this theorem's empirical interpretation.
