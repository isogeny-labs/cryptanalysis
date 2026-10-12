# Distinct-column source shield: proof and verification map

The mathematical source condition is that the 18 folded columns of nine
selected source edges are all distinct. The generic Lean declaration
`SevenPairSource.columns_nodup_iff_matching` in
`../n131_w18_four_seed_sevenpair_source_20261011/MatchingCount.lean` states
the equivalence between column-list `Nodup` and recursively choosing edges
with endpoints distinct from all later endpoints. Its quantifier is over a
list of **any** length, so it applies to nine edges without changing the
theorem. The prior checked module uses pinned Lean 4.34.1; its axiom audit
reported only the standard `propext` and `Quot.sound` foundations.

The finite implementation bridge uses the frozen W18 source table. Each of
its 33,191 canonical codes maps to two distinct folded columns. Two selected
edges violate `Nodup` exactly when their codes are equal or belong to one of
the 65 unordered pairs of different codes sharing a folded column. The
`source_conflicts()` construction builds those 65 pairs from the column
incidence map; the independent degree-two matching coefficient in the
frozen source census also gives `C(33191,2) - 65` admissible pairs.

For each pair of the nine SAT slots, `shielded_build()` adds one clause that
requires at least one of the 17 selector bits to differ, then two orientation
clauses for each conflicting unequal code pair. A mismatch literal is true
exactly when its bit differs from the forbidden code's bit. Thus the added
clauses accept precisely the source-table code tuples satisfying the Lean
matching predicate. The constructed assignment check tests the actual XCNF
clauses and XOR rows; the result audit checks the expected 36 slot pairs,
65 conflicts, formula deltas, source hashes, and source-row census.

The generic mathematical matching equivalence is Lean-checked. The concrete
table's 65-pair census and generated CNF clause semantics are independently
audited computationally; a Lean encoding of the 131,307-row table and CNF
writer is not yet present. A satisfying model still needs Sage point/sign
replay, source-column checks, and relation-rank evaluation.
