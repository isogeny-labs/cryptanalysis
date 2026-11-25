import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.NormNum.Prime

namespace M31CensusAttribution

def smoothAt (bound x : ℕ) := ∀ q : ℕ, q.Prime → q ∣ x → q ≤ bound

/-- The archived second column lifts on the comparison curve and is excluded
by integer smoothness at bound 89. Its x coordinate is divisible by 107. -/
theorem excluded_column :
    (439352624 : ZMod 2147483647)^2 =
      (98625645 : ZMod 2147483647)^3 + 2*98625645+14 ∧
    ¬smoothAt 89 98625645 := by
  constructor
  · decide
  · intro h
    have bad := h 107 (by norm_num) (by decide)
    exact (by decide : ¬107 ≤ 89) bad

end M31CensusAttribution
