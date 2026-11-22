import Std

namespace XorPeel

/-- A peeled affine XOR system. The head equation has a fresh pivot bit;
    `tail` may inspect all later pivot bits and arbitrary free inputs. -/
inductive Tri (U : Type) : Nat → Type where
  | nil : Tri U 0
  | cons {n : Nat} (rhs : Bool) (tail : List Bool → U → Bool)
      (rest : Tri U n) : Tri U (n + 1)

def solve {U : Type} {n : Nat} (s : Tri U n) (u : U) : List Bool :=
  match s with
  | .nil => []
  | .cons rhs tail rest =>
      let xs := solve rest u
      (rhs.xor (tail xs u)) :: xs

def Holds {U : Type} {n : Nat} (s : Tri U n) (u : U) (xs : List Bool) : Prop :=
  match s, xs with
  | .nil, [] => True
  | .nil, _ :: _ => False
  | .cons rhs tail rest, x :: restXs =>
      x.xor (tail restXs u) = rhs ∧ Holds rest u restXs
  | .cons _ _ _, [] => False

theorem xor_twice (a b : Bool) : (a.xor b).xor b = a := by
  cases a <;> cases b <;> decide

theorem solve_length {U : Type} {n : Nat} (s : Tri U n) (u : U) :
    (solve s u).length = n := by
  induction s with
  | nil => rfl
  | cons rhs tail rest ih => simp [solve, ih]

theorem solve_holds {U : Type} {n : Nat} (s : Tri U n) (u : U) :
    Holds s u (solve s u) := by
  induction s with
  | nil => simp [solve, Holds]
  | cons rhs tail rest ih =>
      simp only [solve, Holds]
      exact ⟨xor_twice rhs (tail (solve rest u) u), ih⟩

/-- Every assignment to the free interface extends to a solution of any
    finite system certified by a complete fresh-pivot peel. -/
theorem interface_surjective {U : Type} {n : Nat} (s : Tri U n) (u : U) :
    ∃ xs : List Bool, xs.length = n ∧ Holds s u xs := by
  exact ⟨solve s u, solve_length s u, solve_holds s u⟩

#print axioms xor_twice
#print axioms solve_length
#print axioms solve_holds
#print axioms interface_surjective

end XorPeel
