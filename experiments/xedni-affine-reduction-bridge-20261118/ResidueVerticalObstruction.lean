import ExceptionalSumReduction
import Mathlib.Tactic

/-! A residue-vertical chord has no integral affine endpoint when its reduced
numerator is nonzero. Its two reduced points sum to infinity when they are
inverses in the residue field. -/
namespace XedniResidueVerticalObstruction

open XedniRegularChainReduction XedniRegularGroupLaw

variable {R F : Type*} [CommRing R] [Field F] [DecidableEq F]
variable (f : R →+* F) {A B : R}

omit [DecidableEq F] in
/-- The chord x-coordinate formula, after clearing its denominator, cannot
hold with a source-ring endpoint when the denominator reduces to zero and the
numerator does not. No domain or valuation assumption on the source is needed. -/
theorem no_integral_chord_x (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    ¬ ∃ z : R, (T.y - P.y) ^ 2 =
      (z + P.x + T.x) * (T.x - P.x) ^ 2 := by
  rintro ⟨z, hz⟩
  have hmap := congrArg f hz
  have hzero : f (T.y - P.y) ^ 2 = 0 := by
    simpa [map_pow, map_mul, map_add, hx] using hmap
  exact (pow_ne_zero 2 hy) hzero

/-- Numerator of the affine chord's x-coordinate after multiplying by the
square of its x-difference. -/
def chordXNumerator (P T : CurvePoint R A B) : R :=
  (T.y - P.y) ^ 2 - (P.x + T.x) * (T.x - P.x) ^ 2

/-- Numerator of the affine chord's y-coordinate after multiplying by the
cube of its x-difference. -/
def chordYNumerator (P T : CurvePoint R A B) : R :=
  (T.y - P.y) * (P.x * (T.x - P.x) ^ 2 - chordXNumerator P T) -
    P.y * (T.x - P.x) ^ 3

/-- Over a field, the homogeneous numerator construction agrees exactly
with the usual affine chord formulas whenever the x-difference is nonzero. -/
theorem chord_numerators_correct {K : Type*} [Field K] {a b : K}
    (P T : CurvePoint K a b) (hd : T.x - P.x ≠ 0) :
    chordXNumerator P T / (T.x - P.x) ^ 2 =
        ((T.y - P.y) / (T.x - P.x)) ^ 2 - P.x - T.x ∧
    chordYNumerator P T / (T.x - P.x) ^ 3 =
        ((T.y - P.y) / (T.x - P.x)) *
          (P.x - chordXNumerator P T / (T.x - P.x) ^ 2) - P.y := by
  constructor
  · simp only [chordXNumerator]
    field_simp
    ring
  · simp only [chordYNumerator]
    field_simp

omit [DecidableEq F] in
/-- The standard homogeneous chord triple `(X*d,Y,d³)` reduces to a
nonzero multiple of `(0,1,0)` when its denominator vanishes in the residue
field and its numerator does not. -/
theorem homogeneous_chord_at_infinity (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    f (chordXNumerator P T * (T.x - P.x)) = 0 ∧
      f (chordYNumerator P T) ≠ 0 ∧
      f ((T.x - P.x) ^ 3) = 0 := by
  have hX : f (chordXNumerator P T) = f (T.y - P.y) ^ 2 := by
    simp [chordXNumerator, map_sub, map_mul, map_add, map_pow, hx]
  have hY : f (chordYNumerator P T) = -(f (T.y - P.y)) ^ 3 := by
    simp [chordYNumerator, map_sub, map_mul, map_pow, hx, hX]
    ring
  constructor
  · simp [map_mul, hx]
  constructor
  · rw [hY]
    exact neg_ne_zero.mpr (pow_ne_zero 3 hy)
  · simp [map_pow, hx]

variable [(shortCurve (f A) (f B)).IsElliptic]

private def imagePoint (P : CurvePoint R A B) :
    (shortCurve (f A) (f B)).toAffine.Point :=
  toGroupPoint (mapPoint f P)

/-- Two local affine points that become inverse after reduction sum to the
residue-field point at infinity, even when they are not exact local inverses. -/
theorem residue_inverse_add_zero (P T : CurvePoint R A B)
    (hx : f P.x = f T.x) (hy : f P.y = -f T.y) :
    imagePoint f P + imagePoint f T = 0 := by
  unfold imagePoint toGroupPoint
  simp only [WeierstrassCurve.Affine.Point.mk]
  apply WeierstrassCurve.Affine.Point.add_of_Y_eq
  · exact hx
  · simpa [mapPoint, shortCurve, WeierstrassCurve.Affine.negY] using hy

/-- A residue-inverse pair with nonzero reduced y-difference has a group sum
at infinity and no affine chord endpoint in the source ring. -/
theorem residue_inverse_affine_obstruction (P T : CurvePoint R A B)
    (hx : f P.x = f T.x) (hy : f P.y = -f T.y)
    (hdy : f (T.y - P.y) ≠ 0) :
    imagePoint f P + imagePoint f T = 0 ∧
      ¬ ∃ z : R, (T.y - P.y) ^ 2 =
        (z + P.x + T.x) * (T.x - P.x) ^ 2 := by
  constructor
  · exact residue_inverse_add_zero f P T hx hy
  · apply no_integral_chord_x f P T
    · rw [map_sub, hx, sub_self]
    · exact hdy

/-! An exact integral witness: E : y² = x³ - 5x - 8 at p = 5,
P = (4,6), T = (9,-26), and the chord slope is -32/5. -/

private def reduce5 : ℤ →+* ZMod 5 := Int.castRingHom (ZMod 5)

private def exampleP : CurvePoint ℤ (-5) (-8) :=
  ⟨4, 6, by norm_num⟩

private def exampleT : CurvePoint ℤ (-5) (-8) :=
  ⟨9, -26, by norm_num⟩

local instance : Fact (Nat.Prime 5) := ⟨by norm_num⟩

private instance exampleElliptic :
    (shortCurve (reduce5 (-5)) (reduce5 (-8))).IsElliptic := by
  rw [WeierstrassCurve.isElliptic_iff]
  rw [isUnit_iff_ne_zero]
  norm_num [reduce5, shortCurve, WeierstrassCurve.Δ,
    WeierstrassCurve.b₂, WeierstrassCurve.b₄,
    WeierstrassCurve.b₆, WeierstrassCurve.b₈] ; decide

/-- The witness points become inverses modulo five while their rational
chord has x-coordinate `699/25`, so no integral chord endpoint exists. -/
theorem concrete_residue_vertical :
    imagePoint reduce5 exampleP + imagePoint reduce5 exampleT = 0 ∧
      ¬ ∃ z : ℤ, (exampleT.y - exampleP.y) ^ 2 =
        (z + exampleP.x + exampleT.x) * (exampleT.x - exampleP.x) ^ 2 := by
  apply residue_inverse_affine_obstruction reduce5 exampleP exampleT
  · decide
  · decide
  · decide

#print axioms no_integral_chord_x
#print axioms chord_numerators_correct
#print axioms homogeneous_chord_at_infinity
#print axioms residue_inverse_add_zero
#print axioms residue_inverse_affine_obstruction
#print axioms concrete_residue_vertical

end XedniResidueVerticalObstruction
