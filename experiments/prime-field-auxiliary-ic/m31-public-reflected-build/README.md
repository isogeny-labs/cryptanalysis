# Reflected public pair rows

The builder computes each even row with batch addition and reconstructs the
following odd row by simultaneous sign reflection. It retains the original
pair indices and visits entries in the same order as the control.

Payload.lean proves signed-index negation, equality of reflected and direct
group sums, source-index bounds, equality of grouped and direct triangular
row enumeration, and equality of the resulting table folds for any visitor.
The proof covers arbitrary commutative additive groups. It assumes their
operations satisfy the group axioms. Native field arithmetic, C++ memory
operations and compiler correctness remain outside this model.

Run python3 replay.py to regenerate reference tables, compile both variants,
and measure 24 paired rounds per basis with balanced execution order. Every
resulting key and payload is checked against the independently regenerated,
digest-checked reference after timing.

| Basis | Flat median ms | Reflected median ms | Median paired speedup | Wins |
| --- | ---: | ---: | ---: | ---: |
| Auxiliary | 7.620 | 6.266 | 1.239 | 19/24 |
| Plain | 8.180 | 5.968 | 1.327 | 22/24 |

The supplied replay.csv records one local arm64 comparison. The clock starts
with 500 representatives in memory and covers table construction. Factor-base
generation, relation collection and elimination are outside that measurement.
Cold end-to-end improvement remains unverified. These results establish no
novelty claim or formal runtime bound. Lean contains no timestamp arithmetic.

## Rust benchmark integration

Run `python3 replay.py --implementation rust` to use the Rust builder. The
runner exports the existing prime-field-auxiliary-ic crate from the current
Git HEAD into its temporary Cargo project and compiles offline in release mode.
The default implementation remains cpp. Rust uses the crate's public checked
Curve, Point and BatchScratch APIs, including batch addition and negation.
Both Rust modes use the same contiguous hash index and first-insertion rule.

The Rust replay also checks a 500-representative collision fixture made from
repeated P and 3P entries against Python affine arithmetic. This exercises
first-payload retention with duplicate representatives and sign collisions.
The checked Rust API validates intermediate points, so its instruction costs
differ from the C++ implementation. Compare flat and reflected within one
implementation. The Rust source and timings have local replay evidence only,
with independent PCC standing pending. [pcc:unverified]

Use `python3 replay.py --implementation rust --check-only` for correctness
checks without timing collection. This runs the public reference and collision
fixtures in both modes, plus expected rejection of altered payloads, truncated
references, off-curve representatives and incomplete point input. Each invalid
case must return the Rust checked-error exit code, so an abnormal termination
also fails the test. The C++ implementation supports --check-only for its
existing reference comparisons.

## Symbolic cost model

The Lean model now counts batch inputs and reconstructed inputs for m signed
pairs. The direct traversal submits m(2m+1) inputs to batch addition. The
reflected traversal submits m(m+1) inputs and reconstructs m squared inputs.
The adjacent-row length lemma connects each suffix to its triangular row.
The recurrence model sums these suffix lengths, including infinity results.

The weighted-cost theorem assumes a constant per-input addition cost and a
strictly smaller reconstruction cost. Under those assumptions and m > 0, it
proves a strict reduction in their combined modeled cost. Each reconstructed
entry still receives a table visit. Validation, batch inversion setup,
allocation, hashing, memory traffic and I/O require additional accounting.
This model provides no empirical speedup or cold pipeline result.
