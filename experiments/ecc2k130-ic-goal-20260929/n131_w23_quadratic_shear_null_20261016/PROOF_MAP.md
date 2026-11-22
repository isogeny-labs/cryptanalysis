# Proof and verification map

| Result | Formal or exact evidence | Scope |
| --- | --- | --- |
| The seven shear supports are linearly independent. | The prior checked Lean 4.34.1 theorem `RRShear.seven_relation_supports_independent` in [ShearRelations.lean](../n41_n131_rr_shear_identity_20261016/ShearRelations.lean), with its `#print axioms` audit. | Establishes six independent cubic identities and one independent quadratic identity for the displayed seven-row support pattern. The determinant column-operation bridge is proved in the prior readable report and checked on curve panels by Sage; its complete Lean formalization remains open. |
| Every synthetic chart has sign degree at most three and satisfies all seven shear identities. | `run.py` solves six independent cubic coefficients and one quadratic coefficient, then checks all seven equations; `verify.py` independently recomputes the free SHAKE256 coefficients and checks all saved equations. | Exact finite result for 136 charts per seed and seeds `0,…,7`. This is a designed null law, not a claim about curve points. |
| The eight first-inconsistent-row positions are 8,642–8,649, all in code 68. | `result.json`, saved coefficients, and the independently replayed low-pivot elimination in `terminal.json`. | Exact finite computation on eight frozen deterministic controls. The comparison to the real row 8,642 uses the independently checked [W23 contradiction](../n131_w23_rr_quadratic_capacity_20261016/certificate.json). |

No new structural mathematical theorem is introduced by this empirical null experiment. Its seven linear identities and their independence reuse the pinned prior formal result. The precise random law, coefficient arrays, source hashes, and terminal replay are versioned in this directory.
