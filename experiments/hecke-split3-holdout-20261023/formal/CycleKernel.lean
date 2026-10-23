module

public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! The local recurrence behind the conductor-2 degree-3 cycle kernel. -/
namespace CycleKernel

public theorem period_three (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x (i + 3) = x i := by
  have h0 := h i
  have h1 : x (i + 1) + x (i + 2) + x (i + 3) = 0 := by
    simpa [add_assoc] using h (i + 1)
  linarith

public theorem cycle14_trivial (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0)
    (h14 : ∀ i, x (i + 14) = x i) (i : ℤ) : x i = 0 := by
  have h15 (j : ℤ) : x (j + 15) = x j := by
    calc
      x (j + 15) = x ((j + 12) + 3) := by congr 1; ring
      _ = x (j + 12) := period_three x h (j + 12)
      _ = x ((j + 9) + 3) := by congr 1; ring
      _ = x (j + 9) := period_three x h (j + 9)
      _ = x ((j + 6) + 3) := by congr 1; ring
      _ = x (j + 6) := period_three x h (j + 6)
      _ = x ((j + 3) + 3) := by congr 1; ring
      _ = x (j + 3) := period_three x h (j + 3)
      _ = x j := period_three x h j
  have hstep (j : ℤ) : x (j + 1) = x j := by
    have hp := h14 (j + 1)
    have heq : (j + 1) + 14 = j + 15 := by ring
    rw [heq] at hp
    exact hp.symm.trans (h15 j)
  have hnext := hstep i
  have hnext2 := hstep (i + 1)
  have heq : (i + 1) + 1 = i + 2 := by ring
  rw [heq] at hnext2
  linarith [h i]

end CycleKernel

#print axioms CycleKernel.period_three
#print axioms CycleKernel.cycle14_trivial
