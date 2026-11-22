import Std
import Init.Grind.Ring.Basic

namespace DegreeFall
open Lean.Grind

/-- Scaling by a nonzero first-source product preserves the zero set. -/
theorem scaled_zero_iff {F : Type} [Field F] (p resultant : F) (hp : p ≠ 0) :
    p * resultant = 0 ↔ resultant = 0 := by
  grind

/-- The omitted product-zero branch satisfies the scaled equation identically. -/
theorem zero_product_exception {F : Type} [CommRing F] (resultant : F) :
    (0 : F) * resultant = 0 := by
  grind

/-- Fourth powers are additive in characteristic two. -/
theorem fourth_additive {R : Type} [CommRing R]
    (charTwo : (1 : R) + 1 = 0) (a b : R) :
    (a + b)^4 = a^4 + b^4 := by
  have hs : (a+b)^2 = a^2 + b^2 := by grind
  grind

/-- A binary code bit stays linear under fourth Frobenius power. -/
theorem binary_bit_fourth {R : Type} [CommRing R]
    (coefficient bit : R) (idempotent : bit * bit = bit) :
    (coefficient * bit)^4 = coefficient^4 * bit := by
  grind

/-- Binary algebraic degree of the relevant powers 0 through 5. -/
def binaryDegree : Nat → Nat
  | 0 => 0
  | 1 => 1
  | 2 => 1
  | 3 => 2
  | 4 => 1
  | 5 => 2
  | _ => 6

def scaledSupport : List (Nat × Nat) :=
  [(1,0),(1,2),(1,4),(2,1),(2,3),(3,0),(3,2),
   (3,4),(4,1),(4,3),(5,0),(5,2),(5,4)]

/-- Each of the 13 scaled terms has binary source degree at most three. -/
theorem scaled_support_degree :
    ∀ pair ∈ scaledSupport, binaryDegree pair.1 + binaryDegree pair.2 ≤ 3 := by
  decide

#print axioms scaled_zero_iff
#print axioms zero_product_exception
#print axioms fourth_additive
#print axioms binary_bit_fourth
#print axioms scaled_support_degree
end DegreeFall
