import Std

namespace GuardedDecoder

/-- If every regular base solution has one of the two computed root
branches, the guarded circuit extension preserves the base solution set.
The `regularRoot` hypothesis is the characteristic-two field identity
proved in the accompanying mathematical argument. -/
theorem extension_iff_base {W Code : Type}
    (base : W → Code → Prop) (regular : W → Prop)
    (computedRoot : W → Code → Bool → Prop)
    (regularRoot : ∀ w code, regular w → base w code →
      ∃ branch : Bool, computedRoot w code branch)
    (w : W) (code : Code) :
    (∃ branch : Bool,
      base w code ∧ (regular w → computedRoot w code branch)) ↔
    base w code := by
  constructor
  · rintro ⟨_, baseProof, _⟩
    exact baseProof
  · intro baseProof
    by_cases isRegular : regular w
    · obtain ⟨branch, rootProof⟩ := regularRoot w code isRegular baseProof
      exact ⟨branch, baseProof, fun _ => rootProof⟩
    · exact ⟨false, baseProof, fun regularProof => False.elim (isRegular regularProof)⟩

#print axioms GuardedDecoder.extension_iff_base

end GuardedDecoder
