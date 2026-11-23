import Mathlib

namespace M31LiftHistory

private def parse (line : String) : Option (ℕ × ℕ × ℕ) := do
  let [h,b,n] := line.splitOn "," | none
  return (← h.toNat?, ← b.toNat?, ← n.toNat?)

private def data := (((include_str "history12.csv").trimAscii.toString.splitOn "\n").drop 1).toArray
private def entry (i : ℕ) := parse (data[i]?.getD "")
def count (h : Fin 4096) (b : Bool) : ℕ :=
  ((entry (2*h.val + b.toNat)).getD (0,0,0)).2.2

theorem completeTable : data.size = 8192 ∧
    ∀ i : Fin 8192, (entry i.val).any
      (fun row => row.1 == i.val/2 && row.2.1 == i.val%2 && row.2.2 ≥ 260209) := by
  native_decide

def score (f : Fin 4096 → Bool) := ∑ h, count h (f h)

theorem noPureHistory (h : Fin 4096) (b : Bool) : count h b ≥ 260209 := by
  have : ∀ x : Fin 4096, ∀ y : Bool, count x y ≥ 260209 := by native_decide
  exact this h b

theorem bestScore :
    IsGreatest (Set.range score) 1074925959 := by
  let m (h : Fin 4096) := max (count h false) (count h true)
  have exactSum : ∑ h, m h = 1074925959 := by native_decide
  constructor
  · refine ⟨fun h => decide (count h false ≤ count h true), ?_⟩
    rw [← exactSum]
    apply Finset.sum_congr rfl
    intro h _
    by_cases le : count h false ≤ count h true
    · simp [le, m]
    · simp [le, m, max_eq_left (le_of_not_ge le)]
  · rintro _ ⟨f,rfl⟩
    rw [← exactSum]
    apply Finset.sum_le_sum
    intro h _
    cases f h <;> simp [m]

theorem totalCount : (∑ h : Fin 4096, (count h false + count h true)) = 2147483647 := by native_decide

end M31LiftHistory
