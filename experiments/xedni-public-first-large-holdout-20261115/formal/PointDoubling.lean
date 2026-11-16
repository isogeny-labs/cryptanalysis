import OrderArithmetic

namespace XedniPublicFirstLargeHoldout
instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
theorem panel313_good_prime : ¬ (313 : ℕ) ∣ 1664 := by norm_num

/-- The checked affine point at the first doubling coordinate. -/
def panel313Double : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic := panelCurve_isElliptic 313 panel313_good_prime
  exact WeierstrassCurve.Affine.Point.mk (x := (297 : ZMod 313)) (y := (204 : ZMod 313)) (by
    norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)
/-- The first exact group-law step in the p=313, q=331 order certificate. -/
theorem panel313_double :
    panelGenerator 313 panel313_good_prime +
      panelGenerator 313 panel313_good_prime = panel313Double := by
  letI : (panelCurve 313).IsElliptic := panelCurve_isElliptic 313 panel313_good_prime
  have hne : (2 : ZMod 313) ≠ -2 := by decide
  have hy : (2 : ZMod 313) ≠ (panelCurve 313).negY 2 2 := by
    simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
  have hsl : (panelCurve 313).slope (2 : ZMod 313) 2 2 2 = 81 := by
    rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hy]
    change (11 / 4 : ZMod 313) = 81
    exact mod313_tangent_slope
  change WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (2 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (2 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (297 : ZMod 313) (204 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hy]
  · congr 1
    · change (panelCurve 313).addX 2 2 ((panelCurve 313).slope 2 2 2 2) = 297
      rw [hsl]
      change (81 : ZMod 313) ^ 2 - 2 - 2 = 297
      exact mod313_double_x
    · change (panelCurve 313).addY 2 2 2 ((panelCurve 313).slope 2 2 2 2) = 204
      rw [hsl]
      change (-2 : ZMod 313) + -(81 * ((81 ^ 2) - 2 - 2 - 2)) = 204
      exact mod313_double_y

#print axioms panel313_good_prime
#print axioms panel313_double

end XedniPublicFirstLargeHoldout
