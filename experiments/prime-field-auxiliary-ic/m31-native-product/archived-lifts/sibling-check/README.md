# Full-fiber validation on the M31 auxiliary chain

For a shifted pair u and v the checked identity uv=B with nonzero B
ensures neither point is a pole. Both images under u ↦ u+A+B/u are
u+A+v. In the generated coset order the first half pairs with the second
half; the code tests the identity on each pair, then repeats on its parents.
It checks the terminal singleton and keeps the original distinctness,
generator, curve, homomorphism and walk-closure checks. A complete depth-s
fiber uses 2^s−1 checked pairs. Validating every leaf independently had
used s·2^s inversions just for replaying the maps. At depth five the new
check uses 31 pair products and no inversions in this validation step.

The full M31 branch runs through snapshot/prepare.py's chain entry point.
Partial enumerations use the direct validator. Siblings.lean proves each
accepted merge reproduces both individual rational-map images and that
recursive certification implies successful pointwise evaluation at the
terminal coordinate.

The four-arm panel used the hash-pinned previous chain implementation and
the current working-tree implementation, each combined with either Python
or native NEON lifting. All 24 arm orders occur once. Each observation
rebuilds the entire basis 24 times. The raw panel includes wall and process
CPU clocks. Each arm's final roots, complete auxiliary metadata and all
canonical affine points were checked. Additional replays compared full and
limited M31 chains at depths 1, 2, 5, 8 and 10, and one M61 control. Each
single-coordinate mutation, a truncated list and a wrong terminal value
were rejected on the frozen depth-five fixture.

On the shared Apple M4 Pro, the median paired full-basis wall ratios were
1.387 for pairing alone with the Python lift, 1.470 for pairing alone with
the native lift, and 1.819 for the combined path over the original Python
basis preparation. The last comparison won all 24 blocks. Imports and
library loading precede timing. These timings cover public basis setup.
To replay, build neon.so as in the parent README, then run compare.py
with its absolute path. Replay Siblings.lean in the Lean 4.34.1 mathlib
environment.
