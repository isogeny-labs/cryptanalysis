import PointDoubling

namespace XedniPublicFirstLargeHoldout

/-- Tangent slope at 2G = (297,204) in the p=313 panel group. -/
theorem mod313_second_tangent_slope :
    ((3 * (297 : ZMod 313) ^ 2 - 1) / (2 * 204)) = 242 := by
  have hn : 3 * (297 : ZMod 313) ^ 2 - 1 = 141 := by
    calc
      3 * (297 : ZMod 313) ^ 2 - 1 = (264626 : ZMod 313) := by ring
      _ = 141 := (ZMod.natCast_eq_natCast_iff' 264626 141 313).mpr (by decide)
  have hd : 2 * (204 : ZMod 313) = 95 := by
    calc
      2 * (204 : ZMod 313) = (408 : ZMod 313) := by ring
      _ = 95 := (ZMod.natCast_eq_natCast_iff' 408 95 313).mpr (by decide)
  rw [hn, hd]
  apply (div_eq_iff (by decide : (95 : ZMod 313) ≠ 0)).2
  change (141 : ZMod 313) = (22990 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 141 22990 313).mpr (by decide)

/-- The next doubling gives x-coordinate 65. -/
theorem mod313_quadruple_x : (242 : ZMod 313) ^ 2 - 297 - 297 = 65 := by
  calc
    (242 : ZMod 313) ^ 2 - 297 - 297 = (57970 : ZMod 313) := by ring
    _ = 65 := (ZMod.natCast_eq_natCast_iff' 57970 65 313).mpr (by decide)

/-- The next doubling gives y-coordinate 226. -/
theorem mod313_quadruple_y :
    (-204 : ZMod 313) + -(242 * ((242 ^ 2) - 297 - 297 - 297)) = 226 := by
  calc
    (-204 : ZMod 313) + -(242 * ((242 ^ 2) - 297 - 297 - 297)) =
        (-13957070 : ZMod 313) := by ring
    _ = 226 := by
      change ((-13957070 : ℤ) : ZMod 313) = ((226 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-13957070) 226 313).mpr (by decide)

#print axioms mod313_second_tangent_slope
#print axioms mod313_quadruple_x
#print axioms mod313_quadruple_y

end XedniPublicFirstLargeHoldout
