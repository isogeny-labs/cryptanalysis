# Target-w and final-code support encoding proof map

The [independently audited table](../n41_w9_target_w_bdd_20261017/PROOF_MAP.md)
has 284 distinct pairs `(w,c)`, one for each signed final-pair state
translated by the frozen public point. Every allowed code's four
quartic roots match its four table rows. The current builder rederives
the table from the source points and checks byte-for-byte equality with
that audited table before emitting any clauses.

Assign a fresh Boolean selector `s_i` to each row `(w_i,c_i)`. The
formula has one at-least-one clause `∨_i s_i`. For every coordinate bit
of `w_i` and every bit of `c_i`, a binary clause implements
`s_i → bit = recorded_bit`. If a model satisfies the clauses, one
selector is true and its row equals the model's `(w,c)`. Conversely,
for a table row, making its selector true and all others false
satisfies the added clauses. Distinct `w` values make two different
selectors incompatible automatically; no extra at-most-one circuit is
needed. The frozen base resultant and all folded-column collision
clauses remain in the full formula.

| Result | Declaration or audit | Status |
| --- | --- | --- |
| Existential selector constraints equal finite row membership | `SupportEncoding.selectors_iff_row` | Checked Lean structural theorem; no axioms |
| Exact 284-row target/code table | `audit_roots_sage.py` and `audit_result.json` in predecessor | Independent checked-Sage finite-field and curve audit |
| Positive XCNF extension and source hash equality | `build.py`, `build_result.json` | Exhaustive checks across 284 listed rows |

The pinned Lean toolchain is `leanprover/lean4:v4.34.1` in
`lean-toolchain`. `lean SupportEncoding.lean` succeeded, and
[`lean.stdout`](lean.stdout) reports no axioms under `#print axioms`.
The theorem quantifies over arbitrary finite tables;
it does not assume the desired row membership. The concrete
source-to-table and emitted-clause bridges are checked computationally.
The full curve-specific root equality is a partial Lean formalization
as described in the predecessor's proof map.
