import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import Mathlib.Tactic

namespace XedniCrtRationalWitness

def Wℤ : WeierstrassCurve ℤ :=
  ⟨-987, -1034, 0, 7660, -3997⟩

def W : WeierstrassCurve.Affine ℚ :=
  ⟨-987, -1034, 0, 7660, -3997⟩

theorem rational_model : Wℤ.map (Int.castRingHom ℚ) = W := by
  ext <;> norm_num [Wℤ, W, WeierstrassCurve.map]

#print axioms rational_model

private theorem nonsingular : W.Δ ≠ 0 := by
  norm_num [W, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]

private instance : W.IsElliptic := ⟨isUnit_iff_ne_zero.mpr nonsingular⟩

private theorem eq₁ : W.Equation 14 7 := by
  norm_num [W, WeierstrassCurve.Affine.equation_iff]

private theorem eq₂ : W.Equation 17 10 := by
  norm_num [W, WeierstrassCurve.Affine.equation_iff]

def Q₁ : W.Point := WeierstrassCurve.Affine.Point.mk eq₁
def Q₂ : W.Point := WeierstrassCurve.Affine.Point.mk eq₂

private theorem double : Q₂ + Q₂ = -Q₁ := by
  norm_num [Q₁, Q₂, WeierstrassCurve.Affine.Point.mk,
    WeierstrassCurve.Affine.Point.add_def, WeierstrassCurve.Affine.Point.add,
    WeierstrassCurve.Affine.Point.neg_def, WeierstrassCurve.Affine.Point.neg,
    WeierstrassCurve.Affine.slope, WeierstrassCurve.Affine.addX,
    WeierstrassCurve.Affine.addY, WeierstrassCurve.Affine.negAddY,
    WeierstrassCurve.Affine.negY, W]

theorem rational_relation : Q₁ + Q₂ + Q₂ = 0 := by
  rw [add_assoc, double, add_neg_cancel]

#print axioms rational_relation

private instance : Fact (Nat.Prime 47) := ⟨by norm_num⟩

def W₄₇ : WeierstrassCurve.Affine (ZMod 47) :=
  ⟨0, 0, 0, -1, -2⟩

theorem reduced_model : Wℤ.map (Int.castRingHom (ZMod 47)) = W₄₇ := by
  ext <;> norm_num [Wℤ, W₄₇, WeierstrassCurve.map] <;> decide

#print axioms reduced_model

private theorem nonsingular₄₇ : W₄₇.Δ ≠ 0 := by
  norm_num [W₄₇, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈] <;> decide

private instance : W₄₇.IsElliptic := ⟨isUnit_iff_ne_zero.mpr nonsingular₄₇⟩

private theorem eq₁₄₇ : W₄₇.Equation 14 7 := by
  norm_num [W₄₇, WeierstrassCurve.Affine.equation_iff] <;> decide

private theorem eq₂₄₇ : W₄₇.Equation 17 10 := by
  norm_num [W₄₇, WeierstrassCurve.Affine.equation_iff] <;> decide

def P₁ : W₄₇.Point := WeierstrassCurve.Affine.Point.mk eq₁₄₇
def P₂ : W₄₇.Point := WeierstrassCurve.Affine.Point.mk eq₂₄₇

private theorem double₄₇ : P₂ + P₂ = -P₁ := by
  have hs : (866 : ZMod 47) / 20 = 1 := by
    apply (div_eq_iff (by decide : (20 : ZMod 47) ≠ 0)).2
    decide
  have hnot : (10 : ZMod 47) ≠ -10 := by decide
  norm_num [P₁, P₂, WeierstrassCurve.Affine.Point.mk,
    WeierstrassCurve.Affine.Point.add_def, WeierstrassCurve.Affine.Point.add,
    WeierstrassCurve.Affine.Point.neg_def, WeierstrassCurve.Affine.Point.neg,
    WeierstrassCurve.Affine.slope, WeierstrassCurve.Affine.addX,
    WeierstrassCurve.Affine.addY, WeierstrassCurve.Affine.negAddY,
    WeierstrassCurve.Affine.negY, W₄₇, hs, hnot] <;> decide

theorem reduced_relation : P₁ + P₂ + P₂ = 0 := by
  rw [add_assoc, double₄₇, add_neg_cancel]

#print axioms reduced_relation

theorem eqG : W₄₇.Equation 2 2 := by
  norm_num [W₄₇, WeierstrassCurve.Affine.equation_iff] <;> decide

theorem eqQ : W₄₇.Equation 26 8 := by
  norm_num [W₄₇, WeierstrassCurve.Affine.equation_iff] <;> decide

def G : W₄₇.Point := WeierstrassCurve.Affine.Point.mk eqG
def Q : W₄₇.Point := WeierstrassCurve.Affine.Point.mk eqQ

#print axioms eqG
#print axioms eqQ

theorem public_scalar : (17 : ℕ) • G = Q := by
  change nsmulBinRec 17 G = Q
  unfold G Q
  decide +kernel

#print axioms public_scalar

theorem target_row_29_11 :
    P₁ = Q - (29 : ℕ) • G ∧ P₂ = Q - (11 : ℕ) • G := by
  constructor
  · change P₁ = Q + -(nsmulBinRec 29 G)
    unfold P₁ Q G
    decide +kernel
  · change P₂ = Q + -(nsmulBinRec 11 G)
    unfold P₂ Q G
    decide +kernel

#print axioms target_row_29_11

theorem target_row_5_23 :
    -P₁ = Q - (5 : ℕ) • G ∧ -P₂ = Q - (23 : ℕ) • G := by
  constructor
  · change -P₁ = Q + -(nsmulBinRec 5 G)
    unfold P₁ Q G
    decide +kernel
  · change -P₂ = Q + -(nsmulBinRec 23 G)
    unfold P₂ Q G
    decide +kernel

#print axioms target_row_5_23

theorem mirror_reduced_relation : -P₁ + -P₂ + -P₂ = 0 := by
  have h : -P₁ + -P₂ + -P₂ = -(P₁ + P₂ + P₂) := by abel
  rw [h, reduced_relation, neg_zero]

#print axioms mirror_reduced_relation

def WℤMirror : WeierstrassCurve ℤ :=
  ⟨987, -1034, 0, 7660, -3997⟩

def WMirror : WeierstrassCurve.Affine ℚ :=
  ⟨987, -1034, 0, 7660, -3997⟩

theorem mirror_rational_model : WℤMirror.map (Int.castRingHom ℚ) = WMirror := by
  ext <;> norm_num [WℤMirror, WMirror, WeierstrassCurve.map]

theorem mirror_reduced_model :
    WℤMirror.map (Int.castRingHom (ZMod 47)) = W₄₇ := by
  ext <;> norm_num [WℤMirror, W₄₇, WeierstrassCurve.map] <;> decide

private theorem mirror_nonsingular : WMirror.Δ ≠ 0 := by
  norm_num [WMirror, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]

private instance : WMirror.IsElliptic :=
  ⟨isUnit_iff_ne_zero.mpr mirror_nonsingular⟩

private theorem mirror_eq₁ : WMirror.Equation 14 (-7) := by
  norm_num [WMirror, WeierstrassCurve.Affine.equation_iff]

private theorem mirror_eq₂ : WMirror.Equation 17 (-10) := by
  norm_num [WMirror, WeierstrassCurve.Affine.equation_iff]

def Q₁Mirror : WMirror.Point := WeierstrassCurve.Affine.Point.mk mirror_eq₁
def Q₂Mirror : WMirror.Point := WeierstrassCurve.Affine.Point.mk mirror_eq₂

private theorem mirror_double : Q₂Mirror + Q₂Mirror = -Q₁Mirror := by
  norm_num [Q₁Mirror, Q₂Mirror, WeierstrassCurve.Affine.Point.mk,
    WeierstrassCurve.Affine.Point.add_def, WeierstrassCurve.Affine.Point.add,
    WeierstrassCurve.Affine.Point.neg_def, WeierstrassCurve.Affine.Point.neg,
    WeierstrassCurve.Affine.slope, WeierstrassCurve.Affine.addX,
    WeierstrassCurve.Affine.addY, WeierstrassCurve.Affine.negAddY,
    WeierstrassCurve.Affine.negY, WMirror]

theorem mirror_rational_relation : Q₁Mirror + Q₂Mirror + Q₂Mirror = 0 := by
  rw [add_assoc, mirror_double, add_neg_cancel]

#print axioms mirror_rational_model
#print axioms mirror_reduced_model
#print axioms mirror_rational_relation

end XedniCrtRationalWitness
