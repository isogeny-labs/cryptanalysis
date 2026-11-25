import Mathlib.Tactic

namespace M31FiberRecurrence

def tr {K : Type*} [Field K] (x : K) := x + x⁻¹

theorem next_trace {K : Type*} [Field K] {z w : K} (hz : z ≠ 0) (hw : w ≠ 0) :
    tr w * tr (z*w) - tr z = tr (z*w^2) := by
  unfold tr
  field_simp
  ring

theorem same_fiber {K : Type*} [Field K] (z w : K) (period k : Nat)
    (hw : w ^ period = 1) :
    tr ((z * w^k)^period) = tr (z^period) := by
  rw [mul_pow, ← pow_mul, Nat.mul_comm k period, pow_mul, hw, one_pow, mul_one]

end M31FiberRecurrence
