import Mathlib

namespace SignedLabels
open scoped Sym2

variable {I G : Type*} [AddCommGroup G] (v : I → G)

/-- Distinct unordered pair sums imply unique oriented differences off the diagonal. -/
theorem diff_unique
    (pairs : ∀ a b c d, v a + v b = v c + v d → s(a,b) = s(c,d))
    {a b c d : I} (hab : a ≠ b) (h : v a - v b = v c - v d) :
    a = c ∧ b = d := by
  have cross : v a + v d = v c + v b := by abel_nf at h ⊢; linear_combination (norm := abel) h
  rcases Sym2.eq_iff.mp (pairs a d c b cross) with ⟨ac,db⟩ | ⟨ab,_⟩
  · exact ⟨ac,db.symm⟩
  · exact (hab ab).elim

theorem diff_mod_sign
    (pairs : ∀ a b c d, v a + v b = v c + v d → s(a,b) = s(c,d))
    {a b c d : I} (hab : a ≠ b)
    (h : v a - v b = v c - v d ∨ v a - v b = -(v c - v d)) :
    s(a,b) = s(c,d) := by
  apply Sym2.eq_iff.mpr
  rcases h with h | h
  · exact Or.inl (diff_unique v pairs hab h)
  · rw [neg_sub] at h
    exact Or.inr (diff_unique v pairs hab h)

/-- For incidence-cell labels, summing just the point-side coefficients
gives degree one per cell. It separates sums from differences up to sign. -/
theorem separate (degree : G →+ ℤ) (one : ∀ i, degree (v i) = 1) (a b c d : I) :
    v a + v b ≠ v c - v d ∧ v a + v b ≠ -(v c - v d) ∧
    v a + v b ≠ -(v c + v d) := by
  repeat' apply And.intro
  all_goals
    intro h
    have he := congrArg degree h
    simp [one] at he

#print axioms diff_mod_sign
#print axioms separate
end SignedLabels
