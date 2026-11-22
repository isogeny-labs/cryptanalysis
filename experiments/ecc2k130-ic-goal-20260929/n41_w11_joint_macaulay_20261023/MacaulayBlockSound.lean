import Std
import Init.Grind.Ring.Basic

namespace MacaulayBlockSound
open Lean.Grind

/-- A polynomial Macaulay row is an original equation multiplied by a
    monomial. The multiplier may be any function of the assignment. -/
def rowEval {X : Type} {I : Type} {J : Type} {R : Type} [CommRing R]
    (equation : I → X → R) (monomial : J → X → R)
    (row : I × J) (x : X) : R :=
  monomial row.2 x * equation row.1 x

/-- An exact constant-one row combination rejects every common zero of
    the original equations, regardless of the selected monomial degree. -/
theorem constant_one_block_certificate_sound
    {X : Type} {I : Type} {J : Type} {R : Type} [CommRing R]
    (equation : I → X → R) (monomial : J → X → R)
    (rows : List (I × J)) (one_ne_zero : (1 : R) ≠ 0)
    (identity : ∀ x : X,
      (rows.map (fun row => rowEval equation monomial row x)).sum = 1) :
    ∀ x : X, ∃ i : I, equation i x ≠ 0 := by
  intro x
  classical
  by_cases h : ∃ i : I, equation i x ≠ 0
  · exact h
  have hz : ∀ i : I, equation i x = 0 := by
    intro i
    by_cases hi : equation i x = 0
    · exact hi
    · exact False.elim (h ⟨i, hi⟩)
  have hrows : ∀ row : I × J, rowEval equation monomial row x = 0 := by
    intro row
    rcases row with ⟨i, j⟩
    grind [rowEval]
  have hsum_all : ∀ xs : List (I × J),
      (xs.map (fun row => rowEval equation monomial row x)).sum = 0 := by
    intro xs
    induction xs with
    | nil => rfl
    | cons row rest ih => grind [List.map]
  have hone := identity x
  rw [hsum_all rows] at hone
  exact False.elim (one_ne_zero hone.symm)

#print axioms constant_one_block_certificate_sound

end MacaulayBlockSound
