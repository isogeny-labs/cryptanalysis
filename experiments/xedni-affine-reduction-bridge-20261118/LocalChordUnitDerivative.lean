import SourceChordNonsingular
import PrimeLocalReduction
import Mathlib.RingTheory.LocalRing.ResidueField.Basic
import Mathlib.Tactic

/-! At a residue-vertical chord, the source projective Z derivative is a
unit in a local ring. This is the smoothness condition needed at infinity. -/
namespace XedniLocalChordUnitDerivative

open XedniRegularChainReduction XedniResidueVerticalObstruction
open XedniSourceChordEquation XedniPrimeLocalReduction

variable {R : Type*} [CommRing R]
variable {A B : R}

/-- The projective Z derivative of the short-Weierstrass equation at the
homogeneous chord representative. -/
def chordZDerivative (P T : CurvePoint R A B) : R :=
  let C := sourceChordTriple P T
  C 1 ^ 2 - (2 * A * C 0 * C 2 + 3 * B * C 2 ^ 2)

/-- The explicit expression is mathlib's projective `Z` derivative for the
short-Weierstrass source curve. -/
theorem chordZDerivative_eq_polynomialZ (P T : CurvePoint R A B) :
    MvPolynomial.eval (sourceChordTriple P T)
      (WeierstrassCurve.Projective.polynomialZ
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)) =
      chordZDerivative P T := by
  rw [WeierstrassCurve.Projective.eval_polynomialZ]
  simp [chordZDerivative]

/-- A nonzero residue chord y-coordinate makes the projective Z derivative
a unit of the local source ring. -/
theorem chordZDerivative_isUnit [IsLocalRing R]
    (P T : CurvePoint R A B)
    (hx : IsLocalRing.residue R (T.x - P.x) = 0)
    (hy : IsLocalRing.residue R (T.y - P.y) ≠ 0) :
    IsUnit (chordZDerivative P T) := by
  let f := IsLocalRing.residue R
  let C := sourceChordTriple P T
  obtain ⟨h0, h1, h2⟩ := homogeneous_chord_at_infinity f P T hx hy
  have hc0 : f (C 0) = 0 := by simpa [C, sourceChordTriple] using h0
  have hc1 : f (C 1) ≠ 0 := by simpa [C, sourceChordTriple] using h1
  have hc2 : f (C 2) = 0 := by simpa [C, sourceChordTriple] using h2
  apply (IsLocalRing.residue_ne_zero_iff_isUnit (chordZDerivative P T)).mp
  have hmap : f (chordZDerivative P T) = f (C 1) ^ 2 := by
    simp [chordZDerivative, C, map_sub, map_add, map_mul, map_pow, hc0, hc2]
  rw [hmap]
  exact pow_ne_zero 2 hc1

variable (Pideal : Ideal ℤ) [Pideal.IsPrime]

/-- Specialization to the integer prime-local ring and its checked residue
map used by the recorded xedni lifts. -/
theorem primeLocal_chordZDerivative_isUnit
    {A B : localRing Pideal}
    (U V : CurvePoint (localRing Pideal) A B)
    (hx : reduce Pideal (V.x - U.x) = 0)
    (hy : reduce Pideal (V.y - U.y) ≠ 0) :
    IsUnit (chordZDerivative U V) :=
  chordZDerivative_isUnit U V hx hy

#print axioms chordZDerivative_eq_polynomialZ
#print axioms chordZDerivative_isUnit
#print axioms primeLocal_chordZDerivative_isUnit

end XedniLocalChordUnitDerivative
