import Std
import Init.Grind.Ring.Basic

namespace MacaulaySound
open Lean.Grind

/-- One Boolean Macaulay row is either an equation or that equation
    multiplied by a source-code bit. -/
def rowEval {X : Type} {I : Type} {J : Type} {R : Type} [CommRing R]
    (equation : I → X → R) (bit : J → X → R)
    (row : I × Option J) (x : X) : R :=
  match row.2 with
  | none => equation row.1 x
  | some j => bit j x * equation row.1 x

/-- A concrete row-span certificate for the constant one rejects every
    assignment that satisfies all original equations. -/
theorem constant_one_certificate_sound
    {X : Type} {I : Type} {J : Type} {R : Type} [CommRing R]
    (equation : I → X → R) (bit : J → X → R)
    (rows : List (I × Option J))
    (one_ne_zero : (1 : R) ≠ 0)
    (certificate : ∀ x : X, (rows.map (fun row => rowEval equation bit row x)).sum = 1) :
    ∀ x : X, ∃ i : I, equation i x ≠ 0 := by
  intro x
  classical
  by_cases hw : ∃ i : I, equation i x ≠ 0
  · exact hw
  have h : ∀ i : I, equation i x = 0 := by
    intro i
    by_cases hi : equation i x = 0
    · exact hi
    · exact False.elim (hw ⟨i, hi⟩)
  have hrow : ∀ row : I × Option J, rowEval equation bit row x = 0 := by
    intro row
    rcases row with ⟨i, j⟩
    cases j with
    | none => simp [rowEval, h i]
    | some j => grind [rowEval]
  have hsum_all : ∀ xs : List (I × Option J),
      (xs.map (fun row => rowEval equation bit row x)).sum = 0 := by
    intro xs
    induction xs with
    | nil => rfl
    | cons row rest ih => grind [List.map]
  have hone := certificate x
  rw [hsum_all rows] at hone
  exact False.elim (one_ne_zero hone.symm)

#print axioms constant_one_certificate_sound
end MacaulaySound
