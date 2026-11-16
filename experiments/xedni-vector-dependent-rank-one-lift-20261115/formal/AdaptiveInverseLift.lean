import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace XedniAdaptiveInverseLift

def curveB (x y : ℤ) : ℤ := y ^ 2 - x ^ 3 + x

def modelInt (x y : ℤ) : WeierstrassCurve ℤ :=
  ⟨0, 0, 0, -1, curveB x y⟩

def modelRat (x y : ℤ) : WeierstrassCurve.Affine ℚ :=
  ⟨0, 0, 0, -1, (curveB x y : ℚ)⟩

theorem rational_model (x y : ℤ) :
    (modelInt x y).map (Int.castRingHom ℚ) = modelRat x y := by
  ext <;> simp [modelInt, modelRat, WeierstrassCurve.map]

private theorem no_integer_singular_B (B : ℤ) : 27 * B ^ 2 ≠ 4 := by
  intro h
  omega

private theorem nonsingular (x y : ℤ) : (modelRat x y).Δ ≠ 0 := by
  have h : (27 * (curveB x y : ℚ) ^ 2) ≠ 4 := by
    have hi := no_integer_singular_B (curveB x y)
    exact_mod_cast hi
  intro hd
  norm_num [modelRat, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆,
    WeierstrassCurve.b₈] at hd
  apply h
  nlinarith

private instance (x y : ℤ) : (modelRat x y).IsElliptic :=
  ⟨isUnit_iff_ne_zero.mpr (nonsingular x y)⟩

private theorem eq_pos (x y : ℤ) :
    (modelRat x y).Equation (x : ℚ) (y : ℚ) := by
  simp [modelRat, curveB, WeierstrassCurve.Affine.equation_iff]
  ring

private theorem eq_neg (x y : ℤ) :
    (modelRat x y).Equation (x : ℚ) (-y : ℚ) := by
  simp [modelRat, curveB, WeierstrassCurve.Affine.equation_iff]
  ring

def liftPos (x y : ℤ) : (modelRat x y).Point :=
  WeierstrassCurve.Affine.Point.mk (eq_pos x y)

def liftNeg (x y : ℤ) : (modelRat x y).Point :=
  WeierstrassCurve.Affine.Point.mk (eq_neg x y)

theorem inverse_relation (x y : ℤ) :
    liftPos x y + liftNeg x y = 0 := by
  unfold liftPos liftNeg
  apply WeierstrassCurve.Affine.Point.add_of_Y_eq rfl
  simp [modelRat, WeierstrassCurve.Affine.negY]

def baseModel (p : ℕ) : WeierstrassCurve.Affine (ZMod p) :=
  ⟨0, 0, 0, -1, -2⟩

theorem reduction_model {p : ℕ} (x y : ℤ)
    (hpoint : (y : ZMod p) ^ 2 =
      (x : ZMod p) ^ 3 - (x : ZMod p) - 2) :
    (modelInt x y).map (Int.castRingHom (ZMod p)) = baseModel p := by
  ext <;> simp [modelInt, baseModel, WeierstrassCurve.map, curveB] at *
  linear_combination hpoint

#print axioms rational_model
#print axioms inverse_relation
#print axioms reduction_model

end XedniAdaptiveInverseLift
