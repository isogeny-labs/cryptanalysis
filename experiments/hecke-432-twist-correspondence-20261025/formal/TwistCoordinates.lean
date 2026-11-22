import Mathlib.Tactic.Ring

/-! The coordinate scaling used in the level-27 to level-432 twist probe. -/

namespace TwistCoordinates

variable {K : Type*} [Field K] [CharZero K]

theorem forward (i x y : K) (hi : i ^ 2 = -1)
    (hpoint : y ^ 2 + y = x ^ 3) :
    (-8 * i * (y + 1 / 2)) ^ 2 = (-4 * x) ^ 3 - 16 := by
  calc
    (-8 * i * (y + 1 / 2)) ^ 2 = 64 * i ^ 2 * (y + 1 / 2) ^ 2 := by ring
    _ = -64 * (y ^ 2 + y) - 16 := by rw [hi]; ring
    _ = (-4 * x) ^ 3 - 16 := by rw [hpoint]; ring

#print axioms forward

end TwistCoordinates
