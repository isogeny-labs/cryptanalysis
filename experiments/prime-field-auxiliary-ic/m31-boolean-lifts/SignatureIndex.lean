import Mathlib

namespace SmoothSignatureIndex

/-- A high half-product h accepts a low half-product l precisely up to
floor((p-1)/h). Both products are positive integers. -/
theorem compatible (h l : ℕ) (positive : 0 < h) :
    h*l < 2147483647 ↔ l ≤ 2147483646/h := by
  rw [Nat.le_div_iff_mul_le positive, Nat.mul_comm l h]
  omega

/-- Saturating a product at p does not change any feasibility test whose
other factor is positive. -/
theorem saturate (x y : ℕ) (hy : 0 < y) :
    min x 2147483647 * y < 2147483647 ↔ x*y < 2147483647 := by
  by_cases hx : x ≤ 2147483647
  · rw [min_eq_left hx]
  · rw [min_eq_right (by omega : 2147483647 ≤ x)]
    have ha := Nat.mul_le_mul_left 2147483647 hy
    have hb := Nat.mul_le_mul_left x hy
    simp only [Nat.mul_one] at ha hb
    omega

/-- Offsets delimit disjoint intervals, so the packed ID identifies both
components of every feasible signature. -/
theorem packInjective (offset : ℕ → ℕ) (mono : Monotone offset)
    {a b i j : ℕ} (hi : offset a + i < offset (a+1))
    (hj : offset b + j < offset (b+1)) (eq : offset a + i = offset b + j) :
    a = b ∧ i = j := by
  have hab : a = b := by
    rcases lt_trichotomy a b with h | h | h
    · have := mono (show a+1 ≤ b by omega); omega
    · exact h
    · have := mono (show b+1 ≤ a by omega); omega
  exact ⟨hab, by simpa [hab] using eq⟩

end SmoothSignatureIndex
