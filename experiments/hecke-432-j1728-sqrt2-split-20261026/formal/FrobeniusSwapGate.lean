import Mathlib.Algebra.Polynomial.Eval.Defs

namespace J1728Sqrt2Split

open Polynomial

/-- A fixed point cannot be a root of a product of coprime factors that are
    exchanged by a coefficient automorphism. In the finite-field application,
    the automorphism is Frobenius on `Fₚ²` and the fixed points are `Fₚ`. -/
theorem no_fixed_root_of_swapped_coprime_factors
    {E : Type*} [Field E]
    (sigma : E →+* E)
    (q0 q1 u v : E[X])
    (swap01 : q1 = q0.map sigma)
    (swap10 : q0 = q1.map sigma)
    (bezout : u * q0 + v * q1 = 1)
    (x : E) (fixed : sigma x = x) :
    (q0 * q1).eval x ≠ 0 := by
  intro root
  have product_zero : q0.eval x * q1.eval x = 0 := by
    simpa [eval_mul] using root
  have h0h1 : q0.eval x = 0 ∧ q1.eval x = 0 := by
    rcases mul_eq_zero.mp product_zero with h0 | h1
    · have h1' : q1.eval x = 0 := by
        rw [swap01, ← fixed, eval_map_apply]
        simp [h0]
      exact ⟨h0, h1'⟩
    · have h0' : q0.eval x = 0 := by
        rw [swap10, ← fixed, eval_map_apply]
        simp [h1]
      exact ⟨h0', h1⟩
  have one_zero := congrArg (fun q : E[X] => q.eval x) bezout
  simp [eval_add, eval_mul, h0h1.1, h0h1.2] at one_zero

#print axioms no_fixed_root_of_swapped_coprime_factors

end J1728Sqrt2Split
