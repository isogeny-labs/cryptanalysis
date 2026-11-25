import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace HalfWalk

/-- Affine addition of (x,y) and (0,0) has slope y/x on y²=x³+x. -/
theorem translate {K : Type*} [Field K] (x y : K) (hx : x ≠ 0)
    (hy : y^2 = x^3+x) :
    (y/x)^2-x = x⁻¹ ∧ (y/x)*(x-x⁻¹)-y = -y/x^2 := by
  constructor
  · rw [div_pow, hy]
    field_simp
    ring
  · field_simp
    ring

/-- The second half of the coset has exactly the original order translated
by the midpoint. Adding the midpoint once more closes the walk. -/
theorem second_half {G : Type*} [AddCommGroup G] (t g : G) (h i : ℕ)
    (closure : (2*h) • g = 0) :
    t + (h+i) • g = (t+i • g) + h • g ∧ (t+h • g) + h • g = t := by
  constructor
  · rw [add_nsmul]
    rw [add_comm (h • g) (i • g), add_assoc]
  · rw [two_mul, add_nsmul] at closure
    rw [add_assoc, closure, add_zero]

/-- Each backward pass emits the inverse of the current entry and
recovers the inverse of the preceding prefix. -/
theorem backward {K : Type*} [Field K] (a x : K) (ha : a ≠ 0) (hx : x ≠ 0) :
    a*(a*x)⁻¹ = x⁻¹ ∧ x*(a*x)⁻¹ = a⁻¹ := by
  constructor <;> field_simp

end HalfWalk
#print axioms HalfWalk.translate
#print axioms HalfWalk.second_half
#print axioms HalfWalk.backward
