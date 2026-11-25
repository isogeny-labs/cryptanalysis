import Mathlib.Tactic

namespace M31ProjectiveKernel
variable {F : Type*} [Field F]

theorem affine_double (a b x y : F)
    (h : y^2 = x^3+a*x^2+b*x) (hn : 2*y ≠ 0) :
    ((3*x^2+2*a*x+b)/(2*y))^2-a-2*x =
      (x^2-b)^2/(2*y)^2 := by
  generalize hd : 2*y = d at hn ⊢
  field_simp [hn]
  rw [← hd]
  linear_combination (-(4*a+8*x)) * h

theorem homogeneous (a b x z : F) :
    ((x*z)^2-b*z^2)^2 = (x^2-b)^2*z^4 ∧
    4*(x*z)*z*((x*z)^2+a*(x*z)*z+b*z^2) = 4*(x^3+a*x^2+b*x)*z^4 := by
  constructor <;> ring

theorem terminal_test (a b x y z : F) (hz : z ≠ 0)
    (h : y^2 = x^3+a*x^2+b*x) :
    (x*z)*((x*z)^2+a*(x*z)*z+b*z^2) = 0 ↔ y = 0 := by
  rw [show (x*z)*((x*z)^2+a*(x*z)*z+b*z^2) = y^2*z^3 by rw [h]; ring]
  simp [hz]

end M31ProjectiveKernel
