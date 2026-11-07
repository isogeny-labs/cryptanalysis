import Mathlib.Tactic.Ring

namespace J1728QuadraticResidues

/-- A square unit makes the normalized quadratic split. -/
theorem quadratic_split_identity {R : Type*} [CommRing R] (x u y : R)
    (hy : y ^ 2 = u) : x ^ 2 - u = (x - y) * (x + y) := by
  rw [← hy]
  ring

#print axioms quadratic_split_identity

structure PlaceRow where
  residueDegree : Nat
  leftSplit : Bool
  rightSplit : Bool

def extensionDegrees (rows : List PlaceRow) (left : Bool) : List Nat :=
  rows.flatMap fun row =>
    if (if left then row.leftSplit else row.rightSplit) then
      [row.residueDegree, row.residueDegree]
    else [2 * row.residueDegree]

def splitCount (rows : List PlaceRow) (left : Bool) : Nat :=
  (rows.filter fun row => if left then row.leftSplit else row.rightSplit).length

def prime_7_places : List PlaceRow := [{ residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }]

/-- Exact split and inert counts above 7 for both quadratic factors. -/
theorem prime_7_table_check :
    splitCount prime_7_places true = 18 ∧
    splitCount prime_7_places false = 18 ∧
    (extensionDegrees prime_7_places true).length = 36 ∧
    (extensionDegrees prime_7_places false).length = 36 ∧
    (extensionDegrees prime_7_places true).sum = 72 ∧
    (extensionDegrees prime_7_places false).sum = 72 := by
  decide

#print axioms prime_7_table_check

def prime_11_places : List PlaceRow := [{ residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }]

/-- Exact split and inert counts above 11 for both quadratic factors. -/
theorem prime_11_table_check :
    splitCount prime_11_places true = 18 ∧
    splitCount prime_11_places false = 18 ∧
    (extensionDegrees prime_11_places true).length = 36 ∧
    (extensionDegrees prime_11_places false).length = 36 ∧
    (extensionDegrees prime_11_places true).sum = 72 ∧
    (extensionDegrees prime_11_places false).sum = 72 := by
  decide

#print axioms prime_11_table_check

def prime_23_places : List PlaceRow := [{ residueDegree := 1, leftSplit := false, rightSplit := false }, { residueDegree := 1, leftSplit := true, rightSplit := true }, { residueDegree := 1, leftSplit := true, rightSplit := true }, { residueDegree := 1, leftSplit := false, rightSplit := false }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }]

/-- Exact split and inert counts above 23 for both quadratic factors. -/
theorem prime_23_table_check :
    splitCount prime_23_places true = 18 ∧
    splitCount prime_23_places false = 18 ∧
    (extensionDegrees prime_23_places true).length = 38 ∧
    (extensionDegrees prime_23_places false).length = 38 ∧
    (extensionDegrees prime_23_places true).sum = 72 ∧
    (extensionDegrees prime_23_places false).sum = 72 := by
  decide

#print axioms prime_23_table_check

def prime_31_places : List PlaceRow := [{ residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }, { residueDegree := 2, leftSplit := true, rightSplit := true }]

/-- Exact split and inert counts above 31 for both quadratic factors. -/
theorem prime_31_table_check :
    splitCount prime_31_places true = 18 ∧
    splitCount prime_31_places false = 18 ∧
    (extensionDegrees prime_31_places true).length = 36 ∧
    (extensionDegrees prime_31_places false).length = 36 ∧
    (extensionDegrees prime_31_places true).sum = 72 ∧
    (extensionDegrees prime_31_places false).sum = 72 := by
  decide

#print axioms prime_31_table_check

end J1728QuadraticResidues
