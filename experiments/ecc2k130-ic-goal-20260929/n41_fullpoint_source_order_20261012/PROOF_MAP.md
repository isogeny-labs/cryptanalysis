# Source-order proof map

| Result | Lean declaration or concrete check | Exact scope | Status |
| --- | --- | --- | --- |
| A bijection on variable names preserves XCNF satisfiability | `VariableOrder.satisfiable_rename` in the [earlier checked module](../n41_w8_tenpair_primary_order_20261012/VariableOrder.lean) | CNF and native-XOR lists under a `WirePerm` bijection and the correspondingly permuted assignment | Checked with pinned Lean 4.34.1 in the inherited experiment; its proof map records axioms and exact assumptions |
| This N41 target/source ordering is such a bijection | `run.py` permutation construction and `verify.py` row replay | All 121,456 original variables; flags in IDs 1–4, 1,400 source selectors in 5–1,404, auxiliaries thereafter | Concrete audit passed on all 325,702 CNF and 52,354 XOR rows; the known positive assignment also passed all renamed rows |
| Functional slope circuit models each nonexceptional curve addition | [parent proof map](../n41_fullpoint_functional_slope_20261012/PROOF_MAP.md) | Exact N41 binary field, signed source points, nine affine chart links | Formalization partial as recorded in the parent; variable renaming adds no new curve-law claim |

The inherited Lean theorem applies to this exact formula once the concrete mapping is verified bijective. The row-level audit checks the bridge from the generic theorem to the archived XCNF; it does not infer a public relation from a capped solver search.
