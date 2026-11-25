# Direct combined M31 collector comparison

Frozen before measurement. Compare the corrected original Rust full-collector
control with the combined candidate on the same public M31 target and basis.
The control uses the 1,048,576-slot flat point-key table, SplitMix-style slot
hash, and checked `Curve::batch_add` for every relation trial. The candidate
uses the 524,288-slot sign-packed table, one-multiply slot hash, and the
documented prevalidated batch path. Both use direct pair rows, the same
deterministic walk, checked three-point relations, modular elimination, and
generator-multiplication answer verification. Neither uses reflected rows.

For each frozen auxiliary and plain fixture, run seeds 0, 1 and 2 eight times
each in 24 balanced-order blocks. Each arm regenerates its 500-point basis,
checks it against the published fixture, writes the Rust input, and launches
a fresh process. Charge this work, table construction, relation collection,
elimination, answer verification and process exit to wall and parent-plus-child
CPU. Compilation, frozen fixture JSON loading and the complete index-map audit
are outside the charged window. OS caches remain under host control.

Before timing, dump each index's complete sorted `(point key, first payload)`
map and require byte equality for both bases. Within every timed pair require
equal basis digest, signed table-entry count, trial count, relation count and
verified scalar. Retain all arms and failures. Use shuffle seed 112533 for the
first panel. If it passes identity and favors the candidate, repeat with seed
112534 and report panels separately. A mismatch fails the candidate regardless
of timing. This comparison measures the combined local gain directly; it does
not establish wider-target performance or an asymptotic improvement.
