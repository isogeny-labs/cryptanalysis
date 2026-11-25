# Flat-index hash comparison on the frozen M31 fixtures

The protocol in `HASH_PROTOCOL.md` was written before the first run. Both
binaries use the same 1,048,576-slot contiguous table, linear probing,
key equality checks, direct pair rows, deterministic relation walk and modular
elimination. The candidate changes only the slot hash from a SplitMix-style
finalizer to the top 20 bits of one 64-bit multiplicative product.

Every arm regenerated and checked its 500-point basis, then ran the Rust
collector in a fresh process. The charged clock includes basis generation,
relation collection, elimination and answer verification. All 192 observations
completed across two 24-block panels per fixture. Within every matched pair,
the basis digest, table entry count, trial count, relation count and verified
public answer matched exactly. [pcc:unverified]

| Panel | Fixture | SplitMix wall median ms | Multiply wall median ms | Median paired wall ratio | Multiply wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 194.550 | 186.410 | 1.0446 | 20/24 |
| Initial | Plain | 164.367 | 157.178 | 1.0624 | 21/24 |
| Repeat | Auxiliary | 208.745 | 206.427 | 1.0202 | 16/24 |
| Repeat | Plain | 182.825 | 179.884 | 1.0260 | 18/24 |

| Panel | Fixture | SplitMix CPU median ms | Multiply CPU median ms | Median paired CPU ratio | Multiply wins |
| --- | --- | ---: | ---: | ---: | ---: |
| Initial | Auxiliary | 191.433 | 183.687 | 1.0510 | 20/24 |
| Initial | Plain | 162.957 | 155.726 | 1.0554 | 21/24 |
| Repeat | Auxiliary | 206.481 | 204.430 | 1.0175 | 17/24 |
| Repeat | Plain | 181.608 | 176.748 | 1.0288 | 19/24 |

The direction repeated, while the magnitude changed between panels on the
shared Apple M4 Pro host. These are same-target exploratory measurements with
one target and repeated seeds. They establish a measured local iteration over
the current flat-index control, subject to independent verification, and do
not establish a general M31 performance breakthrough. `hash-raw.csv` and
`hash-confirm.csv` retain every arm. OS caches were not flushed. Compilation
and frozen fixture JSON loading were outside the clock. [pcc:unverified]

The Lean payload proof for reflected rows applies to an arbitrary table
visitor. It does not verify this hash implementation or its runtime. The Rust
collector checks all accepted relations by group addition and the resulting
answer by generator multiplication. Independent certificate replay and signed
PCC standing remain pending.
