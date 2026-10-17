import Std
import Init.Grind.Ring.Basic

namespace AlignedSymmetry
open Lean.Grind

/-- For two distinct source codes, swapping the corresponding equal-rotation
    point slots supplies a strict code order without changing their sum. -/
theorem ordered_pair {G : Type} [AddCommGroup G]
    (a b : Nat × G) (hdifferent : a.1 ≠ b.1) :
    let x := if a.1 < b.1 then a else b
    let y := if a.1 < b.1 then b else a
    x.1 < y.1 ∧ x.2 + y.2 = a.2 + b.2 := by
  dsimp
  by_cases hlt : a.1 < b.1
  · simp [hlt]
  · have hrev : b.1 < a.1 := by omega
    simp [hlt, hrev, AddCommMonoid.add_comm]

/-- Independently permuting the two equal-rotation slot pairs preserves the
    balanced five-point sum. -/
theorem two_pair_swaps {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ : G) (swap₀ swap₁ : Bool) :
    (((if swap₀ then p₁ else p₀) + (if swap₀ then p₀ else p₁)) + p₂) +
      ((if swap₁ then p₄ else p₃) + (if swap₁ then p₃ else p₄)) =
    ((p₀ + p₁) + p₂) + (p₃ + p₄) := by
  cases swap₀ <;> cases swap₁ <;> simp [AddCommMonoid.add_comm]

/-- Two distinct roots of the characteristic-two fixed-seed quadratic
    differ by the source product divided by its leading coefficient. -/
theorem pair_root_difference {F : Type} [Field F]
    (C H p z₀ z₁ Cinv : F)
    (two_zero : ∀ x : F, x + x = 0)
    (inverse : C * Cinv = 1)
    (root₀ : C * z₀ * z₀ + p * z₀ + H = 0)
    (root₁ : C * z₁ * z₁ + p * z₁ + H = 0)
    (distinct : z₀ ≠ z₁) :
    z₀ + z₁ = p * Cinv := by
  have hz₁ := two_zero z₁
  have hsum : z₀ + z₁ ≠ 0 := by grind +ring
  have hproduct : (z₀ + z₁) * (C * (z₀ + z₁) + p) = 0 := by
    have := two_zero H
    grind +ring
  have hcoeff : C * (z₀ + z₁) + p = 0 := by
    have hinv : (z₀ + z₁)⁻¹ * (z₀ + z₁) = 1 := by grind
    have multiplied := congrArg (fun x : F => (z₀ + z₁)⁻¹ * x) hproduct
    grind +ring
  have hp := two_zero p
  have hrelation : C * (z₀ + z₁) = p := by grind +ring
  calc
    z₀ + z₁ = (C * Cinv) * (z₀ + z₁) := by rw [inverse]; grind
    _ = (C * (z₀ + z₁)) * Cinv := by grind +ring
    _ = p * Cinv := by rw [hrelation]

#print axioms ordered_pair
#print axioms two_pair_swaps
#print axioms pair_root_difference

end AlignedSymmetry
