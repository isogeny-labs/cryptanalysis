import OrderArithmeticRemaining

set_option maxRecDepth 4096

namespace XedniPublicFirstLargeHoldout

/-- The affine point at the fifth doubling coordinate. -/
def panel313ThirtyTwo : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (121 : ZMod 313)) (y := (291 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The fifth exact group-law edge of the p=313 order chain. -/
theorem panel313_fifth_double :
    panel313Sixteen + panel313Sixteen = panel313ThirtyTwo := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (223 : ZMod 313) ≠ -223 := by decide
  have hy : (223 : ZMod 313) ≠ (panelCurve 313).negY 211 223 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (211 : ZMod 313) 211 223 223 = 117 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_fifth_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (211 : ZMod 313) (223 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (211 : ZMod 313) (223 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (121 : ZMod 313) (291 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 211 211
          ((panelCurve 313).slope 211 211 223 223) = 121
      rw [hsl]
      change (117 : ZMod 313) ^ 2 - 211 - 211 = 121
      exact mod313_thirtytwo_x
    · change (panelCurve 313).addY 211 211 223
          ((panelCurve 313).slope 211 211 223 223) = 291
      rw [hsl]
      change (-223 : ZMod 313) + -(117 * ((117 ^ 2) - 211 - 211 - 211)) = 291
      exact mod313_thirtytwo_y

#print axioms panel313_fifth_double

/-- The affine point at the sixth doubling coordinate. -/
def panel313SixtyFour : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (218 : ZMod 313)) (y := (5 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The sixth exact group-law edge of the p=313 order chain. -/
theorem panel313_sixth_double :
    panel313ThirtyTwo + panel313ThirtyTwo = panel313SixtyFour := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (291 : ZMod 313) ≠ -291 := by decide
  have hy : (291 : ZMod 313) ≠ (panelCurve 313).negY 121 291 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (121 : ZMod 313) 121 291 291 = 268 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_sixth_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (121 : ZMod 313) (291 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (121 : ZMod 313) (291 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (218 : ZMod 313) (5 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 121 121
          ((panelCurve 313).slope 121 121 291 291) = 218
      rw [hsl]
      change (268 : ZMod 313) ^ 2 - 121 - 121 = 218
      exact mod313_sixtyfour_x
    · change (panelCurve 313).addY 121 121 291
          ((panelCurve 313).slope 121 121 291 291) = 5
      rw [hsl]
      change (-291 : ZMod 313) + -(268 * ((268 ^ 2) - 121 - 121 - 121)) = 5
      exact mod313_sixtyfour_y

#print axioms panel313_sixth_double

/-- The affine point at the seventh doubling coordinate. -/
def panel313OneTwentyEight : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (208 : ZMod 313)) (y := (151 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The seventh exact group-law edge of the p=313 order chain. -/
theorem panel313_seventh_double :
    panel313SixtyFour + panel313SixtyFour = panel313OneTwentyEight := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (5 : ZMod 313) ≠ -5 := by decide
  have hy : (5 : ZMod 313) ≠ (panelCurve 313).negY 218 5 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (218 : ZMod 313) 218 5 5 = 266 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_seventh_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (218 : ZMod 313) (5 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (218 : ZMod 313) (5 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (208 : ZMod 313) (151 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 218 218
          ((panelCurve 313).slope 218 218 5 5) = 208
      rw [hsl]
      change (266 : ZMod 313) ^ 2 - 218 - 218 = 208
      exact mod313_onetwentyeight_x
    · change (panelCurve 313).addY 218 218 5
          ((panelCurve 313).slope 218 218 5 5) = 151
      rw [hsl]
      change (-5 : ZMod 313) + -(266 * ((266 ^ 2) - 218 - 218 - 218)) = 151
      exact mod313_onetwentyeight_y

#print axioms panel313_seventh_double

/-- The affine point at the eighth doubling coordinate. -/
def panel313TwoFiftySix : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (258 : ZMod 313)) (y := (173 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The eighth exact group-law edge of the p=313 order chain. -/
theorem panel313_eighth_double :
    panel313OneTwentyEight + panel313OneTwentyEight = panel313TwoFiftySix := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (151 : ZMod 313) ≠ -151 := by decide
  have hy : (151 : ZMod 313) ≠ (panelCurve 313).negY 208 151 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (208 : ZMod 313) 208 151 151 = 294 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_eighth_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (208 : ZMod 313) (151 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (208 : ZMod 313) (151 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (258 : ZMod 313) (173 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 208 208
          ((panelCurve 313).slope 208 208 151 151) = 258
      rw [hsl]
      change (294 : ZMod 313) ^ 2 - 208 - 208 = 258
      exact mod313_twofiftysix_x
    · change (panelCurve 313).addY 208 208 151
          ((panelCurve 313).slope 208 208 151 151) = 173
      rw [hsl]
      change (-151 : ZMod 313) + -(294 * ((294 ^ 2) - 208 - 208 - 208)) = 173
      exact mod313_twofiftysix_y

#print axioms panel313_eighth_double

end XedniPublicFirstLargeHoldout

