# Integrated M31 bitmap lookup screen

Before editing the candidate, freeze a representation change to the integrated
signed-pair index. Keep the existing exact HashMap and every signed pair
witness. Mark each inserted finite x in a 2^20-bit (128 KiB) bitmap using
`x * 0x9e3779b97f4a7c15` and the high 20 bits. On an m2 query, reject an
unset bit before the exact lookup. A set bit must still use the exact table;
identity uses its separate slot. The bitmap is built inside charged setup.

Development target: the frozen public auxiliary M31 Q=(988441464,1643383878),
interval B384 and B768, m2, 64 lanes, seeds 0,1,2. Compile control from
current HEAD before candidate edits, then build candidate separately. For each
size/seed, rotate fresh-process arm order. Charge wall and parent-plus-child
CPU through process exit and JSON parsing, including basis generation, index
build, online search, elimination and certificate replay. Preserve failed and
incomplete arms. Require identical basis points, certificate, scalar, work
counts and pair counts within each matched pair, and independently check
`[scalar]G=Q`. Report index, online and full cold times. Pass this development
screen only if all six pairs are correct and median paired charged CPU improves
at both B values.

If it passes, freeze a second protocol before running the five previously
published public M31 targets in `fresh-public.json`. Include matched rho on
the same Q values, charge all setup, and keep all censored arms. These five
points were generated before the bitmap candidate, though they are public and
have been used in prior screens; they are a validation panel, not secret
holdout targets.

Prior work: `m31-full-rust-comparison/BLOOM_DIRECT_RESULTS.md` measures a
bitmap in the standalone three-point collector, and `Bloom.lean` proves its
logical no-false-negative premise. This experiment tests a different integrated
m2 query path; no new mathematical speedup or novelty is presumed.
