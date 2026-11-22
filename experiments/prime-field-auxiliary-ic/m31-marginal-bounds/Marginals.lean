import Mathlib
open scoped BigOperators
namespace M31Correlated

/-- A trajectory may contain arbitrarily dependent observations. A certificate
indicator is bounded pointwise by the count of eligible hits divided by m. -/
theorem budget {W I : Type*} [Fintype W] [Fintype I]
    (mass done_ : W → ℚ) (hit : W → I → ℚ) (m h : ℚ)
    (hmass : ∀ w, 0 ≤ mass w)
    (need : ∀ w, m * done_ w ≤ ∑ i, hit w i)
    (marginal : ∀ i, ∑ w, mass w * hit w i ≤ h) :
    m * (∑ w, mass w * done_ w) ≤ (Fintype.card I : ℚ)*h := by
  classical
  calc
    _ = ∑ w, mass w * (m * done_ w) := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro w _
      ring
    _ ≤ ∑ w, mass w * ∑ i, hit w i := by
      exact Finset.sum_le_sum fun w _ => mul_le_mul_of_nonneg_left (need w) (hmass w)
    _ = ∑ i, ∑ w, mass w * hit w i := by
      simp_rw [Finset.mul_sum]
      exact Finset.sum_comm
    _ ≤ ∑ _i : I, h := Finset.sum_le_sum fun i _ => marginal i
    _ = _ := by simp

theorem medianFloor (q k : ℕ)
    (bound : (1:ℚ)/2 ≤ q*(2*(k:ℚ)^2)/(3*2147505293)) :
    3*2147505293 ≤ 4*k^2*q := by
  have h : (3*2147505293:ℚ) ≤ 4*(k:ℚ)^2*q := by
    linarith
  exact_mod_cast h

def minMedian (k : ℕ) : ℕ := (3*2147505293 + 4*k^2-1)/(4*k^2)

theorem thresholds : [17,20,32].map minMedian = [5573111,4026573,1572880] := by decide

theorem seedOneBound :
    (3710:ℚ)/10000 < (19300166*578:ℚ)/(14*2147505293) ∧
    (19300166*578:ℚ)/(14*2147505293) < 3711/10000 := by norm_num

end M31Correlated
