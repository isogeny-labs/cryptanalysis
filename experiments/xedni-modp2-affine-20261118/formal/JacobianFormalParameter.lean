import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace XedniModP2Probe

/-- For nonzero projective denominator and ordinate, the formal parameter
`-x/y` of a Jacobian point `x = X/Z²`, `y = Y/Z³` equals `-XZ/Y`.
The statement is a rational-coordinate identity; its reduction modulo `p²`
also requires the respective integrality and unit hypotheses. -/
theorem jacobian_formal_parameter {K : Type*} [Field K]
    (X Y Z : K) (hY : Y ≠ 0) (hZ : Z ≠ 0) :
    -(X / Z ^ 2) / (Y / Z ^ 3) = -X * Z / Y := by
  field_simp

#print axioms jacobian_formal_parameter

end XedniModP2Probe
