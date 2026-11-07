import Mathlib.Tactic.Ring

namespace J1728QuadraticLocal

/-- Completing the square exposes the quadratic discriminant. -/
theorem quadratic_square_identity {R : Type*} [CommRing R] (x b c : R) :
    (2 * x + b) ^ 2 - (b ^ 2 - 4 * c) = 4 * (x ^ 2 + b * x + c) := by
  ring

#print axioms quadratic_square_identity

structure PlaceRow where
  residueDegree : Nat
  leftValuation : Nat
  rightValuation : Nat
  leftIndex : Nat
  rightIndex : Nat

def allEven (rows : List PlaceRow) : Bool :=
  rows.all fun row => row.leftValuation % 2 == 0 && row.rightValuation % 2 == 0

def allIndex (rows : List PlaceRow) : Bool :=
  rows.all fun row => row.leftIndex == row.leftValuation / 2 &&
                       row.rightIndex == row.rightValuation / 2

def weightedLeft (rows : List PlaceRow) : Nat :=
  rows.foldl (fun total row => total + row.residueDegree * row.leftValuation) 0

def weightedRight (rows : List PlaceRow) : Nat :=
  rows.foldl (fun total row => total + row.residueDegree * row.rightValuation) 0

def prime_7_places : List PlaceRow := [{ residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 2, leftIndex := 0, rightIndex := 1 }, { residueDegree := 2, leftValuation := 0, rightValuation := 2, leftIndex := 0, rightIndex := 1 }, { residueDegree := 2, leftValuation := 0, rightValuation := 2, leftIndex := 0, rightIndex := 1 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 2, rightValuation := 0, leftIndex := 1, rightIndex := 0 }, { residueDegree := 2, leftValuation := 2, rightValuation := 0, leftIndex := 1, rightIndex := 0 }, { residueDegree := 2, leftValuation := 2, rightValuation := 0, leftIndex := 1, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }]

/-- Exact quadratic discriminant parity and norm weights at rational prime 7. -/
theorem prime_7_table_check :
    allEven prime_7_places = true ∧
    allIndex prime_7_places = true ∧
    weightedLeft prime_7_places = 12 ∧
    weightedRight prime_7_places = 12 := by
  decide

#print axioms prime_7_table_check

def prime_11_places : List PlaceRow := [{ residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 2, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 2, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }]

/-- Exact quadratic discriminant parity and norm weights at rational prime 11. -/
theorem prime_11_table_check :
    allEven prime_11_places = true ∧
    allIndex prime_11_places = true ∧
    weightedLeft prime_11_places = 12 ∧
    weightedRight prime_11_places = 12 := by
  decide

#print axioms prime_11_table_check

def prime_23_places : List PlaceRow := [{ residueDegree := 1, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 1, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 1, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 1, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 2, leftValuation := 2, rightValuation := 2, leftIndex := 1, rightIndex := 1 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }]

/-- Exact quadratic discriminant parity and norm weights at rational prime 23. -/
theorem prime_23_table_check :
    allEven prime_23_places = true ∧
    allIndex prime_23_places = true ∧
    weightedLeft prime_23_places = 12 ∧
    weightedRight prime_23_places = 12 := by
  decide

#print axioms prime_23_table_check

def prime_31_places : List PlaceRow := [{ residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }, { residueDegree := 2, leftValuation := 0, rightValuation := 0, leftIndex := 0, rightIndex := 0 }]

/-- Exact quadratic discriminant parity and norm weights at rational prime 31. -/
theorem prime_31_table_check :
    allEven prime_31_places = true ∧
    allIndex prime_31_places = true ∧
    weightedLeft prime_31_places = 0 ∧
    weightedRight prime_31_places = 0 := by
  decide

#print axioms prime_31_table_check

end J1728QuadraticLocal
