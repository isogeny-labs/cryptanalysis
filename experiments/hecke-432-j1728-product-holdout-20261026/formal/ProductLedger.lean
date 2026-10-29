import Mathlib.Data.Nat.Basic

/- Generated from audit.json SHA-256 7a2e4e9bc8b805b50a67f0f0a84a23daff0f1ec2deaa91b2c63d37369f177e98. Each triple is [x_C,y_C,x_E,y_E,x_B,y_B] over F_1439. -/
namespace P1439ProductLedger

structure Row where
  triple : List Nat
  paths27 : Nat
  factor16 : Nat
  predicted : Nat
  observed : Nat
  deriving DecidableEq

def rows : List Row := [
  { triple := [565, 949, 436, 538, 1404, 1093], paths27 := 0, factor16 := 1, predicted := 0, observed := 0 },
  { triple := [565, 949, 436, 901, 1404, 346], paths27 := 0, factor16 := 1, predicted := 0, observed := 0 },
  { triple := [565, 949, 919, 0, 653, 0], paths27 := 0, factor16 := 1, predicted := 0, observed := 0 },
  { triple := [789, 794, 188, 403, 155, 524], paths27 := 2, factor16 := 1, predicted := 2, observed := 2 },
  { triple := [789, 794, 188, 1036, 155, 915], paths27 := 2, factor16 := 1, predicted := 2, observed := 2 },
  { triple := [789, 794, 338, 267, 251, 1431], paths27 := 2, factor16 := 1, predicted := 2, observed := 2 },
  { triple := [789, 794, 338, 1172, 251, 8], paths27 := 2, factor16 := 1, predicted := 2, observed := 2 }
]

theorem seven_fibers : rows.length = 7 := by decide

theorem frozen_product_rule :
    ∀ r ∈ rows, r.predicted = r.paths27 * r.factor16 := by
  simp [rows]

theorem all_predictions_match : ∀ r ∈ rows, r.predicted = r.observed := by
  simp [rows]

theorem three_empty_fibers : (rows.filter (fun r => r.observed == 0)).length = 3 := by decide

theorem four_double_fibers : (rows.filter (fun r => r.observed == 2)).length = 4 := by decide

theorem eight_source_chains : (rows.map (·.observed)).sum = 8 := by decide

#print axioms seven_fibers
#print axioms frozen_product_rule
#print axioms all_predictions_match
#print axioms three_empty_fibers
#print axioms four_double_fibers
#print axioms eight_source_chains

end P1439ProductLedger
