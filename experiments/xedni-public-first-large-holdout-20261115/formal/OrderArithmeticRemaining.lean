import PointDoubling4

namespace XedniPublicFirstLargeHoldout

/-- Tangent slope at (211,223) in the p=313 panel group. -/
theorem mod313_fifth_tangent_slope :
    ((3 * (211 : ZMod 313) ^ 2 - 1) / (2 * 223)) = 117 := by
  have hn : 3 * (211 : ZMod 313) ^ 2 - 1 = 224 := by
    calc
      3 * (211 : ZMod 313) ^ 2 - 1 = (133562 : ZMod 313) := by ring
      _ = 224 := (ZMod.natCast_eq_natCast_iff' 133562 224 313).mpr (by decide)
  have hd : 2 * (223 : ZMod 313) = 133 := by
    calc
      2 * (223 : ZMod 313) = (446 : ZMod 313) := by ring
      _ = 133 := (ZMod.natCast_eq_natCast_iff' 446 133 313).mpr (by decide)
  rw [hn, hd]
  apply (div_eq_iff (by decide : (133 : ZMod 313) ≠ 0)).2
  change (224 : ZMod 313) = (15561 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 224 15561 313).mpr (by decide)

/-- The fifth doubling gives x-coordinate 121. -/
theorem mod313_thirtytwo_x : (117 : ZMod 313) ^ 2 - 211 - 211 = 121 := by
  calc
    (117 : ZMod 313) ^ 2 - 211 - 211 = (13267 : ZMod 313) := by ring
    _ = 121 := (ZMod.natCast_eq_natCast_iff' 13267 121 313).mpr (by decide)

/-- The fifth doubling gives y-coordinate 291. -/
theorem mod313_thirtytwo_y :
    (-223 : ZMod 313) + -(117 * ((117 ^ 2) - 211 - 211 - 211)) = 291 := by
  calc
    (-223 : ZMod 313) + -(117 * ((117 ^ 2) - 211 - 211 - 211)) =
        (-1527775 : ZMod 313) := by ring
    _ = 291 := by
      change ((-1527775 : ℤ) : ZMod 313) = ((291 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-1527775) 291 313).mpr (by decide)

#print axioms mod313_fifth_tangent_slope
#print axioms mod313_thirtytwo_x
#print axioms mod313_thirtytwo_y

/-- Tangent slope at (121,291) in the p=313 panel group. -/
theorem mod313_sixth_tangent_slope :
    ((3 * (121 : ZMod 313) ^ 2 - 1) / (2 * 291)) = 268 := by
  have hn : 3 * (121 : ZMod 313) ^ 2 - 1 = 102 := by
    calc
      3 * (121 : ZMod 313) ^ 2 - 1 = (43922 : ZMod 313) := by ring
      _ = 102 := (ZMod.natCast_eq_natCast_iff' 43922 102 313).mpr (by decide)
  have hd : 2 * (291 : ZMod 313) = 269 := by
    calc
      2 * (291 : ZMod 313) = (582 : ZMod 313) := by ring
      _ = 269 := (ZMod.natCast_eq_natCast_iff' 582 269 313).mpr (by decide)
  rw [hn, hd]
  apply (div_eq_iff (by decide : (269 : ZMod 313) ≠ 0)).2
  change (102 : ZMod 313) = (72092 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 102 72092 313).mpr (by decide)

/-- The sixth doubling gives x-coordinate 218. -/
theorem mod313_sixtyfour_x : (268 : ZMod 313) ^ 2 - 121 - 121 = 218 := by
  calc
    (268 : ZMod 313) ^ 2 - 121 - 121 = (71582 : ZMod 313) := by ring
    _ = 218 := (ZMod.natCast_eq_natCast_iff' 71582 218 313).mpr (by decide)

/-- The sixth doubling gives y-coordinate 5. -/
theorem mod313_sixtyfour_y :
    (-291 : ZMod 313) + -(268 * ((268 ^ 2) - 121 - 121 - 121)) = 5 := by
  calc
    (-291 : ZMod 313) + -(268 * ((268 ^ 2) - 121 - 121 - 121)) =
        (-19151839 : ZMod 313) := by ring
    _ = 5 := by
      change ((-19151839 : ℤ) : ZMod 313) = ((5 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-19151839) 5 313).mpr (by decide)

#print axioms mod313_sixth_tangent_slope
#print axioms mod313_sixtyfour_x
#print axioms mod313_sixtyfour_y

/-- Tangent slope at (218,5) in the p=313 panel group. -/
theorem mod313_seventh_tangent_slope :
    ((3 * (218 : ZMod 313) ^ 2 - 1) / (2 * 5)) = 266 := by
  have hn : 3 * (218 : ZMod 313) ^ 2 - 1 = 156 := by
    calc
      3 * (218 : ZMod 313) ^ 2 - 1 = (142571 : ZMod 313) := by ring
      _ = 156 := (ZMod.natCast_eq_natCast_iff' 142571 156 313).mpr (by decide)
  have hd : 2 * (5 : ZMod 313) = 10 := by
    calc
      2 * (5 : ZMod 313) = (10 : ZMod 313) := by ring
      _ = 10 := (ZMod.natCast_eq_natCast_iff' 10 10 313).mpr (by decide)
  rw [hn, hd]
  apply (div_eq_iff (by decide : (10 : ZMod 313) ≠ 0)).2
  change (156 : ZMod 313) = (2660 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 156 2660 313).mpr (by decide)

/-- The seventh doubling gives x-coordinate 208. -/
theorem mod313_onetwentyeight_x : (266 : ZMod 313) ^ 2 - 218 - 218 = 208 := by
  calc
    (266 : ZMod 313) ^ 2 - 218 - 218 = (70320 : ZMod 313) := by ring
    _ = 208 := (ZMod.natCast_eq_natCast_iff' 70320 208 313).mpr (by decide)

/-- The seventh doubling gives y-coordinate 151. -/
theorem mod313_onetwentyeight_y :
    (-5 : ZMod 313) + -(266 * ((266 ^ 2) - 218 - 218 - 218)) = 151 := by
  calc
    (-5 : ZMod 313) + -(266 * ((266 ^ 2) - 218 - 218 - 218)) =
        (-18647137 : ZMod 313) := by ring
    _ = 151 := by
      change ((-18647137 : ℤ) : ZMod 313) = ((151 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-18647137) 151 313).mpr (by decide)

#print axioms mod313_seventh_tangent_slope
#print axioms mod313_onetwentyeight_x
#print axioms mod313_onetwentyeight_y

/-- Tangent slope at (208,151) in the p=313 panel group. -/
theorem mod313_eighth_tangent_slope :
    ((3 * (208 : ZMod 313) ^ 2 - 1) / (2 * 151)) = 294 := by
  have hn : 3 * (208 : ZMod 313) ^ 2 - 1 = 209 := by
    calc
      3 * (208 : ZMod 313) ^ 2 - 1 = (129791 : ZMod 313) := by ring
      _ = 209 := (ZMod.natCast_eq_natCast_iff' 129791 209 313).mpr (by decide)
  have hd : 2 * (151 : ZMod 313) = 302 := by
    calc
      2 * (151 : ZMod 313) = (302 : ZMod 313) := by ring
      _ = 302 := (ZMod.natCast_eq_natCast_iff' 302 302 313).mpr (by decide)
  rw [hn, hd]
  apply (div_eq_iff (by decide : (302 : ZMod 313) ≠ 0)).2
  change (209 : ZMod 313) = (88788 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 209 88788 313).mpr (by decide)

/-- The eighth doubling gives x-coordinate 258. -/
theorem mod313_twofiftysix_x : (294 : ZMod 313) ^ 2 - 208 - 208 = 258 := by
  calc
    (294 : ZMod 313) ^ 2 - 208 - 208 = (86020 : ZMod 313) := by ring
    _ = 258 := (ZMod.natCast_eq_natCast_iff' 86020 258 313).mpr (by decide)

/-- The eighth doubling gives y-coordinate 173. -/
theorem mod313_twofiftysix_y :
    (-151 : ZMod 313) + -(294 * ((294 ^ 2) - 208 - 208 - 208)) = 173 := by
  calc
    (-151 : ZMod 313) + -(294 * ((294 ^ 2) - 208 - 208 - 208)) =
        (-25228879 : ZMod 313) := by ring
    _ = 173 := by
      change ((-25228879 : ℤ) : ZMod 313) = ((173 : ℤ) : ZMod 313)
      exact (ZMod.intCast_eq_intCast_iff' (-25228879) 173 313).mpr (by decide)

#print axioms mod313_eighth_tangent_slope
#print axioms mod313_twofiftysix_x
#print axioms mod313_twofiftysix_y

end XedniPublicFirstLargeHoldout

