import Mathlib.Tactic

namespace WalkHitOverlap
variable {G : Type*} [AddCommGroup G]

theorem return_iff (H : Set G) (d : G) :
    (∃ a ∈ H, a+d ∈ H) ↔ ∃ a ∈ H, ∃ b ∈ H, b-a=d := by
  constructor
  · rintro ⟨a, ha, hb⟩
    exact ⟨a, ha, a+d, hb, by abel⟩
  · rintro ⟨a, ha, b, hb, rfl⟩
    exact ⟨a, ha, by convert hb using 1; abel⟩

end WalkHitOverlap
