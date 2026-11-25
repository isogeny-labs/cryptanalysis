# Shared-denominator signed-basis collector comparison

Freeze before timing. The control is the combined M31 full Rust collector:
one-multiply hash, sign-packed 6 MiB index, and prevalidated 1,000-point
`batch_add` on each relation trial. The candidate changes only the collector
batch arithmetic. Its input is the same adjacent `(-F, F)` pairs. It computes
one affine denominator inverse per pair, then computes both ordinates from
their distinct numerators. Equal-x and infinity exceptions use individual
checked-formula arithmetic. Both arms retain the same direct pair table,
walker, relation checking, elimination and answer verification.

The candidate must match the control on complete index maps, generated basis
digest, signed table-entry count, trial count, relation count and verified
scalar in every matched pair. A crate test compares both 1,000-point outputs
across ordinary, equal-x, inverse and infinity cases. An algebraic Lean proof
of the shared-denominator chord identity is required before promoting an
algorithmic claim; wall-clock arithmetic is not a proof substitute.

Use both frozen public M31 auxiliary and plain fixtures. Run seeds 0, 1 and 2
eight times each, with balanced arm order and fresh processes. Charge basis
generation and comparison, input writing, table build, relation collection,
elimination, answer verification and process exit to wall and parent-plus-child
CPU. Compilation, fixture JSON loading and complete map audit are outside the
clock. OS caches are not flushed. Keep all failed and completed arms. If the
first panel preserves exact workload identity and favors the candidate,
repeat with a fresh shuffle seed. Use 112535 for the first panel and 112536
for the repeat. A mismatch is a failure regardless of speed.
