import PointDoublingRemaining

namespace XedniPublicFirstLargeHoldout

/-- Slope for the addition yielding 320G. -/
theorem mod313_add320_slope :
    (((173 : ZMod 313) - 5) / ((258 : ZMod 313) - 218)) = 192 := by
  have hd : ((258 : ZMod 313) - 218) ≠ 0 := by decide
  apply (div_eq_iff hd).2
  calc
    ((173 : ZMod 313) - 5) = ((168 : ℤ) : ZMod 313) := by ring
    _ = ((7680 : ℤ) : ZMod 313) :=
      (ZMod.intCast_eq_intCast_iff' 168 7680 313).mpr (by decide)
    _ = 192 * ((258 : ZMod 313) - 218) := by ring

/-- X-coordinate of 320G. -/
theorem mod313_add320_x :
    (192 : ZMod 313) ^ 2 - 258 - 218 = 80 := by
  calc
    (192 : ZMod 313) ^ 2 - 258 - 218 = ((36388 : ℤ) : ZMod 313) := by ring
    _ = 80 := (ZMod.intCast_eq_intCast_iff' 36388 80 313).mpr (by decide)

/-- Y-coordinate of 320G. -/
theorem mod313_add320_y :
    (-173 : ZMod 313) + -(192 * ((192 ^ 2) - 258 - 218 - 258)) = 199 := by
  calc
    (-173 : ZMod 313) + -(192 * ((192 ^ 2) - 258 - 218 - 258)) =
      ((-6937133 : ℤ) : ZMod 313) := by ring
    _ = 199 := (ZMod.intCast_eq_intCast_iff' (-6937133) 199 313).mpr (by decide)

#print axioms mod313_add320_slope
#print axioms mod313_add320_x
#print axioms mod313_add320_y

/-- Slope for the addition yielding 328G. -/
theorem mod313_add328_slope :
    (((199 : ZMod 313) - 9) / ((80 : ZMod 313) - 298)) = 2 := by
  have hd : ((80 : ZMod 313) - 298) ≠ 0 := by decide
  apply (div_eq_iff hd).2
  calc
    ((199 : ZMod 313) - 9) = ((190 : ℤ) : ZMod 313) := by ring
    _ = ((-436 : ℤ) : ZMod 313) :=
      (ZMod.intCast_eq_intCast_iff' 190 (-436) 313).mpr (by decide)
    _ = 2 * ((80 : ZMod 313) - 298) := by ring

/-- X-coordinate of 328G. -/
theorem mod313_add328_x :
    (2 : ZMod 313) ^ 2 - 80 - 298 = 252 := by
  calc
    (2 : ZMod 313) ^ 2 - 80 - 298 = ((-374 : ℤ) : ZMod 313) := by ring
    _ = 252 := (ZMod.intCast_eq_intCast_iff' (-374) 252 313).mpr (by decide)

/-- Y-coordinate of 328G. -/
theorem mod313_add328_y :
    (-199 : ZMod 313) + -(2 * ((2 ^ 2) - 80 - 298 - 80)) = 83 := by
  calc
    (-199 : ZMod 313) + -(2 * ((2 ^ 2) - 80 - 298 - 80)) =
      ((709 : ℤ) : ZMod 313) := by ring
    _ = 83 := (ZMod.intCast_eq_intCast_iff' 709 83 313).mpr (by decide)

#print axioms mod313_add328_slope
#print axioms mod313_add328_x
#print axioms mod313_add328_y

/-- Slope for the addition yielding 330G. -/
theorem mod313_add330_slope :
    (((83 : ZMod 313) - 204) / ((252 : ZMod 313) - 297)) = 267 := by
  have hd : ((252 : ZMod 313) - 297) ≠ 0 := by decide
  apply (div_eq_iff hd).2
  calc
    ((83 : ZMod 313) - 204) = ((-121 : ℤ) : ZMod 313) := by ring
    _ = ((-12015 : ℤ) : ZMod 313) :=
      (ZMod.intCast_eq_intCast_iff' (-121) (-12015) 313).mpr (by decide)
    _ = 267 * ((252 : ZMod 313) - 297) := by ring

/-- X-coordinate of 330G. -/
theorem mod313_add330_x :
    (267 : ZMod 313) ^ 2 - 252 - 297 = 2 := by
  calc
    (267 : ZMod 313) ^ 2 - 252 - 297 = ((70740 : ℤ) : ZMod 313) := by ring
    _ = 2 := (ZMod.intCast_eq_intCast_iff' 70740 2 313).mpr (by decide)

/-- Y-coordinate of 330G. -/
theorem mod313_add330_y :
    (-83 : ZMod 313) + -(267 * ((267 ^ 2) - 252 - 297 - 252)) = 311 := by
  calc
    (-83 : ZMod 313) + -(267 * ((267 ^ 2) - 252 - 297 - 252)) =
      ((-18820379 : ℤ) : ZMod 313) := by ring
    _ = 311 := (ZMod.intCast_eq_intCast_iff' (-18820379) 311 313).mpr (by decide)

#print axioms mod313_add330_slope
#print axioms mod313_add330_x
#print axioms mod313_add330_y

end XedniPublicFirstLargeHoldout

