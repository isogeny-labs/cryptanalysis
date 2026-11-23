import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.NumberTheory.LucasLehmer

namespace M31SmoothOrbit

abbrev K := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) := ⟨by
  change (mersenne 31).Prime
  apply lucas_lehmer_sufficiency 31 (by decide)
  norm_num⟩

private theorem chi_two : quadraticChar K 2 = 1 := by
  rw [show (2 : K) = 65536^2 by decide]
  exact quadraticChar_sq_one' (by decide)

theorem rotate (x : K) (k : Nat) :
    quadraticChar K (2^k*x) = quadraticChar K x := by
  rw [map_mul, map_pow, chi_two, one_pow, one_mul]

theorem reciprocal (x : K) (hx : x ≠ 0) :
    quadraticChar K x⁻¹ = quadraticChar K x := by
  calc
    _ = quadraticChar K (x⁻¹) * quadraticChar K (x^2) := by rw [quadraticChar_sq_one' hx, mul_one]
    _ = quadraticChar K x := by rw [← map_mul]; congr 1; field_simp

theorem negate (x : K) : quadraticChar K (-x) = -quadraticChar K x := by
  have h : quadraticChar K (-1) = -1 := by
    rw [quadraticChar_neg_one (by rw [ZMod.ringChar_zmod_n]; decide), ZMod.card]
    decide
  rw [← neg_one_mul x, map_mul, h, neg_one_mul]

end M31SmoothOrbit
