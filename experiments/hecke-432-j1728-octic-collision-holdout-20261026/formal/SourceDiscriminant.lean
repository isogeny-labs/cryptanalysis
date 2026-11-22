import Mathlib.Tactic.Ring

namespace J1728SourceDiscriminant

/-- A source x-coordinate with nonsquare curve discriminant cannot lift to a
    rational point on C : y² + y = x³ - 7. -/
theorem no_source_point_of_nonsquare_discriminant
    {F : Type*} [Field F] (x : F)
    (nonsquare : ∀ z : F, z * z ≠ 4 * x ^ 3 - 27) :
    ¬ ∃ y : F, y ^ 2 + y = x ^ 3 - 7 := by
  rintro ⟨y, hy⟩
  apply nonsquare (2 * y + 1)
  calc
    (2 * y + 1) * (2 * y + 1) = 4 * (y ^ 2 + y) + 1 := by ring
    _ = 4 * (x ^ 3 - 7) + 1 := by rw [hy]
    _ = 4 * x ^ 3 - 27 := by ring

#print axioms no_source_point_of_nonsquare_discriminant

end J1728SourceDiscriminant
