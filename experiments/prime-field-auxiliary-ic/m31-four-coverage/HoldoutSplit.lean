import Mathlib.Tactic

namespace M31HoldoutSplit

/-- Allocations to one side of the absolute coefficients (2,2,2,1,1). -/
abbrev Allocation := Fin 3 × Fin 3 × Fin 3 × Fin 2 × Fin 2

def weight (s : Allocation) : Nat :=
  s.1.val + s.2.1.val + s.2.2.1.val + s.2.2.2.1.val + s.2.2.2.2.val

def balanced := Finset.univ.filter (fun s => weight s = 4)

/-- Choose the side containing the last unit coefficient, breaking exchange symmetry. -/
def representatives := balanced.filter (fun s => s.2.2.2.2 = 1)

def opposite (s : Allocation) : Allocation :=
  (Fin.rev s.1, Fin.rev s.2.1, Fin.rev s.2.2.1, Fin.rev s.2.2.2.1, Fin.rev s.2.2.2.2)

theorem splits : balanced.card = 26 ∧ representatives.card = 13 := by decide +kernel

theorem exchange : ∀ s : Allocation, opposite (opposite s) = s ∧ opposite s ≠ s ∧
    weight (opposite s) + weight s = 8 ∧
    ((opposite s).2.2.2.2 = 1 ↔ s.2.2.2.2 ≠ 1) := by decide +kernel

end M31HoldoutSplit
