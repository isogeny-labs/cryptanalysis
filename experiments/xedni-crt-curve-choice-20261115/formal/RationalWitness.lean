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

end XedniCrtRationalWitness
