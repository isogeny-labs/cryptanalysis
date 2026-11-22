import Mathlib
namespace TwistJoint
theorem product {F : Type*} [CommRing F] (x : F) :
    (x^3+2*x+14)*(x^3+2*x-14) =
    (x^2)^3+4*(x^2)^2+4*x^2-196 := by ring
theorem reciprocal {F : Type*} [Field F] (u : F) (h : u ≠ 0) :
    u*(u^3+4*u^2+4*u-196) =
    u^4*(1+4/u+4/u^2-196/u^3) := by field_simp
theorem reflected {F : Type*} [CommRing F] (x : F) :
    (-x)^3 + 2*(-x) - 14 = -(x^3+2*x+14) := by ring
end TwistJoint
