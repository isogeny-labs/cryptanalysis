import Mathlib.Tactic
import Mathlib.Algebra.BigOperators.Group.Multiset.Basic

namespace M31Overlap
variable {G : Type*} [AddCommGroup G]

/-- A cancelling pair lies on the left, on the right, or across the equality.
Multisets make the positions of the summands immaterial. -/
theorem classify (L R : Multiset G) (hl : L.card = 3) (hr : R.card = 4)
    (eqn : L.sum = R.sum)
    (cancel :
      (∃ t A, L = t ::ₘ (-t) ::ₘ A) ∨
      (∃ t B, R = t ::ₘ (-t) ::ₘ B) ∨
      (∃ t A B, L = t ::ₘ A ∧ R = t ::ₘ B)) :
    (∃ A : Multiset G, A.card = 1 ∧ A.sum = R.sum ∧ L.sum = A.sum) ∨
    (∃ B : Multiset G, B.card = 2 ∧ L.sum = B.sum ∧ R.sum = B.sum) ∨
    (∃ (t : G) (A B : Multiset G), A.card = 2 ∧ B.card = 3 ∧
       A.sum = B.sum ∧ L.sum = t + A.sum) := by
  rcases cancel with ⟨t,A,rfl⟩ | ⟨t,B,rfl⟩ | ⟨t,A,B,rfl,rfl⟩
  · left
    exact ⟨A, by simp at hl; omega, by simpa [add_assoc] using eqn, by simp⟩
  · right; left
    exact ⟨B, by simp at hr; omega, by simpa [add_assoc] using eqn, by simp⟩
  · right; right
    exact ⟨t,A,B,by simp at hl; omega,by simp at hr; omega,by simpa using eqn,by simp⟩

theorem class_count_floor (n : ℕ) (h : 3439976 ≤ 2 * Nat.choose 7 3 * n) :
    49143 ≤ n := by norm_num [Nat.choose] at h; omega
end M31Overlap
