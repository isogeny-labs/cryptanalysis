import SourceChordAddition
import Mathlib.Tactic

/-! Distinct affine source points select the chord branch of mathlib's
projective addition, and the resulting projective class is the source chord
class. -/
namespace XedniSourceChordDistinctAddition

open XedniRegularChainReduction XedniSourceChordEquation
open XedniSourceChordAddition
open WeierstrassCurve.Projective

variable {R : Type*} [CommRing R] {A B : R}

/-- Distinct affine x-coordinates make the two standard projective
representatives inequivalent over any commutative source ring. -/
theorem affineTriple_not_equiv (P T : CurvePoint R A B) (hx : P.x ≠ T.x) :
    ¬affineTriple P ≈ affineTriple T := by
  apply WeierstrassCurve.Projective.not_equiv_of_X_ne
  simpa [affineTriple] using hx

/-- In the distinct-x case, mathlib's projective addition operation chooses
the chord formula, which is the source homogeneous chord scaled by `-1`. -/
theorem add_eq_neg_sourceChordTriple (P T : CurvePoint R A B)
    (hx : P.x ≠ T.x) :
    WeierstrassCurve.Projective.add (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
      (affineTriple P) (affineTriple T) =
      -sourceChordTriple P T := by
  rw [WeierstrassCurve.Projective.add_of_not_equiv (affineTriple_not_equiv P T hx)]
  exact addXYZ_eq_neg_sourceChordTriple P T

/-- The chosen addition representative and source chord have the same
projective point class, since multiplication by `-1` is a unit scaling. -/
theorem addMap_eq_sourceChordClass (P T : CurvePoint R A B)
    (hx : P.x ≠ T.x) :
    WeierstrassCurve.Projective.addMap (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
      (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R)
      (⟦affineTriple T⟧ : WeierstrassCurve.Projective.PointClass R) =
      (⟦sourceChordTriple P T⟧ : WeierstrassCurve.Projective.PointClass R) := by
  change (⟦WeierstrassCurve.Projective.add (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
      (affineTriple P) (affineTriple T)⟧ :
      WeierstrassCurve.Projective.PointClass R) = ⟦sourceChordTriple P T⟧
  rw [add_eq_neg_sourceChordTriple P T hx]
  have hunit : IsUnit (-1 : R) := (isUnit_one : IsUnit (1 : R)).neg
  simpa only [neg_one_smul] using
    (WeierstrassCurve.Projective.smul_eq (sourceChordTriple P T) hunit)

#print axioms affineTriple_not_equiv
#print axioms add_eq_neg_sourceChordTriple
#print axioms addMap_eq_sourceChordClass

end XedniSourceChordDistinctAddition
