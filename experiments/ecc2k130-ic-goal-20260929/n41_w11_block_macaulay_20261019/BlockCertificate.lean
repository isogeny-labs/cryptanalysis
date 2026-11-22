import Std
import Init.Grind.Ring.Basic

namespace BlockCertificate
open Lean.Grind

/-- A Macaulay row is an original equation multiplied by an arbitrary
Boolean-code monomial. The multiplier may be the empty product. -/
def rowEval {X I J R : Type} [CommRing R]
    (equation : I → X → R) (multiplier : J → X → R)
    (row : I × J) (x : X) : R :=
  multiplier row.2 x * equation row.1 x

/-- An exact constant-one row-span identity excludes every simultaneous
zero of the original field-coordinate equations, regardless of which
code variables occur in the row multipliers. -/
theorem constant_one_block_certificate_sound
    {X I J R : Type} [CommRing R]
    (equation : I → X → R) (multiplier : J → X → R)
    (rows : List (I × J)) (one_ne_zero : (1 : R) ≠ 0)
    (certificate : ∀ x : X,
      (rows.map (fun row => rowEval equation multiplier row x)).sum = 1) :
    ∀ x : X, ∃ i : I, equation i x ≠ 0 := by
  intro x
  classical
  by_cases hw : ∃ i : I, equation i x ≠ 0
  · exact hw
  have hz : ∀ i : I, equation i x = 0 := by
    intro i
    by_cases hi : equation i x = 0
    · exact hi
    · exact False.elim (hw ⟨i, hi⟩)
  have hrow : ∀ row : I × J, rowEval equation multiplier row x = 0 := by
    intro row
    rcases row with ⟨i, j⟩
    simp only [rowEval, hz i, Semiring.mul_zero]
  have hsum : ∀ xs : List (I × J),
      (xs.map (fun row => rowEval equation multiplier row x)).sum = 0 := by
    intro xs
    induction xs with
    | nil => rfl
    | cons row rest ih => grind [List.map]
  have hone := certificate x
  rw [hsum rows] at hone
  exact False.elim (one_ne_zero hone.symm)

#print axioms BlockCertificate.constant_one_block_certificate_sound

end BlockCertificate
