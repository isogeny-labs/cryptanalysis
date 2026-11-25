import Mathlib.Tactic

namespace M31SignedSquare
abbrev p : ℤ := 2147483647
def step (x : ℤ) := x*x / 2147483648 - (p - x*x % 2147483648)
def canon (x : ℤ) := if x < 0 then x+p else x

/-- The signed fold fits a signed word, is closed under another square, and
represents the canonical square modulo the Mersenne prime. -/
theorem step_correct (x : ℤ) (ha : -p ≤ x) (hb : x < p) :
    -p ≤ step x ∧ step x < p ∧ step x % p = x^2 % p := by
  have hbound : x*x ≤ p*p := by
    nlinarith [mul_nonneg (show 0 ≤ p+x by omega) (show 0 ≤ p-x by omega)]
  have hpos : 0 ≤ x*x := mul_self_nonneg x
  have hdiv := Int.emod_add_mul_ediv (x*x) 2147483648
  unfold step p at *
  rw [pow_two]
  omega

theorem canon_correct (x : ℤ) (ha : -p ≤ x) (hb : x < p) :
    canon x = x % p := by
  unfold canon p at *
  split <;> omega

/-- Repeated squaring needs one canonicalization after the entire chain. -/
theorem chain_correct (x : ℤ) (ha : -p ≤ x) (hb : x < p) (n : ℕ) :
    canon (step^[n] x) = x^(2^n) % p := by
  have loop : ∀ i : ℕ, -p ≤ step^[i] x ∧ step^[i] x < p ∧
      (step^[i] x) % p = x^(2^i) % p := by
    intro i
    induction i with
    | zero => simp [ha,hb]
    | succ i ih =>
      rw [Function.iterate_succ_apply', pow_succ (2:ℕ), pow_mul]
      obtain ⟨l,u,h⟩ := step_correct _ ih.1 ih.2.1
      refine ⟨l,u,h.trans ?_⟩
      simp only [pow_two]
      rw [Int.mul_emod, ih.2.2, ← Int.mul_emod]
  obtain ⟨l,u,h⟩ := loop n
  exact (canon_correct _ l u).trans h
end M31SignedSquare
