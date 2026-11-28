# Reusable point tables for two-slot relations

`prepared::PairTable` enumerates and validates two prime-field factor bases once.
For each public query `R`, it scans the first base in selector order, derives
`Q = R - P`, and tests the other base with a hash table of **full canonical
points**. Before returning a witness, it replays both original arithmetic
membership predicates and the group sum. A hash match alone is never accepted.

Use `PairTable::new(curve, bases, statistics, meter)` for a reusable standalone
pair, then `table.decompose(target, smallest_first, statistics, meter)` for each
query. The table owns its curve and base configuration, is immutable and cannot
be deserialized from partial/untrusted lists. Both point signs and infinity
remain distinct keys; infinity is excluded from factor bases. Query subgroup
validation remains in place, including for a fixed nontrivial cofactor.

`prepared::solve` integrates this lookup into the existing relation collector.
A private lifecycle hook prepares one table state per nonempty fresh trial,
using the collector's **existing complete base enumerations**. It does not
extract their roots again or consume the relation-label RNG. State is dropped
before a new trial; it is never a cache indexed by a partial configuration.
Original relation coefficients, matrix columns, elimination, scalar recovery
and certificate verification remain in the reduction.

From this crate's directory, the file runner supports:

```sh
cargo run --locked --release -- solve-hashed examples/fixture.json NEW_RECEIPT.json
cargo run --locked --release -- verify NEW_RECEIPT.json
```

These are execution interfaces, not authorization to bypass the owning
repository's checkpoint, backend or measurement requirements. `solve-hashed`
requires exactly two slots. Original `solve`, `solve-selectors`, `solve-width`
and `finite::prime_decompose` remain available as controls. The usual exclusive
output, bounded input and strict typed-JSON rules remain. Diagnostics report
pair preparations, retained points, queries, full-point lookups and replays.
Those are informational producer counters, not authenticated execution history.

`smallest_first` compares original selector limits, with ties retaining slot
zero. It does not change to actual cardinality order. Rejected selectors can be
skipped after complete preparation, while valid candidates retain their original
order. Hash-table iteration never chooses witnesses. Complete absence is `None`;
resource exhaustion, failed allocation or integrity failure remains an error.
Under uncapped controls the first witness/absence and full seeded certificate
are compared with the original selector oracle. Different work envelopes may
produce different completion, which must be reported separately.

Preparation keeps ordered point vectors and full-key point-to-column hash maps.
The legacy `prepared::solve` still retains the reduction's independent matrix
indexes, while `optimized::solve` shares each slot's hash map with its matrix
and graph paths. All retained copies, construction,
key/hash/equality work and memory must be charged in a measured comparison.
The existing native meter bounds preparation/query work and hash capacity, but
is not a full arithmetic, byte or runtime price. This integration establishes
no measured speedup or changed relation probability. [pcc:unverified]

## Development controls

The new public controls cover every point of the fixed public F17 group with
multiple seeds, unequal/tied selector limits and both slot policies; empty-base
absence; work/vector errors; fixed-cofactor subgroup rejection; complete seeded
certificates and final relation RNG state; forged certificates; and actual
`solve-hashed`/`verify` CLI replay plus exclusive output preservation. Module
controls force constant hashes, inject a forged table hit for arithmetic replay,
and check state rebuilding across all queries of three fresh trials. Crypto
also has a separate root-request diagnostic control because its mirror does
not expose that Meter field. These are software controls, not scientific
measurements or an independent full audit. [pcc:unverified]

## Sources checked

- [HAC 3.56](https://cacr.uwaterloo.ca/hac/about/chap3.pdf): established table
  matching with construction and memory costs; no novelty claim for hashing.
- [Rust HashSet](https://doc.rust-lang.org/std/collections/struct.HashSet.html):
  full-key Eq/Hash consistency, immutable keys and exact equality after collisions.
- `finite.rs`, `reduction.rs` and `curve.rs`: original final-slot derivation,
  canonical affine points, complete enumeration and arithmetic replay contracts.

The original selector oracle already derives the final point, so this feature
investigates preparation/membership reuse rather than claiming to replace a
quadratic scan in that baseline. [pcc:unverified]

## Joint public-coefficient target generation

`prepared::solve_joint` / `solve-hashed-joint` uses a reusable three-point
table for the existing public `uG+vQ` relation target. HAC Algorithm14.88
(additive notation, two bases) shares one doubling chain. The table is
created lazily after the collector's original subgroup validation, reused
across attempts and fresh base trials, and remains bound to that solve's
curve/generator/target. Preparation costs and all checked affine additions
consume the same meter; no unchecked formula or scalar reduction is added.

Standalone `joint::JointTable::new` validates both subgroup points. Its
`evaluate` handles zero/mixed-width scalars and identity/equal/opposite
points. It is variable-time public-coefficient arithmetic. The table owns
three points plus its curve; this storage and its one-time sum must be
included in a cold comparison. Cloning/hashing and the meter remain unpriced.

The existing `solve-hashed` path still uses two separate multiplications,
and both paths use the same pair search and final certificate verifier.
No relation coefficient is passed to the point-decomposition oracle.
Complete seeded certificate, RNG and search-event equality are development
controls. A reduced addition count is not a runtime speedup. [pcc:unverified]

Source: [HAC14.88 and14.90, pp617–618](https://cacr.uwaterloo.ca/hac/about/chap14.pdf).

## Optional coordinate-bit buckets

`PairTable::enable_lsh(bits, seed, meter)` builds a separate bit-sampling index
from both **complete validated** factor bases. `bits` is 1–24, bounded by the
combined coordinate width; `seed` is public and selects distinct coordinate
bit positions without consuming relation-label RNG. A query derives the same
exact complement `Q=R-P` as before and visits its signature bucket. Every
candidate still receives full point equality, followed by the original
factor-base membership and sum replay for a witness. Equal points have equal
signatures, so the bucket index cannot turn an exact hit into a miss.

`prepared::solve_joint_lsh` exposes this as an opt-in two-slot relation
collector. The default `solve_joint` and CLI retain their full-point hash
sets. The new `lsh_probes` and `lsh_candidates` counters record bucket work,
not elapsed time. Bit-sampling is an LSH family for coordinate Hamming
distance, but no additive-relation locality is established for these random
hashed bases. It therefore does **not** reduce complement additions or imply
a relation-yield gain. Extra index memory and per-candidate comparisons may
make it slower than the exact hash table; a matched cold/online measurement is
still required. [pcc:unverified]

Source: [Indyk–Motwani, *Approximate Nearest Neighbors: Towards Removing the
Curse of Dimensionality*](https://graphics.stanford.edu/courses/cs468-06-fall/Papers/06%20indyk%20motwani%20-%20stoc98.pdf), for the bit-sampling LSH construction, applied here only as an exact-key candidate index.
