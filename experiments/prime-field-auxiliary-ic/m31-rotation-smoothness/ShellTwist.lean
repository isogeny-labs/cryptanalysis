import Mathlib.Tactic

namespace SmoothTwist

/-- Each pair counts (target misses, target lifts). For each successive
smoothness bound, the two rows represent twist miss and twist lift.
Subtract the previous cumulative census to obtain disjoint shells. The
source counts are the four joint populations replayed in twist_counts.gp. -/
def cells : Fin 8 → ℕ × ℕ := ![
  (1331, 1220), (1219, 1298),
  (9557-1331, 9271-1220), (9208-1219, 9381-1298),
  (61985-9557, 61577-9271), (61619-9208, 61282-9381),
  (463771-61985, 462382-61577), (463698-61619, 463016-61282)]

def correct (predict : Fin 8 → Bool) : ℕ :=
  ∑ i, if predict i then (cells i).2 else (cells i).1

def majority (i : Fin 8) : Bool := decide ((cells i).1 < (cells i).2)

theorem best_possible (predict : Fin 8 → Bool) : correct predict ≤ 927642 := by
  calc
    correct predict ≤ ∑ i : Fin 8, max (cells i).1 (cells i).2 := by
      apply Finset.sum_le_sum
      intro i _
      cases predict i <;> simp
    _ = 927642 := by decide

theorem attained : correct majority = 927642 := by decide

theorem constant_miss : correct (fun _ => false) = 927469 := by decide

theorem population : ∑ i : Fin 8, ((cells i).1 + (cells i).2) = 1852867 := by decide

/-- Keep or discard each entire feature cell. Counts are conditional on
the enumerated population. -/
def retained (keep : Fin 8 → Bool) : ℕ :=
  ∑ i, if keep i then (cells i).2 else 0

def screened (keep : Fin 8 → Bool) : ℕ :=
  ∑ i, if keep i then (cells i).1 + (cells i).2 else 0

theorem precision_at_90 : ∀ keep : Fin 8 → Bool,
    10 * retained keep ≥ 9 * 925398 →
    retained keep * 1729727 ≤ 864226 * screened keep := by native_decide

theorem precision_at_90_attained :
    let keep : Fin 8 → Bool := ![false,true,false,true,true,false,true,true]
    retained keep = 864226 ∧ screened keep = 1729727 := by decide

#print axioms precision_at_90
#print axioms best_possible
#print axioms attained
end SmoothTwist
