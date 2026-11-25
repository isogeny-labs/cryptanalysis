import Mathlib.GroupTheory.OrderOfElement
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace DuplicationCycles

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

def returns (m n : ℕ) := (2 : ZMod m)^n = 1 ∨ (2 : ZMod m)^n = -1

def firstReturn (m k : ℕ) := returns m k ∧ ∀ n, 0 < n → n < k → ¬returns m n

private theorem divides_double {m n : ℕ} (h : returns m n) :
    orderOf (2 : ZMod m) ∣ n*2 := by
  apply orderOf_dvd_of_pow_eq_one
  rw [pow_mul]
  rcases h with h | h <;> simp [h]

private theorem ord_2147505293 : orderOf (2 : ZMod 2147505293) = 2147505292 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by rw [← fast_eq _ 32 _ (by decide)]; decide)
  intro q hq hd
  rw [show 2147505292 = 2*2*811*661993 by decide] at hd
  simp only [hq.dvd_mul, Nat.dvd_prime (by norm_num : Nat.Prime 2), Nat.dvd_prime (by norm_num : Nat.Prime 811), Nat.dvd_prime (by norm_num : Nat.Prime 661993),hq.ne_one,false_or, or_assoc] at hd
  rcases hd with rfl | rfl | rfl | rfl <;> rw [← fast_eq _ 32 _ (by decide)] <;> decide

theorem period_2147505293 : firstReturn 2147505293 1073752646 := by
  constructor
  · unfold returns
    right
    rw [← fast_eq _ 32 _ (by decide)]
    decide
  · intro n hn hsmall ret
    have hd := divides_double ret
    rw [ord_2147505293] at hd
    omega

private theorem ord_53 : orderOf (2 : ZMod 53) = 52 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by rw [← fast_eq _ 32 _ (by decide)]; decide)
  intro q hq hd
  rw [show 52 = 2*2*13 by decide] at hd
  simp only [hq.dvd_mul, Nat.dvd_prime (by norm_num : Nat.Prime 2), Nat.dvd_prime (by norm_num : Nat.Prime 13),hq.ne_one,false_or, or_assoc] at hd
  rcases hd with rfl | rfl | rfl <;> rw [← fast_eq _ 32 _ (by decide)] <;> decide

theorem period_53 : firstReturn 53 26 := by
  constructor
  · unfold returns
    right
    rw [← fast_eq _ 32 _ (by decide)]
    decide
  · intro n hn hsmall ret
    have hd := divides_double ret
    rw [ord_53] at hd
    omega

private theorem ord_40518151 : orderOf (2 : ZMod 40518151) = 1350605 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by rw [← fast_eq _ 32 _ (by decide)]; decide)
  intro q hq hd
  rw [show 1350605 = 5*270121 by decide] at hd
  simp only [hq.dvd_mul, Nat.dvd_prime (by norm_num : Nat.Prime 5), Nat.dvd_prime (by norm_num : Nat.Prime 270121),hq.ne_one,false_or] at hd
  rcases hd with rfl | rfl <;> rw [← fast_eq _ 32 _ (by decide)] <;> decide

theorem period_40518151 : firstReturn 40518151 1350605 := by
  constructor
  · unfold returns
    left
    rw [← fast_eq _ 32 _ (by decide)]
    decide
  · intro n hn hsmall ret
    have hd := divides_double ret
    rw [ord_40518151] at hd
    have cop : Nat.Coprime 1350605 2 := by decide
    exact (Nat.not_le.mpr hsmall) (Nat.le_of_dvd hn (cop.dvd_of_dvd_mul_right hd))

private theorem ord_2147462003 : orderOf (2 : ZMod 2147462003) = 70231460 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by rw [← fast_eq _ 32 _ (by decide)]; decide)
  intro q hq hd
  rw [show 70231460 = 2*2*5*13*270121 by decide] at hd
  simp only [hq.dvd_mul, Nat.dvd_prime (by norm_num : Nat.Prime 2), Nat.dvd_prime (by norm_num : Nat.Prime 5), Nat.dvd_prime (by norm_num : Nat.Prime 13), Nat.dvd_prime (by norm_num : Nat.Prime 270121),hq.ne_one,false_or, or_assoc] at hd
  rcases hd with rfl | rfl | rfl | rfl | rfl <;> rw [← fast_eq _ 32 _ (by decide)] <;> decide

theorem period_2147462003 : firstReturn 2147462003 70231460 := by
  constructor
  · unfold returns
    left
    rw [← fast_eq _ 32 _ (by decide)]
    decide
  · intro n hn hsmall ret
    have hd := divides_double ret
    rw [ord_2147462003] at hd
    have he : n = 35115730 := by omega
    subst n
    exact (by rw [← fast_eq _ 32 35115730 (by decide)]; decide : ¬ ((2 : ZMod 2147462003)^35115730 = 1 ∨ (2 : ZMod 2147462003)^35115730 = -1)) ret

theorem signed_periods : firstReturn 2147505293 1073752646 ∧ firstReturn 53 26 ∧
    firstReturn 40518151 1350605 ∧ firstReturn 2147462003 70231460 :=
  ⟨period_2147505293, period_53, period_40518151, period_2147462003⟩

#print axioms signed_periods
end DuplicationCycles
