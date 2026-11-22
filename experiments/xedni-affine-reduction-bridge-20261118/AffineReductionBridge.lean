import Mathlib

/-!
Regular affine addition formulas commute with a ring homomorphism when their
slope denominator is a unit in the source ring. A p-local rational point can
use this with reduction to a residue field whenever that unit condition holds.
-/

namespace XedniAffineReductionBridge

variable {R S : Type*} [CommRing R] [Field S] (f : R →+* S)

def regularSlope (numerator : R) (denominator : Rˣ) : R :=
  numerator * (denominator⁻¹ : Rˣ)

def addX (x₁ x₂ slope : R) : R := slope ^ 2 - x₁ - x₂

def addY (x₁ y₁ x₃ slope : R) : R := slope * (x₁ - x₃) - y₁

theorem map_regularSlope (numerator : R) (denominator : Rˣ) :
    f (regularSlope numerator denominator) = f numerator / f (denominator : R) := by
  have hmul : f (denominator : R) * f ((denominator⁻¹ : Rˣ) : R) = 1 := by
    rw [← map_mul]
    simp
  have hinv : f ((denominator⁻¹ : Rˣ) : R) = (f (denominator : R))⁻¹ :=
    (inv_eq_of_mul_eq_one_right hmul).symm
  simp [regularSlope, map_mul, hinv, div_eq_mul_inv]

theorem map_addX (x₁ x₂ slope : R) :
    f (addX x₁ x₂ slope) = addX (f x₁) (f x₂) (f slope) := by
  simp [addX]

theorem map_addY (x₁ y₁ x₃ slope : R) :
    f (addY x₁ y₁ x₃ slope) = addY (f x₁) (f y₁) (f x₃) (f slope) := by
  simp [addY]

theorem regular_chord_reduction
    (x₁ y₁ x₂ y₂ : R) (denominator : Rˣ)
    (hden : (denominator : R) = x₂ - x₁) :
    let slope := regularSlope (y₂ - y₁) denominator
    let x₃ := addX x₁ x₂ slope
    let y₃ := addY x₁ y₁ x₃ slope
    f slope = (f y₂ - f y₁) / (f x₂ - f x₁) ∧
      f x₃ = addX (f x₁) (f x₂) (f slope) ∧
      f y₃ = addY (f x₁) (f y₁) (f x₃) (f slope) := by
  dsimp
  constructor
  · rw [map_regularSlope, map_sub, hden, map_sub]
  constructor
  · exact map_addX f x₁ x₂ _
  · exact map_addY f x₁ y₁ _ _

theorem regular_tangent_reduction
    (A x y : R) (denominator : Rˣ)
    (hden : (denominator : R) = 2 * y) :
    let slope := regularSlope (3 * x ^ 2 + A) denominator
    let x₂ := addX x x slope
    let y₂ := addY x y x₂ slope
    f slope = (3 * (f x) ^ 2 + f A) / (2 * f y) ∧
      f x₂ = addX (f x) (f x) (f slope) ∧
      f y₂ = addY (f x) (f y) (f x₂) (f slope) := by
  dsimp
  constructor
  · rw [map_regularSlope, map_add, map_mul, map_pow, hden, map_mul]
    simp only [map_ofNat]
  constructor
  · exact map_addX f x x _
  · exact map_addY f x y _ _

#print axioms map_regularSlope
#print axioms map_addX
#print axioms map_addY
#print axioms regular_chord_reduction
#print axioms regular_tangent_reduction

end XedniAffineReductionBridge
