import OrderAddition

set_option maxRecDepth 4096

namespace XedniPublicFirstLargeHoldout

/-- The affine point at 320G. -/
def panel313ThreeTwenty : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (80 : ZMod 313)) (y := (199 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- Exact group-law addition yielding 320G. -/
theorem panel313_add320 :
    panel313TwoFiftySix + panel313SixtyFour = panel313ThreeTwenty := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hx : (258 : ZMod 313) ≠ 218 := by decide
  have hsl : (panelCurve 313).slope (258 : ZMod 313) 218 173 5 = 192 := by
    rw [WeierstrassCurve.Affine.slope_of_X_ne hx]
    exact mod313_add320_slope
  change WeierstrassCurve.Affine.Point.some (258 : ZMod 313) (173 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (218 : ZMod 313) (5 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (80 : ZMod 313) (199 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_of_X_ne hx]
  · congr 1
    · change (panelCurve 313).addX 258 218
          ((panelCurve 313).slope 258 218 173 5) = 80
      rw [hsl]
      change (192 : ZMod 313) ^ 2 - 258 - 218 = 80
      exact mod313_add320_x
    · change (panelCurve 313).addY 258 218 173
          ((panelCurve 313).slope 258 218 173 5) = 199
      rw [hsl]
      change (-173 : ZMod 313) + -(192 * ((192 ^ 2) - 258 - 218 - 258)) = 199
      exact mod313_add320_y

#print axioms panel313_add320

/-- The affine point at 328G. -/
def panel313ThreeTwentyEight : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (252 : ZMod 313)) (y := (83 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- Exact group-law addition yielding 328G. -/
theorem panel313_add328 :
    panel313ThreeTwenty + panel313Octuple = panel313ThreeTwentyEight := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hx : (80 : ZMod 313) ≠ 298 := by decide
  have hsl : (panelCurve 313).slope (80 : ZMod 313) 298 199 9 = 2 := by
    rw [WeierstrassCurve.Affine.slope_of_X_ne hx]
    exact mod313_add328_slope
  change WeierstrassCurve.Affine.Point.some (80 : ZMod 313) (199 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (298 : ZMod 313) (9 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (252 : ZMod 313) (83 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_of_X_ne hx]
  · congr 1
    · change (panelCurve 313).addX 80 298
          ((panelCurve 313).slope 80 298 199 9) = 252
      rw [hsl]
      change (2 : ZMod 313) ^ 2 - 80 - 298 = 252
      exact mod313_add328_x
    · change (panelCurve 313).addY 80 298 199
          ((panelCurve 313).slope 80 298 199 9) = 83
      rw [hsl]
      change (-199 : ZMod 313) + -(2 * ((2 ^ 2) - 80 - 298 - 80)) = 83
      exact mod313_add328_y

#print axioms panel313_add328

/-- The affine point at 330G. -/
def panel313ThreeThirty : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (2 : ZMod 313)) (y := (311 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- Exact group-law addition yielding 330G. -/
theorem panel313_add330 :
    panel313ThreeTwentyEight + panel313Double = panel313ThreeThirty := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hx : (252 : ZMod 313) ≠ 297 := by decide
  have hsl : (panelCurve 313).slope (252 : ZMod 313) 297 83 204 = 267 := by
    rw [WeierstrassCurve.Affine.slope_of_X_ne hx]
    exact mod313_add330_slope
  change WeierstrassCurve.Affine.Point.some (252 : ZMod 313) (83 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (297 : ZMod 313) (204 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (311 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_of_X_ne hx]
  · congr 1
    · change (panelCurve 313).addX 252 297
          ((panelCurve 313).slope 252 297 83 204) = 2
      rw [hsl]
      change (267 : ZMod 313) ^ 2 - 252 - 297 = 2
      exact mod313_add330_x
    · change (panelCurve 313).addY 252 297 83
          ((panelCurve 313).slope 252 297 83 204) = 311
      rw [hsl]
      change (-83 : ZMod 313) + -(267 * ((267 ^ 2) - 252 - 297 - 252)) = 311
      exact mod313_add330_y

#print axioms panel313_add330

/-- The last addition in the saved p=313 order certificate. -/
theorem panel313_add331 :
    panel313ThreeThirty + panelGenerator 313 panel313_good_prime = 0 := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  change WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (311 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (2 : ZMod 313) _ = 0
  apply WeierstrassCurve.Affine.Point.add_of_Y_eq rfl
  change (311 : ZMod 313) = -2
  decide

#print axioms panel313_add331

end XedniPublicFirstLargeHoldout

