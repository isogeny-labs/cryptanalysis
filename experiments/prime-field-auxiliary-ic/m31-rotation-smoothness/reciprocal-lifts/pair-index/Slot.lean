import Mathlib.Data.ZMod.Basic

namespace ReciprocalIndex

def radix : ℕ := 2^32
def pack (key ordinal : ℕ) := key * radix + ordinal

/-- A slot simultaneously carries a nonzero field key and a 32-bit ordinal.
The arithmetic assumptions ensure that its representation fits a uint64. -/
theorem slot_fields (key ordinal : ℕ) (hk : 0 < key) (hkey : key < radix)
    (ho : ordinal < radix) :
    pack key ordinal ≠ 0 ∧ pack key ordinal < 2^64 ∧
    pack key ordinal / radix = key ∧ pack key ordinal % radix = ordinal := by
  unfold pack radix at *
  omega

/-- Probing consecutive slots can reach any empty slot within one traversal. -/
theorem can_reach_empty {n : ℕ} [NeZero n] {α : Type*}
    (slots : ZMod n → Option α) (start empty : ZMod n) (h : slots empty = none) :
    ∃ steps : ℕ, steps < n ∧ slots (start + steps) = none := by
  refine ⟨(empty-start).val, ZMod.val_lt _, ?_⟩
  simpa [ZMod.natCast_zmod_val] using h

end ReciprocalIndex

#print axioms ReciprocalIndex.slot_fields
#print axioms ReciprocalIndex.can_reach_empty
