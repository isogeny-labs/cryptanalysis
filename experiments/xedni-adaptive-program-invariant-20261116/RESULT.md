# Adaptive group programs retain affine representations

The checked `dlp_program_invariant` theorem shows that every point in the
final trace of **any finite label-adaptive addition/subtraction program**
started from public `G` and `Q=w • G` equals evaluation of its corresponding
affine form in `w`, multiplied by `G`. Each command may inspect all currently
visible abstract labels, including equality patterns created by prior
collisions. The program and trace lengths are tracked in Lean's types.
This supplies the arbitrary-length representation invariant needed to apply
the one-step actual-hit bound from PR #1636 along an adaptive execution.

The frozen Z/7 control enumerated six target scalars and all 7! bijective
encodings per scalar. Its three label-dependent commands processed **30,240**
complete cases and **90,720** group operations. An independent audit replayed
each saved encoding, command, group point, affine form, and first-collision
step. It found **zero** representation mismatches. The first collision was
at step 1 in 5,040 cases, step 2 in 5,040, step 3 in 15,840; 4,320 cases
remained collision-free through all three steps. Both addition and
subtraction occurred, 53,280 and 37,440 times respectively. Deterministic
gzip JSONL shards retain every case.

The next proof step is a probability/counting recurrence over the transcript
tree that charges the first informative collision and handles symbolically
identical forms. The present theorem establishes trace correctness for
arbitrary finite add/sub programs; it does not by itself bound the chance of
finding a target-dependent relation. Coordinate-guided rational lifts need
their own observation model.

Lean v4.35.0-rc4 and Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9 are pinned. `lake build
AdaptiveProgramInvariant` passed 3,142 jobs, and all twelve new axiom audits
list only standard Lean foundations. `SEAL.sha256` binds the protocol,
source, complete replay shards, independent audit, build receipt, and proof
map.
