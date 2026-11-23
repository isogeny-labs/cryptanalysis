import Mathlib

namespace M31TwistExtension

abbrev R := ZMod 2147505293
abbrev p : R := 2147483647
set_option maxRecDepth 65536 in
instance : Fact (Nat.Prime 2147505293) := ⟨by norm_num⟩

/-- Use the trace from the twist cardinality. The two roots are distinct. -/
theorem trace_factor (x : R) :
    x^2 - 21645*x + p = (x+1)*(x+p) := by
  have hc : (-21645 : R) = 1+p := by decide
  linear_combination (norm := ring) x * hc

theorem distinct_roots : (-1 : R) ≠ -p := by decide

-- Binary digits are least significant first. Each square takes place in R.
private def exponent : List Bool → ℕ
  | [] => 0
  | b::bs => 2*exponent bs + (if b then 1 else 0)

private def modularPower (x : R) : List Bool → R
  | [] => 1
  | b::bs => let y := modularPower x bs; y*y*(if b then x else 1)

private theorem modularPower_spec (x : R) (bits : List Bool) :
    x^(exponent bits) = modularPower x bits := by
  induction bits with
  | nil => simp [exponent, modularPower]
  | cons b bs ih =>
    cases b <;> simp [exponent, modularPower, two_mul, pow_add, ih]

set_option maxRecDepth 8192 in
theorem second_order : orderOf (-p) = 536876323 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by
    change (-p)^(536876323 : ℕ) = 1
    rw [show (536876323 : ℕ) = exponent (Nat.bits 536876323) by decide +kernel, modularPower_spec]
    decide +kernel)
  intro r hr hd
  change r ∣ 811 * 661993 at hd
  rcases hr.dvd_mul.mp hd with h | h
  · rcases (Nat.dvd_prime (by decide : Nat.Prime 811)).mp h with e | e
    · exact (hr.ne_one e).elim
    · subst r
      change (-p)^(661993 : ℕ) ≠ 1
      rw [show (661993 : ℕ) = exponent (Nat.bits 661993) by decide +kernel, modularPower_spec]
      decide +kernel
  · rcases (Nat.dvd_prime (by norm_num : Nat.Prime 661993)).mp h with e | e
    · exact (hr.ne_one e).elim
    · subst r
      change (-p)^(811 : ℕ) ≠ 1
      rw [show (811 : ℕ) = exponent (Nat.bits 811) by decide +kernel, modularPower_spec]
      decide +kernel

private theorem fixed_scalar (a x : R) : a*x=x ↔ x=0 ∨ a=1 := by
  constructor
  · intro h
    have hz : (a-1)*x=0 := by linear_combination h
    exact (mul_eq_zero.mp hz).elim (fun z => Or.inr (sub_eq_zero.mp z)) Or.inl
  · rintro (rfl | rfl) <;> simp

/-- Rational vectors of the degree-d Frobenius power in the eigenbasis. -/
theorem fixed_coordinates (d : ℕ) (x y : R) :
    ((-1 : R)^d*x=x ∧ (-p)^d*y=y) ↔
      (x=0 ∨ 2 ∣ d) ∧ (y=0 ∨ 536876323 ∣ d) := by
  rw [fixed_scalar, fixed_scalar, neg_one_pow_eq_one_iff_even (by decide : (-1:R) ≠ 1),
    even_iff_two_dvd, ← orderOf_dvd_iff_pow_eq_one, second_order]

theorem both_directions (d : ℕ) :
    (2 ∣ d ∧ 536876323 ∣ d) ↔ 1073752646 ∣ d := by
  constructor
  · rintro ⟨h, k⟩
    exact (show Nat.lcm 2 536876323 = 1073752646 by decide) ▸ Nat.lcm_dvd h k
  · intro h
    exact ⟨dvd_trans (by decide : 2 ∣ 1073752646) h,
      dvd_trans (by decide : 536876323 ∣ 1073752646) h⟩

end M31TwistExtension
