import Mathlib.Algebra.Group.Units.Equiv
import Mathlib.Algebra.BigOperators.Group.Finset.Sigma
import Mathlib.Algebra.BigOperators.Ring.Finset

namespace ReciprocalLifts

/-- For binary lift masks, every ordered pair of set bits contributes to one phase. -/
theorem pooledPhaseCount {G : Type*} [AddCommGroup G] [Fintype G]
    (a b : G → ℕ) :
    (∑ j : G, ∑ i : G, a i * b (i - j)) = (∑ i, a i) * ∑ k, b k := by
  rw [Finset.sum_comm, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro i _
  rw [← Finset.mul_sum]
  congr 1
  simp only [sub_eq_add_neg]
  exact Equiv.sum_comp ((Equiv.neg G).trans (Equiv.addLeft i)) b

end ReciprocalLifts
