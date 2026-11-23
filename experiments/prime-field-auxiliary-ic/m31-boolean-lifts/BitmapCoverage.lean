import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace M31Bitmap

/-- Enumerating representatives from zero through floor(n/2) covers every square. -/
theorem half_range {n : ℕ} [NeZero n] (z : ZMod n) :
    (∃ y : ZMod n, y^2 = z) ↔ ∃ k : ℕ, k ≤ n/2 ∧ (k : ZMod n)^2 = z := by
  constructor
  · rintro ⟨y, rfl⟩
    by_cases small : y.val ≤ n/2
    · exact ⟨y.val, small, by rw [ZMod.natCast_zmod_val]⟩
    · have nonzero : y ≠ 0 := by
        intro h
        simp [h] at small
      letI : NeZero y := ⟨nonzero⟩
      refine ⟨(-y).val, ?_, ?_⟩
      · rw [ZMod.val_neg_of_ne_zero]
        omega
      · rw [ZMod.natCast_zmod_val]
        ring
  · rintro ⟨k, _, h⟩
    exact ⟨k, h⟩

end M31Bitmap
