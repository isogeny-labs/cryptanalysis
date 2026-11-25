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
