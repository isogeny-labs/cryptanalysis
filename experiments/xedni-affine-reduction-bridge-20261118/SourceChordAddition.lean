import LocalChordUnitDerivative
import Mathlib.Tactic

/-! The denominator-free chord representative agrees, up to the unit `-1`,
with mathlib's projective addition coordinates over a commutative ring. -/
namespace XedniSourceChordAddition

open XedniRegularChainReduction XedniResidueVerticalObstruction
open XedniSourceChordEquation

variable {R : Type*} [CommRing R] {A B : R}

/-- The standard affine projective representative of a source curve point. -/
def affineTriple (P : CurvePoint R A B) : Fin 3 → R := ![P.x, P.y, 1]

/-- The source chord triple is mathlib's projective addition representative
scaled by the unit `-1`. This is a polynomial identity valid even when the
x-difference is a nonunit. -/
theorem addXYZ_eq_neg_sourceChordTriple (P T : CurvePoint R A B) :
    WeierstrassCurve.Projective.addXYZ (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
      (affineTriple P) (affineTriple T) =
      -sourceChordTriple P T := by
  funext i
  fin_cases i
  · simp [WeierstrassCurve.Projective.addXYZ,
      WeierstrassCurve.Projective.addX, affineTriple,
      sourceChordTriple, chordXNumerator]
    linear_combination (norm := ring1)
      (-P.x + 2 * T.x) * P.onCurve + (-2 * P.x + T.x) * T.onCurve
  · simp [WeierstrassCurve.Projective.addXYZ,
      WeierstrassCurve.Projective.addY,
      WeierstrassCurve.Projective.negY,
      WeierstrassCurve.Projective.negAddY, affineTriple,
      sourceChordTriple, chordYNumerator, chordXNumerator]
    linear_combination (norm := ring1)
      (P.y - 2 * T.y) * P.onCurve + (2 * P.y - T.y) * T.onCurve
  · simp [WeierstrassCurve.Projective.addXYZ,
      WeierstrassCurve.Projective.addZ, affineTriple,
      sourceChordTriple]
    linear_combination (norm := ring1) P.onCurve - T.onCurve

#print axioms addXYZ_eq_neg_sourceChordTriple

end XedniSourceChordAddition
