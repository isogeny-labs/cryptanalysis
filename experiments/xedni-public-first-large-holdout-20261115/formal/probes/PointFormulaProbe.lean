import ConcreteCurveRecovery
open XedniPublicFirstLargeHoldout
private instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
private theorem hp313 : ¬ (313 : ℕ) ∣ 1664 := by norm_num
private def G2 : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic := panelCurve_isElliptic 313 hp313
  exact WeierstrassCurve.Affine.Point.mk (x := (297 : ZMod 313)) (y := (204 : ZMod 313)) (by
    norm_num [panelCurve, WeierstrassCurve.Affine.equation_iff] <;> decide)
private theorem slope313 : (11 / 4 : ZMod 313) = 81 := by
  apply (div_eq_iff (by decide : (4 : ZMod 313) ≠ 0)).2
  change (11 : ZMod 313) = (324 : ZMod 313)
  exact (ZMod.natCast_eq_natCast_iff' 11 324 313).mpr (by decide)
private theorem x313 : (81 : ZMod 313) ^ 2 - 2 - 2 = 297 := by
  calc
    (81 : ZMod 313) ^ 2 - 2 - 2 = (6557 : ZMod 313) := by ring
    _ = 297 := (ZMod.natCast_eq_natCast_iff' 6557 297 313).mpr (by decide)
private theorem y313 :
    (-2 : ZMod 313) + -(81 * ((81 ^ 2) - 2 - 2 - 2)) = 204 := by
  calc
    (-2 : ZMod 313) + -(81 * ((81 ^ 2) - 2 - 2 - 2)) =
        (-23897 : ZMod 313) := by ring
    _ = 204 := (ZMod.intCast_eq_intCast_iff' (-23897) 204 313).mpr (by decide)
example : panelGenerator 313 hp313 + panelGenerator 313 hp313 = G2 := by
  letI : (panelCurve 313).IsElliptic := panelCurve_isElliptic 313 hp313
  have hne : (2 : ZMod 313) ≠ -2 := by decide
  change WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (2 : ZMod 313) _ +
    WeierstrassCurve.Affine.Point.some (2 : ZMod 313) (2 : ZMod 313) _ =
    WeierstrassCurve.Affine.Point.some (297 : ZMod 313) (204 : ZMod 313) _
  rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne]
  · congr 1 <;> norm_num [panelCurve, WeierstrassCurve.Affine.slope,
      WeierstrassCurve.Affine.addX, WeierstrassCurve.Affine.addY,
      WeierstrassCurve.Affine.negAddY, WeierstrassCurve.Affine.negY, hne] <;>
      rw [slope313]
      · exact x313
      · exact y313
  · simpa [panelCurve, WeierstrassCurve.Affine.negY] using hne
