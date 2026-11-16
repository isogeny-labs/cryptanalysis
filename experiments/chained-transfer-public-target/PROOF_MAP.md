# Public-target bridge proof map

The source module is `native/lean/PublicTargetBridge.lean`. Both ORIGINAL
producer Lean4.35 and consumer Lean4.34.1 gates audit nine declarations with
zero trusted declarations. Original consumer PCC verification locally passes
all nine exact statement bindings. These observations remain unsigned until
the required signed main verdict; this is partial formalization.
[pcc:unverified]

| Written step | Exact declaration in PublicTargetBridge | Local exact claim |
| --- | --- | --- |
| Same raw divisor key shifts by newP-oldP | raw_reference_change | PCC-20261113-4491e0 |
| Subtract geometric delta for the same actual class | same_actual_class_translation | PCC-20261113-01219f |
| Exceptional key and old zero | exceptional_basepoint_translation | PCC-20261113-ae629f |
| Corrected affine key translation respects addition | translated_key_bridge_addition | PCC-20261113-66ff6a |
| Raw origin cancels in the two descent differences | affine_offset_cancels_in_two_differences | PCC-20261113-2358db |
| Ratio recovers the scalar when the denominator has an inverse | three_affine_log_ratio | PCC-20261113-473a23 |
| General quadratic-to-short model polynomial identity | short_model_cleared_polynomial | PCC-20261113-391b45 |
| The actual divided formula when three is a unit | short_model_with_unit_three | PCC-20261113-c3da38 |
| Quartic ordinate reflection and its Weierstrass coordinates | quartic_ordinate_sign_bridge | PCC-20261113-5a6e46 |

`lean-bindings-01/claims.json` retains every exact theorem statement and
declaration hash; its verdicts were produced by the unchanged original PCC
verifier under consumer4.34.1. Original whole Lean01 failurefef40b and frozen
body-only correctione58e94 remain alongside whole producer15b373 and
consumer131a2f captures. No theorem hypothesis or result was weakened.
[pcc:unverified]

The abstract module/ring statements do not define the actual divisor or Picard
groups, prove the Hasse theorem, certify the N4 relation kernel/descent, or
construct the completed V2 maps. In particular, the infinity involution
`iota(P)=T-P`, the source model orientation S=-I, the factor2delta for a raw
degree-six input, and identification of concrete canonical keys still need
their written/native bridges and additional faithful formalization where
feasible. Native P1 checks its concrete source order using original arithmetic
plus the stated Hasse/Lagrange argument; it does not formalize that argument
merely by checking integer endpoints. [pcc:unverified]

No custom axioms, sorry, native_decide, verifier changes, new trusted manifests
or signed execution/performance conclusions are introduced. The observed
foundation set is propext, Classical.choice and Quot.sound. See
[DERIVATION.md](DERIVATION.md) for the full conditional geometric reasoning.
[pcc:unverified]
