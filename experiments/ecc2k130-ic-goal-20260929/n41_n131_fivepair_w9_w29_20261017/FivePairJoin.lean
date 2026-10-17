import Std
import Init.Grind.Ring.Basic

namespace FivePairJoin
open Lean.Grind

/-- The four links of the five-pair circuit sum precisely its five inputs. -/
theorem balanced_five_sum {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ : G) :
    ((p₀ + p₁) + (p₂ + p₃)) + p₄ =
      ((((p₀ + p₁) + p₂) + p₃) + p₄) := by
  rw [← AddCommMonoid.add_assoc (p₀ + p₁) p₂ p₃]

/-- The three-plus-two links have the same five-point sum. -/
theorem balanced_three_two_sum {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ : G) :
    (((p₀ + p₁) + p₂) + (p₃ + p₄)) =
      ((((p₀ + p₁) + p₂) + p₃) + p₄) := by
  rw [← AddCommMonoid.add_assoc]

/-- The left-triple/right-pair lookup key preserves every exact sum. -/
theorem target_conditioned_lookup {G : Type} [AddCommGroup G]
    (left right target : G) :
    left + right = target ↔ left = target - right := by
  constructor
  · intro h
    calc
      left = (left + right) - right := AddCommGroup.add_sub_cancel.symm
      _ = target - right := by rw [h]
  · intro h
    calc
      left + right = (target - right) + right := by rw [h]
      _ = target := AddCommGroup.sub_add_cancel

/-- Transporting a target-orbit hit back through an additive inverse map
    gives a relation on the original public target. -/
theorem orbit_transport {G : Type} [AddCommGroup G]
    (f g : G → G) (p₀ p₁ p₂ p₃ p₄ target : G)
    (hgf : ∀ x, g (f x) = x)
    (hadd : ∀ x y, g (x + y) = g x + g y)
    (hit : ((((p₀ + p₁) + p₂) + p₃) + p₄) = f target) :
    ((((g p₀ + g p₁) + g p₂) + g p₃) + g p₄) = target := by
  have mapped := congrArg g hit
  rw [hadd, hadd, hadd, hadd, hgf] at mapped
  exact mapped

#print axioms balanced_five_sum
#print axioms balanced_three_two_sum
#print axioms target_conditioned_lookup
#print axioms orbit_transport

end FivePairJoin
