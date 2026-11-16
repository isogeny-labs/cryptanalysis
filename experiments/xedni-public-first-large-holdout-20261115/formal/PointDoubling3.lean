import OrderArithmetic3

set_option maxRecDepth 4096

namespace XedniPublicFirstLargeHoldout

/-- The affine point at the third doubling coordinate. -/
def panel313Octuple : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (298 : ZMod 313)) (y := (9 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The third exact group-law edge of the p=313 order chain. -/
theorem panel313_third_double :
    panel313Quadruple + panel313Quadruple = panel313Octuple := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (226 : ZMod 313) ≠ -226 := by decide
  have hy : (226 : ZMod 313) ≠ (panelCurve 313).negY 65 226 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (65 : ZMod 313) 65 226 226 = 179 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_third_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (65 : ZMod 313) (226 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (65 : ZMod 313) (226 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (298 : ZMod 313) (9 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 65 65
          ((panelCurve 313).slope 65 65 226 226) = 298
      rw [hsl]
      change (179 : ZMod 313) ^ 2 - 65 - 65 = 298
      exact mod313_octuple_x
    · change (panelCurve 313).addY 65 65 226
          ((panelCurve 313).slope 65 65 226 226) = 9
      rw [hsl]
      change (-226 : ZMod 313) + -(179 * ((179 ^ 2) - 65 - 65 - 65)) = 9
      exact mod313_octuple_y

#print axioms panel313_third_double

end XedniPublicFirstLargeHoldout
