import Mathlib.Tactic
import ArchiveData

namespace M31ArchiveCheck
open M31ArchiveData

theorem fixture_identity :
    archived.length = 17 ∧ public71.length = 71 ∧
    archived.Nodup ∧ public71.Nodup ∧
    archived.filter (fun point => public71.contains point) = [(3,417540811)] := by
  decide +kernel

-- Each pair contains a lower bound on total ns and an upper bound on removable ns.
theorem rounded_bounds :
    timingBounds.all (fun (total, removed) =>
      0 < total && 1000427 * removed < 427 * total) := by
  decide +kernel

theorem deletion_bound (bounds : Nat × Nat) (row : bounds ∈ timingBounds)
    (total removed : ℚ) (floor_total : (bounds.1 : ℚ) ≤ total)
    (ceil_removed : removed ≤ (bounds.2 : ℚ)) :
    total / (total - removed) < 1000427 / 1000000 := by
  have good := List.all_eq_true.mp rounded_bounds bounds row
  simp only [Bool.and_eq_true, decide_eq_true_eq] at good
  have pos : (0 : ℚ) < bounds.1 := by exact_mod_cast good.1
  have share : 1000427 * (bounds.2 : ℚ) < 427 * (bounds.1 : ℚ) := by
    exact_mod_cast good.2
  apply (div_lt_iff₀ (show 0 < total - removed by linarith)).2
  linarith

end M31ArchiveCheck
