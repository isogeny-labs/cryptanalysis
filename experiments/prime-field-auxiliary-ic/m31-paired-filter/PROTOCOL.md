# Paired x-filter integration in indexed three-term decomposition

The current `PairIndex::probe(m=3)` uses generic batch addition for
`target-F_i` and `target+F_i`, then probes the exact pair table. The field
module already provides `batch_add_paired_x_filtered_assume_valid`, which
shares the denominator for each signed pair and can reject a bitmap miss
before materializing y. Previous `m31-fused-native-collector` work fused a
similar scan in a separate collector and observed about 12–15% charged
improvement; this integration is an engineering test, not a new algebraic
method or novel complexity claim.

Implement only the m=3 paired path when chunks contain complete consecutive
signed pairs; retain generic addition for odd chunks and m=4. The bitmap
predicate may only reject an x absent from the exact pair table. A `None`
output from the filtered adder must be distinguished from a genuine identity
candidate before lookup. Keep first-witness order, exact certificate replay,
all input caps, and every m=2 result unchanged.

Correctness: existing field batch tests plus targeted PairIndex differential
tests on all points of a small curve, including exceptional equal-x and
identity candidates, odd chunks and bitmap/no-bitmap configurations.
Compile the baseline from commit `7e46f47a31c524e9cafb2a2b85fa2ac7857bebd0` and the
candidate from the eventual implementation commit with isolated target dirs.
The development pilot uses the frozen public M31 target index 0, seed 0,
interval B384, m=3, indexed, lanes 64, chunk 64, four million query and
five-second online caps. Compare fresh-process cold external wall and CPU,
setup/index/online, query and certificate identities. If the candidate is
correct and at least 1.5x faster in both external wall and CPU on the pilot,
freeze a five-target x three-seed validation before running it. That
validation must include the current m=2 B384 and matched rho as complete
cold controls. If the pilot misses the gate, retain its negative result and
do not promote the implementation.
