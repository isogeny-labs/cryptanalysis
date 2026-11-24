import Mathlib.Algebra.BigOperators.Associated
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Data.Nat.Log

namespace SmoothDivisor

/-- One maximal prime power for each permitted prime. -/
def multiple (s : Finset ℕ) (cap : ℕ) : ℕ :=
  ∏ q ∈ s, q ^ Nat.log q cap

theorem dvd_multiple_iff {s : Finset ℕ} (hs : ∀ q ∈ s, Nat.Prime q)
    {n cap : ℕ} (hn : 0 < n) (hc : n ≤ cap) :
    n ∣ multiple s cap ↔ ∀ p, Nat.Prime p → p ∣ n → p ∈ s := by
  constructor
  · intro h p hp hpn
    obtain ⟨q, hq, hd⟩ := (hp.prime.dvd_finset_prod_iff _).mp (dvd_trans hpn h)
    exact (Nat.prime_dvd_prime_iff_eq hp (hs q hq)).mp (hp.dvd_of_dvd_pow hd) ▸ hq
  · intro h
    apply (Nat.dvd_iff_prime_pow_dvd_dvd _ _).mpr
    intro p k hp hd
    cases k with
    | zero => simp
    | succ k =>
      have hm := h p hp (dvd_trans (dvd_pow_self p (Nat.succ_ne_zero k)) hd)
      have he := Nat.le_log_of_pow_le hp.one_lt ((Nat.le_of_dvd hn hd).trans hc)
      exact dvd_trans (pow_dvd_pow p he) (Finset.dvd_prod_of_mem _ hm)

end SmoothDivisor
