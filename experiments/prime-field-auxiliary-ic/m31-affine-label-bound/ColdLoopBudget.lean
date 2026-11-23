import Mathlib

namespace M31ColdLoopBudget

/-- Times in microseconds. Keep cold wall time outside the measured loop fixed.
The bounds allow half a unit in the last displayed digit of each loop timer,
and round the archived cold total down and rho up to integer microseconds. -/
theorem seedZero (cold oldLoop rho newLoop : ℝ)
    (hc : 9685107 ≤ cold) (hl : oldLoop ≤ 9676515) (hr : rho ≤ 7092)
    (hn : 0 ≤ newLoop) : rho + 1500 ≤ cold - oldLoop + newLoop := by
  linarith

/-- For seeds one and two, an unchanged residual forces a large reduction
in total loop time even if the number of processed queries can change. -/
theorem remainingSeeds (cold oldLoop rho newLoop : ℝ)
    (parity : cold - oldLoop + newLoop ≤ rho)
    (record :
      (5167235 ≤ cold ∧ 5160075 ≤ oldLoop ∧ oldLoop ≤ 5160085 ∧ rho ≤ 21869) ∨
      (11667566 ≤ cold ∧ 11662550 ≤ oldLoop ∧ oldLoop ≤ 11662650 ∧ rho ≤ 18319)) :
    (newLoop ≤ 14719 ∧ 350 * newLoop < oldLoop) ∧
    (11667566 ≤ cold → newLoop ≤ 13403 ∧ 870 * newLoop < oldLoop) := by
  rcases record with h | h <;> constructor
  all_goals first | constructor <;> linarith | intro hc; constructor <;> linarith

end M31ColdLoopBudget
