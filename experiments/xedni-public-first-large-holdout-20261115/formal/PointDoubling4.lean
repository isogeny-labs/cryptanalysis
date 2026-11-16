import OrderArithmetic4

set_option maxRecDepth 4096

namespace XedniPublicFirstLargeHoldout

/-- The affine point at the fourth doubling coordinate. -/
def panel313Sixteen : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (211 : ZMod 313)) (y := (223 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The fourth exact group-law edge of the p=313 order chain. -/
theorem panel313_fourth_double :
    panel313Octuple + panel313Octuple = panel313Sixteen := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (9 : ZMod 313) ≠ -9 := by decide
  have hy : (9 : ZMod 313) ≠ (panelCurve 313).negY 298 9 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (298 : ZMod 313) 298 9 9 = 107 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_fourth_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (298 : ZMod 313) (9 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (298 : ZMod 313) (9 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (211 : ZMod 313) (223 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 298 298
          ((panelCurve 313).slope 298 298 9 9) = 211
      rw [hsl]
      change (107 : ZMod 313) ^ 2 - 298 - 298 = 211
      exact mod313_sixteen_x
    · change (panelCurve 313).addY 298 298 9
          ((panelCurve 313).slope 298 298 9 9) = 223
      rw [hsl]
      change (-9 : ZMod 313) + -(107 * ((107 ^ 2) - 298 - 298 - 298)) = 223
      exact mod313_sixteen_y

#print axioms panel313_fourth_double

end XedniPublicFirstLargeHoldout
