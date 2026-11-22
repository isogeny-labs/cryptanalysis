import RationalCurveBridge
import Mathlib.RingTheory.LocalRing.ResidueField.Basic

/-!
Transfer a regular rational chord or tangent calculation to a `RegularStep`
over the integer localization. A nonzero `ZMod p` slope denominator supplies
the required unit, and the embedding into `ℚ` checks the affine formulas.
-/

namespace XedniRationalRegularStep

open XedniLocalZModReduction XedniPrimeLocalReduction
open XedniRationalCurveBridge XedniRegularChainReduction
open XedniAffineReductionBridge

variable (p : ℕ) [Fact (Nat.Prime p)]

local instance : (primeIdeal p).IsMaximal := Int.ideal_span_isMaximal_of_prime p
local instance : (primeIdeal p).IsPrime := inferInstance

theorem unit_of_reduction_ne_zero (z : localIntegers p)
    (h : reduceZMod p z ≠ 0) : IsUnit z := by
  have hres : reduce (primeIdeal p) z ≠ 0 := by
    intro hz
    apply h
    simp [reduceZMod, hz]
  exact (IsLocalRing.residue_ne_zero_iff_isUnit z).mp hres

/-- A rational chord calculation with nonzero reduced denominator gives a
regular step in the local ring. -/
theorem chord_step {A B : localIntegers p}
    {P T Q : CurvePoint (localIntegers p) A B}
    (x₁ y₁ x₂ y₂ x₃ y₃ : ℚ)
    (hPx : localToRat p P.x = x₁) (hPy : localToRat p P.y = y₁)
    (hTx : localToRat p T.x = x₂) (hTy : localToRat p T.y = y₂)
    (hQx : localToRat p Q.x = x₃) (hQy : localToRat p Q.y = y₃)
    (hden : reduceZMod p (T.x - P.x) ≠ 0)
    (hx : x₃ = addX x₁ x₂ ((y₂ - y₁) / (x₂ - x₁)))
    (hy : y₃ = addY x₁ y₁ x₃ ((y₂ - y₁) / (x₂ - x₁))) :
    RegularStep P T Q := by
  obtain ⟨d, hd⟩ := unit_of_reduction_ne_zero p (T.x - P.x) hden
  have hslope : localToRat p (regularSlope (T.y - P.y) d) =
      (y₂ - y₁) / (x₂ - x₁) := by
    rw [map_regularSlope, hd, map_sub, map_sub, hTx, hPx, hTy, hPy]
  left
  refine ⟨d, hd, ?_, ?_⟩
  · apply localToRat_injective p
    rw [map_addX, hslope, hQx, hPx, hTx]
    exact hx
  · apply localToRat_injective p
    rw [map_addY, hslope, hQy, hPx, hPy, hQx]
    exact hy

/-- A rational tangent calculation with nonzero reduced denominator gives a
regular step in the local ring. -/
theorem tangent_step {A B : localIntegers p}
    {P T Q : CurvePoint (localIntegers p) A B}
    (hPT : P = T) (a x y x₂ y₂ : ℚ)
    (hA : localToRat p A = a)
    (hPx : localToRat p P.x = x) (hPy : localToRat p P.y = y)
    (hQx : localToRat p Q.x = x₂) (hQy : localToRat p Q.y = y₂)
    (hden : reduceZMod p (2 * P.y) ≠ 0)
    (hx : x₂ = addX x x ((3 * x ^ 2 + a) / (2 * y)))
    (hy : y₂ = addY x y x₂ ((3 * x ^ 2 + a) / (2 * y))) :
    RegularStep P T Q := by
  obtain ⟨d, hd⟩ := unit_of_reduction_ne_zero p (2 * P.y) hden
  have hslope : localToRat p (regularSlope (3 * P.x ^ 2 + A) d) =
      (3 * x ^ 2 + a) / (2 * y) := by
    rw [map_regularSlope, hd]
    simp only [map_add, map_mul, map_pow, map_ofNat, hPx, hPy, hA]
  right
  refine ⟨hPT, d, hd, ?_, ?_⟩
  · apply localToRat_injective p
    rw [map_addX, hslope, hQx, hPx]
    exact hx
  · apply localToRat_injective p
    rw [map_addY, hslope, hQy, hPx, hPy, hQx]
    exact hy

#print axioms unit_of_reduction_ne_zero
#print axioms chord_step
#print axioms tangent_step

end XedniRationalRegularStep
