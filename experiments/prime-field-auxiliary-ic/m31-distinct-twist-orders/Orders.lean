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

def cubic (b x : F) := x^3 + x + b

private theorem shortEquation (b x y : F) :
    (curve b).Equation x y ↔ y^2 = cubic b x := by
  simp [WeierstrassCurve.Affine.equation_iff, curve, cubic]

private def fiberEquiv (b : F) (smooth : (curve b).Δ ≠ 0) :
    (curve b).Point ≃ Option ((x : F) × {y : F // y^2 = cubic b x}) where
  toFun
    | .zero => none
    | .some (x := x) (y := y) h => some ⟨x,y,(shortEquation b x y).mp h.1⟩
  invFun
    | none => .zero
    | some ⟨x,y,h⟩ => .some (x := x) (y := y) (((curve b).equation_iff_nonsingular_of_Δ_ne_zero smooth).mp
        ((shortEquation b x y).mpr h))
  left_inv P := by cases P <;> rfl
  right_inv z := by rcases z with _ | ⟨x,y,h⟩ <;> rfl

private noncomputable def roots (a : F) := ({y : F | y^2 = a} : Set F).toFinset.card

private theorem countShort (b : F) (smooth : (curve b).Δ ≠ 0) :
    Nat.card (curve b).Point = (∑ x : F, roots (cubic b x)) + 1 := by
  classical
  rw [Nat.card_congr (fiberEquiv b smooth)]
  simp [Nat.card_eq_fintype_card, roots, Fintype.card_subtype]

private theorem rootPair (a : F) : roots a + roots (-a) = 2 := by
  have char_ne : ringChar F ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  have minus : quadraticChar F (-1) = -1 := by
    apply (quadraticChar_neg_one char_ne).trans
    rw [show Fintype.card F = 2147483647 from ZMod.card _]
    decide
  have h := quadraticChar_card_sqrts char_ne a
  have negProd {K : Type} [Ring K] (v : K) : (-1 : K)*v = -v := neg_one_mul v
  have c : quadraticChar F (-a) = -quadraticChar F a := calc
    _ = quadraticChar F ((-1)*a) := congrArg _ (negProd a).symm
    _ = quadraticChar F (-1) * quadraticChar F a := map_mul _ _ _
    _ = -quadraticChar F a := by rw [minus]; exact neg_one_mul _
  have j := quadraticChar_card_sqrts char_ne (-a)
  rw [c] at j
  unfold roots
  omega

/-- The -1 twist has coefficients (1,-b). Pair the fibers at x and -x,
including their zero ordinates, and count both points at infinity. -/
theorem twistPair (b : F) (h : (curve b).Δ ≠ 0) (ht : (curve (-b)).Δ ≠ 0) :
    Nat.card (curve b).Point + Nat.card (curve (-b)).Point = 4294967296 := by
  rw [countShort _ h, countShort _ ht]
  have reflect := (Equiv.neg F).sum_comp Finset.univ (fun x => roots (cubic (-b) x)) (by simp)
  simp only [Equiv.neg_apply] at reflect
  have negPoly {K : Type} [CommRing K] (u v : K) :
      (-u)^3 + (-u) + (-v) = -(u^3 + u + v) := by ring
  have replacement : (∑ x : F, roots (cubic (-b) x)) = ∑ x : F, roots (-(cubic b x)) := by
    refine reflect.symm.trans (Finset.sum_congr rfl fun x _ => ?_)
    exact congrArg roots (negPoly x b)
  rw [replacement]
  have pair : (∑ x : F, roots (cubic b x)) + (∑ x : F, roots (-(cubic b x))) =
      2 * Fintype.card F := by
    rw [← Finset.sum_add_distrib]
    simp [rootPair, Nat.mul_comm]
  rw [show Fintype.card F = 2147483647 from ZMod.card _] at pair
  omega

private theorem choose : ∀ i : Fin 48, 15789877 ∣ (4294967296 - 89481001 * i.val) → i.val = 24 := by
    native_decide

private theorem finish (k : ℕ) (A T : ℕ) (s : A + T = 4294967296) (dvd : 15789877 ∣ A)
      (eqn : T = 89481001 * k) : A = 2147423272 ∧ T = 2147544024 := by
    have bound : k < 48 := by
      clear dvd
      omega
    have v := choose ⟨k, bound⟩ (by simpa only [Fin.val_mk, ← eqn, ← s, Nat.add_sub_cancel] using dvd)
    change k = 24 at v
    subst k
    norm_num at eqn
    omega

theorem distinct_orders :
    Nat.card (curve 1).Point = 2147423272 ∧ Nat.card (curve (-1)).Point = 2147544024 := by
  have total := twistPair 1 (by native_decide) (by native_decide)
  have ha := prime_divides a 769 (by native_decide)
    (WeierstrassCurve.Affine.Point.some_ne_zero _) (by native_decide)
  have hb := prime_divides b 20533 (by native_decide)
    (WeierstrassCurve.Affine.Point.some_ne_zero _) (by native_decide)
  have cop : Nat.Coprime 769 20533 := by decide
  have d := cop.mul_dvd_of_dvd_of_dvd ha hb
  change 15789877 ∣ Nat.card (curve 1).Point at d
  obtain ⟨k, hk⟩ := prime_divides t 89481001 (by native_decide)
    (WeierstrassCurve.Affine.Point.some_ne_zero _) (by native_decide)
  exact finish k _ _ total d hk

end M31DistinctAuxiliary
