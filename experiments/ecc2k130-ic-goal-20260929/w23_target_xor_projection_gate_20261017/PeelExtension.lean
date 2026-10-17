import Std

namespace PeelExtension

def xorDot (coeff tail : List Bool) : Bool :=
  ((coeff.zip tail).map fun (a, b) => a && b).foldl Bool.xor false

def solve : List (Bool × List Bool) → List Bool
  | [] => []
  | (rhs, coeff) :: rows =>
      let tail := solve rows
      (Bool.xor rhs (xorDot coeff tail)) :: tail

def satisfies : List (Bool × List Bool) → List Bool → Prop
  | [], [] => True
  | (rhs, coeff) :: rows, x :: tail =>
      Bool.xor x (xorDot coeff tail) = rhs ∧ satisfies rows tail
  | _, _ => False

/-- Every upper triangular XOR system with one pivot per row has a solution
for arbitrary right hand sides and arbitrary coefficients on later pivots. -/
theorem target_xor_any_rhs_satisfiable (rows : List (Bool × List Bool)) :
    satisfies rows (solve rows) := by
  induction rows with
  | nil => simp [solve, satisfies]
  | cons head rows ih =>
      rcases head with ⟨rhs, coeff⟩
      simp [solve, satisfies, ih]

#print axioms target_xor_any_rhs_satisfiable

end PeelExtension
