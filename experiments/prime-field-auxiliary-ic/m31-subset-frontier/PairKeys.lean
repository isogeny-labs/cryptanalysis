import Mathlib.Tactic

namespace M31SubsetFrontier

/-- Every pair of orbit representatives gives at most two distinct invariant keys. -/
theorem pair_keys {G K : Type*} [AddCommGroup G]
    (x : G → K) (hx : ∀ g, x (-g) = x g) (a b : G) :
    ({x (a+b), x (a + -b), x (-a+b), x (-a + -b)} : Set K) =
    {x (a+b), x (a + -b)} := by
  have h₁ : x (-a+b) = x (a + -b) := by
    convert hx (a + -b) using 2
    abel
  have h₂ : x (-a + -b) = x (a+b) := by
    convert hx (a+b) using 2
    abel
  rw [h₁,h₂]
  ext k
  simp only [Set.mem_insert_iff, Set.mem_singleton_iff]
  tauto

end M31SubsetFrontier
