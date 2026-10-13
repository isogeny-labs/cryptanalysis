# Proof map

| Result | Declaration or check | Exact scope and status |
| --- | --- | --- |
| A separating signature on the two complete subtotal roots selects the plus root | `signature_selects_plus` in [SignatureSelect.lean](SignatureSelect.lean) | Checked with `leanprover/lean4:v4.34.1`; [output](lean_check.log) reports no axioms. Quantifies over arbitrary point and signature types, a two-root completeness hypothesis, and distinct signature values. |
| Each frozen W18 pair code has two pair-output reciprocal roots | [Sage census](census_sage.py), [census result](census_result.json), [table audit](table_audit_result.json) | Complete `33191`-code seed-212 source. Quadratic identity checked for each root in Sage producer; independent structural table audit checks cardinality and source masks. |
| The selected 14-bit hash separates plus and minus for all source roots | [hash selector](select_hash.py), [manifest](hash_manifest.json), [independent table audit](table_audit_result.json) | Exhaustive `66382`-root certificate, seed 42, exact mask list and table hash. |
| Characteristic-two x-only linked-sum formula | Readable derivation in [RESULT.md](RESULT.md), producer sampled Sage group checks | The recurrence and cancellation are mathematically explicit. A faithful Lean theorem over the actual characteristic-two curve remains open: it needs the field/curve definitions, the `y^(2^j)=A_j+B_jy` induction, and the Semaev two-root bridge. Do not treat the generic signature theorem as that bridge. |
| All saved roots equal signed curve-addition outcomes | [point audit](audit_sage.py) and [addition-formula audit](audit_fast_sage.py) | Both are frozen and running; terminal verification status is pending. |
| Constructed SAT assignment satisfies the gated circuit | [control result](sat/control_result.json) | Complete CNF and native-XOR check on one constructed N131 target, with 14-bit gate. |

Toolchain is pinned in [lean-toolchain](lean-toolchain). Command: `lean SignatureSelect.lean`; output and `#print axioms` are preserved in [lean_check.log](lean_check.log). The first unsuccessful syntax check is preserved in [lean_check_attempt1.log](lean_check_attempt1.log). `lean4checker --fresh` was not available. The full concrete source and group-action theorem remains a formalization task; the feasible structural implication is proved.
