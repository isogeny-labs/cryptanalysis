import Mathlib.GroupTheory.OrderOfElement
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace M31TwistExtension

private def fast {m : ℕ} (x : ZMod m) : ℕ → ℕ → ZMod m
  | 0, _ => 1
  | fuel+1, n =>
    let r := fast x fuel (n/2)
    if n%2 = 0 then r*r else r*r*x

private theorem fast_eq {m : ℕ} (x : ZMod m) (fuel n : ℕ) (hn : n < 2^fuel) :
    fast x fuel n = x^n := by
  induction fuel generalizing n with
  | zero =>
    have : n = 0 := by simpa only [pow_zero, Nat.lt_one_iff] using hn
    simp [this,fast]
  | succ fuel ih =>
    rw [pow_succ] at hn
    simp only [fast, ih (n/2) (by omega), ← pow_add]
    split
    · congr 1
      omega
    · rw [← pow_succ]
      congr 1
      omega

/-- The second Frobenius root for the twist modulo the fixture group order. -/
abbrev root : ZMod 2147505293 := -2147483647

theorem root_order : orderOf root = 536876323 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by rw [← fast_eq _ 32 _ (by decide)]; decide)
  intro q hq hd
  rw [show 536876323 = 811*661993 by decide] at hd
  simp only [hq.dvd_mul, Nat.dvd_prime (by norm_num : Nat.Prime 811),
    Nat.dvd_prime (by norm_num : Nat.Prime 661993), hq.ne_one, false_or] at hd
  rcases hd with rfl | rfl <;> rw [← fast_eq _ 32 _ (by decide)] <;> decide

theorem root_returns (d : ℕ) : root^d = 1 ↔ 536876323 ∣ d := by
  rw [← root_order, orderOf_dvd_iff_pow_eq_one]

/-- The point-count residue from the two twist Frobenius roots in odd degree. -/
theorem odd_count_residue (d : ℕ) (hd : Odd d) :
    (1 - (-1 : ZMod 2147505293)^d) * (1 - root^d) = 0 ↔ 536876323 ∣ d := by
  rw [hd.neg_one_pow, ← root_returns]
  have unit : (1073752647 : ZMod 2147505293) * (1 - (-1)) = 1 := by decide
  constructor
  · intro h
    have h' := congrArg (fun x : ZMod 2147505293 => 1073752647 * x) h
    change 1073752647 * ((1 - (-1)) * (1 - root^d)) = 1073752647 * 0 at h'
    rw [← mul_assoc, unit, one_mul, mul_zero, sub_eq_zero] at h'
    exact h'.symm
  · intro h
    simp [h]

end M31TwistExtension
