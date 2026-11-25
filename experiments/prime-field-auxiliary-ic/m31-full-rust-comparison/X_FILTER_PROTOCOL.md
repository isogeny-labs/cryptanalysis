# X-filtered signed-basis collector comparison

Freeze before timing. Both arms use the sign-packed 6 MiB index,
one-multiply slot hash, paired shared-x batch denominators, direct pair rows,
the same deterministic relation walk and modular elimination. The control
materializes both affine ordinates for every factor-base pair. The candidate
first computes each chord x-coordinate, asks the exact sign-packed index
whether that x exists, and materializes y only when it does. A missing x
proves both point signs absent from the table. Exceptional additions follow
the ordinary full-add path, then apply the same exact x test.

The candidate must preserve the complete sorted index map, basis digest,
signed entry count, trial count, relation count and generator-verified scalar
within every matched pair. A library unit test must compare every filtered
output with a full checked batch under an independently specified x predicate.
The Lean semantic obligation is that dropping a point whose x is absent from
an exact index preserves the first successful table lookup; it is separate
from empirical timing.

Run both frozen public M31 auxiliary and plain fixtures, seeds 0, 1 and 2,
eight balanced-order rounds per seed, with one fresh process per arm. Charge
basis regeneration, fixture comparison, input writing, table construction,
relation collection, elimination, answer verification and process exit to
wall and parent-plus-child CPU. Compilation, frozen JSON loading and complete
index-map audit precede the timer. OS caches are not flushed. Use shuffle
seed 112537 first. If workload identity holds and both bases favor the
candidate, repeat with seed 112538 and retain all arms. A mismatch fails the
candidate regardless of timing; a small or unstable gain is not a broader
algorithmic performance claim.
