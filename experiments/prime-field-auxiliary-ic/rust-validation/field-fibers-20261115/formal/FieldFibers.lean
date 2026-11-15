import Mathlib.Tactic.Ring

/- Algebraic identities for the compiled kernel, over arbitrary commutative
rings. They do not prove finite-field fiber completeness, primitive torus trace
selection, target-curve lifting, Semaev relation sufficiency, or runtime cost.
Build/axiom-audit status is recorded in the adjacent report. -/
namespace AuxiliaryIC.FieldFibers
variable {R : Type*} [CommRing R]

theorem opposite_pair (d c h r : R) :
    (d*r^2-c*r+h)*(d*(-r)^2-c*(-r)+h) =
    (h+r^2*d-c*r)*(h+r^2*d+c*r) := by ring

theorem cube_trace (u v : R) :
    (u+v)*((u+v)^2-3*(u*v)) = u^3+v^3 := by ring

theorem seventh_trace (u v : R) :
    (u+v)*((u+v)^6-7*(u*v)*((u+v)^2-u*v)^2) = u^7+v^7 := by ring

theorem torus_push (d c h z : R) :
    d^2*z^2-(c^2-2*d*h-4*d^2)*z+(h^2-2*(c^2-2*d*h)+4*d^2) =
    d^2*(z+2)^2-(c^2-2*d*h)*(z+2)+h^2 := by ring

theorem terminal_pair (d c h u v : R) :
    (d*u^2-c*u+h)*(d*v^2-c*v+h) =
    h^2-h*c*(u+v)+h*d*((u+v)^2-2*u*v)+c^2*(u*v)-c*d*(u*v)*(u+v)+d^2*(u*v)^2 := by ring

#print axioms opposite_pair
#print axioms cube_trace
#print axioms seventh_trace
#print axioms torus_push
#print axioms terminal_pair
end AuxiliaryIC.FieldFibers
