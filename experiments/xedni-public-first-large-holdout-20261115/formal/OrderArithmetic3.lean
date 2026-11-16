import PointDoubling2

namespace XedniPublicFirstLargeHoldout

/-- Tangent slope at 4G = (65,226) in the p=313 panel group. -/
theorem mod313_third_tangent_slope :
    ((3 * (65 : ZMod 313) ^ 2 - 1) / (2 * 226)) = 179 := by
  have hn : 3 * (65 : ZMod 313) ^ 2 - 1 = 154 := by
    calc
      3 * (65 : ZMod 313) ^ 2 - 1 = (12674 : ZMod 313) := by ring
      _ = 154 := (ZMod.natCast_eq_natCast_iff' 12674 154 313).mpr (by decide)
  have hd : 2 * (226 : ZMod 313) = 139 := by
    calc
      2 * (226 : ZMod 313) = (452 : ZMod 313) := by ring
      _ = 139 := (ZMod.natCast_eq_natCast_iff' 452 139 313).mpr (by decide)
  rw [hn, hd]
  apply (div_eq_iff (by decide : (139 : ZMod 313) ≠ 0)).2
  change (154 : ZMod 313) = (24881 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 154 24881 313).mpr (by decide)

/-- The third doubling gives x-coordinate 298. -/
theorem mod313_octuple_x : (179 : ZMod 313) ^ 2 - 65 - 65 = 298 := by
  calc
    (179 : ZMod 313) ^ 2 - 65 - 65 = (31911 : ZMod 313) := by ring
    _ = 298 := (ZMod.natCast_eq_natCast_iff' 31911 298 313).mpr (by decide)

/-- The third doubling gives y-coordinate 9. -/
theorem mod313_octuple_y :
    (-226 : ZMod 313) + -(179 * ((179 ^ 2) - 65 - 65 - 65)) = 9 := by
  calc
    (-226 : ZMod 313) + -(179 * ((179 ^ 2) - 65 - 65 - 65)) =
        (-5700660 : ZMod 313) := by ring
    _ = 9 := by
      change ((-5700660 : ℤ) : ZMod 313) = ((9 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-5700660) 9 313).mpr (by decide)

#print axioms mod313_third_tangent_slope
#print axioms mod313_octuple_x
#print axioms mod313_octuple_y

end XedniPublicFirstLargeHoldout
