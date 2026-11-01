# Common-translation certificate for the 48 multi-lift rows

All **48** rows in the level-432 image census with two coordinate lifts per
level-27 j-pair give exactly two Frobenius-compatible lift pairs. Both pairs
have the **same nonzero difference** on \(C=X_0(27)\), so each row determines
one B image without choosing a coordinate branch. `audit_sage.py` recomputes
both j-pair inversions from the sealed 864-row census and checks every
compatible pair by elliptic-curve arithmetic.

For each row the second plus lift is the first plus lift translated by a
point \(T\), and the same \(T\) translates the first minus lift to the
second minus lift. Thus
\((P_++T)-(P_-+T)=P_+-P_-\). The 48 translations
are nonzero points of order **279** on \(C(\mathbf F_{883})\), with three
distinct recorded coordinate values, each occurring 16 times. This order
is an observed property of these finite-field rows, not an assumption of
the cancellation argument.

`CommonTranslation.same_translation_preserves_difference` is the checked
Lean 4 additive-group implication. The actual equal translations, order,
and nonzero differences are independently checked in `result.json`; a Lean
formalization of the level-27 coordinate inversion and elliptic-curve
arithmetic for these 48 inputs remains open. The proof uses only standard
Lean foundations according to `#print axioms`.

Replay with the checked repository launcher:
`./sage -python experiments/hecke-432-lift-ambiguity-20261025/audit_sage.py`.
The Sage runtime receipt and checksum seal bind the result. This validates
the branch-resolution gate of the 36-point noncuspidal image and the
37-point whole-source image reported in the preceding experiments.
