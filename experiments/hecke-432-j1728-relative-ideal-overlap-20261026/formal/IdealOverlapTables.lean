import Mathlib.Tactic.NormNum

namespace J1728IdealOverlap

structure PlaceRow where
  residueDegree : Nat
  relativeValuation : Nat
  resultantValuation : Nat

def overlapCount (rows : List PlaceRow) : Nat :=
  (rows.filter fun row => decide (0 < row.relativeValuation ∧ 0 < row.resultantValuation)).length

def weightedRelative (rows : List PlaceRow) : Nat :=
  rows.foldl (fun total row => total + row.residueDegree * row.relativeValuation) 0

def weightedResultant (rows : List PlaceRow) : Nat :=
  rows.foldl (fun total row => total + row.residueDegree * row.resultantValuation) 0

def degree_4_prime_7 : List PlaceRow := [{ residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }]

/-- Exact saved valuation-table count and norm weights for degree 4 at 7. -/
theorem degree_4_prime_7_check :
    overlapCount degree_4_prime_7 = 0 ∧
    weightedRelative degree_4_prime_7 = 12 ∧
    weightedResultant degree_4_prime_7 = 6 := by
  decide

#print axioms degree_4_prime_7_check

def degree_4_prime_11 : List PlaceRow := [{ residueDegree := 1, relativeValuation := 4, resultantValuation := 4 }, { residueDegree := 1, relativeValuation := 0, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 4, resultantValuation := 4 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 2 }]

/-- Exact saved valuation-table count and norm weights for degree 4 at 11. -/
theorem degree_4_prime_11_check :
    overlapCount degree_4_prime_11 = 2 ∧
    weightedRelative degree_4_prime_11 = 12 ∧
    weightedResultant degree_4_prime_11 = 18 := by
  decide

#print axioms degree_4_prime_11_check

def degree_4_prime_23 : List PlaceRow := [{ residueDegree := 1, relativeValuation := 0, resultantValuation := 2 }, { residueDegree := 1, relativeValuation := 4, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 4, resultantValuation := 0 }]

/-- Exact saved valuation-table count and norm weights for degree 4 at 23. -/
theorem degree_4_prime_23_check :
    overlapCount degree_4_prime_23 = 0 ∧
    weightedRelative degree_4_prime_23 = 12 ∧
    weightedResultant degree_4_prime_23 = 12 := by
  decide

#print axioms degree_4_prime_23_check

def degree_4_prime_31 : List PlaceRow := [{ residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }]

/-- Exact saved valuation-table count and norm weights for degree 4 at 31. -/
theorem degree_4_prime_31_check :
    overlapCount degree_4_prime_31 = 0 ∧
    weightedRelative degree_4_prime_31 = 0 ∧
    weightedResultant degree_4_prime_31 = 0 := by
  decide

#print axioms degree_4_prime_31_check

def degree_8_prime_7 : List PlaceRow := [{ residueDegree := 2, relativeValuation := 2, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 3 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 3 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 3 }, { residueDegree := 2, relativeValuation := 6, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 6, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 6, resultantValuation := 0 }]

/-- Exact saved valuation-table count and norm weights for degree 8 at 7. -/
theorem degree_8_prime_7_check :
    overlapCount degree_8_prime_7 = 3 ∧
    weightedRelative degree_8_prime_7 = 48 ∧
    weightedResultant degree_8_prime_7 = 30 := by
  decide

#print axioms degree_8_prime_7_check

def degree_8_prime_11 : List PlaceRow := [{ residueDegree := 1, relativeValuation := 4, resultantValuation := 6 }, { residueDegree := 1, relativeValuation := 0, resultantValuation := 4 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 1 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 4, resultantValuation := 6 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 4 }]

/-- Exact saved valuation-table count and norm weights for degree 8 at 11. -/
theorem degree_8_prime_11_check :
    overlapCount degree_8_prime_11 = 2 ∧
    weightedRelative degree_8_prime_11 = 24 ∧
    weightedResultant degree_8_prime_11 = 36 := by
  decide

#print axioms degree_8_prime_11_check

def degree_8_prime_23 : List PlaceRow := [{ residueDegree := 1, relativeValuation := 8, resultantValuation := 0 }, { residueDegree := 1, relativeValuation := 0, resultantValuation := 4 }, { residueDegree := 2, relativeValuation := 4, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 4, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 4, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 8, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 4 }]

/-- Exact saved valuation-table count and norm weights for degree 8 at 23. -/
theorem degree_8_prime_23_check :
    overlapCount degree_8_prime_23 = 0 ∧
    weightedRelative degree_8_prime_23 = 48 ∧
    weightedResultant degree_8_prime_23 = 12 := by
  decide

#print axioms degree_8_prime_23_check

def degree_8_prime_31 : List PlaceRow := [{ residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 2, resultantValuation := 2 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }, { residueDegree := 2, relativeValuation := 0, resultantValuation := 0 }]

/-- Exact saved valuation-table count and norm weights for degree 8 at 31. -/
theorem degree_8_prime_31_check :
    overlapCount degree_8_prime_31 = 3 ∧
    weightedRelative degree_8_prime_31 = 12 ∧
    weightedResultant degree_8_prime_31 = 12 := by
  decide

#print axioms degree_8_prime_31_check

end J1728IdealOverlap
