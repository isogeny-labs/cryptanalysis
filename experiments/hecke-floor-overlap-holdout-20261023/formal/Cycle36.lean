module

public import Mathlib.Tactic.Linarith
public import Mathlib.Tactic.Ring
public import Mathlib.Algebra.Ring.Rat

/-! The rational recurrence underlying degree-3 projected Hecke cycles. -/
namespace Cycle36

public theorem period_three (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x (i + 3) = x i := by
  have h0 := h i
  have h1 : x (i + 1) + x (i + 2) + x (i + 3) = 0 := by
    simpa [add_assoc] using h (i + 1)
  linarith

public theorem third_value (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x (i + 2) = -x i - x (i + 1) := by
  linarith [h i]

public theorem period_three_mul (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0)
    (n : ℕ) (i : ℤ) : x (i + 3 * (n : ℤ)) = x i := by
  induction n with
  | zero => simp
  | succ n ih =>
      calc
        x (i + 3 * ((n + 1 : ℕ) : ℤ)) = x ((i + 3 * (n : ℤ)) + 3) := by
          congr 1
          push_cast
          ring
        _ = x (i + 3 * (n : ℤ)) := period_three x h (i + 3 * (n : ℤ))
        _ = x i := ih

public theorem cycle36_periodic (x : ℤ → ℚ)
    (h : ∀ i, x i + x (i + 1) + x (i + 2) = 0) (i : ℤ) :
    x (i + 36) = x i := by
  simpa using period_three_mul x h 12 i

end Cycle36

#print axioms Cycle36.period_three
#print axioms Cycle36.third_value
#print axioms Cycle36.period_three_mul
#print axioms Cycle36.cycle36_periodic
