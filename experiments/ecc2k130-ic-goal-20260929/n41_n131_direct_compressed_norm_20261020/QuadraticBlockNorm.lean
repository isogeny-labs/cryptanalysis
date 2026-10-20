import Std
import Init.Grind.Ring.Basic

namespace QuadraticBlockNorm
open Lean.Grind

/-- A quadratic extension norm, with `Z = Y² + δY` in characteristic two. -/
theorem quadratic_norm {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0)
    (U V Y δ : F) :
    (U + Y * V) * (U + (Y + δ) * V) =
      U * U + δ * U * V + (Y * Y + δ * Y) * V * V := by
  have hz := charTwo (U * Y * V)
  grind +ring

/-- The quartic is represented by a quadratic `U(Z)` and linear `V(Z)`. -/
theorem quartic_decomposition {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0)
    (a₀ a₁ a₂ a₃ a₄ Y δ : F) :
    let Z := Y * Y + δ * Y
    let U := a₀ + (a₂ + δ*a₃ + δ*δ*a₄)*Z + a₄*Z*Z
    let V := a₁ + δ*a₂ + δ*δ*a₃ + δ*δ*δ*a₄ + a₃*Z
    a₀ + a₁*Y + a₂*Y*Y + a₃*Y*Y*Y + a₄*Y*Y*Y*Y = U + Y*V := by
  dsimp
  have hz₁ := charTwo (a₂ * δ * Y)
  have hz₂ := charTwo (a₃ * δ * Y * Y)
  have hz₃ := charTwo (a₃ * δ * δ * Y)
  have hz₄ := charTwo (a₄ * δ * δ * Y * Y)
  have hz₅ := charTwo (a₄ * δ * δ * δ * Y)
  have hz₆ := charTwo (a₄ * δ * Y * Y * Y)
  grind +ring

/-- One binary direction is eliminated without expanding in the original
source coordinate. This is the update used by the executable recurrence. -/
theorem quartic_norm_step {F : Type} [CommRing F]
    (charTwo : ∀ a : F, a + a = 0)
    (a₀ a₁ a₂ a₃ a₄ Y δ : F) :
    let Z := Y*Y + δ*Y
    let U := a₀ + (a₂ + δ*a₃ + δ*δ*a₄)*Z + a₄*Z*Z
    let V := a₁ + δ*a₂ + δ*δ*a₃ + δ*δ*δ*a₄ + a₃*Z
    (a₀ + a₁*Y + a₂*Y*Y + a₃*Y*Y*Y + a₄*Y*Y*Y*Y) *
      (a₀ + a₁*(Y+δ) + a₂*(Y+δ)*(Y+δ) +
       a₃*(Y+δ)*(Y+δ)*(Y+δ) + a₄*(Y+δ)*(Y+δ)*(Y+δ)*(Y+δ)) =
      U*U + δ*U*V + Z*V*V := by
  dsimp
  have hz : (Y+δ)*(Y+δ)+δ*(Y+δ) = Y*Y+δ*Y := by
    have h₁ := charTwo (Y*δ)
    have h₂ := charTwo (δ*δ)
    grind +ring
  have hl := quartic_decomposition charTwo a₀ a₁ a₂ a₃ a₄ Y δ
  have hr := quartic_decomposition charTwo a₀ a₁ a₂ a₃ a₄ (Y+δ) δ
  dsimp at hl hr
  rw [hz] at hr
  rw [hl, hr]
  exact quadratic_norm charTwo
    (a₀ + (a₂ + δ*a₃ + δ*δ*a₄)*(Y*Y+δ*Y) + a₄*(Y*Y+δ*Y)*(Y*Y+δ*Y))
    (a₁ + δ*a₂ + δ*δ*a₃ + δ*δ*δ*a₄ + a₃*(Y*Y+δ*Y)) Y δ

#print axioms quadratic_norm
#print axioms quartic_decomposition
#print axioms quartic_norm_step

end QuadraticBlockNorm
