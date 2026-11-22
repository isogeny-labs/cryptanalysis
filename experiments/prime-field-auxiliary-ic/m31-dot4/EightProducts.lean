import Mathlib.Tactic
theorem bias_ok (s : ℤ) (hlo : -(8*1073741823^2) ≤ s) (hhi : s ≤ 8*1073741823^2) :
    -(2^63) ≤ s ∧ s < 2^63 ∧ 0 ≤ s+2147483647*2^32 ∧
    s+2147483647*2^32 < 2^64 ∧
    (s+2147483647*2^32)%2147483647 = s%2147483647 := by omega
theorem ninth_overflows : (2^63 : ℤ) ≤ 9*1073741823^2 := by decide
theorem carry_fold (s : ℕ) (h : s ≤ 8*2147483646^2) :
    let r := if s < 2^64 then s else s-2^64+4
    r < 2^64 ∧ r%2147483647 = s%2147483647 := by
  dsimp
  split <;> omega

/-- The unsigned comparison in the C kernel detects a lost high bit. -/
theorem word_carry_test (a b : UInt64) :
    a + b < a ↔ 2^64 ≤ a.toNat + b.toNat := by
  rw [UInt64.lt_iff_toNat_lt, UInt64.toNat_add]
  have ha := a.toNat_lt
  have hb := b.toNat_lt
  omega

/-- The word-level correction and final remainder return the natural sum modulo M31. -/
theorem word_carry_reduce (a b : UInt64) (h : a.toNat+b.toNat ≤ 8*2147483646^2) :
    ((a+b+(if a+b<a then 4 else 0)) % 2147483647).toNat =
      (a.toNat+b.toNat)%2147483647 := by
  by_cases carry : a+b<a
  · have wrap := (word_carry_test a b).mp carry
    simp only [if_pos carry, UInt64.toNat_mod, UInt64.toNat_add]
    change (((a.toNat+b.toNat)%2^64+4)%2^64)%2147483647 = _
    omega
  · have nowrap := mt (word_carry_test a b).mpr carry
    simp only [if_neg carry, UInt64.toNat_mod, UInt64.toNat_add]
    change (((a.toNat+b.toNat)%2^64+0)%2^64)%2147483647 = _
    omega
