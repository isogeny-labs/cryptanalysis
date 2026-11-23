import Mathlib.Data.Nat.Digits.Lemmas

namespace ReciprocalLifts

/-- Across the frozen orbit pairs, a displacement receives at most one
contribution per coordinate of each orbit. -/
theorem phaseCountBound (hits : List ℕ) (perOrbit : ∀ c ∈ hits, c ≤ 31)
    (pairs : hits.length ≤ 3302) : hits.sum ≤ 3302 * 31 := by
  have localBound (xs : List ℕ) (h : ∀ c ∈ xs, c ≤ 31) : xs.sum ≤ xs.length * 31 := by
    induction xs with
    | nil => simp
    | cons x xs ih =>
      have hx := h x (by simp)
      have ht := ih (fun c hc => h c (by simp [hc]))
      simp only [List.sum_cons, List.length_cons]
      omega
  exact (localBound hits perOrbit).trans (Nat.mul_le_mul_right 31 pairs)

/-- Recover a coefficient with the shift and mask used by the census prototype.
Coefficients past the end of the packed number read as zero. -/
theorem unpackPhaseDigit (counts : List ℕ) (j : ℕ)
    (bound : ∀ c ∈ counts, c ≤ 3302 * 31) :
    ((Nat.ofDigits (2^17) counts >>> (17*j)) &&& (2^17 - 1)) =
      (counts.drop j).headD 0 := by
  have fits : ∀ c ∈ counts, c < 2^17 := fun c hc =>
    lt_of_le_of_lt (bound c hc) (by decide)
  rw [Nat.and_two_pow_sub_one_eq_mod, Nat.shiftRight_eq_div_pow, pow_mul,
    Nat.ofDigits_div_pow_eq_ofDigits_drop j (by decide) counts fits,
    Nat.ofDigits_mod_eq_head!]
  cases h : counts.drop j with
  | nil => simp
  | cons c cs =>
    have hc : c ∈ counts.drop j := by simp [h]
    exact Nat.mod_eq_of_lt (fits c (List.mem_of_mem_drop hc))

/-- The coefficient from bit i on the left and reversed bit k on the right
belongs to exactly the phase i-k modulo 31. -/
theorem phaseDisplacements (i k j : Fin 31) :
    (i.val + 31 - k.val) % 31 = j.val ↔
      i.val + (31 - k.val) = j.val ∨ i.val + (31 - k.val) = 31 + j.val := by
  have := i.isLt
  have := k.isLt
  have := j.isLt
  omega

end ReciprocalLifts
