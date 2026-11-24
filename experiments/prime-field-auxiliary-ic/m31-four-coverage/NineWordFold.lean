import Lean.Elab.Tactic.Omega

namespace M31NineWordFold

abbrev p : Nat := 2147483647
abbrev radix : Nat := 2147483648

theorem pair_fits (a b : Nat) (ha : a ≤ p) (hb : b ≤ p) : a + b < 2^32 := by
  unfold p at *
  omega

/-- Covers the full nine-word input range, including the redundant zero p. -/
theorem canonical (s : Nat) (hs : s ≤ 9*p) :
    let t := s % radix + s / radix
    s < 2^64 ∧ t < 2^32 ∧ (if t ≥ p then t-p else t) = s % p := by
  dsimp [p, radix] at *
  split <;> omega

end M31NineWordFold
