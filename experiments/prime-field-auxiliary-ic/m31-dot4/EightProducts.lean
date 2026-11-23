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

/-- Two full 64-bit partial sums fit after separate 31-bit folds.
One more fold and one conditional subtraction yield the canonical residue. -/
theorem deferred_fold (s t : ℕ) (hs : s < 2^64) (ht : t < 2^64) :
    let u := s%2^31 + s/2^31 + t%2^31 + t/2^31
    let v := u%2^31 + u/2^31
    u < 2^35 ∧ v < 2*2147483647 ∧
      (if v ≥ 2147483647 then v-2147483647 else v) = (s+t)%2147483647 := by
  dsimp
  split <;> omega

/-- NEON widening multiply-add groups even and odd columns into separate lanes.
The column arguments are natural products of two canonical M31 residues. -/
theorem neon_lane_fold (a b c d e f g h : ℕ)
    (bounds : ∀ x ∈ [a,b,c,d,e,f,g,h], x ≤ 2147483646^2) :
    let s := a+c+e+g
    let t := b+d+f+h
    let u := s%2^31 + s/2^31 + (t%2^31 + t/2^31)
    let v := u%2^31 + u/2^31
    s < 2^64 ∧ t < 2^64 ∧ u < 2^35 ∧ v < 2^32 ∧
      (if v ≥ 2147483647 then v-2147483647 else v) =
        (a+b+c+d+e+f+g+h)%2147483647 := by
  simp only [List.mem_cons, List.not_mem_nil, or_false, forall_eq_or_imp,
    forall_eq] at bounds
  dsimp
  have hs : a+c+e+g < 2^64 := by omega
  have ht : b+d+f+h < 2^64 := by omega
  have result := deferred_fold _ _ hs ht
  dsimp at result
  rw [← Nat.add_assoc] at *
  exact ⟨hs, ht, by omega, by omega, by convert result.2.2 using 1; omega⟩
