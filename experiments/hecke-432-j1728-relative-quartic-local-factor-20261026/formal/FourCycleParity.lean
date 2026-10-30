import Mathlib.GroupTheory.Perm.Fin
import Mathlib.GroupTheory.Perm.Cycle.Basic

namespace J1728QuarticLocalFactor

theorem four_cycle_odd :
    Equiv.Perm.sign (Fin.cycleRange (Fin.last 3)) = -1 := by
  rw [Fin.sign_cycleRange]
  decide

theorem every_four_cycle_odd {α : Type*} [Fintype α] [DecidableEq α]
    (σ : Equiv.Perm α) (hcycle : σ.IsCycle) (hcard : σ.support.card = 4) :
    Equiv.Perm.sign σ = -1 := by
  rw [hcycle.sign, hcard]
  decide

#print axioms four_cycle_odd
#print axioms every_four_cycle_odd

end J1728QuarticLocalFactor
