import Mathlib.NumberTheory.SmoothNumbers
import Mathlib.Data.Nat.Log
import Mathlib.Algebra.BigOperators.Associated

namespace FiberMembership

/-- Largest needed power of every permitted prime, for inputs up to N. -/
def multiple (N b : ℕ) := ∏ q ∈ (b+1).primesBelow, q ^ Nat.log q N

theorem test {n N b : ℕ} (hn : 0 < n) (hN : n ≤ N) :
    n ∈ Nat.smoothNumbers (b+1) ↔ n ∣ multiple N b := by
  constructor
  · intro hs
    apply (Nat.dvd_iff_prime_pow_dvd_dvd _ _).mpr
    intro q k hq hpow
    cases k with
    | zero => simp
    | succ k =>
      have hqn := (dvd_pow_self q (Nat.succ_ne_zero k)).trans hpow
      have hsmall := Nat.mem_smoothNumbers'.mp hs q hq hqn
      have hmem := Nat.mem_primesBelow.mpr ⟨hsmall, hq⟩
      have hlog := Nat.le_log_of_pow_le hq.one_lt ((Nat.le_of_dvd hn hpow).trans hN)
      exact (pow_dvd_pow q hlog).trans (Finset.dvd_prod_of_mem (fun r => r ^ Nat.log r N) hmem)
  · intro h
    apply Nat.mem_smoothNumbers'.mpr
    intro q hq hqn
    obtain ⟨r, hr, hd⟩ := (hq.prime.dvd_finsetProd_iff _).mp (hqn.trans h)
    have heq := (Nat.prime_dvd_prime_iff_eq hq (Nat.mem_primesBelow.mp hr).2).mp
      (hq.dvd_of_dvd_pow hd)
    exact heq ▸ (Nat.mem_primesBelow.mp hr).1

set_option maxRecDepth 65536 in
/-- Concrete divisibility constants for the two measured bounds. -/
theorem m31_constants :
    multiple 2147483646 89 = 0x7891a0b4745e4f8f8e34b5b7012a732f43be67cf1cf032b12f0af61ce07e50fe63a59c6d75198ff58bcc4b2bfd38261fca1ade0d857964ce0156215c92e774da88ef141d4b94b387a50263bb9bfc3ae293a340000000 ∧
    multiple 2147483646 211 = 0x2434cfedec86ccb3568700d17e441524d14e609a0b591987eed89003735201f556f36271e356e698fa09c6ba0a3120cdb9c5a48e0eed3a88f32ded000269b3993e6a596a97e5f620aec260507b07a41b48b82c3971b68aac19f8aeba19c3afb29b393a68282f591a88b05f83a4d5584588859fdf3d182df808671dbe815967b463ca103f283ab7acb8e67e0fa4b9629eb0a8b0cfe558e96cb69b3e62e4655e70ce3fa080ef40000000 := by
  decide +kernel

end FiberMembership
#print axioms FiberMembership.test
#print axioms FiberMembership.m31_constants
