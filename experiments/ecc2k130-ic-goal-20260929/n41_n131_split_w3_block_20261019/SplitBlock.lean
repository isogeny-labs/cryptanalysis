import Std

namespace SplitBlock

/-- Two exhaustive width-two cases exclude every width-three left code.
The predicates are explicit so each case can be discharged by its separately
replayed polynomial certificate and the source-code-to-equation bridge. -/
theorem two_width_two_cases_cover_width_three
    {X : Type} (code : X → Nat) (root : X → Prop)
    (first : ∀ x, code x < 4 → ¬ root x)
    (second : ∀ x, 4 ≤ code x → code x < 8 → ¬ root x) :
    ∀ x, code x < 8 → ¬ root x := by
  intro x hwide
  by_cases hfirst : code x < 4
  · exact first x hfirst
  · exact second x (Nat.le_of_not_gt hfirst) hwide

#print axioms SplitBlock.two_width_two_cases_cover_width_three

end SplitBlock
