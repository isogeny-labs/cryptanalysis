import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace TorsionFiber

theorem same_parent {K : Type*} [Field K] (a b u v : K) (hu : u ≠ 0) (hv : v ≠ 0) :
    u + a + b/u = v + a + b/v ↔ u = v ∨ u*v = b := by
  have identity : (u + a + b/u - (v + a + b/v)) * (u*v) = (u-v)*(u*v-b) := by
    field_simp
    ring
  constructor
  · intro h
    rw [h, sub_self, zero_mul] at identity
    simpa only [mul_eq_zero, sub_eq_zero] using identity.symm
  · intro h
    have hz : (u-v)*(u*v-b) = 0 := by
      simpa only [mul_eq_zero, sub_eq_zero] using h
    rw [hz] at identity
    exact sub_eq_zero.mp ((mul_eq_zero.mp identity).resolve_right (mul_ne_zero hu hv))

theorem scaled_sibling_keys {K : Type*} [Field K] (s u b : K) (hu : u ≠ 0) :
    (s*u)^31 * (s*(b/u))^31 = (s^2*b)^31 := by
  rw [← mul_pow]
  congr 1
  field_simp

end TorsionFiber
#print axioms TorsionFiber.same_parent
#print axioms TorsionFiber.scaled_sibling_keys
