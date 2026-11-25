# Sign-packed factor-base hash comparison

Freeze before timing. Compare the existing flat point-key index with a
sign-packed index in the same full Rust M31 collector. The candidate groups
the two point signs under one x-coordinate slot, with distinct first-inserted
payloads selected by y parity. Its 524,288 slots each contain x and two
payload words (6 MiB). The control has 1,048,576 slots of key and payload
(8 MiB). Both use the one-multiply hash, direct pair rows, prevalidated batch
collection, the same deterministic walk, relation checks and elimination.

For a finite point over the odd M31 field, its x and y parity determine its
full affine coordinate. The index must retain the first payload separately
for both signs, including collisions between different factor-base pairs.
The exact-map audit was added after the first two timing panels. The current
runner regenerates each basis, builds both indexes, dumps each complete sorted
`(point key, first payload)` map, and requires byte-for-byte equality and a
matching entry count. This audit is outside the charged panels. Run it alone
with `M31_AUDIT_ONLY=1` to check the original measured source path.
The test rejects any pair whose basis digest, scalar, trial count, relation
count or signed table-entry count differs.

Run `python3 experiments/prime-field-auxiliary-ic/m31-full-rust-comparison/sign_replay.py`
from the repository root, saving stdout. Set `M31_REPLAY_TMPDIR` if the
default temporary volume is full. The runner uses the frozen public auxiliary
and plain M31 fixtures, three seeds, eight balanced-order rounds per seed,
and fresh processes for all 96 arms. The timer charges basis generation and
comparison, file writing, table build, relation collection, elimination,
and answer verification. Compilation and fixture JSON loading precede the
clock. Report matched wall and CPU ratios, win counts and all failures.
If the first panel preserves workload identity and favors the candidate,
repeat the same 24-block protocol with shuffle seed 112532. Keep the panels
separate and retain every arm.

If payload or workload identity differs, the candidate fails regardless of
timing. If it preserves identity but does not improve charged whole-run time
on both bases, keep it as a negative result. A favorable local panel remains
producer evidence pending independent replay and broader target validation.
