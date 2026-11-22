import Std
import Init.Grind.Ring.Basic

namespace DualThreeJoin
open Lean.Grind

/-- Exact point witnesses for both three-pair halves compose to the public
target. The norm and S3 coordinate equations are necessary conditions used
to search for these witnesses; point equality is checked separately. -/
theorem exact_halves_join {G : Type} [AddCommGroup G]
    (p₀ p₁ p₂ p₃ p₄ p₅ left right target : G)
    (hleft : (p₀ + p₁) + p₂ = left)
    (hright : (p₃ + p₄) + p₅ = right)
    (htarget : left + right = target) :
    ((p₀ + p₁) + p₂) + ((p₃ + p₄) + p₅) = target := by
  rw [hleft, hright, htarget]

#print axioms exact_halves_join

end DualThreeJoin
