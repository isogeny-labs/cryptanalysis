import Mathlib.NumberTheory.SmoothNumbers
import Mathlib.Data.ZMod.Basic

namespace OddOrbit

abbrev p := 2147483647
abbrev F := ZMod p

/-- Every smooth representative in the orbit has an odd smooth divisor
with the same orbit key, still inside the canonical field range. -/
theorem odd_representative (x : F) (b : ℕ) :
    (∃ n : ℕ, n < p ∧ (n:F)^31 = x^31 ∧ n ∈ Nat.smoothNumbers (b+1)) ↔
    (∃ m : ℕ, Odd m ∧ m < p ∧ (m:F)^31 = x^31 ∧ m ∈ Nat.smoothNumbers (b+1)) := by
  constructor
  · rintro ⟨n,hn,hkey,hs⟩
    obtain ⟨k,m,hm,he⟩ := Nat.exists_eq_two_pow_mul_odd hs.1
    have hd : m ∣ n := ⟨2^k, by simpa [mul_comm] using he⟩
    refine ⟨m, hm, lt_of_le_of_lt (Nat.le_of_dvd (Nat.pos_of_ne_zero hs.1) hd) hn,
      ?_, Nat.mem_smoothNumbers_of_dvd hs hd⟩
    rw [he, Nat.cast_mul, Nat.cast_pow, Nat.cast_ofNat, mul_pow, ← pow_mul,
      Nat.mul_comm k 31, pow_mul, show (2:F)^31 = 1 by decide, one_pow, one_mul] at hkey
    exact hkey
  · rintro ⟨m,_,hm,hkey,hs⟩
    exact ⟨m,hm,hkey,hs⟩

end OddOrbit
#print axioms OddOrbit.odd_representative
