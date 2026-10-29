import Mathlib.Tactic.NormNum

namespace J1728QuarticLocalTables

structure PlaceRow where
  residueDegree : Nat
  leftPolynomialValuation : Nat
  rightPolynomialValuation : Nat

def allEven (rows : List PlaceRow) : Bool :=
  rows.all fun row => row.leftPolynomialValuation % 2 == 0 &&
                       row.rightPolynomialValuation % 2 == 0

def positiveCount (rows : List PlaceRow) (left : Bool) : Nat :=
  (rows.filter fun row => if left then 0 < row.leftPolynomialValuation
                         else 0 < row.rightPolynomialValuation).length

def weightedIndex (rows : List PlaceRow) (left : Bool) : Nat :=
  rows.foldl (fun total row => total + row.residueDegree *
    (if left then row.leftPolynomialValuation / 2
     else row.rightPolynomialValuation / 2)) 0

def prime_7_places : List PlaceRow := [{ residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 4 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 4 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 4 }, { residueDegree := 2, leftPolynomialValuation := 4, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 4, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 4, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }]

/-- Exact local index table at rational prime 7, given zero maximal discriminant. -/
theorem prime_7_index_table :
    allEven prime_7_places = true ∧
    positiveCount prime_7_places true = 9 ∧
    positiveCount prime_7_places false = 9 ∧
    weightedIndex prime_7_places true = 24 ∧
    weightedIndex prime_7_places false = 24 := by
  decide

#print axioms prime_7_index_table

def prime_11_places : List PlaceRow := [{ residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }]

/-- Exact local index table at rational prime 11, given zero maximal discriminant. -/
theorem prime_11_index_table :
    allEven prime_11_places = true ∧
    positiveCount prime_11_places true = 6 ∧
    positiveCount prime_11_places false = 6 ∧
    weightedIndex prime_11_places true = 12 ∧
    weightedIndex prime_11_places false = 12 := by
  decide

#print axioms prime_11_index_table

def prime_23_places : List PlaceRow := [{ residueDegree := 1, leftPolynomialValuation := 4, rightPolynomialValuation := 4 }, { residueDegree := 1, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 1, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 1, leftPolynomialValuation := 4, rightPolynomialValuation := 4 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 4, rightPolynomialValuation := 4 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 4, rightPolynomialValuation := 4 }]

/-- Exact local index table at rational prime 23, given zero maximal discriminant. -/
theorem prime_23_index_table :
    allEven prime_23_places = true ∧
    positiveCount prime_23_places true = 10 ∧
    positiveCount prime_23_places false = 10 ∧
    weightedIndex prime_23_places true = 24 ∧
    weightedIndex prime_23_places false = 24 := by
  decide

#print axioms prime_23_index_table

def prime_31_places : List PlaceRow := [{ residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 2 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 2, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }, { residueDegree := 2, leftPolynomialValuation := 0, rightPolynomialValuation := 0 }]

/-- Exact local index table at rational prime 31, given zero maximal discriminant. -/
theorem prime_31_index_table :
    allEven prime_31_places = true ∧
    positiveCount prime_31_places true = 3 ∧
    positiveCount prime_31_places false = 3 ∧
    weightedIndex prime_31_places true = 6 ∧
    weightedIndex prime_31_places false = 6 := by
  decide

#print axioms prime_31_index_table

end J1728QuarticLocalTables
