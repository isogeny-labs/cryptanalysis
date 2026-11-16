import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace XedniNonisomorphicRelation

/-- On a nontorsion rank-one generator, the rational group relation with
vector `(1,2)` is exactly the integer coordinate equation. -/
theorem rank_one_relation_iff {A : Type*} [AddCommGroup A]
    (P : A) (a b : ℤ)
    (hnontorsion : ∀ n : ℤ, n • P = 0 → n = 0) :
    a • P + (2 : ℤ) • (b • P) = 0 ↔ a + 2 * b = 0 := by
  have hcalc : a • P + (2 : ℤ) • (b • P) = (a + 2 * b) • P := by
    simp only [mul_zsmul, add_zsmul]
  rw [hcalc]
  constructor
  · exact hnontorsion (a + 2 * b)
  · intro h
    simp [h]

/-- A nonzero coefficient sum permits scalar recovery in any field. -/
theorem recover_of_relation {F : Type*} [Field F]
    (w t₁ t₂ : F) (hthree : (3 : F) ≠ 0)
    (hrelation : (w - t₁) + 2 * (w - t₂) = 0) :
    w = (t₁ + 2 * t₂) / 3 := by
  apply (eq_div_iff hthree).2
  linear_combination hrelation

#print axioms rank_one_relation_iff
#print axioms recover_of_relation

end XedniNonisomorphicRelation
