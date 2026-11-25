import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Data.Nat.Log
import Mathlib.Tactic

namespace SmoothDivisor

/-- A multiple with sufficient exponents on the allowed primes and no
exponents outside them recognizes smooth representatives by divisibility. -/
theorem recognizes (x M B : ℕ) (hx : x ≠ 0) (hM : M ≠ 0)
    (inside : ∀ q ≤ B, x.factorization q ≤ M.factorization q)
    (outside : ∀ q > B, M.factorization q = 0) :
    x ∣ M ↔ ∀ q > B, x.factorization q = 0 := by
  rw [← Nat.factorization_le_iff_dvd hx hM]
  constructor
  · intro h q hq
    exact Nat.eq_zero_of_le_zero ((outside q hq) ▸ h q)
  · intro h q
    by_cases hq : q ≤ B
    · exact inside q hq
    · rw [h q (Nat.lt_of_not_ge hq)]
      exact Nat.zero_le _

def primesThrough (B : ℕ) : Finset ℕ := (Finset.range (B+1)).filter Nat.Prime

def multiple (B L : ℕ) := ∏ q ∈ primesThrough B, q ^ Nat.log q L

theorem concrete_recognizes (x B L : ℕ) (hx : x ≠ 0) (hL : x ≤ L) :
    x ∣ multiple B L ↔ ∀ q > B, x.factorization q = 0 := by
  have prime_mem : ∀ q ∈ primesThrough B, Nat.Prime q :=
    fun q h => (Finset.mem_filter.mp h).2
  have hn : ∀ q ∈ primesThrough B, q ^ Nat.log q L ≠ 0 :=
    fun q h => pow_ne_zero _ (prime_mem q h).ne_zero
  apply recognizes x _ B hx (Finset.prod_ne_zero_iff.mpr hn)
  · intro q hq
    by_cases hp : Nat.Prime q
    · have hm : q ∈ primesThrough B := Finset.mem_filter.mpr
          ⟨Finset.mem_range.mpr (Nat.lt_succ_of_le hq), hp⟩
      have hdiv : q ^ Nat.log q L ∣ multiple B L :=
        Finset.dvd_prod_of_mem _ hm
      have hpow : q ^ x.factorization q ≤ L :=
        (Nat.le_of_dvd (Nat.pos_of_ne_zero hx) (Nat.ordProj_dvd x q)).trans hL
      have hsmall := Nat.le_log_of_pow_le hp.one_lt hpow
      have hle := (Nat.factorization_le_iff_dvd (hn q hm)
                    (Finset.prod_ne_zero_iff.mpr hn)).mpr hdiv q
      exact hsmall.trans (by simpa [hp.factorization_pow] using hle)
    · simp [Nat.factorization_eq_zero_of_not_prime x hp]
  · intro q hq
    rw [Nat.factorization_prod_apply hn]
    apply Finset.sum_eq_zero
    intro r hr
    have hrB := Finset.mem_range.mp (Finset.mem_filter.mp hr).1
    have hne : r ≠ q := by omega
    simp [(prime_mem r hr).factorization_pow, hne]

def benchmarkValue : ℕ := 625216672325643829086928172522075709771768859842051162592817191554914256179360444986969089092581735436451111039576130140224439785963991645417779262178493464554701209800196087968805648203650861667615952517160883839948564013165610447131761473189223307010652196977782195933603199273417600860246529957294261773458283932217789377077340663364667704962799094624537266240673711783936000000000000

set_option maxRecDepth 10000 in
theorem benchmark_value : multiple 211 (2^30-1) = benchmarkValue := by decide +kernel

theorem benchmark_recognizes (x : ℕ) (hx : x ≠ 0) (hL : x ≤ 2^30-1) :
    x ∣ benchmarkValue ↔ ∀ q > 211, x.factorization q = 0 := by
  rw [← benchmark_value]
  exact concrete_recognizes x 211 _ hx hL

theorem benchmark_remainder (x : ℕ) (hx : x ≠ 0) (hL : x ≤ 2^30-1) :
    benchmarkValue % x = 0 ↔ ∀ q : ℕ, q.Prime → q ∣ x → q ≤ 211 := by
  rw [← Nat.dvd_iff_mod_eq_zero, benchmark_recognizes x hx hL]
  constructor
  · intro h q hp hd
    by_contra! hq
    have hpos := hp.factorization_pos_of_dvd hx hd
    rw [h q hq] at hpos
    omega
  · intro h q hq
    by_cases hp : q.Prime
    · by_contra hn
      exact (Nat.not_le_of_gt hq) (h q hp (Nat.dvd_of_factorization_pos hn))
    · exact Nat.factorization_eq_zero_of_not_prime x hp

end SmoothDivisor
