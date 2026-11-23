import Mathlib.Tactic

namespace M31BlockDistance

/-- A table with a unit change bound on every edge certifies a lower bound
on the number of bit flips required to reach any zero of the table. -/
theorem lower_bound {V B : Type} (flip : V → B → V) (dist : V → ℕ)
    (edge : ∀ v b, dist v ≤ dist (flip v b) + 1) (v : V) (bits : List B)
    (zero : dist (bits.foldl flip v) = 0) : dist v ≤ bits.length := by
  induction bits generalizing v with
  | nil => simpa using zero.le
  | cons b rest ih =>
    have tail := ih (flip v b) zero
    have first := edge v b
    simp only [List.length_cons]
    omega

end M31BlockDistance
