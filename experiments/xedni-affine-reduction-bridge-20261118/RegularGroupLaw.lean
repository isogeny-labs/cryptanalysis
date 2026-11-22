import RegularChainReduction

/-!
Identify the regular affine step relation with mathlib's elliptic-curve group
addition for a short Weierstrass curve over a field.
-/

namespace XedniRegularGroupLaw

open XedniRegularChainReduction XedniAffineReductionBridge

variable {F : Type*} [Field F] [DecidableEq F]

def shortCurve (A B : F) : WeierstrassCurve F := ⟨0, 0, 0, A, B⟩

theorem short_equation {A B : F} (P : CurvePoint F A B) :
    (shortCurve A B).toAffine.Equation P.x P.y := by
  rw [WeierstrassCurve.Affine.equation_iff]
  simpa [shortCurve] using P.onCurve

def toGroupPoint {A B : F} [(shortCurve A B).IsElliptic]
    (P : CurvePoint F A B) : (shortCurve A B).toAffine.Point :=
  WeierstrassCurve.Affine.Point.mk (short_equation P)

private theorem short_addX {A B x₁ x₂ slope : F} :
    (shortCurve A B).toAffine.addX x₁ x₂ slope = addX x₁ x₂ slope := by
  simp [shortCurve, WeierstrassCurve.Affine.addX, addX]

private theorem short_addY {A B x₁ x₂ y₁ slope : F} :
    (shortCurve A B).toAffine.addY x₁ x₂ y₁ slope =
      addY x₁ y₁ (addX x₁ x₂ slope) slope := by
  simp [shortCurve, WeierstrassCurve.Affine.addY,
    WeierstrassCurve.Affine.negY, WeierstrassCurve.Affine.negAddY,
    WeierstrassCurve.Affine.addX, addX, addY]
  ring

theorem fieldStep_group_add {A B : F} [(shortCurve A B).IsElliptic]
    {P T Q : CurvePoint F A B} (h : FieldStep P T Q) :
    toGroupPoint Q = toGroupPoint P + toGroupPoint T := by
  rcases h with ⟨hden, hx, hy⟩ | ⟨hPT, hden, hx, hy⟩
  · have hxe : P.x ≠ T.x := by
      intro heq
      exact hden (by rw [heq, sub_self])
    have hslope : (shortCurve A B).toAffine.slope P.x T.x P.y T.y =
        (T.y - P.y) / (T.x - P.x) := by
      rw [WeierstrassCurve.Affine.slope_of_X_ne hxe]
      apply (div_eq_div_iff (sub_ne_zero.mpr hxe) hden).2
      ring
    unfold toGroupPoint
    simp only [WeierstrassCurve.Affine.Point.mk]
    rw [WeierstrassCurve.Affine.Point.add_of_X_ne hxe]
    simp only [WeierstrassCurve.Affine.Point.some.injEq]
    constructor
    · rw [hx, hslope, short_addX]
    · rw [hy, hslope, short_addY, hx]
  · subst T
    have hyne : P.y ≠ (shortCurve A B).toAffine.negY P.x P.y := by
      intro heq
      apply hden
      simp [shortCurve, WeierstrassCurve.Affine.negY] at heq
      linear_combination heq
    have hslope : (shortCurve A B).toAffine.slope P.x P.x P.y P.y =
        (3 * P.x ^ 2 + A) / (2 * P.y) := by
      rw [WeierstrassCurve.Affine.slope_of_Y_ne rfl hyne]
      simp [shortCurve, WeierstrassCurve.Affine.negY]
      ring
    unfold toGroupPoint
    simp only [WeierstrassCurve.Affine.Point.mk]
    rw [WeierstrassCurve.Affine.Point.add_self_of_Y_ne hyne]
    simp only [WeierstrassCurve.Affine.Point.some.injEq]
    constructor
    · rw [hx, hslope, short_addX]
    · rw [hy, hslope, short_addY, hx]

theorem fieldChain_group_relation {A B : F} [(shortCurve A B).IsElliptic]
    {P T Q : CurvePoint F A B} (h : FieldChain T P Q) :
    ∃ n : ℕ, toGroupPoint Q = toGroupPoint P + n • toGroupPoint T := by
  induction h with
  | refl P => exact ⟨0, by simp⟩
  | step h tail ih =>
      obtain ⟨n, hn⟩ := ih
      refine ⟨n + 1, ?_⟩
      calc
        toGroupPoint _ = toGroupPoint _ + n • toGroupPoint _ := hn
        _ = (toGroupPoint _ + toGroupPoint _) + n • toGroupPoint _ := by
          rw [← fieldStep_group_add h]
        _ = toGroupPoint _ + (n + 1) • toGroupPoint _ := by
          simp [add_nsmul, add_assoc, add_comm, add_left_comm]

theorem reduced_regularChain_group_relation {R : Type*} [CommRing R]
    (f : R →+* F) {A B : R}
    [(shortCurve (f A) (f B)).IsElliptic]
    {P T Q : CurvePoint R A B} (h : RegularChain T P Q) :
    ∃ n : ℕ, toGroupPoint (mapPoint f Q) =
      toGroupPoint (mapPoint f P) + n • toGroupPoint (mapPoint f T) :=
  fieldChain_group_relation (map_regularChain f h)

#print axioms short_equation
#print axioms fieldStep_group_add
#print axioms fieldChain_group_relation
#print axioms reduced_regularChain_group_relation

end XedniRegularGroupLaw
