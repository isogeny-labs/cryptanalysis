import Signed

namespace M31SignedSquare

/-- A signed representative and its canonical residue return the same
smaller root, including the representation -p of zero. -/
theorem root_magnitude (x : ℤ) :
    min |x| (p - |x|) = min (canon x) (p - canon x) := by
  by_cases h : x < 0
  · rw [abs_of_neg h]
    simp only [canon, h, ↓reduceIte]
    omega
  · rw [abs_of_nonneg (le_of_not_gt h)]
    simp [canon, h]

/-- Validating one further signed square gives the same checked result
as taking the canonical 29-square candidate and testing its square. -/
theorem checked (x : ℤ) (lo : 0 ≤ x) (hi : x < p) :
    let y := step^[29] x
    let r := x ^ (2 ^ 29 : ℕ) % p
    (if canon (step y) = x then min |y| (p - |y|) else p) =
      (if r ^ 2 % p = x then min r (p - r) else p) := by
  have low : -p ≤ x := by unfold p; omega
  have closed (n : ℕ) : -p ≤ step^[n] x ∧ step^[n] x < p := by
    induction n with
    | zero => exact ⟨low, hi⟩
    | succ n ih =>
      rw [Function.iterate_succ_apply']
      have h := step_correct _ ih.1 ih.2
      exact ⟨h.1, h.2.1⟩
  dsimp only
  have hy := closed 29
  have hr := chain_correct x low hi 29
  have hs := step_correct _ hy.1 hy.2
  rw [root_magnitude _, canon_correct _ hs.1 hs.2.1, hs.2.2, hr]
  have hmod : (step^[29] x) % p = x ^ (2 ^ 29 : ℕ) % p :=
    (canon_correct _ hy.1 hy.2).symm.trans hr
  have hsq : (step^[29] x) ^ 2 % p = (x ^ (2 ^ 29 : ℕ) % p) ^ 2 % p := by
    simp only [pow_two]
    rw [Int.mul_emod (step^[29] x) (step^[29] x), hmod]
  rw [hsq]

#print axioms checked
end M31SignedSquare
