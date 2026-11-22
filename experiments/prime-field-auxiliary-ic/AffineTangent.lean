import Mathlib.Tactic.Ring

namespace AffineTangent
variable {F : Type*} [CommRing F]

/-- The affine tangent update preserves the short Weierstrass equation. -/
theorem tangent_on_curve (a b x y m : F) (point : y^2 = x^3 + a*x + b)
    (tangent : (2*y)*m = 3*x^2+a) :
    let u := m^2-2*x
    (m*(x-u)-y)^2 = u^3+a*u+b := by
  dsimp
  calc
    _ = (m^2-2*x)^3+a*(m^2-2*x)+b +
        (y^2-(x^3+a*x+b)) + (m^2-3*x)*((2*y)*m-(3*x^2+a)) := by ring
    _ = _ := by rw [point,tangent]; ring

#print axioms tangent_on_curve
end AffineTangent
