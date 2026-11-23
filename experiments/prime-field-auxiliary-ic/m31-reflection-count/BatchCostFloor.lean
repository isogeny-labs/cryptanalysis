import Std.Tactic

namespace M31Reflection.BatchCostFloor

/-- End-to-end seconds from efb9330c1, field31_s5_base0,
{v2_batch,rho}_seed{0,1,2}.audited.json. Scaling each archived decimal
by 10^18 preserves its value. The scale does not imply timer precision. -/
def archived : Fin 3 → Nat × Nat
  | 0 => (9685107568999229000, 7091595000019879)
  | 1 => (5167235504999553000, 21868216999791912)
  | 2 => (11667566436000925000, 18318452001039986)

def floorRatio : Fin 3 → Nat
  | 0 => 330
  | 1 => 57
  | 2 => 154

/-- Conditional cost model. Both versions pay the same remaining cost.
The 4.13 factor is a hypothesis about the component. -/
theorem whole_cost (oldPart newPart other : Nat)
    (h : 100 * oldPart ≤ 413 * newPart) :
    100 * (oldPart + other) ≤ 413 * (newPart + other) := by omega

theorem archived_gap (i : Fin 3) :
    413 * (floorRatio i * (archived i).2) < 100 * (archived i).1 := by
  revert i
  decide

/-- Each hypothetical new total still exceeds its seed-specific multiple
of the measured same-target rho time. -/
theorem residual_gap (i : Fin 3) (oldPart newPart other : Nat)
    (total : oldPart + other = (archived i).1)
    (cap : 100 * oldPart ≤ 413 * newPart) :
    floorRatio i * (archived i).2 < newPart + other := by
  have h := whole_cost oldPart newPart other cap
  rw [total] at h
  have g := archived_gap i
  omega

#print axioms residual_gap

/-- The recorded linear_seconds values for the same three batch runs, in
the same integer units as archived. -/
def linearTime : Fin 3 → Nat
  | 0 => 46553000000000
  | 1 => 33548000000000
  | 2 => 21488000000000

/-- With the query stream held fixed, the entire recorded linear phase
accounts for less than 6.5 parts per million of each end-to-end time. -/
theorem linear_share (i : Fin 3) :
    2000000 * linearTime i < 13 * (archived i).1 := by
  revert i
  decide

#print axioms linear_share
end M31Reflection.BatchCostFloor
