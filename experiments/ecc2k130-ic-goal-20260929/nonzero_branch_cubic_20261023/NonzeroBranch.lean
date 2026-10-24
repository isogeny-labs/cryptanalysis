import Std
import Init.Grind.Ring.Basic

namespace NonzeroBranch
open Lean.Grind

/-- A fixed-one code bit distinguishes the branch from the zero and seed codes. -/
theorem excludes_zero_and_seed {Code : Type} {F : Type} [Field F]
    (encode : Code → F) (bit : Code → Bool) (zeroCode seedCode code : Code)
    (injective : Function.Injective encode)
    (zero_encoding : encode zeroCode = 0)
    (zero_bit : bit zeroCode = false) (seed_bit : bit seedCode = false)
    (branch_bit : bit code = true) :
    encode code ≠ 0 ∧ encode code ≠ encode seedCode := by
  constructor
  · intro h
    have hc : code = zeroCode := injective (h.trans zero_encoding.symm)
    simp [hc, zero_bit] at branch_bit
  · intro h
    have hc : code = seedCode := injective h
    simp [hc, seed_bit] at branch_bit

/-- The pair product is nonzero on a branch excluding both roots a=0 and a=s. -/
theorem product_ne_zero {F : Type} [Field F] (a s : F)
    (characteristic_two : s + s = 0) (a_nonzero : a ≠ 0) (a_not_seed : a ≠ s) :
    a * (a + s) ≠ 0 := by
  have hs : a + s ≠ 0 := by
    intro h
    have heq : a = s := by
      calc
        a = a + 0 := by grind
        _ = a + (s + s) := by rw [characteristic_two]
        _ = (a + s) + s := by grind
        _ = s := by grind
    exact a_not_seed heq
  grind

/-- On this branch, the cubic scaled equation and original resultant have identical zeros. -/
theorem cubic_branch_exact {F : Type} [Field F] (a s resultant : F)
    (characteristic_two : s + s = 0) (a_nonzero : a ≠ 0) (a_not_seed : a ≠ s) :
    (a * (a + s)) * resultant = 0 ↔ resultant = 0 := by
  have hp := product_ne_zero a s characteristic_two a_nonzero a_not_seed
  grind

#print axioms excludes_zero_and_seed
#print axioms product_ne_zero
#print axioms cubic_branch_exact
end NonzeroBranch
