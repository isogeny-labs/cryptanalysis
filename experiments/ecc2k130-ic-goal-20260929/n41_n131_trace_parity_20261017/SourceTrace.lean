import Std
import Init.Grind.Ring.Basic

namespace SourceTrace
open Lean.Grind

/-- The fixed-seed source product factors through d=1+h after substituting
    a=d*b and s=h²+h. This is valid over any commutative ring. -/
theorem fixed_seed_product {F : Type} [CommRing F] (h b : F) :
    (((1 + h) * b) ^ 2 + (h ^ 2 + h) * ((1 + h) * b)) =
      ((1 + h) ^ 2) * (b ^ 2 + h * b) := by
  grind +ring

/-- Absolute trace of the quotient b²+hb agrees with trace of a=(1+h)b
    when trace is additive and square-invariant. -/
theorem quotient_trace {F B : Type} [CommRing F] [AddCommGroup B]
    (tr : F → B)
    (trace_add : ∀ x y, tr (x + y) = tr x + tr y)
    (trace_square : ∀ x, tr (x ^ 2) = tr x)
    (h b : F) :
    tr (b ^ 2 + h * b) = tr ((1 + h) * b) := by
  calc
    tr (b ^ 2 + h * b) = tr (b ^ 2) + tr (h * b) := trace_add _ _
    _ = tr b + tr (h * b) := by rw [trace_square]
    _ = tr (b + h * b) := (trace_add _ _).symm
    _ = tr ((1 + h) * b) := congrArg tr (by grind +ring)

/-- Multiplication by the inverse square of d=1+h gives the exact quotient
    p/C, with C=d², as b²+hb for b=a/d. -/
theorem fixed_seed_quotient {F : Type} [CommRing F]
    (h a dInv : F) (dInv_spec : (1 + h) * dInv = 1) :
    (a ^ 2 + (h ^ 2 + h) * a) * dInv ^ 2 =
      (a * dInv) ^ 2 + h * (a * dInv) := by
  grind +ring

/-- Under the actual fixed-seed quotient and an additive square-invariant
    trace, the two roots differ by an element whose trace is Tr(a). -/
theorem fixed_seed_quotient_trace {F B : Type} [CommRing F] [AddCommGroup B]
    (tr : F → B)
    (trace_add : ∀ x y, tr (x + y) = tr x + tr y)
    (trace_square : ∀ x, tr (x ^ 2) = tr x)
    (h a dInv : F) (dInv_spec : (1 + h) * dInv = 1) :
    tr ((a ^ 2 + (h ^ 2 + h) * a) * dInv ^ 2) = tr a := by
  rw [fixed_seed_quotient h a dInv dInv_spec]
  rw [quotient_trace tr trace_add trace_square h (a * dInv)]
  exact congrArg tr (by grind +ring)

#print axioms fixed_seed_product
#print axioms quotient_trace
#print axioms fixed_seed_quotient
#print axioms fixed_seed_quotient_trace

end SourceTrace
