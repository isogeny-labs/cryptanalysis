import Mathlib

namespace M31TwistSmallFactor

abbrev F := ZMod 53
abbrev p : F := 2147483647

/-- The target curve has trace -21645 and its twist has the opposite trace. -/
theorem polynomials (x : F) :
    x^2 + 21645*x + p = (x+1)*(x+p) ∧
    x^2 - 21645*x + p = (x-1)*(x-p) := by
  rw [show (21645 : F) = 1+p by decide]
  constructor <;> ring

private theorem order52 (x : F) (h : x = p ∨ x = -p) : orderOf x = 52 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by
    rcases h with rfl | rfl <;> decide)
  intro r hr hd
  have opts : r = 2 ∨ r = 13 := by
    change r ∣ 2 * 2 * 13 at hd
    rcases hr.dvd_mul.mp hd with h | h
    · rcases hr.dvd_mul.mp h with h | h <;>
        exact Or.inl ((Nat.prime_dvd_prime_iff_eq hr (by decide : Nat.Prime 2)).mp h)
    · exact Or.inr ((Nat.prime_dvd_prime_iff_eq hr (by decide : Nat.Prime 13)).mp h)
  rcases opts with rfl | rfl <;> rcases h with rfl | rfl <;> decide

/-- In the 53-torsion eigenbasis of the target curve, the two lines
are fixed in degrees divisible by 2 and 52 respectively. -/
theorem target_degrees (d : ℕ) :
    ((-1 : F)^d = 1 ↔ 2 ∣ d) ∧ ((-p)^d = 1 ↔ 52 ∣ d) := by
  constructor
  · rw [neg_one_pow_eq_one_iff_even (by decide : (-1:F) ≠ 1), even_iff_two_dvd]
  · rw [← orderOf_dvd_iff_pow_eq_one, order52 _ (Or.inr rfl)]

theorem twist_second_degree (d : ℕ) : p^d = 1 ↔ 52 ∣ d := by
  rw [← orderOf_dvd_iff_pow_eq_one, order52 _ (Or.inl rfl)]

#print axioms target_degrees
#print axioms twist_second_degree
end M31TwistSmallFactor
