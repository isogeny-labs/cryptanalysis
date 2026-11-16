# Proof map

Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` are pinned in `formal/`. The imported `AdaptiveInverseLift.lean` is an exact copy of the checked source at SHA-256 `7e553b80159c0f2408e58a7498cce59de8f972145c1c788210ff52f31c9b58b8`. `formal/build-output.txt` records the successful build and `#print axioms`.

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Public relation supplies one common scalar preimage | `XedniVectorDependentRankOneLift.public_factorization` | Field `K`; `b≠0`; `aU+bV=0` | Checked |
| Rank-one multiples satisfy the coefficient relation | `XedniVectorDependentRankOneLift.rank_one_relation` | Any additive commutative group; integers `a,b`; common point `P` | Checked |
| Rational point specialization | `XedniVectorDependentRankOneLift.rational_rank_one_relation` | Exact `liftPos x y` on `modelRat x y`; all integer `x,y,a,b` | Checked |
| Integral/rational model and reduction | `XedniAdaptiveInverseLift.rational_model`, `reduction_model` | Integer `x,y`; reduction additionally assumes the displayed finite-field point equation | Checked imported declarations |
| Public relation recovers the target scalar | `XedniDirectRelation.finite_relation_recovers` | Nonzero coefficient sum, compatible public sampled points | Checked in earlier PR; source SHA-256 `ab7e93ecca78edab04edb9047bd181bf830e686e4470aba3b602272dd857bf53` |
| Reduction of constructed multiples to the exact public points | `audit_sage.py` | Eight specified prime-order curves, every one of 6,136 saved events | Independently checked Sage; Lean bridge open |

The remaining Lean bridge requires a formal good-reduction map from the rational elliptic-curve point group to the specified finite-field curve and proof that it commutes with integer scalar multiplication, including the point at infinity and denominator cases. The group identity and model reduction are checked in Lean; the concrete reduction of every constructed multiple is checked by Sage.
