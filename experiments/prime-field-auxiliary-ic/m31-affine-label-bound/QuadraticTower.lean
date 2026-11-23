import Mathlib

set_option backward.isDefEq.respectTransparency false

namespace M31QuadraticTower

abbrev p : ℕ := 2147483647

/-- Standard doubling of a point count: if N = q+1-t, the count over
the quadratic extension is N*(q+1+t). Here q = p^(2^k). -/
def count (n : ℕ) : ℕ → ℤ
  | 0 => n
  | k+1 => count n k * (2*((p : ℤ)^(2^k)+1) - count n k)

theorem noMinusOne {n : ℕ} [Fact n.Prime] (a : ZMod n) (ha : a ≠ 0)
    (e m : ℕ) (factor : e*m = n-1) (he : Even e) (hm : Odd m)
    (nontrivial : a^e ≠ 1) (k : ℕ) : a^(2^k) ≠ -1 := by
  intro bad
  have period : (a^e)^m = 1 := by rw [← pow_mul, factor, ZMod.pow_card_sub_one_eq_one ha]
  have binary : (a^e)^(2^k) = 1 := by
    rw [← pow_mul, Nat.mul_comm e, pow_mul, bad]
    exact he.neg_one_pow
  have h1 := orderOf_dvd_iff_pow_eq_one.mpr period
  have h2 := orderOf_dvd_iff_pow_eq_one.mpr binary
  have one := Nat.dvd_one.mp (hm.coprime_two_right.pow_right k ▸ Nat.dvd_gcd h1 h2)
  exact nontrivial (orderOf_eq_one_iff.mp one)

theorem multiplicityOne {n : ℕ} [Fact n.Prime] (two : (2 : ZMod n) ≠ 0)
    (avoid : ∀ k : ℕ, (p : ZMod n)^(2^k) ≠ -1) (k : ℕ) :
    ∃ c : ℤ, count n k = n*c ∧ (c : ZMod n) ≠ 0 := by
  induction k with
  | zero => exact ⟨1, by simp [count], by simp⟩
  | succ k ih =>
    obtain ⟨c,hc,hn⟩ := ih
    refine ⟨c*(2*((p : ℤ)^(2^k)+1) - count n k), ?_, ?_⟩
    · rw [count, hc]; ring
    · have hq : (p : ZMod n)^(2^k)+1 ≠ 0 := by
        intro h
        exact avoid k (eq_neg_of_add_eq_zero_left h)
      rw [hc]
      push_cast
      simp only [ZMod.natCast_self, zero_mul, sub_zero]
      exact mul_ne_zero hn (mul_ne_zero two hq)

theorem first (k : ℕ) :
    ∃ c : ℤ, count 2147505293 k = 2147505293*c ∧ (c : ZMod 2147505293) ≠ 0 := by
  let : Fact (Nat.Prime 2147505293) := ⟨by native_decide⟩
  apply multiplicityOne (by decide)
  exact noMinusOne _ (by decide) 4 536876323 (by decide) (by decide) (by decide) (by decide)

theorem second (k : ℕ) :
    ∃ c : ℤ, count 2147506201 k = 2147506201*c ∧ (c : ZMod 2147506201) ≠ 0 := by
  let : Fact (Nat.Prime 2147506201) := ⟨by native_decide⟩
  apply multiplicityOne (by decide)
  exact noMinusOne _ (by decide) 8 268438275 (by decide) (by decide) (by decide) (by decide)

end M31QuadraticTower
