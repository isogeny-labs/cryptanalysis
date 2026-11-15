import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import Mathlib.Tactic

namespace XedniCrtRationalWitness

def W : WeierstrassCurve.Affine ℚ :=
  ⟨-987, -1034, 0, 7660, -3997⟩

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

end XedniCrtRationalWitness
