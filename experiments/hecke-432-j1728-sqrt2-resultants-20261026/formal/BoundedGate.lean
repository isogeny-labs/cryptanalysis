import Mathlib.Algebra.Polynomial.Eval.Defs

namespace J1728BoundedGate

open Polynomial

/-- The final structural step of the reduction gate. The arithmetic
    certificate supplies the two root-exclusion hypotheses after reduction. -/
theorem no_root_of_two_excluded_pairs
    {F : Type*} [Field F] (u q₂ q₂' q₄ q₄' : F[X]) (x : F)
    (unit_nonzero : u.eval x ≠ 0)
    (quadratic_pair_nonzero : (q₂ * q₂').eval x ≠ 0)
    (quartic_pair_nonzero : (q₄ * q₄').eval x ≠ 0) :
    (u * (q₂ * q₂') * (q₄ * q₄')).eval x ≠ 0 := by
  simp only [eval_mul]
  exact mul_ne_zero
    (mul_ne_zero unit_nonzero (by simpa only [eval_mul] using quadratic_pair_nonzero))
    (by simpa only [eval_mul] using quartic_pair_nonzero)

#print axioms no_root_of_two_excluded_pairs

end J1728BoundedGate
