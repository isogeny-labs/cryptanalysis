import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic

namespace M31Square
abbrev p := 2147483647
local instance : Fact (Nat.Prime p) := ⟨by
  change (mersenne 31).Prime
  apply lucas_lehmer_sufficiency 31 (by decide)
  norm_num⟩

theorem square_test (x : ZMod p) : x^(2^30 : ℕ) = x ↔ IsSquare x := by
  constructor
  · intro h
    refine ⟨x^(2^29 : ℕ), ?_⟩
    rw [← pow_add]
    exact h.symm
  · rintro ⟨y, rfl⟩
    calc
      (y*y)^(2^30 : ℕ) = (y^2)^(2^30 : ℕ) := by rw [pow_two]
      _ = y^(p+1) := by rw [← pow_mul]; rfl
      _ = y*y := by rw [pow_succ, ZMod.pow_card]

end M31Square
