import Std
import Init.Grind.Ring.Basic

namespace LinearizedAnnihilator
open Lean.Grind

/-- One linearized-polynomial update adds the coset of `b` to its kernel.
    This is the structural step used to build the compact product-span
    annihilator from a binary basis. -/
theorem extend_kernel_iff {F : Type} [Field F]
    (charTwo : ∀ t : F, t+t=0)
    (L : F → F) (hadd : ∀ x y, L (x+y) = L x + L y)
    (b x : F) :
    (L x)^2 + (L b)*(L x) = 0 ↔ L x = 0 ∨ L (x+b) = 0 := by
  have hfactor : (L x)^2 + (L b)*(L x) = (L x)*((L x)+(L b)) := by
    grind +ring
  have hcoset : L (x+b)= (L x)+(L b) := hadd x b
  rw [hfactor, hcoset]
  constructor
  · intro hzero
    exact Field.of_mul_eq_zero hzero
  · intro hor
    rcases hor with hz | hz
    · rw [hz]
      grind +ring
    · rw [hz]
      grind +ring

#print axioms extend_kernel_iff

end LinearizedAnnihilator
