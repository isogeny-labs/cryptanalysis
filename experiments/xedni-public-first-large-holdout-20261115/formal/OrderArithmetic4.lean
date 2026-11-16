import PointDoubling3

namespace XedniPublicFirstLargeHoldout

/-- Tangent slope at 8G = (298,9) in the p=313 panel group. -/
theorem mod313_fourth_tangent_slope :
    ((3 * (298 : ZMod 313) ^ 2 - 1) / (2 * 9)) = 107 := by
  have hn : 3 * (298 : ZMod 313) ^ 2 - 1 = 48 := by
    calc
      3 * (298 : ZMod 313) ^ 2 - 1 = (266411 : ZMod 313) := by ring
      _ = 48 := (ZMod.natCast_eq_natCast_iff' 266411 48 313).mpr (by decide)
  change (48 : ZMod 313) / 18 = 107
  apply (div_eq_iff (by decide : (18 : ZMod 313) ≠ 0)).2
  change (48 : ZMod 313) = (1926 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 48 1926 313).mpr (by decide)

/-- The fourth doubling gives x-coordinate 211. -/
theorem mod313_sixteen_x : (107 : ZMod 313) ^ 2 - 298 - 298 = 211 := by
  calc
    (107 : ZMod 313) ^ 2 - 298 - 298 = (10853 : ZMod 313) := by ring
    _ = 211 := (ZMod.natCast_eq_natCast_iff' 10853 211 313).mpr (by decide)

/-- The fourth doubling gives y-coordinate 223. -/
theorem mod313_sixteen_y :
    (-9 : ZMod 313) + -(107 * ((107 ^ 2) - 298 - 298 - 298)) = 223 := by
  calc
    (-9 : ZMod 313) + -(107 * ((107 ^ 2) - 298 - 298 - 298)) =
        (-1129394 : ZMod 313) := by ring
    _ = 223 := by
      change ((-1129394 : ℤ) : ZMod 313) = ((223 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-1129394) 223 313).mpr (by decide)

#print axioms mod313_fourth_tangent_slope
#print axioms mod313_sixteen_x
#print axioms mod313_sixteen_y

end XedniPublicFirstLargeHoldout
