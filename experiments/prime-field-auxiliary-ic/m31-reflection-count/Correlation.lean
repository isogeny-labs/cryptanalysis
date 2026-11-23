import QuotientOrders

namespace M31Reflection

open Finset
section Algebra
variable {K : Type*} [Field K] [Fintype K] [DecidableEq K]
local notation "χ" => quadraticChar K
def cubic (x : K) := x^3 + 2*x + 14
private def g (u : K) := 196 - u*(u+2)^2
private def left (x : K) := x^3 - 4*x^2 + 4*x + 196
private def right (x : K) := x^3 - 4*x^2 - 784*x - 38416

private theorem square_sum (oddChar : ringChar K ≠ 2) (h : K → ℤ) :
    ∑ x, h (x^2) = ∑ u, (χ u + 1) * h u := by
  classical
  rw [← Finset.sum_fiberwise' univ (fun x : K => x^2) h]
  apply sum_congr rfl
  intro u _
  rw [sum_const, nsmul_eq_mul]
  congr 1
  convert quadraticChar_card_sqrts oddChar u using 2
  congr 1
  ext x
  simp

private theorem reciprocal (nz : (196 : K) ≠ 0) (u : K) :
    χ (u*g u) = χ (right (196*u⁻¹)) - (if u = 0 then χ (right 0) else 0) := by
  by_cases hu : u = 0
  · simp [hu, g]
  · simp only [hu, ↓reduceIte, sub_zero]
    have scale : (196*u⁻¹^2 : K) ≠ 0 := mul_ne_zero nz (pow_ne_zero _ (inv_ne_zero hu))
    have h : right (196*u⁻¹) = (196*u⁻¹^2)^2 * (u*g u) := by
      unfold right g
      field_simp
      ring
    rw [h, map_mul (quadraticChar K) (_^2), quadraticChar_sq_one' scale, one_mul]

theorem correlation_decomposition (oddChar : ringChar K ≠ 2) (nz : (196 : K) ≠ 0) :
    ∑ x, χ (cubic x * cubic (-x)) = (∑ v, χ (left v)) + (∑ v, χ (right v)) - χ (right 0) := by
  classical
  have poly (x : K) : cubic x * cubic (-x) = g (x^2) := by unfold cubic g; ring
  have lhs (u : K) : g u = left (-u) := by unfold g left; ring
  have a := Equiv.sum_comp (Equiv.neg K) (fun v => χ (left v))
  have b := Equiv.sum_comp ((Equiv.inv K).trans (Equiv.mulLeft₀ (196:K) nz)) (fun v => χ (right v))
  change (∑ u : K, χ (left (-u))) = _ at a
  change (∑ u : K, χ (right (196*u⁻¹))) = _ at b
  simp_rw [poly]
  rw [square_sum oddChar (fun u => χ (g u))]
  simp only [add_mul, one_mul, ← map_mul, Finset.sum_add_distrib, reciprocal nz, Finset.sum_sub_distrib]
  simp_rw [lhs]
  rw [a, b]
  simp
  ring

omit [Fintype K] [DecidableEq K] in
private theorem left_model (x : K) : x^3 + (-4)*x^2 + 4*x + 196 = left x := by unfold left; ring

omit [Fintype K] [DecidableEq K] in
private theorem right_model (x : K) : x^3 + (-4)*x^2 + (-784)*x + (-38416) = right x := by unfold right; ring

end Algebra

private abbrev χ := quadraticChar F
private theorem oddChar : ringChar F ≠ 2 := (ZMod.ringChar_zmod_n _).trans_ne (by decide)

section PointCount
variable {K : Type*} [Field K] [Fintype K] [DecidableEq K]

private def fibers (E : WeierstrassCurve.Affine K) (h : K → K)
    (eqn : ∀ x y, E.Nonsingular x y ↔ y^2 = h x) :
    E.Point ≃ Option (Σ x : K, {y : K // y^2 = h x}) where
  toFun
    | .zero => none
    | .some x y hy => some ⟨x, y, (eqn x y).mp hy⟩
  invFun
    | none => .zero
    | some ⟨x, y, hy⟩ => .some x y ((eqn x y).mpr hy)
  left_inv q := by cases q <;> rfl
  right_inv q := by rcases q with _ | ⟨x,y,hy⟩ <;> rfl

private theorem trace_sum (oddChar : ringChar K ≠ 2) (E : WeierstrassCurve.Affine K) (h : K → K)
    (eqn : ∀ x y, E.Nonsingular x y ↔ y^2 = h x) :
    (Nat.card E.Point : ℤ) = (∑ x, quadraticChar K (h x)) + (Fintype.card K + 1) := by
  classical
  rw [Nat.card_congr (fibers E h eqn), Nat.card_eq_fintype_card, Fintype.card_option,
      Fintype.card_sigma, Nat.cast_add, Nat.cast_one, Nat.cast_sum]
  have counts (x : K) : (Fintype.card {y : K // y^2 = h x} : ℤ) = quadraticChar K (h x) + 1 := by
    have z := quadraticChar_card_sqrts oddChar (h x)
    rw [Set.toFinset_card] at z
    convert z using 2
    exact Fintype.card_congr (Equiv.refl _)
  simp_rw [counts]
  rw [Finset.sum_add_distrib]
  simp only [Finset.sum_const, Finset.card_univ, nsmul_eq_mul, mul_one]
  ring

end PointCount

private theorem left_trace : (Nat.card leftCurve.Point : ℤ) = (∑ x : F, χ (left x)) + (Fintype.card F + 1) := by
  apply trace_sum oddChar leftCurve left
  ·
    intro x y
    rw [← leftCurve.equation_iff_nonsingular_of_Δ_ne_zero smooth.1, leftCurve.equation_iff]
    simp only [leftCurve, zero_mul, add_zero]
    exact (congrArg (fun t : F => y^2 = t) (left_model x)).to_iff

private theorem right_trace : (Nat.card rightCurve.Point : ℤ) = (∑ x : F, χ (right x)) + (Fintype.card F + 1) := by
  apply trace_sum oddChar rightCurve right
  ·
    intro x y
    rw [← rightCurve.equation_iff_nonsingular_of_Δ_ne_zero smooth.2, rightCurve.equation_iff]
    simp only [rightCurve, zero_mul, add_zero]
    exact (congrArg (fun t : F => y^2 = t) (right_model x)).to_iff

private theorem correction : χ (right 0) = -1 := by
  have rz : right 0 = (-1 : F) * 196^2 := by native_decide
  have sign : χ (-1) = -1 := by
    apply quadraticChar_neg_one_iff_not_isSquare.mpr
    intro hs
    exact (by decide : ¬ (2147483647 % 4 ≠ 3)) (ZMod.exists_sq_eq_neg_one_iff.mp hs)
  rw [rz, map_mul, quadraticChar_sq_one' (by native_decide : (196 : F) ≠ 0), sign, neg_one_mul]

theorem correlation_exact :
    ∑ x : F, quadraticChar F (cubic x * cubic (-x)) = 105943 := by
  have a := left_trace
  have b := right_trace
  rw [quotient_cardinalities.1, ZMod.card] at a
  rw [quotient_cardinalities.2, ZMod.card] at b
  apply (correlation_decomposition oddChar (by native_decide)).trans
  rw [correction]
  have close (l r : ℤ) (hl : 2147552589 = l+2147483648)
      (hr : 2147520649 = r+2147483648) : l+r-(-1) = 105943 := by omega
  exact close _ _ a b

end M31Reflection
