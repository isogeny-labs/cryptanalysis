import Mathlib.Data.Nat.Basic

namespace SmoothGeneration

/-- Removing parents outside the product bound preserves the ordered child
list, including all multiplicities. -/
theorem prune_parents {α : Type*} (parents : List ℕ) (q limit : ℕ)
    (children : ℕ → List α) (cut : ∀ x, limit < x*q → children x = []) :
    (parents.filter fun x => decide (x*q ≤ limit)).flatMap children =
      parents.flatMap children := by
  induction parents with
  | nil => rfl
  | cons x xs ih =>
    by_cases h : x*q ≤ limit
    · simp [h, ih]
    · simp [h, ih, cut x (Nat.lt_of_not_ge h)]

/-- As primes increase, a discarded parent cannot become eligible again. -/
theorem monotone_cut (x q r limit : ℕ) (h : q ≤ r) (hx : limit < x*q) :
    limit < x*r := lt_of_lt_of_le hx (Nat.mul_le_mul_left x h)

end SmoothGeneration
