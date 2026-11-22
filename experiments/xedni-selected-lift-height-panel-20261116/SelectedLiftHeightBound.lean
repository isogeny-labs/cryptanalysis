import Mathlib

/-!
If the least positive height μ is at most an observed positive selected height m,
then the observed maximum M gives a lower bound M/m for M/μ.
The statement does not identify m with μ.
-/

theorem selected_height_ratio_lower_bound
    (μ m M : ℝ) (hμ : 0 < μ) (hμm : μ ≤ m) (hM : 0 ≤ M) :
    M / m ≤ M / μ := by
  have hm : 0 < m := lt_of_lt_of_le hμ hμm
  apply (div_le_div_iff₀ hm hμ).2
  nlinarith [mul_nonneg hM (sub_nonneg.mpr hμm)]

#print axioms selected_height_ratio_lower_bound
