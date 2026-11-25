import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Ring.Commute
import Mathlib.Tactic

namespace M31AffineCount

/-- On a sign-closed set of affine points with no fixed point of negation,
each occupied abscissa represents precisely two points. Infinity is separate. -/
theorem affine_card {F : Type*} [Field F] [DecidableEq F]
    (s : Finset (F × F)) (rhs : F → F)
    (curve : ∀ p ∈ s, p.2 ^ 2 = rhs p.1)
    (closed : ∀ p ∈ s, (p.1, -p.2) ∈ s)
    (free : ∀ p ∈ s, p.2 ≠ -p.2) :
    s.card = 2 * (s.image Prod.fst).card := by
  have fiber (x : F) (hx : x ∈ s.image Prod.fst) :
      (s.filter (fun p => p.1 = x)).card = 2 := by
    obtain ⟨⟨x', y⟩, hy, rfl⟩ := Finset.mem_image.mp hx
    have pair : s.filter (fun p => p.1 = x') = {(x',y), (x',-y)} := by
      ext p
      obtain ⟨u,v⟩ := p
      constructor
      · intro hm
        obtain ⟨hv, rfl⟩ := Finset.mem_filter.mp hm
        have hsq : v ^ 2 = y ^ 2 := (curve _ hv).trans (curve _ hy).symm
        rcases sq_eq_sq_iff_eq_or_eq_neg.mp hsq with h | h <;> simp [h]
      · intro hm
        rcases Finset.mem_insert.mp hm with h | h
        · cases h
          exact Finset.mem_filter.mpr ⟨hy, rfl⟩
        · have h' := Finset.mem_singleton.mp h
          cases h'
          exact Finset.mem_filter.mpr ⟨closed _ hy, rfl⟩
    rw [pair]
    simpa using Finset.card_pair (show (x', y) ≠ (x', -y) from
      fun h => free _ hy (congrArg Prod.snd h))
  calc
    _ = _ := Finset.card_eq_sum_card_image Prod.fst s
    _ = ∑ _x ∈ s.image Prod.fst, 2 := Finset.sum_congr rfl fiber
    _ = _ := by simp [Nat.mul_comm]

#print axioms affine_card
end M31AffineCount
