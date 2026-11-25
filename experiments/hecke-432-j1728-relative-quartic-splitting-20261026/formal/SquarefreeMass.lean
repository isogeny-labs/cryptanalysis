import Std

namespace J1728QuarticSquarefree

-- The first component records degree mass in simple residue factors;
-- the second records degree mass retained in repeated blocks.
def partitionMass : List (Nat × Nat) → Nat × Nat
  | [] => (0, 0)
  | (d, e) :: tail =>
      let rest := partitionMass tail
      if e = 1 then (d + rest.1, rest.2)
      else (rest.1, d * e + rest.2)

theorem partitionMass_total (factors : List (Nat × Nat)) :
    (partitionMass factors).1 + (partitionMass factors).2 =
      (factors.map fun x => x.1 * x.2).sum := by
  induction factors with
  | nil => simp [partitionMass]
  | cons pair tail ih =>
      obtain ⟨d, e⟩ := pair
      by_cases he : e = 1
      · simp [partitionMass, he, ih, Nat.add_left_comm, Nat.add_comm]
      · simp [partitionMass, he, ih, Nat.add_left_comm]

theorem selected_absolute_mass :
    96 + 48 = 144 ∧ 120 + 24 = 144 ∧
    96 + 48 = 144 ∧ 132 + 12 = 144 := by
  decide

#print axioms partitionMass_total
#print axioms selected_absolute_mass

end J1728QuarticSquarefree
