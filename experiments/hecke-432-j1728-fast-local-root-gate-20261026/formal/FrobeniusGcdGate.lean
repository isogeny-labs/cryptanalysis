import Mathlib.Algebra.Polynomial.FieldDivision

namespace J1728FastLocalGate

open Polynomial

/-- When `q`-power Frobenius fixes the coefficient field, the gcd with
    `X ^ q - X` has exactly the rational roots of `R`. -/
theorem frobenius_gcd_root_iff
    {F : Type*} [Field F] [DecidableEq F]
    (q : ℕ) (fixed : ∀ x : F, x ^ q = x)
    (R : F[X]) (x : F) :
    (EuclideanDomain.gcd R (X ^ q - X)).eval x = 0 ↔
      R.eval x = 0 := by
  change (EuclideanDomain.gcd R (X ^ q - X)).IsRoot x ↔ R.IsRoot x
  rw [isRoot_gcd_iff_isRoot_left_right]
  simp [eval_sub, eval_pow, fixed x]

#print axioms frobenius_gcd_root_iff

end J1728FastLocalGate
