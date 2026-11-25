# Validated batch collector comparison

Frozen before timing. Compare the existing checked `Curve::batch_add` call
against `Curve::batch_add_assume_valid` in the full Rust flat collector. Both
arms use the one-multiply hash, the same deterministic walk, 500-point
auxiliary or plain public M31 basis, three-point relation verification,
modular elimination, and final generator-multiplication answer check.

The precondition for the candidate is explicit: the fixed factor-base points
are checked with `Curve::point` and negated with `Curve::negate`; the running
point is initially constructed by checked curve operations and updated by
`Curve::add`. Both input slices have the same length. The control repeats
membership checks inside every batch call. The candidate omits those repeated
checks and uses the identical batch-add arithmetic.

Run `python3 experiments/prime-field-auxiliary-ic/m31-full-rust-comparison/validated_replay.py`
from the repository root, saving stdout as CSV. Set `M31_REPLAY_TMPDIR` to a
volume with enough free space when the default temporary directory is full.
The runner builds both
variants from one source tree and runs 24 balanced-order matched blocks for
each basis, using seeds 0, 1, 2 eight times each. Each arm is a fresh process.
Charge basis regeneration, fixture comparison, file writing, collection,
elimination, and answer check to wall and parent-plus-child CPU. Compilation,
frozen fixture loading, and OS cache state are outside the clock.

For every pair require equal basis SHA-256, scalar, trial count, relation
count, and table entry count. Report median paired control/candidate wall and
CPU ratios, win counts, and any failures. This is a local producer run; it
does not certify broader targets or a general speedup.
