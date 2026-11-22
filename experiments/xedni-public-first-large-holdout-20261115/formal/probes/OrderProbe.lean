import ConcreteCurveRecovery
open XedniPublicFirstLargeHoldout
private instance : Fact (Nat.Prime 313) := ⟨by norm_num⟩
private theorem hp313 : ¬ (313 : ℕ) ∣ 1664 := by norm_num
private def G2 : (panelCurve 313).Point := by
  letI : (panelCurve 313).IsElliptic := panelCurve_isElliptic 313 hp313
  exact WeierstrassCurve.Affine.Point.mk (x := (297 : ZMod 313)) (y := (204 : ZMod 313)) (by decide)
example : (2 : ℕ) • panelGenerator 313 hp313 = G2 := by decide
