import Mathlib.Algebra.Polynomial.Eval.Defs
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace J1728SquareThreeGate

open Polynomial

/-- An evaluated integer-polynomial certificate `P² - 3D² = fH` excludes a
    root of `f` over a field where `3` is nonsquare and `D` stays nonzero. -/
theorem no_eliminant_root_from_sqrt_three_certificate
    {F : Type*} [Field F]
    (f P H : F[X]) (d : F)
    (certificate : P * P - C ((3 : F) * d * d) = f * H)
    (d_ne_zero : d ≠ 0)
    (three_nonsquare : ∀ s : F, s * s ≠ 3)
    (x : F) : f.eval x ≠ 0 := by
  intro root
  have evaluated := congrArg (fun q : F[X] => q.eval x) certificate
  simp only [eval_sub, eval_mul, eval_C, root, zero_mul] at evaluated
  have product_eq : P.eval x * P.eval x = (3 : F) * d * d := sub_eq_zero.mp evaluated
  have scaled_square : (P.eval x * d⁻¹) * (P.eval x * d⁻¹) = (3 : F) := by
    calc
      _ = (P.eval x * P.eval x) * (d⁻¹ * d⁻¹) := by ring
      _ = ((3 : F) * d * d) * (d⁻¹ * d⁻¹) := by rw [product_eq]
      _ = 3 := by field_simp [d_ne_zero]
  exact three_nonsquare _ scaled_square

/-- The C-curve equation forces its quadratic y-discriminant to be a square. -/
theorem curve_discriminant_is_square
    {F : Type*} [CommRing F] (x y : F)
    (on_curve : y * y + y = x * x * x - 7) :
    (2 * y + 1) * (2 * y + 1) = 4 * x * x * x - 27 := by
  calc
    (2 * y + 1) * (2 * y + 1) = 4 * (y * y + y) + 1 := by ring
    _ = 4 * (x * x * x - 7) + 1 := by rw [on_curve]
    _ = 4 * x * x * x - 27 := by ring

#print axioms no_eliminant_root_from_sqrt_three_certificate
#print axioms curve_discriminant_is_square

end J1728SquareThreeGate
