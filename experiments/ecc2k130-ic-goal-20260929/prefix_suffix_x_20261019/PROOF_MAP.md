# Proof map

Toolchain: `leanprover/lean4:v4.34.1`, pinned in `lean-toolchain`. `PrefixSuffix.lean` was built with `lean PrefixSuffix.lean`; `lean.stdout` and `lean.stderr` retain the build and `#print axioms` output. `lean4checker --fresh` was unavailable on this host.

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Every actual suffix lies under one of two target residual keys | `PrefixSuffix.residual_key_covered` | Arbitrary additive commutative group; arbitrary key function whose fibers contain only a point and its negative; prefix and representative share a key; prefix plus suffix equals target. Checked. |
| An indexed suffix is reached by the residual lookup | `PrefixSuffix.indexed_decomposition_covered` | Above hypotheses plus the suffix belonging to its own key bucket. Checked. |

Both declarations use only `propext` in the recorded axiom audit. The proof has no `sorry`, `admit`, custom axiom, or unverified native evaluation.

The computational bridge is specific to `y²+xy=x³+1` over the exact N41 and N131 binary fields: for a nonidentity point, equal x coordinates identify the point or its negative. The implementation represents the identity separately with a `None` key and verifies all 1,024 complete assignments per box against direct group addition. A faithful Lean definition of these curve groups, their negation rule, and this x-fiber theorem remains open. The generic theorem states the precise property needed for completeness; it does not assume the desired lookup conclusion.
