import Std
import Init.Grind.Ring.Basic

namespace SignANF
open Lean.Grind

/-- The two-sign algebraic normal form of a four-entry source row bit. -/
def eval (v00 v01 v10 v11 sa sb : Bool) : Bool :=
  Bool.xor
    (Bool.xor v00 (sa && Bool.xor v00 v10))
    (Bool.xor (sb && Bool.xor v00 v01)
      ((sa && sb) && Bool.xor (Bool.xor v00 v01) (Bool.xor v10 v11)))

/-- Every sign assignment returns its corresponding source-table bit. -/
theorem covers_four (v00 v01 v10 v11 sa sb : Bool) :
    eval v00 v01 v10 v11 sa sb =
      if sa then (if sb then v11 else v10)
      else (if sb then v01 else v00) := by
  cases v00 <;> cases v01 <;> cases v10 <;> cases v11 <;>
    cases sa <;> cases sb <;> decide

/-- Simultaneously negating two selected endpoints negates their pair sum. -/
theorem simultaneous_sign_flip {G : Type} [AddCommGroup G] (a b : G) :
    (-a) + (-b) = -(a + b) := by
  exact (AddCommGroup.neg_add a b).symm

#print axioms covers_four
#print axioms simultaneous_sign_flip
end SignANF
