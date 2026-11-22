import Std

/-! A left inverse turns membership in a binary linear source-product image
    into a projector equation and recovers the unique source selector. -/
namespace SelectorProjection

variable {Source Product : Type}

theorem projector_eq_iff_range
    (encode : Source → Product) (decode : Product → Source)
    (hleft : ∀ s, decode (encode s) = s) (p : Product) :
    encode (decode p) = p ↔ ∃ s, encode s = p := by
  constructor
  · intro hp
    exact ⟨decode p, hp⟩
  · rintro ⟨s, rfl⟩
    rw [hleft]

theorem unique_selector_of_projector
    (encode : Source → Product) (decode : Product → Source)
    (hleft : ∀ s, decode (encode s) = s)
    (p : Product) (hp : encode (decode p) = p) :
    ∃ s, encode s = p ∧ ∀ t, encode t = p → t = s := by
  refine ⟨decode p, hp, ?_⟩
  intro s hs
  calc
    s = decode (encode s) := (hleft s).symm
    _ = decode p := by rw [hs]

#print axioms SelectorProjection.projector_eq_iff_range
#print axioms SelectorProjection.unique_selector_of_projector
end SelectorProjection
