import Mathlib.Algebra.Group.Basic

namespace M31InverseSchedule

/-- Three squarings of x^127 place the low seven-bit block at bit 3.
Seven further squarings advance to the next block. -/
theorem exponent {M : Type*} [Monoid M] (x : M) :
    let b₀ := (x^127)^8
    let b₁ := b₀^128
    let b₂ := b₁^128
    let b₃ := b₂^128
    x^5 * b₀ * b₁ * b₂ * b₃ = x^(2147483647-2 : ℕ) := by
  dsimp only
  simp only [← pow_mul, ← pow_add]

end M31InverseSchedule
