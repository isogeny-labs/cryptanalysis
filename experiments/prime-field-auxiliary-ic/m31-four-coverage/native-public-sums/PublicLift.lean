import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.Tactic

namespace M31PublicLift

abbrev p : ℕ := 2147483647
abbrev F := ZMod p
private instance : Fact (Nat.Prime p) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

/-- Bound for the partially reduced cubic used by the native lift. -/
theorem cubic_bound {r x : ℕ} (hr : r < p) (hx : x < p) :
    r*x + 2*x + 14 ≤ p^2 + 13 := by
  have h := Nat.mul_le_mul (show r ≤ p-1 by omega) (show x ≤ p-1 by omega)
  unfold p at *
  omega

/-- On the entire lift input interval the Mersenne fold fits in a 32-bit
word, and one conditional subtraction gives the canonical remainder. -/
theorem reduce_bound (t : ℕ) (ht : t ≤ p^2 + 13) :
    let f := (t &&& (2^31-1)) + (t >>> 31)
    t < 2^64 ∧ f < 2^32 ∧ (if p ≤ f then f-p else f) = t % p := by
  rw [Nat.and_two_pow_sub_one_eq_mod, Nat.shiftRight_eq_div_pow]
  dsimp
  have h := Nat.mod_add_div t (2^31)
  unfold p at *
  split <;> omega

def squares (a : F) : ℕ → F
  | 0 => a
  | n+1 => squares a n ^ 2

theorem squares_pow (a : F) (n : ℕ) : squares a n = a^(2^n) := by
  induction n with
  | zero => simp [squares]
  | succ n ih => rw [squares, ih, ← pow_mul, pow_succ]

/-- The native verification accepts exactly the square inputs, including zero. -/
theorem accepts_iff (a : F) : (squares a 29)^2 = a ↔ ∃ z : F, z^2 = a := by
  constructor
  · exact fun h => ⟨_, h⟩
  · rintro ⟨z, rfl⟩
    rw [squares_pow, ← pow_mul, ← pow_mul]
    change z^(p+1) = z^2
    rw [pow_succ, ZMod.pow_card, pow_two]

/-- Choosing the smaller representative preserves the square and separates it
from the failure sentinel p, even for the root zero. -/
theorem canonical_root {y : ℕ} (hy : y < p) :
    min y (p-y) ≤ p/2 ∧ min y (p-y) < p ∧
    ((min y (p-y) : ℕ) : F)^2 = (y : F)^2 := by
  constructor
  · omega
  constructor
  · omega
  rcases le_total y (p-y) with h | h
  · rw [min_eq_left h]
  · rw [min_eq_right h, Nat.cast_sub hy.le]
    rw [show (p : F) = 0 by decide]
    simp

#print axioms canonical_root
#print axioms reduce_bound
#print axioms accepts_iff
end M31PublicLift
