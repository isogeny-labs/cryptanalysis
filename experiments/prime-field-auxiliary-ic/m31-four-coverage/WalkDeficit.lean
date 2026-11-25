import Mathlib

namespace M31FourCoverage.Walk
/-- For a centered mass difference, the positive deficit is half the L1 norm.
Taking d(g) = 1 - |G| P(g) makes its uniform average total variation. -/
theorem deficit_eq_half_l1 {ι : Type*} [Fintype ι] (d : ι → ℝ) (h : ∑ i, d i = 0) :
    2 * ∑ i, max (d i) 0 = ∑ i, |d i| := by
  have pointwise (i : ι) : 2 * max (d i) 0 = |d i| + d i := by
    rcases le_total (d i) 0 with hi | hi
    · rw [max_eq_right hi, abs_of_nonpos hi]; ring
    · rw [max_eq_left hi, abs_of_nonneg hi]; ring
  rw [Finset.mul_sum]
  simp_rw [pointwise]
  rw [Finset.sum_add_distrib, h, add_zero]

/-- Opposite generators exchange the predecessor and successor terms. -/
theorem symmetric_pair_step {G : Type*} [AddCommGroup G] (count : G → ℕ) (x b : G) :
    count (x-b) + count (x-(-b)) = count (x+b) + count (x+(-b)) := by
  simp [sub_eq_add_neg, add_comm]
end M31FourCoverage.Walk
