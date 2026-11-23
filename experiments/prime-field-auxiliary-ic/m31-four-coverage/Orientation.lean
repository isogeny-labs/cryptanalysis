import Mathlib

namespace M31FourCoverage
variable {G : Type*} [AddCommGroup G] [DecidableEq G]

/-- One orientation from each disjoint negation pair suffices for counting. -/
theorem oriented_card (s : Finset G) (h : ∀ x ∈ s, -x ∉ s) :
    (s ∪ s.image (fun x => -x)).card = 2*s.card := by
  have hd : Disjoint s (s.image (fun x => -x)) := by
    rw [Finset.disjoint_left]
    intro x hx hi
    obtain ⟨y, hy, rfl⟩ := Finset.mem_image.mp hi
    exact h y hy hx
  rw [Finset.card_union_of_disjoint hd, Finset.card_image_of_injective _ neg_injective]
  omega

end M31FourCoverage

namespace M31FourCoverage
variable {G : Type*} [AddCommGroup G] [DecidableEq G] [Fintype G]

/-- Summing the overlap over all translations counts every ordered pair once.
The inner sum counts points of A whose translate by -g belongs to B. -/
theorem translate_overlap_sum (a b : Finset G) :
    (∑ g : G, ∑ x ∈ a, ∑ y ∈ b, (if g = x-y then 1 else 0 : ℕ)) =
    a.card*b.card := by
  rw [Finset.sum_comm]
  calc
    _ = ∑ _x ∈ a, b.card := by
      apply Finset.sum_congr rfl
      intro x hx
      rw [Finset.sum_comm]
      simp
    _ = _ := by simp

end M31FourCoverage

namespace M31FourCoverage

/-- A negation-stable coefficient domain has equal representation counts at
opposite outputs whenever evaluation commutes with negation. -/
theorem opposite_multiplicities {V G : Type*} [AddGroup V] [AddGroup G]
    [DecidableEq V] [DecidableEq G] (s : Finset V) (eval : V → G)
    (closed : ∀ v ∈ s, -v ∈ s) (odd : ∀ v, eval (-v) = -eval v) (g : G) :
    (s.filter (fun v => eval v = g)).card = (s.filter (fun v => eval v = -g)).card := by
  have h : (s.filter (fun v => eval v = g)).image (fun v => -v) =
      s.filter (fun v => eval v = -g) := by
    ext x
    constructor
    · intro hx
      obtain ⟨v,hv,rfl⟩ := Finset.mem_image.mp hx
      obtain ⟨hs,he⟩ := Finset.mem_filter.mp hv
      exact Finset.mem_filter.mpr ⟨closed v hs, by rw [odd, he]⟩
    · intro hx
      obtain ⟨hs,he⟩ := Finset.mem_filter.mp hx
      exact Finset.mem_image.mpr ⟨-x, Finset.mem_filter.mpr
        ⟨closed x hs, by rw [odd, he, neg_neg]⟩, neg_neg x⟩
  rw [← h, Finset.card_image_of_injective _ neg_injective]

end M31FourCoverage
