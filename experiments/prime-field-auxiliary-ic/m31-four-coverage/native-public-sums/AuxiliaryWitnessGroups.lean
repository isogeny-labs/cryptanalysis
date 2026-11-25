import AuxiliaryTwistOrders
import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point

namespace M31.AuxiliaryWitnessGroups

open TwistRootCertificate (p F)
open TwistQuotients (CurvePoints)
open AuxiliaryTwistOrders (twist first second)

private instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def W₁ : WeierstrassCurve F := ⟨0,-4,0,4,196⟩
def W₂ : WeierstrassCurve F := ⟨0,-4,0,-784,-(196^2)⟩

private theorem model₁ (x y : F) :
    W₁.toAffine.Nonsingular x y ↔ y^2 = twist first x := by
  rw [← W₁.toAffine.equation_iff_nonsingular_of_Δ_ne_zero (by decide), W₁.toAffine.equation_iff]
  simp [W₁, twist, first]
  ring_nf

private theorem model₂ (x y : F) :
    W₂.toAffine.Nonsingular x y ↔ y^2 = twist second x := by
  rw [← W₂.toAffine.equation_iff_nonsingular_of_Δ_ne_zero (by decide), W₂.toAffine.equation_iff]
  simp [W₂, twist, second]
  ring_nf

/-- The point at infinity and each affine coordinate pair are preserved. -/
def coordinates (W : WeierstrassCurve F) (f : F → F)
    (h : ∀ x y, W.toAffine.Nonsingular x y ↔ y^2 = f x) :
    W.toAffine.Point ≃ CurvePoints f where
  toFun
    | .zero => none
    | .some (x := x) (y := y) proof => some ⟨x, y, (h x y).mp proof⟩
  invFun
    | none => .zero
    | some ⟨x, y, proof⟩ => .some ((h x y).mpr proof)
  left_inv := by intro P; cases P <;> rfl
  right_inv := by rintro (_ | ⟨x,y,h⟩) <;> rfl

def P₁ : W₁.toAffine.Point := .some ((model₁ 3 1498289385).mpr (by decide))
def P₂ : W₂.toAffine.Point := .some ((model₂ 2 221281234).mpr (by decide))

private theorem divides_count {W : WeierstrassCurve F} {f : F → F}
    (e : W.toAffine.Point ≃ CurvePoints f) (P : W.toAffine.Point) :
    addOrderOf P ∣ Fintype.card (CurvePoints f) := by
  rw [← Nat.card_eq_fintype_card, ← Nat.card_congr e]
  exact addOrderOf_dvd_natCard P

theorem census_of_witness_orders (h₁ : addOrderOf P₁ = 2147552589)
    (h₂ : addOrderOf P₂ = 2147520649) :
    Nat.card {x : F // IsSquare (x^3 + 2*x + 14) ∧ IsSquare (x^3 + 2*x - 14)} =
      536844426 := by
  apply AuxiliaryTwistOrders.census_of_twist_divisors
  · rw [← h₁]
    exact divides_count (coordinates _ _ model₁) P₁
  · rw [← h₂]
    exact divides_count (coordinates _ _ model₂) P₂

end M31.AuxiliaryWitnessGroups
