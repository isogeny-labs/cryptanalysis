import Std.Tactic
set_option autoImplicit false
namespace NormArithmetic
open Lean.Grind

/-- Multiplication by the conjugate gives the quadratic norm and zero imaginary
part. The parameter n is the square of the adjoining basis element. -/
theorem conjugate_product {R : Type} [CommRing R] (n a b : R) :
    a*a+n*b*(-b) = a^2-n*b^2 ∧ a*(-b)+b*a = 0 := by
  grind

/-- The inverse coefficient formula, conditional on a genuine inverse of the
norm. No field construction, nonzero test or integer encoding is assumed. -/
theorem scaled_conjugate_inverse {R : Type} [CommRing R]
    (n a b t : R) (h : (a^2-n*b^2)*t = 1) :
    a*(a*t)+n*b*(-(b*t)) = 1 ∧
      a*(-(b*t))+b*(a*t) = 0 := by
  grind

/-- Its norm is the selected inverse t of the original norm. -/
theorem inverse_pair_norm {R : Type} [CommRing R]
    (n a b t : R) (h : (a^2-n*b^2)*t = 1) :
    (a*t)^2-n*(-(b*t))^2 = t := by
  grind

end NormArithmetic
#print axioms NormArithmetic.conjugate_product
#print axioms NormArithmetic.scaled_conjugate_inverse
#print axioms NormArithmetic.inverse_pair_norm
