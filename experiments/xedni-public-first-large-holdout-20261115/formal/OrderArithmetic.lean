import ConcreteCurveRecovery
import Mathlib.Tactic

namespace XedniPublicFirstLargeHoldout

/-- The tangent slope at (2,2) on the first panel curve, modulo 313. -/
theorem mod313_tangent_slope : (11 / 4 : ZMod 313) = 81 := by
  apply (div_eq_iff (by decide : (4 : ZMod 313) ≠ 0)).2
  change (11 : ZMod 313) = (324 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 11 324 313).mpr (by decide)

/-- The first doubled point has x-coordinate 297. -/
theorem mod313_double_x : (81 : ZMod 313) ^ 2 - 2 - 2 = 297 := by
  calc
    (81 : ZMod 313) ^ 2 - 2 - 2 = (6557 : ZMod 313) := by ring
    _ = 297 := (ZMod.natCast_eq_natCast_iff' 6557 297 313).mpr (by decide)

/-- The first doubled point has y-coordinate 204. -/
theorem mod313_double_y :
    (-2 : ZMod 313) + -(81 * ((81 ^ 2) - 2 - 2 - 2)) = 204 := by
  calc
    (-2 : ZMod 313) + -(81 * ((81 ^ 2) - 2 - 2 - 2)) =
        (-530957 : ZMod 313) := by ring
    _ = 204 := by
      change ((-530957 : ℤ) : ZMod 313) = ((204 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-530957) 204 313).mpr (by decide)

#print axioms mod313_tangent_slope
#print axioms mod313_double_x
#print axioms mod313_double_y

end XedniPublicFirstLargeHoldout
