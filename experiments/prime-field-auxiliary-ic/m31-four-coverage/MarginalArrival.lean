import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace M31MarginalArrival

/-- Each successful history needs at least k hits. Each query slot has the
same total hit count across histories. No joint-distribution assumption. -/
theorem count_bound {H Q : Type*} (histories : Finset H) (queries : Finset Q)
    (hit : H → Q → ℕ) (success : H → Bool) (k m : ℕ)
    (necessary : ∀ h ∈ histories, success h = true → k ≤ ∑ q ∈ queries, hit h q)
    (marginal : ∀ q ∈ queries, ∑ h ∈ histories, hit h q = m) :
    (histories.filter (fun h => success h)).card * k ≤ queries.card * m := by
  classical
  calc
    _ = ∑ h ∈ histories, (if success h then k else 0) := by
      rw [← Finset.sum_filter]
      simp
    _ ≤ ∑ h ∈ histories, ∑ q ∈ queries, hit h q := by
      apply Finset.sum_le_sum
      intro h hh
      split
      · exact necessary h hh ‹_›
      · exact Nat.zero_le _
    _ = ∑ q ∈ queries, ∑ h ∈ histories, hit h q := Finset.sum_comm
    _ = queries.card * m := by
      rw [Finset.sum_congr rfl marginal]
      simp

end M31MarginalArrival
