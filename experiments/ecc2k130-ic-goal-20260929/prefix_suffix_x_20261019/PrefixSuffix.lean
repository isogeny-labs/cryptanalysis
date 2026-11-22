import Std

namespace PrefixSuffix
open Lean.Grind

/-- The target residual of any prefix lies in one of two buckets determined by
one representative of its sign orbit. -/
theorem residual_key_covered {G K : Type} [AddCommGroup G]
    (key : G → K) (p rep s q : G)
    (hfiber : ∀ a b : G, key a = key b → a = b ∨ a = -b)
    (hkey : key p = key rep) (hsum : p + s = q) :
    key s = key (q - rep) ∨ key s = key (q + rep) := by
  have hs : s = q - p := by
    calc
      s = (p + s) - p := by
        rw [AddCommMonoid.add_comm p s, AddCommGroup.add_sub_cancel]
      _ = q - p := by rw [hsum]
  rcases hfiber p rep hkey with hp | hp
  · left
    rw [hs, hp]
  · right
    rw [hs, hp, AddCommGroup.sub_eq_add_neg, AddCommGroup.neg_neg]

/-- Every actual target decomposition reaches the indexed suffix under one
of the two target-conditioned residual keys. -/
theorem indexed_decomposition_covered {G K : Type} [AddCommGroup G]
    (key : G → K) (index : K → List G) (p rep s q : G)
    (hfiber : ∀ a b : G, key a = key b → a = b ∨ a = -b)
    (hkey : key p = key rep) (hsum : p + s = q)
    (hindexed : s ∈ index (key s)) :
    s ∈ index (key (q - rep)) ∨ s ∈ index (key (q + rep)) := by
  rcases residual_key_covered key p rep s q hfiber hkey hsum with h | h
  · left
    rw [← h]
    exact hindexed
  · right
    rw [← h]
    exact hindexed

#print axioms residual_key_covered
#print axioms indexed_decomposition_covered
end PrefixSuffix
