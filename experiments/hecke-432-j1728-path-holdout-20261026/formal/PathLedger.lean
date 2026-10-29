import Mathlib.Data.Nat.Basic

/- Generated from audit.json SHA-256 c67e34fdcee72932de2ffa4372a1c47019edabe8f256776c38d5b5ad41028fd9. Each triple is [x_C,y_C,x_E,y_E,x_B,y_B] over F_1367. -/
namespace P1367PathLedger

structure Row where
  triple : List Nat
  predicted : Nat
  observed : Nat
  deriving DecidableEq

def rows : List Row := [
  { triple := [286, 538, 95, 317, 695, 715], predicted := 2, observed := 2 },
  { triple := [286, 538, 95, 1050, 695, 652], predicted := 2, observed := 2 },
  { triple := [286, 538, 1362, 647, 1268, 66], predicted := 2, observed := 2 },
  { triple := [286, 538, 1362, 720, 1268, 1301], predicted := 2, observed := 2 },
  { triple := [920, 172, 315, 423, 370, 1095], predicted := 0, observed := 0 },
  { triple := [920, 172, 315, 944, 370, 272], predicted := 0, observed := 0 },
  { triple := [920, 172, 347, 0, 340, 0], predicted := 0, observed := 0 }
]

theorem seven_fibers : rows.length = 7 := by decide

theorem all_predictions_match : ∀ r ∈ rows, r.predicted = r.observed := by
  simp [rows]

theorem three_empty_fibers : (rows.filter (fun r => r.observed == 0)).length = 3 := by decide

theorem four_double_fibers : (rows.filter (fun r => r.observed == 2)).length = 4 := by decide

theorem eight_source_chains : (rows.map (·.observed)).sum = 8 := by decide

#print axioms seven_fibers
#print axioms all_predictions_match
#print axioms three_empty_fibers
#print axioms four_double_fibers
#print axioms eight_source_chains

end P1367PathLedger
