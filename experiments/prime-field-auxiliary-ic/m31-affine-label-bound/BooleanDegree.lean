import Mathlib

namespace M31BooleanDegree

abbrev F := ZMod 2147483647

def liftBit (b x : Nat) : Bool :=
  let u : F := x
  decide ((u^3 + 2*u + (b : F))^1073741823 = 1)

/-- High bits fixed by the aligned origin; all low bits vary independently. -/
def cubeWeight (b origin width : Nat) : Nat :=
  ((List.range (2^width)).filter fun i => liftBit b (origin+i)).length

theorem smallWitness : cubeWeight 14 8 3 = 3 ∧ cubeWeight 36 8 3 = 5 := by
  native_decide

theorem largeWitness : cubeWeight 14 0 16 = 32495 ∧ cubeWeight 36 131072 16 = 32887 := by
  native_decide

/-- Each monomial involving fewer than all free variables has zero total
over the Boolean cube in characteristic two: its number of ones is 2^(d-k).
The same holds for any finite sum of these monomial weights. -/
theorem parityLower {I : Type*} (terms : Finset I) (width : Nat) (arity : I → Nat)
    (proper : ∀ i ∈ terms, arity i < width) :
    ∑ i ∈ terms, (2 : ZMod 2)^(width-arity i) = 0 := by
  apply Finset.sum_eq_zero
  intro i hi
  have pos := Nat.sub_pos_of_lt (proper i hi)
  exact (congrArg (fun t : ZMod 2 => t^(width-arity i)) (show (2 : ZMod 2) = 0 by decide)).trans (zero_pow (Nat.ne_of_gt pos))

end M31BooleanDegree
