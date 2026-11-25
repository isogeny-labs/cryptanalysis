import Mathlib

namespace M31DistinctAuxiliary

abbrev F := ZMod 2147483647
instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩

def curve (b : F) : WeierstrassCurve.Affine F := ⟨0,0,0,1,b⟩

private def infinity {W : WeierstrassCurve.Affine F} : W.Point → Bool
  | .zero => true
  | .some _ => false

private theorem prime_divides {W : WeierstrassCurve.Affine F} (A : W.Point) (q : ℕ)
    (prime : q.Prime) (nonzero : A ≠ 0) (multiple : infinity (q • A) = true) :
    q ∣ Nat.card W.Point := by
  have h : q • A = 0 := by
    cases e : q • A with
    | zero => rfl
    | some hpt => simp [e, infinity] at multiple
  rcases (Nat.dvd_prime prime).mp (addOrderOf_dvd_of_nsmul_eq_zero h) with h₁ | hq
  · exact (nonzero (AddMonoid.addOrderOf_eq_one_iff.mp h₁)).elim
  · rw [← hq]
    exact addOrderOf_dvd_natCard A

private def a : (curve 1).Point := .some (x := 1930649686) (y := 877617207) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)
private def b : (curve 1).Point := .some (x := 1067557457) (y := 695868095) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)
private def t : (curve (-1)).Point := .some (x := 594119006) (y := 1538268577) (by
  rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
  native_decide)

theorem auxiliary_card (lo : 2147390967 ≤ Nat.card (curve 1).Point)
    (hi : Nat.card (curve 1).Point ≤ 2147576329) :
    Nat.card (curve 1).Point = 2147423272 := by
  have ha := prime_divides a 769 (by native_decide)
    (WeierstrassCurve.Affine.Point.some_ne_zero _) (by native_decide)
  have hb := prime_divides b 20533 (by native_decide)
    (WeierstrassCurve.Affine.Point.some_ne_zero _) (by native_decide)
  have cop : Nat.Coprime 769 20533 := by decide
  have h := cop.mul_dvd_of_dvd_of_dvd ha hb
  change 15789877 ∣ Nat.card (curve 1).Point at h
  omega

theorem twist_card (lo : 2147390967 ≤ Nat.card (curve (-1)).Point)
    (hi : Nat.card (curve (-1)).Point ≤ 2147576329) :
    Nat.card (curve (-1)).Point = 2147544024 := by
  have h := prime_divides t 89481001 (by native_decide)
    (WeierstrassCurve.Affine.Point.some_ne_zero _) (by native_decide)
  omega

end M31DistinctAuxiliary
