# Proof map

The pinned toolchain is `leanprover/lean4:v4.34.1`. The command
`lean NoQuadraticFilter.lean` built the actual theorem module, and
the [log](lean_check.log) records `#print axioms` as only `propext`,
`Classical.choice`, and `Quot.sound`. The module has no `sorry`,
`admit`, custom claim axiom, or kernel bypass. `lean4checker --fresh`
was unavailable.

| Claim | Declaration or audit | Exact scope | Status |
| --- | --- | --- | --- |
| A functional additive in its feature-vector argument, zero on a full-span output family, is zero everywhere | `NoQuadraticFilter.no_nonzero_filter` | Arbitrary commutative rings `V,F`; explicit additivity, zero, full-span, and vanishing hypotheses | Kernel checked |
| Degree-at-most-two evaluation is additive in its 862-dimensional coefficient feature vector | `probe_sage.py` and `verify.py` fixed monomial order and XOR row construction | GF(2) constant, 41 singleton and 820 pair monomials | Computational bridge; direct Lean feature definition open |
| All admissible pair unions span the 862-dimensional feature space | `full_census.cpp`, `full_result.json`, `verify.py` | Exact N41 W8 source, 1,554 admissible pairs, all valid third codes; rank 862 each | Native computation; three Sage/pure-Python independent controls |
| Every signed state and raw sum is the intended curve output | Frozen source table and 128 Sage addition checks; prior `n41_w8_three_code_pair_union_20261015/audit_result.json` | Exact field, curve, signed-source and distinct-column law | Sampled independent bridge; full curve-level Lean formalization open |

The full-rank calculation implies the full-span hypothesis for the
binary feature space. The checked Lean theorem then rules out any
nonzero degree-at-most-two polynomial that vanishes on an entire
admissible pair union. The finite 862-column rank certificates are
native computation with independent checks on three pairs; they are
not represented as Lean data certificates, so concrete formalization
is partial.
