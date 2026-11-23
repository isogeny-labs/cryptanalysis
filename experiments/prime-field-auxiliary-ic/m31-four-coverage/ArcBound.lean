import Mathlib.Analysis.SpecialFunctions.Trigonometric.Bounds
import Mathlib.Analysis.Real.Pi.Bounds
import Mathlib.Tactic

namespace M31FourCoverage.ArcBound

/-- A certificate for the loss at an endpoint whose folded phase is at
least the threshold. The argument t is half the folded phase in radians. -/
theorem loss (x t : ℝ) (hx : 0 < x) (small : x ≤ 1)
    (hxt : x ≤ t) (ht : t ≤ Real.pi / 2) :
    2*(x-x^3/6)^2 ≤ 1-Real.cos (2*t) := by
  have h₁ := (Real.sin_gt_sub_cube hx).le
  have h₂ := Real.sin_le_sin_of_le_of_le_pi_div_two (by linarith [Real.pi_pos] : -(Real.pi/2) ≤ x) ht hxt
  have h₃ : 0 ≤ x-x^3/6 := by
    nlinarith [mul_nonneg (mul_nonneg hx.le (sub_nonneg.mpr small))
      (show 0 ≤ 1+x by linarith)]
  have h := pow_le_pow_left₀ h₃ (h₁.trans h₂) 2
  linarith [Real.sin_sq_eq_half_sub t]

/-- Bound the sum of the selected masses using an arbitrary clipping level. -/
theorem arc_mass {I : Type*} [Fintype I] (s : Finset I) (w : I → ℕ) (k : ℕ) :
    ∑ i ∈ s, w i ≤ s.card*k + ∑ i, (w i-k) := by
  calc
    _ ≤ ∑ i ∈ s, (k + (w i-k)) := Finset.sum_le_sum (fun _ _ => by omega)
    _ = s.card*k + ∑ i ∈ s, (w i-k) := by simp [Finset.sum_add_distrib]
    _ ≤ _ := by
      apply Nat.add_le_add_left
      exact Finset.sum_le_univ_sum_of_nonneg (fun i => Nat.zero_le _)

/-- Integrate nonnegative increments over nested phase thresholds. -/
theorem layers {I J : Type*} [Fintype I] [Fintype J]
    (weight loss : I → ℝ) (price outside : J → ℝ) (active : J → I → Prop)
    [∀ j, DecidablePred (active j)]
    (hw : ∀ i, 0 ≤ weight i) (hp : ∀ j, 0 ≤ price j)
    (pointwise : ∀ i, (∑ j, if active j i then price j else 0) ≤ loss i)
    (mass : ∀ j, outside j ≤ ∑ i, if active j i then weight i else 0) :
    (∑ j, price j * outside j) ≤ ∑ i, weight i * loss i := by
  calc
    _ ≤ ∑ j, price j * ∑ i, if active j i then weight i else 0 :=
      Finset.sum_le_sum fun j _ => mul_le_mul_of_nonneg_left (mass j) (hp j)
    _ = ∑ i, weight i * ∑ j, if active j i then price j else 0 := by
      simp_rw [Finset.mul_sum]
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro i _
      apply Finset.sum_congr rfl
      intro j _
      split_ifs <;> simp [mul_comm]
    _ ≤ _ := Finset.sum_le_sum fun i _ => mul_le_mul_of_nonneg_left (pointwise i) (hw i)

end M31FourCoverage.ArcBound
