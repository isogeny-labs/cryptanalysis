# Shared-x denominator panel on frozen M31 fixtures

The prespecified protocol is in `PAIRED_BATCH_PROTOCOL.md`. The candidate
processes adjacent `(-F, F)` steps with one denominator inverse for both
signs. Ordinary pairs share the batch prefix product; equal-x, infinity and
nonpaired-x cases use individual additions. The control is the already
measured combined collector with identical hash, table, walk and elimination.

Both 24-block panels per public basis completed. Within all 96 matched pairs,
basis digest, complete index-map digest, signed entry count, trial count,
relation count and checked scalar 123456789 agreed. The crate differential
test compared all 1,000 outputs with checked batch addition across ordinary
and exceptional inputs; all 15 library unit tests passed locally.
[pcc:unverified]

| Panel | Fixture | Standard wall median ms | Shared-x wall median ms | Median paired standard/shared-x wall ratio | Shared-x wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 160.793 | 160.198 | 1.0111 | 14/24 |
| Initial | Plain | 137.786 | 135.152 | 1.0553 | 16/24 |
| Repeat | Auxiliary | 485.512 | 509.601 | 1.0111 | 13/24 |
| Repeat | Plain | 640.959 | 548.115 | 1.1148 | 14/24 |

| Panel | Fixture | Standard CPU median ms | Shared-x CPU median ms | Median paired standard/shared-x CPU ratio | Shared-x wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 155.324 | 152.841 | 1.0250 | 17/24 |
| Initial | Plain | 133.973 | 131.536 | 1.0566 | 16/24 |
| Repeat | Auxiliary | 205.541 | 206.049 | 1.0165 | 13/24 |
| Repeat | Plain | 191.964 | 183.669 | 1.0782 | 19/24 |

The repeat ran under much heavier host contention, visible in its wall and
CPU medians. Paired ratios reduce but do not remove this uncertainty. The
candidate saves denominator work, yet the whole-run gain is small and not
stable enough to call a performance breakthrough. Both raw CSVs retain all
arms. The charged window includes basis generation, index construction,
relation collection, elimination and answer verification. Compilation and
frozen JSON loading are outside it; OS caches were not flushed.

This path gives a sound place to test an x-coordinate lookup filter. In the
sign-packed index, an absent x guarantees both signs are absent, so a future
candidate can defer ordinate materialization until an x slot exists. That
construction and its cost are not measured here. A Lean proof of the paired
chord formula remains pending; the current evidence is differential Rust
testing plus full-pipeline matched replay.

Measurement SHA-256: `paired_batch_replay.py`
`2b5b5437af4d7990345a8560d5e0955cbb3488aa5dca6e3e8c7f3a69b06e4d17`,
initial CSV `2266085f05554705ddcf331a570a1fae9fe855f0eeb798de79fb2f46982ba643`,
repeat CSV `94db79db29a5d8c1a1d205e52adc7daa6c73fb7b948cd7bd89a1b26556f979a5`.
