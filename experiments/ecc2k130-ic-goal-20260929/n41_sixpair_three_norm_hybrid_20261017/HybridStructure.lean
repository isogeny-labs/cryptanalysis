import Std
import Init.Grind.Ring.Basic

namespace HybridStructure
open Lean.Grind

/-- The two three-pair subtotals preserve the ordered six-pair sum. -/
theorem two_triples_are_six_sum {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ p₅ : G) :
    ((p₀ + p₁) + p₂) + ((p₃ + p₄) + p₅) =
      (((((p₀ + p₁) + p₂) + p₃) + p₄) + p₅) := by
  simp only [AddCommMonoid.add_assoc]

/-- If both source families are closed under point negation, an x-coordinate
match to either sign of the public target has an oriented target witness. -/
theorem orient_target {G : Type} [AddCommGroup G]
    (left right : G → Prop) (target : G)
    (left_neg : ∀ x, left x → left (-x))
    (right_neg : ∀ x, right x → right (-x))
    (match_either : ∃ l r, left l ∧ right r ∧
      (l + r = target ∨ l + r = -target)) :
    ∃ l r, left l ∧ right r ∧ l + r = target := by
  obtain ⟨l, r, hl, hr, hsum⟩ := match_either
  rcases hsum with h | h
  · exact ⟨l, r, hl, hr, h⟩
  · refine ⟨-l, -r, left_neg l hl, right_neg r hr, ?_⟩
    calc
      -l + -r = -(l + r) := by rw [AddCommGroup.neg_add]
      _ = target := by rw [h, AddCommGroup.neg_neg]

#print axioms two_triples_are_six_sum
#print axioms orient_target

end HybridStructure
