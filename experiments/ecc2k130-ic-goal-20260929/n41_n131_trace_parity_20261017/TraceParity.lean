import Std
import Init.Grind.Ring.Basic

namespace TraceParity
open Lean.Grind

/-- Applying an additive, square-invariant trace to the characteristic-two
    reciprocal S3 equation eliminates its product term exactly. -/
theorem s3_trace {F B : Type} [AddCommGroup F] [AddCommGroup B]
    (tr : F → B) (sq : F → F) (mul : F → F → F)
    (trace_add : ∀ x y, tr (x + y) = tr x + tr y)
    (trace_square : ∀ x, tr (sq x) = tr x)
    (trace_zero : tr 0 = 0)
    (two_zero : ∀ x : B, x + x = 0)
    (a b z : F)
    (equation : ((sq (mul (mul a b) z) + mul (mul a b) z) +
        sq (a + b)) + sq z = 0) :
    (tr a + tr b) + tr z = 0 := by
  have mapped := congrArg tr equation
  have expanded : (((tr (mul (mul a b) z) + tr (mul (mul a b) z)) +
      (tr a + tr b)) + tr z) = 0 := by
    simpa only [trace_add, trace_square, trace_zero] using mapped
  simpa only [two_zero, AddCommMonoid.zero_add] using expanded

/-- In an exponent-two additive group, an S3 trace link determines the
    trace of its output from the traces of its two inputs. -/
theorem link_output {B : Type} [AddCommGroup B]
    (two_zero : ∀ x : B, x + x = 0)
    (a b z : B) (link : (a + b) + z = 0) : z = a + b := by
  calc
    z = 0 + z := (AddCommMonoid.zero_add z).symm
    _ = ((a + b) + z) + z := by rw [link]
    _ = (a + b) + (z + z) := AddCommMonoid.add_assoc _ _ _
    _ = a + b := by rw [two_zero, AddCommMonoid.add_zero]

/-- A quadratic pair with root difference of trace zero has a trace value
    independent of the selected root.  The field-specific root difference
    and its zero trace are explicit hypotheses. -/
theorem paired_root_trace {F B : Type} [AddCommGroup F] [AddCommGroup B]
    (tr : F → B) (trace_add : ∀ x y, tr (x + y) = tr x + tr y)
    (z partner difference : F)
    (partner_eq : partner = z + difference)
    (difference_trace_zero : tr difference = 0) :
    tr partner = tr z := by
  rw [partner_eq, trace_add, difference_trace_zero, AddCommMonoid.add_zero]

/-- The four balanced five-pair S3 links imply a single parity equation
    coupling all five pair outputs directly to the public target. -/
theorem five_pair_trace {B : Type} [AddCommGroup B]
    (two_zero : ∀ x : B, x + x = 0)
    (p₀ p₁ p₂ p₃ p₄ u v w target : B)
    (h₁ : (p₀ + p₁) + u = 0)
    (h₂ : (u + p₂) + v = 0)
    (h₃ : (p₃ + p₄) + w = 0)
    (h₄ : (v + w) + target = 0) :
    ((((p₀ + p₁) + p₂) + p₃) + p₄) = target := by
  have hu : u = p₀ + p₁ := link_output two_zero p₀ p₁ u h₁
  have hv : v = u + p₂ := link_output two_zero u p₂ v h₂
  have hw : w = p₃ + p₄ := link_output two_zero p₃ p₄ w h₃
  have ht : target = v + w := link_output two_zero v w target h₄
  rw [ht, hv, hu, hw]
  exact AddCommMonoid.add_assoc ((p₀ + p₁) + p₂) p₃ p₄

#print axioms s3_trace
#print axioms link_output
#print axioms paired_root_trace
#print axioms five_pair_trace

end TraceParity
