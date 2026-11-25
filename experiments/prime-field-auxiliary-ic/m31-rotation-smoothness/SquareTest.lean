import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic

import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic

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

/-- The census sets its nonsquare bit when the thirty-square test fails. -/
def nonsquareBit (x : ZMod p) : Bool := decide (x^(2^30 : ℕ) ≠ x)

private theorem bit_eq (x : ZMod p) :
    nonsquareBit x = decide (quadraticChar (ZMod p) x = -1) := by
  unfold nonsquareBit
  simp only [ne_eq, square_test, quadraticChar_neg_one_iff_not_isSquare]

theorem nonsquareBit_mul {x y : ZMod p} (hx : x ≠ 0) (hy : y ≠ 0) :
    nonsquareBit (x*y) = (nonsquareBit x ^^ nonsquareBit y) := by
  simp only [bit_eq, map_mul]
  rcases quadraticChar_dichotomy hx with h | h <;>
    rcases quadraticChar_dichotomy hy with k | k <;> simp [h, k]

theorem nonsquareBit_rotate (x : ZMod p) (i : ℕ) :
    nonsquareBit (2^i*x) = nonsquareBit x := by
  have twoSquare : IsSquare (2 : ZMod p) := ⟨65536, by decide⟩
  have twoChar := (quadraticChar_one_iff_isSquare (by decide : (2 : ZMod p) ≠ 0)).2 twoSquare
  simp [bit_eq, map_mul, map_pow, twoChar]

end M31Square
