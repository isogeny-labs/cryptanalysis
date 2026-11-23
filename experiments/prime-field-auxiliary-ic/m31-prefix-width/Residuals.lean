import Mathlib

/-- Distinct normalized residual signatures force distinct states even if
the state carries an additional output-complement flag. -/
theorem residual_state_injective {P S : Type*} (state : P → S)
    (flag : P → Bool) (value : S → BitVec 64) (sig : P → BitVec 64)
    (rep : ∀ p, sig p = if flag p then ~~~(value (state p)) else value (state p))
    (separates : ∀ p q, sig p = sig q ∨ sig p = ~~~(sig q) → p = q) :
    Function.Injective state := by
  intro p q h
  apply separates
  rw [rep p, rep q, h]
  cases flag p <;> cases flag q <;> simp

/-- A k-bit prefix requires at least 2^k states when its signatures separate. -/
theorem residual_width {k : ℕ} {S : Type*} [Fintype S] (state : Fin (2^k) → S)
    (flag : Fin (2^k) → Bool) (value : S → BitVec 64) (sig : Fin (2^k) → BitVec 64)
    (rep : ∀ p, sig p = if flag p then ~~~(value (state p)) else value (state p))
    (separates : ∀ p q, sig p = sig q ∨ sig p = ~~~(sig q) → p = q) :
    2^k ≤ Fintype.card S := by
  simpa using Fintype.card_le_of_injective state
    (residual_state_injective state flag value sig rep separates)
