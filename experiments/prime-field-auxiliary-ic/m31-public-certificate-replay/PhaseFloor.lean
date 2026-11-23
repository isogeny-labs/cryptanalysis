import Mathlib

namespace M31ArchivedPhaseFloor

/-- Times in tenths of a microsecond. These scalar bounds are taken from
the minimum IC phase times and maximum rho time in the archived panel. -/
theorem independentFloors (pair search rho : ℚ)
    (hp : 601040 ≤ pair) (hs : 4351190 ≤ search) (hr : rho ≤ 200969) :
    (299 : ℚ)/100 * rho < pair ∧ (2165 : ℚ)/100 * rho < search := by
  constructor <;> linarith

/-- Even granting zero cost to every other phase, retaining either measured
phase prevents parity anywhere in this panel. -/
theorem unchangedPhase (pair search rho other : ℚ)
    (hp : 601040 ≤ pair) (hs : 4351190 ≤ search) (hr : rho ≤ 200969)
    (ho : 0 ≤ other) : rho < pair + other ∧ rho < search + other := by
  constructor <;> linarith

end M31ArchivedPhaseFloor
