import OrderArithmetic2

set_option maxRecDepth 4096

namespace XedniPublicFirstLargeHoldout

/-- The affine point at the second doubling coordinate. -/
def panel313Quadruple : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk
    (x := (65 : ZMod 313)) (y := (226 : ZMod 313)) (by
      norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)

/-- The second exact group-law edge of the p=313 order chain. -/
theorem panel313_second_double :
    panel313Double + panel313Double = panel313Quadruple := by
  letI : (panelCurve 313).IsElliptic :=
    panelCurve_isElliptic 313 panel313_good_prime
  have hne : (204 : ZMod 313) ≠ -204 := by decide
  have hy : (204 : ZMod 313) ≠ (panelCurve 313).negY 297 204 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (297 : ZMod 313) 297 204 204 = 242 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    convert mod313_second_tangent_slope using 1 <;>
      simp [panelCurve, WeierstrassCurve.Affine.negY] <;> ring
  change WeierstrassCurve.Affine.Point.some (297 : ZMod 313) (204 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (297 : ZMod 313) (204 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (65 : ZMod 313) (226 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 297 297
          ((panelCurve 313).slope 297 297 204 204) = 65
      rw [hsl]
      change (242 : ZMod 313) ^ 2 - 297 - 297 = 65
      exact mod313_quadruple_x
    · change (panelCurve 313).addY 297 297 204
          ((panelCurve 313).slope 297 297 204 204) = 226
      rw [hsl]
      change (-204 : ZMod 313) + -(242 * ((242 ^ 2) - 297 - 297 - 297)) = 226
      exact mod313_quadruple_y

#print axioms panel313_second_double

end XedniPublicFirstLargeHoldout
