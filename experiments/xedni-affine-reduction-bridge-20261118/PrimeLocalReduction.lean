import RegularGroupLaw
import Mathlib.RingTheory.Localization.AtPrime.Basic
import Mathlib.RingTheory.LocalRing.ResidueField.Defs

/-!
Instantiate the regular-chain group theorem over the localization of the
integers at a prime ideal. The residue field is canonically equivalent to the
integer quotient, with the expected numerator/denominator reduction formula.
-/

namespace XedniPrimeLocalReduction

open XedniRegularChainReduction XedniRegularGroupLaw

variable (P : Ideal ℤ) [P.IsPrime]

abbrev localRing := Localization.AtPrime P
abbrev residueField := IsLocalRing.ResidueField (localRing P)

noncomputable local instance : DecidableEq (residueField P) := Classical.decEq _

def reduce : localRing P →+* residueField P :=
  IsLocalRing.residue (localRing P)

theorem denominator_is_unit (s : P.primeCompl) :
    IsUnit ((algebraMap ℤ (localRing P)) (s : ℤ)) :=
  IsLocalization.map_units (localRing P) s

theorem local_chain_group_relation {A B : localRing P}
    [(shortCurve (reduce P A) (reduce P B)).IsElliptic]
    {X T Y : CurvePoint (localRing P) A B}
    (h : RegularChain T X Y) :
    ∃ n : ℕ, toGroupPoint (mapPoint (reduce P) Y) =
      toGroupPoint (mapPoint (reduce P) X) +
        n • toGroupPoint (mapPoint (reduce P) T) := by
  classical
  exact reduced_regularChain_group_relation (reduce P) h

variable [P.IsMaximal]

attribute [local instance] Ideal.Quotient.field

noncomputable def quotientEquivResidue : (ℤ ⧸ P) ≃+* residueField P :=
  (IsLocalization.AtPrime.equivQuotMaximalIdeal P (localRing P)).toRingEquiv

theorem integer_reduction (z : ℤ) :
    quotientEquivResidue P (Ideal.Quotient.mk P z) =
      reduce P ((algebraMap ℤ (localRing P)) z) := by
  exact IsLocalization.AtPrime.equivQuotMaximalIdeal_apply_mk P (localRing P) z

theorem fraction_reduction (z : ℤ) (s : P.primeCompl) :
    (quotientEquivResidue P).symm
      (reduce P (IsLocalization.mk' (localRing P) z s)) =
        (Ideal.Quotient.mk P z) * (Ideal.Quotient.mk P (s : ℤ))⁻¹ := by
  exact IsLocalization.AtPrime.equivQuotMaximalIdeal_symm_apply_mk P (localRing P) z s

#print axioms denominator_is_unit
#print axioms integer_reduction
#print axioms fraction_reduction
#print axioms local_chain_group_relation

end XedniPrimeLocalReduction
