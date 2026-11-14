# Norm-halving proof map

Both unchanged original gates (Lean4.34.1 consumer,4.35.0 producer) pass the same ten declarations with zero trusted research axioms. Every named root prints only standard `propext`, `Classical.choice`, `Quot.sound`. Nine exact original PCC statement bindings pass locally; the reused abscissa identity is not counted again. Total82 is a partial binding count, not82 geometric formalizations. PCC-20261114-3ba28f pins the acceptance and prior rejected attempts. [pcc:unverified]

| Declaration in `NormHalving` | Exact scope | Binding suffix |
| --- | --- | --- |
| `halving_abscissa_identity` | Universal commutative-ring expansion, reused existing formula | Existing proof; not new |
| `halving_ordinate_identity` | Universal cleared ordinate identity, no division | 7cfb9f |
| `halves_differ_by_two_torsion` | Equal doubles imply two-torsion difference in an IntModule | 0e81c2 |
| `halves_fixed_by_frobenius_square` | Subtraction/scalar-preserving sigma, rational Q and fixed two-torsion imply sigma²(a)=a | 03c69b |
| `odd_class_has_explicit_norm_lift` | Phi-linear, Phi N=[2], actual odd-order assumption | 4127df |
| `preimage_from_odd_and_cofactor` | Full preimage derived from odd+cofactor decomposition and actual cofactor lift | 3aea5b |
| `correction_exists_for_every_half` | A full preimage and its norm give an actual two-torsion correction for every half | e582c4 |
| `corrected_evaluator_matches_beta` | Actual correction and quotient commuting square imply evaluator=beta | 442f34 |
| `corrected_lift_independent` | Both corrected evaluations equal through the same explicit square | 22b021 |
| `strongest_scalar_baseline_identity` | Explicit scalar linearity and Psi N=[2]beta imply baseline=beta | 508ce1 |

Each suffix is PCC-20261114-…; exact statements, declaration digests and local verdicts are in [bindings](evidence/norm-halving-bindings-01/claims.json). The actual source is [NormHalving.lean](norm-halving-evaluator/lean/NormHalving.lean). Original PCC checks exact declaration headers and holes; it does not certify that abstract parameters have the intended geometric interpretations. All are unsigned local passes. [pcc:unverified]

The actual finite-field representation, full rational two-torsion, Weil-restriction/quotient squares, Picard models/origins, norm identities on their precise domains, source isogenies/orders, cofactor lifts and dictionary, native code correspondence and point-count input remain written/native obligations. They are not silently imported as conclusions of the abstract proofs. The derivation supplies a full elliptic-domain lift from existing odd/cofactor data rather than inferring it from geometric surjectivity alone. [pcc:unverified]

Original Lean attempts01 and02 failed before acceptance03: universal matching exceeded the generation bound, then group cancellation needed explicit identities. Every failed build and recovery diagnostic remains retained. The accepted module has no holes, custom axioms or native evaluation bypasses. Exact-Z coefficient expansion and original certificate replay are additional native checks (d91395); their source pointer does not make the old issuer run Lean. [pcc:unverified]
