import Mathlib

/-- Conservative bounds on the archived basis charge and total time suffice
even if the complete basis charge is removed. Durations are seconds. -/
theorem preparationCeiling (basis total saved : ℚ) (hb : basis ≤ 1155 / 1000000)
    (ht : 5167/1000 ≤ total) (hs : saved ≤ basis) :
    saved/total < 23/100000 := by
  have hp : 0 < total := by linarith
  rw [div_lt_iff₀ hp]
  linarith
