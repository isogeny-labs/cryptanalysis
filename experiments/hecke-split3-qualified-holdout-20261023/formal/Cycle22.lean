module

public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! Rational projected row dependencies on a length-22 degree-3 cycle vanish. -/
namespace Cycle22

public theorem period_three (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x (i + 3) = x i := by
  have h0 := h i
  have h1 : x (i + 1) + x (i + 2) + x (i + 3) = 0 := by
    simpa [add_assoc] using h (i + 1)
  linarith

public theorem cycle22_trivial (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0)
    (h22 : ∀ i, x (i + 22) = x i) (i : ℤ) : x i = 0 := by
  have h21 (j : ℤ) : x (j + 21) = x j := by
    calc
      x (j + 21) = x ((j + 18) + 3) := by congr 1; ring
      _ = x (j + 18) := period_three x h (j + 18)
      _ = x ((j + 15) + 3) := by congr 1; ring
      _ = x (j + 15) := period_three x h (j + 15)
      _ = x ((j + 12) + 3) := by congr 1; ring
      _ = x (j + 12) := period_three x h (j + 12)
      _ = x ((j + 9) + 3) := by congr 1; ring
      _ = x (j + 9) := period_three x h (j + 9)
      _ = x ((j + 6) + 3) := by congr 1; ring
      _ = x (j + 6) := period_three x h (j + 6)
      _ = x ((j + 3) + 3) := by congr 1; ring
      _ = x (j + 3) := period_three x h (j + 3)
      _ = x j := period_three x h j
  have hstep (j : ℤ) : x (j + 1) = x j := by
    have hp := h22 j
    have heq : j + 22 = (j + 1) + 21 := by ring
    rw [heq] at hp
    exact (h21 (j + 1)).symm.trans hp
  have hnext := hstep i
  have hnext2 := hstep (i + 1)
  have heq : (i + 1) + 1 = i + 2 := by ring
  rw [heq] at hnext2
  linarith [h i]

end Cycle22

#print axioms Cycle22.period_three
#print axioms Cycle22.cycle22_trivial
